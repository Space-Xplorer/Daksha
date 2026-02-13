"""
Simple OCR service wrapper with mock functionality.

This module provides a simplified OCR service that works without Tesseract.
"""

import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """
    Simple OCR service with mock extraction for testing.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize OCR service."""
        self.groq_api_key = groq_api_key
        logger.info("OCR service initialized in mock mode")
    
    def extract_text(self, file_path: str, preprocess: bool = True) -> str:
        """
        Mock text extraction based on filename.
        
        Args:
            file_path: Path to file
            preprocess: Ignored in mock mode
            
        Returns:
            Mock extracted text
        """
        filename = Path(file_path).stem.lower()
        
        # Return mock text based on document type
        if "cibil" in filename or "credit" in filename:
            return """
            CIBIL CREDIT REPORT
            Name: Rajesh Kumar
            CIBIL Score: 750
            Report Date: 2026-01-15
            Credit History: 5 years
            """
        
        elif "salary" in filename or "payslip" in filename:
            return """
            SALARY SLIP
            Employee: Rajesh Kumar
            Month: January 2026
            Gross Salary: ₹100,000
            Net Salary: ₹85,000
            """
        
        elif "itr" in filename or "form16" in filename or "form-16" in filename or "tds" in filename:
            return """
            INCOME TAX RETURN
            Name: Rajesh Kumar
            Assessment Year: 2025-26
            Total Income: ₹1,200,000
            """
        
        elif "bank" in filename or "statement" in filename:
            return """
            BANK STATEMENT
            Account Holder: Rajesh Kumar
            Period: Jan-Jun 2026
            Average Balance: ₹250,000
            """
        
        elif "diagnostic" in filename or "blood" in filename:
            return """
            DIAGNOSTIC REPORT
            Patient: Rajesh Kumar
            Date: 2026-02-01
            HbA1c: 5.8%
            Cholesterol: 180 mg/dL
            Blood Sugar (Fasting): 95 mg/dL
            """
        
        elif "physical" in filename or "exam" in filename:
            return """
            PHYSICAL EXAMINATION REPORT
            Patient: Rajesh Kumar
            Date: 2026-02-01
            Height: 175 cm
            Weight: 75 kg
            Blood Pressure: 120/80 mmHg
            Heart Rate: 72 bpm
            """
        
        elif "medical" in filename or "declaration" in filename:
            return """
            MEDICAL DECLARATION
            Patient: Rajesh Kumar
            Smoker: No
            Regular Exercise: Yes
            Pre-existing Conditions: None
            Family History: No major diseases
            """
        elif "aadhaar" in filename or "aadhar" in filename:
            return """
            AADHAAR CARD
            Name: Rajesh Kumar
            Aadhaar: 1234 5678 9012
            DOB: 15-05-1990
            Gender: Male
            """
        elif "passport" in filename:
            return """
            PASSPORT
            Name: Rajesh Kumar
            Passport No: P1234567
            DOB: 15-05-1990
            Gender: Male
            """
        elif "voter" in filename:
            return """
            VOTER ID
            Name: Rajesh Kumar
            EPIC No: ABC1234567
            DOB: 15-05-1990
            Gender: Male
            """
        elif "utility" in filename or "electric" in filename or "water" in filename or "gas" in filename:
            return """
            UTILITY BILL
            Name: Rajesh Kumar
            Date: 01-02-2026
            Address: 123 MG Road, Bengaluru
            """
        elif "gst" in filename or "trade" in filename:
            return """
            BUSINESS PROOF
            Name: Rajesh Kumar
            GSTIN: 29ABCDE1234F1Z5
            Date: 2024-05-10
            """
        elif "discharge" in filename:
            return """
            DISCHARGE SUMMARY
            Patient: Rajesh Kumar
            Date: 2021-07-15
            """
        elif "prescription" in filename:
            return """
            PRESCRIPTION HISTORY
            Patient: Rajesh Kumar
            Date: 2022-03-10
            """
        elif "birth" in filename or "marksheet" in filename or "10th" in filename:
            return """
            PROOF OF AGE
            Name: Rajesh Kumar
            DOB: 15-05-1990
            Gender: Male
            """
        
        else:
            return "Mock document text"
    
    def classify_document(self, text: str, filename: str = "", use_llm: bool = False) -> str:
        """
        Classify document type based on content and filename.
        
        Args:
            text: Extracted text
            filename: Filename
            use_llm: Ignored in mock mode
            
        Returns:
            Document type
        """
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        # Check filename first
        if "cibil" in filename_lower or "credit" in filename_lower:
            return "cibil_report"
        elif "salary" in filename_lower or "payslip" in filename_lower:
            return "salary_slip"
        elif "itr" in filename_lower or "form16" in filename_lower or "form-16" in filename_lower or "tds" in filename_lower:
            return "itr_form16"
        elif "bank" in filename_lower and "statement" in filename_lower:
            return "bank_statement"
        elif "property" in filename_lower:
            return "property_document"
        elif "aadhaar" in filename_lower or "aadhar" in filename_lower:
            return "aadhaar_card"
        elif "gst" in filename_lower:
            return "gst_certificate"
        elif "trade" in filename_lower and "license" in filename_lower:
            return "trade_license"
        elif "passport" in filename_lower:
            return "passport"
        elif "voter" in filename_lower:
            return "voter_id"
        elif "utility" in filename_lower or "electric" in filename_lower or "water" in filename_lower or "gas" in filename_lower:
            return "utility_bill"
        elif "diagnostic" in filename_lower or "blood" in filename_lower:
            return "diagnostic_report"
        elif "physical" in filename_lower or "exam" in filename_lower:
            return "physical_exam"
        elif "medical" in filename_lower and "declaration" in filename_lower:
            return "medical_declaration"
        elif "discharge" in filename_lower:
            return "discharge_summary"
        elif "prescription" in filename_lower:
            return "prescription_history"
        elif "birth" in filename_lower:
            return "birth_certificate"
        elif "marksheet" in filename_lower or "10th" in filename_lower:
            return "tenth_marksheet"
        
        # Check content keywords
        if "cibil" in text_lower or "credit score" in text_lower:
            return "cibil_report"
        elif "salary slip" in text_lower:
            return "salary_slip"
        elif "income tax" in text_lower:
            return "itr_form16"
        elif "bank statement" in text_lower:
            return "bank_statement"
        elif "aadhaar" in text_lower or "aadhar" in text_lower:
            return "aadhaar_card"
        elif "gstin" in text_lower:
            return "gst_certificate"
        elif "trade license" in text_lower:
            return "trade_license"
        elif "passport" in text_lower:
            return "passport"
        elif "voter id" in text_lower or "epic" in text_lower:
            return "voter_id"
        elif "utility bill" in text_lower:
            return "utility_bill"
        elif "hba1c" in text_lower:
            return "diagnostic_report"
        elif "blood pressure" in text_lower and "height" in text_lower:
            return "physical_exam"
        elif "smoker" in text_lower and "pre-existing" in text_lower:
            return "medical_declaration"
        elif "discharge summary" in text_lower:
            return "discharge_summary"
        elif "prescription" in text_lower:
            return "prescription_history"
        elif "birth certificate" in text_lower:
            return "birth_certificate"
        elif "marksheet" in text_lower:
            return "tenth_marksheet"
        
        return "unknown"
    
    def extract_field(self, text: str, field_name: str) -> Optional[Any]:
        """
        Extract field using regex patterns.
        
        Args:
            text: Text to extract from
            field_name: Field name
            
        Returns:
            Extracted value or None
        """
        patterns = {
            "cibil_score": r"(?:CIBIL|Credit)\s*Score[:\s]*(\d{3})",
            "monthly_income": r"(?:Gross|Net)\s*(?:Salary|Income)[:\s]*₹?\s*([\d,]+)",
            "annual_income": r"(?:Total|Gross|Annual)\s*Income[:\s]*₹?\s*([\d,]+)",
            "hba1c": r"HbA1c[:\s]*([\d.]+)\s*%",
            "cholesterol": r"(?:Total\s*)?Cholesterol[:\s]*([\d.]+)\s*mg/dL",
            "blood_sugar": r"Blood\s*Sugar(?:\s*\(Fasting\))?[:\s]*([\d.]+)\s*mg/dL",
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
        
        if field_name not in patterns:
            return None
        
        pattern = patterns[field_name]
        match = re.search(pattern, text, re.IGNORECASE)
        
        if not match:
            return None
        
        # Handle blood pressure special case
        if field_name == "blood_pressure":
            return (int(match.group(1)), int(match.group(2)))
        
        return match.group(1)
    
    def process_document(
        self,
        file_path: str,
        preprocess: bool = True,
        classify: bool = True,
        extract_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process document and extract information.
        
        Args:
            file_path: Path to document
            preprocess: Ignored in mock mode
            classify: Whether to classify document
            extract_fields: Fields to extract
            
        Returns:
            Dictionary with text, document_type, and fields
        """
        result = {}
        
        # Extract text
        text = self.extract_text(file_path, preprocess)
        result['text'] = text
        result['text_length'] = len(text)
        
        # Classify document
        if classify:
            filename = Path(file_path).name
            doc_type = self.classify_document(text, filename)
            result['document_type'] = doc_type
        
        # Extract fields
        if extract_fields:
            fields = {}
            for field_name in extract_fields:
                value = self.extract_field(text, field_name)
                if value is not None:
                    fields[field_name] = value
            result['fields'] = fields
        
        return result
