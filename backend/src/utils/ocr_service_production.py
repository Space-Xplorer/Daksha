"""
Production OCR service with Tesseract and LLM-based classification.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ProductionOCRService:
    """Production OCR service using Tesseract."""
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize production OCR service."""
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        
        # Configure Tesseract path
        tesseract_path = os.getenv('TESSERACT_PATH')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Test Tesseract installation
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise RuntimeError("Tesseract OCR not available. Please install Tesseract and set TESSERACT_PATH in .env")
    
    def extract_text(self, file_path: str, preprocess: bool = True) -> str:
        """
        Extract text from document using Tesseract OCR.
        
        Args:
            file_path: Path to document (PDF or image)
            preprocess: Whether to preprocess image
            
        Returns:
            Extracted text
        """
        try:
            # Convert PDF to images if needed
            if file_path.lower().endswith('.pdf'):
                images = convert_from_path(file_path, dpi=300)
                image = images[0]  # Process first page
            else:
                image = Image.open(file_path)
            
            # Convert to numpy array for preprocessing
            img_array = np.array(image)
            
            # Preprocess if requested
            if preprocess:
                img_array = self._preprocess_image(img_array)
            
            # Extract text with confidence
            data = pytesseract.image_to_data(
                img_array,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Combine text
            text = ' '.join([
                word for word, conf in zip(data['text'], data['conf'])
                if conf > 0  # Filter out low confidence
            ])
            
            return text
            
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            raise
    
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
