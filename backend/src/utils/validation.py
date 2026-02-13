"""
Input validation logic.

This module implements validation for loan and insurance application inputs.
"""

from typing import Dict, Any, List, Tuple, Literal, Optional
from enum import Enum


class DocumentType(Enum):
    """Enumeration of supported document types."""
    # Loan documents
    CIBIL_REPORT = "cibil_report"
    SALARY_SLIP = "salary_slip"
    ITR_FORM16 = "itr_form16"
    ITR = "itr"
    FORM_16 = "form_16"
    TDS_CERTIFICATE = "tds_certificate"
    BANK_STATEMENT = "bank_statement"
    PROPERTY_DOCUMENT = "property_document"
    VEHICLE_REGISTRATION = "vehicle_registration"
    GST_CERTIFICATE = "gst_certificate"
    TRADE_LICENSE = "trade_license"
    
    # Insurance documents
    DIAGNOSTIC_REPORT = "diagnostic_report"
    PHYSICAL_EXAM = "physical_exam"
    MEDICAL_DECLARATION = "medical_declaration"
    FAMILY_MEDICAL_RECORDS = "family_medical_records"
    ECG_REPORT = "ecg_report"
    PRESCRIPTION_HISTORY = "prescription_history"
    DISCHARGE_SUMMARY = "discharge_summary"
    MEDICAL_HISTORY = "medical_history"
    BIRTH_CERTIFICATE = "birth_certificate"
    TENTH_MARKSHEET = "tenth_marksheet"
    
    # Common documents
    AADHAAR_CARD = "aadhaar_card"
    PAN_CARD = "pan_card"
    PASSPORT = "passport"
    VOTER_ID = "voter_id"
    UTILITY_BILL = "utility_bill"


class LoanType(Enum):
    """Enumeration of supported loan types."""
    HOME = "home"
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    BUSINESS = "business"


class EmploymentType(Enum):
    """Enumeration of employment types."""
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    BUSINESS = "business"


class OccupationRisk(Enum):
    """Enumeration of occupation risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Field mappings for loan applications
LOAN_REQUIRED_FIELDS = {
    "cibil_score": int,
    "annual_income": float,
    "loan_amount": float,
    "employment_type": str,
    "existing_debt": float,
    "age": int,
    "employment_years": int
}

# Field mappings for insurance applications
INSURANCE_REQUIRED_FIELDS = {
    "age": int,
    "bmi": float,
    "smoker": bool,
    "coverage_amount": float
}

# Optional insurance fields
INSURANCE_OPTIONAL_FIELDS = {
    "pre_existing_conditions": list,
    "family_history": list,
    "occupation_risk": str,
    "bloodpressure": int,
    "diabetes": int,
    "cholesterol": float,
    "regular_ex": bool
}


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_loan_application(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate loan application data.
    
    Args:
        data: Loan application data dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    for field, expected_type in LOAN_REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
            continue
            
        if not isinstance(data[field], expected_type):
            errors.append(f"Invalid type for {field}: expected {expected_type.__name__}, got {type(data[field]).__name__}")
    
    # Validate field ranges
    if "cibil_score" in data:
        if not (300 <= data["cibil_score"] <= 900):
            errors.append("Invalid cibil_score: must be between 300 and 900")
    
    if "annual_income" in data:
        if data["annual_income"] <= 0:
            errors.append("Invalid annual_income: must be greater than 0")
    
    if "loan_amount" in data:
        if data["loan_amount"] <= 0:
            errors.append("Invalid loan_amount: must be greater than 0")
    
    if "existing_debt" in data:
        if data["existing_debt"] < 0:
            errors.append("Invalid existing_debt: must be greater than or equal to 0")
    
    if "age" in data:
        if not (18 <= data["age"] <= 100):
            errors.append("Invalid age: must be between 18 and 100")
    
    if "employment_years" in data:
        if data["employment_years"] < 0:
            errors.append("Invalid employment_years: must be greater than or equal to 0")
    
    if "employment_type" in data:
        valid_types = [e.value for e in EmploymentType]
        if data["employment_type"] not in valid_types:
            errors.append(f"Invalid employment_type: must be one of {valid_types}")
    
    return len(errors) == 0, errors


def validate_insurance_application(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate insurance application data.
    
    Args:
        data: Insurance application data dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    for field, expected_type in INSURANCE_REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
            continue
            
        if not isinstance(data[field], expected_type):
            errors.append(f"Invalid type for {field}: expected {expected_type.__name__}, got {type(data[field]).__name__}")
    
    # Validate field ranges
    if "age" in data:
        if not (18 <= data["age"] <= 100):
            errors.append("Invalid age: must be between 18 and 100")
    
    if "bmi" in data:
        if not (10.0 <= data["bmi"] <= 60.0):
            errors.append("Invalid bmi: must be between 10.0 and 60.0")
    
    if "coverage_amount" in data:
        if data["coverage_amount"] <= 0:
            errors.append("Invalid coverage_amount: must be greater than 0")
    
    # Validate optional fields
    if "occupation_risk" in data:
        valid_risks = [r.value for r in OccupationRisk]
        if data["occupation_risk"] not in valid_risks:
            errors.append(f"Invalid occupation_risk: must be one of {valid_risks}")
    
    if "pre_existing_conditions" in data:
        if not isinstance(data["pre_existing_conditions"], list):
            errors.append("Invalid pre_existing_conditions: must be a list")
    
    if "family_history" in data:
        if not isinstance(data["family_history"], list):
            errors.append("Invalid family_history: must be a list")
    
    return len(errors) == 0, errors


def validate_request_type(
    request_type: str,
    applicant_data: Dict[str, Any],
    loan_type: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate request type and corresponding data.
    
    Args:
        request_type: Type of request (loan, insurance, both)
        applicant_data: Applicant data dictionary
        loan_type: Type of loan (required if request_type includes loan)
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Validate request_type
    if request_type not in ["loan", "insurance", "both"]:
        errors.append(f"Invalid request_type: must be one of ['loan', 'insurance', 'both']")
        return False, errors
    
    # Validate loan_type if needed
    if request_type in ["loan", "both"]:
        if not loan_type:
            errors.append("loan_type is required when request_type is 'loan' or 'both'")
        else:
            valid_loan_types = [lt.value for lt in LoanType]
            if loan_type not in valid_loan_types:
                errors.append(f"Invalid loan_type: must be one of {valid_loan_types}")
    
    # Validate applicant data based on request type
    if request_type in ["loan", "both"]:
        is_valid, loan_errors = validate_loan_application(applicant_data)
        errors.extend(loan_errors)
    
    if request_type in ["insurance", "both"]:
        is_valid, insurance_errors = validate_insurance_application(applicant_data)
        errors.extend(insurance_errors)
    
    return len(errors) == 0, errors


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize input data to prevent injection attacks.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Sanitized data dictionary
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potentially malicious patterns
            value = value.strip()
            # Remove SQL injection patterns
            dangerous_patterns = ["--", ";", "/*", "*/", "xp_", "sp_", "DROP", "DELETE", "INSERT", "UPDATE"]
            for pattern in dangerous_patterns:
                if pattern.lower() in value.lower():
                    value = value.replace(pattern, "")
            # Limit string length
            value = value[:500]
        
        sanitized[key] = value
    
    return sanitized
