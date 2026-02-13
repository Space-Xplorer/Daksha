"""
Production OCR service with OCR.space API and optional Tesseract fallback.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import logging
import os
import json
import mimetypes
import threading
import urllib.request
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)

class ProductionOCRService:
    """Production OCR service using OCR.space with optional Tesseract fallback."""

    FIELD_PATTERNS = {
        "cibil_score": r"(?:CIBIL|Credit)\s*Score[:\s]*(\d{3})",
        "monthly_income": r"(?:Gross|Net)\s*(?:Salary|Income)[:\s]*₹?\s*([\d,]+)",
        "annual_income": r"(?:Total|Gross|Annual)\s*Income[:\s]*₹?\s*([\d,]+)",
        "hba1c": r"HbA1c[:\s]*([\d.]+)\s*%",
        "cholesterol": r"(?:Total\s*)?Cholesterol[:\s]*([\d.]+)\s*mg/dL",
        "blood_sugar": r"Blood\s*Sugar[:\s]*(?:\(Fasting\))?\s*([\d.]+)\s*mg/dL",
        "height": r"Height[:\s]*([\d.]+)\s*(?:cm|CM)",
        "weight": r"Weight[:\s]*([\d.]+)\s*(?:kg|KG)",
        "blood_pressure": r"(?:Blood\s*Pressure|BP)[:\s]*(\d{2,3})/(\d{2,3})",
        "heart_rate": r"Heart\s*Rate[:\s]*(\d{2,3})\s*bpm",
        "bank_balance": r"(?:Average|Closing)\s*Balance[:\s]*₹?\s*([\d,]+)",
        "property_value": r"(?:Market|Assessed)\s*Value[:\s]*₹?\s*([\d,]+)",
        "date": r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        "name": r"(?:Name|Full\s*Name)[:\s]*([A-Za-z\s]+)",
        "gender": r"(?:Gender|Sex)[:\s]*(Male|Female|M|F|Other)",
        "aadhaar_number": r"(?:Aadhaar|Aadhar)[:\s]*(\d{4}\s*\d{4}\s*\d{4})",
        "pan_number": r"(?:PAN|Permanent\s*Account\s*Number)[:\s]*([A-Z]{5}\d{4}[A-Z])",
        "passport_number": r"(?:Passport\s*(?:No|Number))[:\s]*([A-Z0-9]{6,9})",
        "voter_id_number": r"(?:EPIC|Voter\s*ID)[:\s]*([A-Z]{3}\d{7})"
    }
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize production OCR service."""
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')

        self.ocr_key = os.getenv('OCR_KEY')
        self.ocr_api_url = os.getenv('OCR_API_URL', 'https://api.ocr.space/parse/image')
        self.ocr_language = os.getenv('OCR_LANGUAGE', 'eng')
        self.ocr_engine = os.getenv('OCR_ENGINE', '1')
        self.ocr_timeout = self._safe_int_env('OCR_API_TIMEOUT', 30)
        self.ocr_monthly_limit = self._safe_int_env('OCR_MONTHLY_LIMIT', 25000)

        self._usage_lock = threading.Lock()
        self._usage_path = self._resolve_usage_path(os.getenv('OCR_USAGE_PATH'))

        self.tesseract_available = False
        tesseract_path = os.getenv('TESSERACT_PATH')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        if not self.ocr_key:
            self._init_tesseract()
        else:
            logger.info("OCR.space key detected, using OCR.space API as primary OCR")

    def _safe_int_env(self, name: str, default: int) -> int:
        value = os.getenv(name)
        if value is None or value == "":
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid value for {name}, using default {default}")
            return default
    
    def extract_text(self, file_path: str, preprocess: bool = True) -> str:
        """
        Extract text from document using OCR.space or Tesseract fallback.

        Args:
            file_path: Path to document (PDF or image)
            preprocess: Whether to preprocess image for Tesseract

        Returns:
            Extracted text
        """
        if self.ocr_key:
            try:
                return self._extract_text_with_ocr_space(file_path)
            except Exception as e:
                logger.warning(f"OCR.space failed for {file_path}: {e}")
                if not self.tesseract_available:
                    self._init_tesseract()
                if self.tesseract_available:
                    return self._extract_text_with_tesseract(file_path, preprocess)
                raise

        if not self.tesseract_available:
            raise RuntimeError("No OCR provider available. Set OCR_KEY or install Tesseract.")

        return self._extract_text_with_tesseract(file_path, preprocess)

    def _init_tesseract(self) -> None:
        """Initialize Tesseract if available."""
        try:
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

    def _extract_text_with_tesseract(self, file_path: str, preprocess: bool) -> str:
        """Extract text using Tesseract OCR."""
        try:
            if file_path.lower().endswith('.pdf'):
                images = convert_from_path(file_path, dpi=300)
                image = images[0]
            else:
                image = Image.open(file_path)

            img_array = np.array(image)
            if preprocess:
                img_array = self._preprocess_image(img_array)

            data = pytesseract.image_to_data(
                img_array,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )

            text = ' '.join([
                word for word, conf in zip(data['text'], data['conf'])
                if conf > 0
            ])

            return text

        except Exception as e:
            logger.error(f"Tesseract extraction failed for {file_path}: {e}")
            raise

    def _extract_text_with_ocr_space(self, file_path: str) -> str:
        """Extract text using OCR.space API with monthly usage cap."""
        if not self._consume_monthly_quota():
            if not self.tesseract_available:
                self._init_tesseract()
            if self.tesseract_available:
                logger.warning("OCR.space monthly limit reached. Falling back to Tesseract.")
                return self._extract_text_with_tesseract(file_path, preprocess=True)
            raise RuntimeError("OCR.space monthly limit reached and no fallback available.")

        with open(file_path, 'rb') as file_handle:
            file_bytes = file_handle.read()

        filename = Path(file_path).name
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        fields = {
            'language': self.ocr_language,
            'isOverlayRequired': 'false',
            'OCREngine': self.ocr_engine
        }
        body, content_type_header = self._build_multipart_form(fields, {
            'file': (filename, file_bytes, content_type)
        })

        request = urllib.request.Request(
            self.ocr_api_url,
            data=body,
            headers={
                'apikey': self.ocr_key,
                'Content-Type': content_type_header
            },
            method='POST'
        )

        with urllib.request.urlopen(request, timeout=self.ocr_timeout) as response:
            payload = response.read().decode('utf-8')

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid OCR.space response: {e}")

        if data.get('IsErroredOnProcessing'):
            raise RuntimeError(data.get('ErrorMessage') or 'OCR.space error')

        parsed_results = data.get('ParsedResults') or []
        if not parsed_results:
            return ''

        texts = [result.get('ParsedText', '') for result in parsed_results if result.get('ParsedText')]
        return '\n'.join(texts).strip()

    def _consume_monthly_quota(self) -> bool:
        """Increment OCR usage for the month if under limit."""
        if self.ocr_monthly_limit <= 0:
            return True

        current_month = datetime.utcnow().strftime('%Y-%m')

        with self._usage_lock:
            usage = self._read_usage()
            if usage.get('month') != current_month:
                usage = {'month': current_month, 'count': 0}

            if usage.get('count', 0) >= self.ocr_monthly_limit:
                return False

            usage['count'] = usage.get('count', 0) + 1
            self._write_usage(usage)

        return True

    def _read_usage(self) -> Dict[str, Any]:
        if not self._usage_path.exists():
            return {}

        try:
            with open(self._usage_path, 'r', encoding='utf-8') as file_handle:
                return json.load(file_handle)
        except Exception:
            return {}

    def _write_usage(self, usage: Dict[str, Any]) -> None:
        self._usage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._usage_path, 'w', encoding='utf-8') as file_handle:
            json.dump(usage, file_handle)

    def _resolve_usage_path(self, override: Optional[str]) -> Path:
        if override:
            return Path(override)

        backend_dir = Path(__file__).resolve().parents[2]
        return backend_dir / 'temp' / 'ocr_usage.json'

    def _build_multipart_form(
        self,
        fields: Dict[str, str],
        files: Dict[str, Any]
    ) -> Tuple[bytes, str]:
        boundary = uuid4().hex
        boundary_bytes = boundary.encode('ascii')
        body = bytearray()

        for name, value in fields.items():
            body.extend(b'--' + boundary_bytes + b'\r\n')
            body.extend(f'Content-Disposition: form-data; name="{name}"'.encode('ascii'))
            body.extend(b'\r\n\r\n')
            body.extend(str(value).encode('utf-8'))
            body.extend(b'\r\n')

        for name, (filename, content, content_type) in files.items():
            body.extend(b'--' + boundary_bytes + b'\r\n')
            body.extend(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode('ascii')
            )
            body.extend(b'\r\n')
            body.extend(f'Content-Type: {content_type}'.encode('ascii'))
            body.extend(b'\r\n\r\n')
            body.extend(content)
            body.extend(b'\r\n')

        body.extend(b'--' + boundary_bytes + b'--\r\n')

        content_type_header = f'multipart/form-data; boundary={boundary}'
        return bytes(body), content_type_header
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Binarization (Otsu's method)
        _, binary = cv2.threshold(
            denoised, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        return binary
    
    def classify_document(self, text: str, filename: str = "") -> str:
        """
        Classify document type using LLM.
        
        Args:
            text: Extracted text
            filename: Original filename
            
        Returns:
            Document type
        """
        if not self.groq_api_key:
            # Fallback to filename-based classification
            logger.warning("GROQ_API_KEY not set, using filename-based classification")
            return self._classify_by_filename(filename)
        
        try:
            from langchain_groq import ChatGroq
            
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                api_key=self.groq_api_key
            )
            
            prompt = f"""Classify this document into ONE of these types:
- cibil_report
- salary_slip
- itr_form16
- bank_statement
- diagnostic_report
- medical_history
- tenth_marksheet
- aadhaar_card
- pan_card
- passport
- voter_id
- utility_bill
- gst_certificate
- trade_license
- unknown

Document text (first 500 chars):
{text[:500]}

Filename: {filename}

Respond with ONLY the document type, nothing else."""
            
            response = llm.invoke(prompt).content.strip().lower()
            
            # Validate response
            valid_types = [
                'cibil_report', 'salary_slip', 'itr_form16', 'bank_statement',
                'diagnostic_report', 'medical_history', 'tenth_marksheet',
                'aadhaar_card', 'pan_card', 'passport', 'voter_id',
                'utility_bill', 'gst_certificate', 'trade_license', 'unknown'
            ]
            
            if response in valid_types:
                return response
            else:
                logger.warning(f"Invalid classification: {response}")
                return 'unknown'
                
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._classify_by_filename(filename)
    
    def _classify_by_filename(self, filename: str) -> str:
        """Fallback classification based on filename."""
        filename_lower = filename.lower()
        
        if 'cibil' in filename_lower or 'credit' in filename_lower:
            return 'cibil_report'
        elif 'salary' in filename_lower or 'payslip' in filename_lower:
            return 'salary_slip'
        elif 'itr' in filename_lower or 'form16' in filename_lower:
            return 'itr_form16'
        elif 'bank' in filename_lower and 'statement' in filename_lower:
            return 'bank_statement'
        elif 'diagnostic' in filename_lower:
            return 'diagnostic_report'
        elif 'medical' in filename_lower:
            return 'medical_history'
        elif 'marksheet' in filename_lower or '10th' in filename_lower:
            return 'tenth_marksheet'
        elif 'aadhaar' in filename_lower or 'aadhar' in filename_lower:
            return 'aadhaar_card'
        elif 'pan' in filename_lower:
            return 'pan_card'
        else:
            return 'unknown'
    
    def process_document(
        self,
        file_path: str,
        preprocess: bool = True,
        classify: bool = True
    ) -> Dict[str, Any]:
        """
        Process document: extract text, classify, and calculate confidence.
        
        Args:
            file_path: Path to document
            preprocess: Whether to preprocess image
            classify: Whether to classify document
            
        Returns:
            Dictionary with text, document_type, confidence
        """
        result = {}
        
        # Extract text
        text = self.extract_text(file_path, preprocess)
        result['text'] = text
        result['text_length'] = len(text)
        
        # Calculate confidence (based on text quality)
        confidence = self._calculate_confidence(text)
        result['confidence'] = confidence
        
        # Classify document
        if classify:
            filename = Path(file_path).name
            doc_type = self.classify_document(text, filename)
            result['document_type'] = doc_type
        
        return result
    
    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence score based on text quality.
        
        Args:
            text: Extracted text
            
        Returns:
            Confidence score (0-100)
        """
        if not text or len(text) < 10:
            return 0.0
        
        # Calculate metrics
        total_chars = len(text)
        alpha_chars = sum(c.isalpha() for c in text)
        digit_chars = sum(c.isdigit() for c in text)
        space_chars = sum(c.isspace() for c in text)
        
        # Calculate ratios
        alpha_ratio = alpha_chars / total_chars if total_chars > 0 else 0
        digit_ratio = digit_chars / total_chars if total_chars > 0 else 0
        space_ratio = space_chars / total_chars if total_chars > 0 else 0
        
        # Good text should have reasonable ratios
        confidence = 50.0  # Base confidence
        
        # Boost for good alpha ratio (40-80%)
        if 0.4 <= alpha_ratio <= 0.8:
            confidence += 30.0
        
        # Boost for some digits (5-20%)
        if 0.05 <= digit_ratio <= 0.2:
            confidence += 10.0
        
        # Boost for reasonable spacing (10-20%)
        if 0.1 <= space_ratio <= 0.2:
            confidence += 10.0
        
        return min(100.0, confidence)

    def extract_field(self, text: str, field_name: str) -> Optional[Any]:
        """
        Extract field using regex patterns.

        Args:
            text: Text to extract from
            field_name: Field name

        Returns:
            Extracted value or None
        """
        import re

        pattern = self.FIELD_PATTERNS.get(field_name)
        if not pattern:
            return None

        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None

        if field_name == "blood_pressure":
            return (int(match.group(1)), int(match.group(2)))

        return match.group(1)
