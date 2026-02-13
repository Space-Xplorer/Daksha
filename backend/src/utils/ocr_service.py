"""
OCR service wrapper for document processing.

This module provides OCR functionality using Tesseract with image preprocessing,
document classification using LLM, and field extraction using regex patterns.
Includes confidence scoring and async LLM support.
"""

import os
import re
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import logging

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
    import cv2
except ImportError as e:
    logging.warning(f"OCR dependencies not fully installed: {e}")

try:
    from pdf2image import convert_from_path
except ImportError:
    logging.warning("pdf2image not installed. PDF processing will not be available.")

try:
    from langchain_groq import ChatGroq
except ImportError:
    logging.warning("langchain_groq not installed. Document classification will be limited.")


# Configure logging
logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR service wrapper using Tesseract with advanced preprocessing
    and LLM-based document classification.
    """

    # Document type mapping
    DOCUMENT_TYPES = {
        "loan": [
            "cibil_report",
            "salary_slip",
            "itr_form16",
            "itr",
            "form_16",
            "tds_certificate",
            "bank_statement",
            "property_document",
            "vehicle_registration",
            "aadhaar_card",
            "pan_card",
            "passport",
            "voter_id",
            "utility_bill",
            "gst_certificate",
            "trade_license"
        ],
        "insurance": [
            "diagnostic_report",
            "physical_exam",
            "medical_declaration",
            "family_medical_records",
            "ecg_report",
            "prescription_history",
            "discharge_summary",
            "aadhaar_card",
            "pan_card",
            "passport",
            "voter_id",
            "utility_bill",
            "medical_history",
            "birth_certificate",
            "tenth_marksheet"
        ]
    }

    # Regex patterns for common field extraction
    FIELD_PATTERNS = {
        # Financial fields
        "cibil_score": [
            r"(?:CIBIL|Credit)\s*Score[:\s]*(\d{3})",
            r"Score[:\s]*(\d{3})",
            r"Credit\s*Rating[:\s]*(\d{3})"
        ],
        "pan_number": [
            r"(?:PAN|Permanent\s*Account\s*Number)[:\s]*([A-Z]{5}\d{4}[A-Z])",
            r"\b([A-Z]{5}\d{4}[A-Z])\b"
        ],
        "aadhaar_number": [
            r"(?:Aadhaar|Aadhar)[:\s]*(\d{4}\s*\d{4}\s*\d{4})",
            r"\b(\d{4}\s*\d{4}\s*\d{4})\b"
        ],
        "passport_number": [
            r"(?:Passport\s*(?:No|Number))[:\s]*([A-Z0-9]{6,9})",
            r"\b([A-Z]{1}[0-9]{7})\b"
        ],
        "voter_id_number": [
            r"(?:EPIC|Voter\s*ID)[:\s]*([A-Z]{3}\d{7})",
            r"\b([A-Z]{3}\d{7})\b"
        ],
        "annual_income": [
            r"(?:Annual|Gross|Total)\s*Income[:\s]*₹?\s*([\d,]+)",
            r"Gross\s*(?:Annual\s*)?Income[:\s]*₹?\s*([\d,]+)",
            r"Income\s*(?:per\s*annum)?[:\s]*₹?\s*([\d,]+)"
        ],
        "monthly_income": [
            r"(?:Monthly|Net|Gross)\s*(?:Salary|Income)[:\s]*₹?\s*([\d,]+)",
            r"Salary[:\s]*₹?\s*([\d,]+)"
        ],
        "loan_amount": [
            r"(?:Loan|Amount\s*Required)[:\s]*₹?\s*([\d,]+)",
            r"Principal\s*Amount[:\s]*₹?\s*([\d,]+)"
        ],
        "existing_debt": [
            r"(?:Existing|Outstanding)\s*(?:Debt|Loan)[:\s]*₹?\s*([\d,]+)",
            r"Total\s*(?:Debt|Liabilities)[:\s]*₹?\s*([\d,]+)"
        ],
        "bank_balance": [
            r"(?:Average|Current|Closing)\s*Balance[:\s]*₹?\s*([\d,]+)",
            r"Balance[:\s]*₹?\s*([\d,]+)"
        ],
        "property_value": [
            r"(?:Market|Assessed|Property)\s*Value[:\s]*₹?\s*([\d,]+)",
            r"Valuation[:\s]*₹?\s*([\d,]+)"
        ],

        # Health fields
        "bmi": [
            r"BMI[:\s]*([\d.]+)",
            r"Body\s*Mass\s*Index[:\s]*([\d.]+)"
        ],
        "height": [
            r"Height[:\s]*([\d.]+)\s*(?:cm|CM|centimeters?)",
            r"Ht[:\s]*([\d.]+)\s*(?:cm|CM)"
        ],
        "weight": [
            r"Weight[:\s]*([\d.]+)\s*(?:kg|KG|kilograms?)",
            r"Wt[:\s]*([\d.]+)\s*(?:kg|KG)"
        ],
        "blood_pressure": [
            r"(?:Blood\s*Pressure|BP)[:\s]*(\d{2,3})/(\d{2,3})",
            r"BP[:\s]*(\d{2,3})/(\d{2,3})"
        ],
        "heart_rate": [
            r"(?:Heart\s*Rate|Pulse)[:\s]*(\d{2,3})\s*(?:bpm|BPM)?",
            r"HR[:\s]*(\d{2,3})"
        ],
        "hba1c": [
            r"HbA1c[:\s]*([\d.]+)\s*%?",
            r"Glycated\s*Hemoglobin[:\s]*([\d.]+)"
        ],
        "cholesterol": [
            r"(?:Total\s*)?Cholesterol[:\s]*([\d.]+)\s*(?:mg/dL)?",
            r"Cholesterol\s*Total[:\s]*([\d.]+)"
        ],
        "blood_sugar": [
            r"(?:Blood\s*)?(?:Glucose|Sugar)[:\s]*([\d.]+)\s*(?:mg/dL)?",
            r"Fasting\s*(?:Blood\s*)?Sugar[:\s]*([\d.]+)"
        ],
        "creatinine": [
            r"Creatinine[:\s]*([\d.]+)\s*(?:mg/dL)?",
            r"Serum\s*Creatinine[:\s]*([\d.]+)"
        ],

        # Common fields
        "age": [
            r"Age[:\s]*(\d{1,3})\s*(?:years?|yrs?)?",
            r"(?:DOB|Date\s*of\s*Birth)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
        ],
        "gender": [
            r"(?:Gender|Sex)[:\s]*(Male|Female|M|F|Other)",
            r"\b(Male|Female)\b"
        ],
        "name": [
            r"(?:Name|Full\s*Name)[:\s]*([A-Za-z\s]+)",
            r"Applicant\s*Name[:\s]*([A-Za-z\s]+)"
        ],
        "date": [
            r"(?:Date|Dated)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b"
        ]
    }

    def __init__(self, groq_api_key: Optional[str] = None, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR service.

        Args:
            groq_api_key: Optional Groq API key for LLM-based classification
            tesseract_cmd: Optional path to Tesseract executable
        """
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")

        # Set Tesseract path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Initialize LLM for document classification if API key available
        self.llm = None
        if self.groq_api_key:
            try:
                self.llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                    api_key=self.groq_api_key
                )
                logger.info("LLM initialized for document classification")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")
        else:
            logger.warning("No Groq API key provided. Document classification will use rule-based approach.")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.

        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Noise reduction
        - Thresholding

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Apply noise reduction
            image = image.filter(ImageFilter.MedianFilter(size=3))

            # Convert to numpy array for OpenCV operations
            img_array = np.array(image)

            # Apply adaptive thresholding
            img_array = cv2.adaptiveThreshold(
                img_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )

            # Convert back to PIL Image
            image = Image.fromarray(img_array)

            logger.debug("Image preprocessing completed")
            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}. Using original image.")
            return image

    def extract_text_from_image(self, image_path: str, preprocess: bool = True) -> str:
        """
        Extract text from image file using Tesseract OCR.

        Args:
            image_path: Path to image file
            preprocess: Whether to apply preprocessing

        Returns:
            Extracted text
        """
        try:
            # Load image
            image = Image.open(image_path)

            # Preprocess if requested
            if preprocess:
                image = self.preprocess_image(image)

            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, lang='eng')

            logger.info(f"Extracted {len(text)} characters from {Path(image_path).name}")
            return text

        except Exception as e:
            logger.error(f"Failed to extract text from image {image_path}: {e}")
            return ""
    
    def extract_text_with_confidence(self, image_path: str, preprocess: bool = True) -> Tuple[str, float, List[Dict[str, Any]]]:
        """
        Extract text from image with confidence scores using Tesseract OCR.

        Args:
            image_path: Path to image file
            preprocess: Whether to apply preprocessing

        Returns:
            Tuple of (extracted_text, average_confidence, word_details)
            where word_details is a list of dicts with text, confidence, and bbox
        """
        try:
            # Load image
            image = Image.open(image_path)

            # Preprocess if requested
            if preprocess:
                image = self.preprocess_image(image)

            # Extract text with confidence data using Tesseract
            data = pytesseract.image_to_data(image, lang='eng', output_type=pytesseract.Output.DICT)
            
            # Build text and collect confidence scores
            words = []
            word_details = []
            confidences = []
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text_item = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                # Filter out empty text and low confidence (<= 0)
                if text_item and conf > 0:
                    words.append(text_item)
                    confidences.append(conf)
                    
                    word_details.append({
                        'text': text_item,
                        'confidence': conf,
                        'bbox': {
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            # Combine words into full text
            full_text = ' '.join(words)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(
                f"Extracted {len(words)} words from {Path(image_path).name} "
                f"with average confidence {avg_confidence:.1f}%"
            )
            
            return full_text, avg_confidence, word_details

        except Exception as e:
            logger.error(f"Failed to extract text with confidence from {image_path}: {e}")
            return "", 0.0, []

    def extract_text_from_pdf(self, pdf_path: str, preprocess: bool = True) -> str:
        """
        Extract text from PDF file by converting to images.

        Args:
            pdf_path: Path to PDF file
            preprocess: Whether to apply preprocessing

        Returns:
            Extracted text from all pages
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)

            # Extract text from each page
            all_text = []
            for i, image in enumerate(images):
                if preprocess:
                    image = self.preprocess_image(image)

                text = pytesseract.image_to_string(image, lang='eng')
                all_text.append(f"--- Page {i+1} ---\n{text}")

            full_text = "\n\n".join(all_text)
            logger.info(f"Extracted {len(full_text)} characters from {len(images)} pages of {Path(pdf_path).name}")
            return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            return ""

    def extract_text(self, file_path: str, preprocess: bool = True) -> str:
        """
        Extract text from image or PDF file.

        Args:
            file_path: Path to file
            preprocess: Whether to apply preprocessing

        Returns:
            Extracted text
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return ""

        # Determine file type and extract accordingly
        if file_path.suffix.lower() in ['.pdf']:
            return self.extract_text_from_pdf(str(file_path), preprocess)
        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self.extract_text_from_image(str(file_path), preprocess)
        else:
            logger.error(f"Unsupported file type: {file_path.suffix}")
            return ""

    def classify_document_rule_based(self, text: str, filename: str = "") -> str:
        """
        Classify document type using rule-based approach (fallback).

        Args:
            text: Extracted text
            filename: Original filename for hints

        Returns:
            Document type
        """
        text_lower = text.lower()
        filename_lower = filename.lower()

        # Check for keywords in text and filename
        keywords = {
            "cibil_report": ["cibil", "credit score", "credit report", "credit information"],
            "salary_slip": ["salary slip", "pay slip", "payslip", "salary statement", "earnings"],
            "itr_form16": ["itr", "form 16", "income tax", "tax return", "assessment year"],
            "itr": ["itr", "income tax return"],
            "form_16": ["form 16", "tds"],
            "tds_certificate": ["tds certificate", "tax deducted at source"],
            "bank_statement": ["bank statement", "account statement", "transaction history"],
            "property_document": ["property", "deed", "registry", "land", "apartment"],
            "vehicle_registration": ["vehicle", "registration", "rc book", "registration certificate"],
            "aadhaar_card": ["aadhaar", "aadhar", "uid", "uidai"],
            "pan_card": ["pan card", "permanent account", "income tax department"],
            "passport": ["passport", "passport no", "passport number"],
            "voter_id": ["voter id", "epic", "election commission"],
            "utility_bill": ["utility bill", "electricity bill", "water bill", "gas bill"],
            "gst_certificate": ["gst", "gstin", "goods and services tax"],
            "trade_license": ["trade license", "trade licence"],
            "diagnostic_report": ["diagnostic", "blood report", "lab report", "pathology", "hba1c", "cholesterol"],
            "physical_exam": ["physical exam", "medical examination", "height", "weight", "bmi", "blood pressure"],
            "medical_declaration": ["medical declaration", "health questionnaire", "medical history"],
            "family_medical_records": ["family history", "hereditary", "family medical"],
            "ecg_report": ["ecg", "electrocardiogram", "ekg", "heart"],
            "prescription_history": ["prescription", "medication", "rx"],
            "discharge_summary": ["discharge", "hospital", "admission", "treatment"],
            "medical_history": ["medical history", "past prescription", "chronic"],
            "birth_certificate": ["birth certificate", "date of birth"],
            "tenth_marksheet": ["10th", "tenth", "marksheet", "ssc"]
        }

        # Score each document type
        scores = {}
        for doc_type, terms in keywords.items():
            score = sum(1 for term in terms if term in text_lower or term in filename_lower)
            if score > 0:
                scores[doc_type] = score

        # Return document type with highest score
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            logger.info(f"Rule-based classification: {best_match[0]} (score: {best_match[1]})")
            return best_match[0]

        # Default to unknown
        logger.warning("Could not classify document using rule-based approach")
        return "unknown"

    def classify_document_llm(self, text: str, filename: str = "") -> str:
        """
        Classify document type using LLM.

        Args:
            text: Extracted text
            filename: Original filename for hints

        Returns:
            Document type
        """
        if not self.llm:
            logger.warning("LLM not available, falling back to rule-based classification")
            return self.classify_document_rule_based(text, filename)

        # Truncate text for efficiency
        text_sample = text[:2000] if len(text) > 2000 else text

        # Get all possible document types
        all_doc_types = list(set(
            self.DOCUMENT_TYPES["loan"] + self.DOCUMENT_TYPES["insurance"]
        ))

        prompt = f"""You are a document classification expert. Analyze the following text extracted from a document and classify it into one of these types:

{', '.join(all_doc_types)}

Filename: {filename}

Document Text:
{text_sample}

Return ONLY the document type from the list above. If you cannot determine the type, return "unknown".

Document Type:"""

        try:
            response = self.llm.invoke(prompt).content.strip().lower()

            # Clean up response
            response = response.replace("_", " ").strip()

            # Find best match from valid types
            for doc_type in all_doc_types:
                if doc_type.replace("_", " ") in response or response in doc_type.replace("_", " "):
                    logger.info(f"LLM classification: {doc_type}")
                    return doc_type

            # If no match, fall back to rule-based
            logger.warning(f"LLM returned unclear classification: {response}, falling back to rule-based")
            return self.classify_document_rule_based(text, filename)

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self.classify_document_rule_based(text, filename)

    async def classify_document_llm_async(self, text: str, filename: str = "") -> str:
        """
        Classify document type using LLM asynchronously.

        Args:
            text: Extracted text
            filename: Original filename for hints

        Returns:
            Document type
        """
        if not self.llm:
            logger.warning("LLM not available, falling back to rule-based classification")
            return self.classify_document_rule_based(text, filename)

        # Truncate text for efficiency
        text_sample = text[:2000] if len(text) > 2000 else text

        # Get all possible document types
        all_doc_types = list(set(
            self.DOCUMENT_TYPES["loan"] + self.DOCUMENT_TYPES["insurance"]
        ))

        prompt = f"""You are a document classification expert. Analyze the following text extracted from a document and classify it into one of these types:

{', '.join(all_doc_types)}

Filename: {filename}

Document Text:
{text_sample}

Return ONLY the document type from the list above. If you cannot determine the type, return "unknown".

Document Type:"""

        try:
            response = await self.llm.ainvoke(prompt)
            response_text = response.content.strip().lower()

            # Clean up response
            response_text = response_text.replace("_", " ").strip()

            # Find best match from valid types
            for doc_type in all_doc_types:
                if doc_type.replace("_", " ") in response_text or response_text in doc_type.replace("_", " "):
                    logger.info(f"LLM async classification: {doc_type}")
                    return doc_type

            # If no match, fall back to rule-based
            logger.warning(f"LLM returned unclear classification: {response_text}, falling back to rule-based")
            return self.classify_document_rule_based(text, filename)

        except Exception as e:
            logger.error(f"LLM async classification failed: {e}")
            return self.classify_document_rule_based(text, filename)

    def classify_document(self, text: str, filename: str = "", use_llm: bool = True) -> str:
        """
        Classify document type.

        Args:
            text: Extracted text
            filename: Original filename for hints
            use_llm: Whether to use LLM (falls back to rule-based if unavailable)

        Returns:
            Document type
        """
        if use_llm and self.llm:
            return self.classify_document_llm(text, filename)
        else:
            return self.classify_document_rule_based(text, filename)

    def extract_field(self, text: str, field_name: str) -> Optional[Any]:
        """
        Extract a specific field from text using regex patterns.

        Args:
            text: Text to extract from
            field_name: Name of field to extract

        Returns:
            Extracted field value or None
        """
        if field_name not in self.FIELD_PATTERNS:
            logger.warning(f"No pattern defined for field: {field_name}")
            return None

        patterns = self.FIELD_PATTERNS[field_name]

        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Handle blood pressure special case (returns tuple)
                if field_name == "blood_pressure" and len(match.groups()) == 2:
                    systolic = int(match.group(1))
                    diastolic = int(match.group(2))
                    logger.debug(f"Extracted {field_name}: {systolic}/{diastolic}")
                    return (systolic, diastolic)

                # Handle regular fields
                value = match.group(1)

                # Clean up numeric values
                if field_name in ['cibil_score', 'annual_income', 'monthly_income',
                                  'loan_amount', 'existing_debt', 'bank_balance',
                                  'property_value']:
                    value = value.replace(',', '')

                logger.debug(f"Extracted {field_name}: {value}")
                return value

        logger.debug(f"Could not extract {field_name}")
        return None

    def extract_fields(self, text: str, field_names: List[str]) -> Dict[str, Any]:
        """
        Extract multiple fields from text.

        Args:
            text: Text to extract from
            field_names: List of field names to extract

        Returns:
            Dictionary of extracted fields
        """
        extracted = {}
        for field_name in field_names:
            value = self.extract_field(text, field_name)
            if value is not None:
                extracted[field_name] = value

        logger.info(f"Extracted {len(extracted)}/{len(field_names)} fields")
        return extracted

    def process_document(
        self,
        file_path: str,
        preprocess: bool = True,
        classify: bool = True,
        extract_fields: Optional[List[str]] = None,
        include_confidence: bool = False
    ) -> Dict[str, Any]:
        """
        Complete document processing pipeline.

        Args:
            file_path: Path to document
            preprocess: Whether to apply image preprocessing
            classify: Whether to classify document type
            extract_fields: Optional list of fields to extract
            include_confidence: Whether to include OCR confidence scores

        Returns:
            Dictionary with:
            - text: Extracted text
            - document_type: Classified document type (if classify=True)
            - fields: Extracted fields (if extract_fields provided)
            - confidence: Average confidence score (if include_confidence=True)
            - word_details: Per-word confidence details (if include_confidence=True)
        """
        result = {}

        # Extract text with optional confidence
        if include_confidence:
            file_path_obj = Path(file_path)
            if file_path_obj.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                text, avg_conf, word_details = self.extract_text_with_confidence(file_path, preprocess)
                result['text'] = text
                result['confidence'] = avg_conf
                result['word_details'] = word_details
                result['text_length'] = len(text)
            else:
                # For PDFs, fall back to regular extraction
                text = self.extract_text(file_path, preprocess)
                result['text'] = text
                result['text_length'] = len(text)
                result['confidence'] = None
                result['word_details'] = []
        else:
            text = self.extract_text(file_path, preprocess)
            result['text'] = text
            result['text_length'] = len(text)

        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return result

        # Classify document
        if classify:
            filename = Path(file_path).name
            doc_type = self.classify_document(text, filename)
            result['document_type'] = doc_type

        # Extract fields
        if extract_fields:
            fields = self.extract_fields(text, extract_fields)
            result['fields'] = fields

        return result


# Convenience functions
def create_ocr_service(groq_api_key: Optional[str] = None) -> OCRService:
    """
    Create and return an OCR service instance.

    Args:
        groq_api_key: Optional Groq API key

    Returns:
        OCRService instance
    """
    return OCRService(groq_api_key=groq_api_key)


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    # Create OCR service
    ocr = create_ocr_service()

    # Example: process a document
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = ocr.process_document(
            file_path,
            preprocess=True,
            classify=True,
            extract_fields=['cibil_score', 'annual_income', 'bmi', 'blood_pressure']
        )

        print(json.dumps(result, indent=2))
    else:
        print("Usage: python ocr_service.py <file_path>")
