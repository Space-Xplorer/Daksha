"""
ApplicationState TypedDict definition.

This module defines the main state object passed through the LangGraph workflow.
"""

from typing import TypedDict, Literal, Optional, Dict, List, Any
from datetime import datetime


class ApplicationState(TypedDict, total=False):
    """
    Main state object passed through the LangGraph workflow.
    
    This state is updated by each agent as the application flows through
    the system. All fields are optional to allow incremental updates.
    """
    
    # Request metadata
    request_id: str
    request_type: Literal["loan", "insurance", "both"]
    loan_type: Optional[str]  # "home", "personal", "vehicle", "business"
    timestamp: str
    
    # KYC data (from Mock DigiLocker)
    kyc_verified: bool
    kyc_attempted: bool
    digilocker_id: Optional[str]
    verified_name: Optional[str]
    verified_dob: Optional[str]
    verified_gender: Optional[str]
    submitted_name: Optional[str]
    submitted_dob: Optional[str]
    
    # Uploaded documents
    uploaded_documents: List[Dict[str, Any]]  # [{type, file_path, content}, ...]
    
    # OCR extracted data (pre-filled form)
    extracted_data: Dict[str, Any]
    
    # User-edited data (final applicant data)
    applicant_data: Dict[str, Any]
    
    # Document verification
    document_verification: Dict[str, Any]
    onboarding_completed: bool
    
    # Compliance check results
    compliance_checked: bool
    compliance_passed: bool
    compliance_violations: List[Dict[str, str]]  # [{rule, reason, severity}, ...]
    
    # ML model outputs
    loan_prediction: Optional[Dict[str, Any]]  # {approved: bool, probability: float, reasoning: dict}
    insurance_prediction: Optional[Dict[str, Any]]  # {premium: float, reasoning: dict}
    
    # LLM verification
    loan_verified: bool
    insurance_verified: bool
    loan_verification: Optional[Dict[str, Any]]  # {verified: bool, concerns: list, confidence: float}
    insurance_verification: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    
    # Explanation outputs
    loan_explanation: Optional[str]
    insurance_explanation: Optional[str]
    
    # Supervisor decision
    supervisor_decision: Optional[Dict[str, Any]]
    supervisor_action: Optional[Literal["proceed", "request_more_info", "reject", "finalize"]]
    escalate_to_human: bool
    escalation_reason: Optional[str]
    
    # HITL (Human-in-the-Loop)
    hitl_checkpoint: bool  # Whether workflow is paused for human review
    hitl_data_corrected: bool  # Whether human has corrected the data
    hitl_corrections: Optional[Dict[str, Any]]  # User corrections to extracted data
    
    # Retry and loopback
    retry_count: int
    loopback_requested: bool
    loopback_target: Optional[str]  # Which agent to loop back to
    loopback_reason: Optional[str]
    
    # Error categorization
    error_category: Optional[str]
    error_routing: Optional[str]
    
    # Workflow control
    current_agent: str
    errors: List[Any]  # Can be strings or dicts with error details
    completed: bool
    rejected: bool
    rejection_reason: Optional[str]


def create_initial_state(
    request_type: Literal["loan", "insurance", "both"],
    applicant_data: Dict[str, Any],
    loan_type: Optional[str] = None,
    submitted_name: Optional[str] = None,
    submitted_dob: Optional[str] = None,
    uploaded_documents: Optional[List[Dict[str, Any]]] = None
) -> ApplicationState:
    """
    Create an initial ApplicationState with required fields.
    
    Args:
        request_type: Type of request (loan, insurance, or both)
        applicant_data: Initial applicant data
        loan_type: Type of loan if request_type includes loan
        submitted_name: Name submitted for KYC verification
        submitted_dob: Date of birth submitted for KYC verification
        uploaded_documents: List of uploaded documents
        
    Returns:
        ApplicationState with initialized fields
    """
    import uuid
    
    state: ApplicationState = {
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "request_type": request_type,
        "loan_type": loan_type,
        "timestamp": datetime.utcnow().isoformat(),
        
        # KYC
        "kyc_verified": False,
        "kyc_attempted": False,
        "submitted_name": submitted_name,
        "submitted_dob": submitted_dob,
        
        # Documents
        "uploaded_documents": uploaded_documents or [],
        "extracted_data": {},
        "applicant_data": applicant_data,
        "document_verification": {},
        "onboarding_completed": False,
        
        # Compliance
        "compliance_checked": False,
        "compliance_passed": False,
        "compliance_violations": [],
        
        # Predictions
        "loan_prediction": None,
        "insurance_prediction": None,
        
        # Verification
        "loan_verified": False,
        "insurance_verified": False,
        "loan_verification": None,
        "insurance_verification": None,
        "verification_result": None,
        
        # Explanations
        "loan_explanation": None,
        "insurance_explanation": None,
        
        # Supervisor
        "supervisor_decision": None,
        "supervisor_action": None,
        "escalate_to_human": False,
        "escalation_reason": None,
        
        # HITL
        "hitl_checkpoint": False,
        "hitl_data_corrected": False,
        "hitl_corrections": None,
        
        # Retry and loopback
        "retry_count": 0,
        "loopback_requested": False,
        "loopback_target": None,
        "loopback_reason": None,
        
        # Error categorization
        "error_category": None,
        "error_routing": None,
        
        # Workflow
        "current_agent": "kyc",
        "errors": [],
        "completed": False,
        "rejected": False,
        "rejection_reason": None
    }
    
    return state


# Field mappings for loan applications
LOAN_FIELDS = {
    "cibil_score": int,
    "annual_income": float,
    "income_annum": float,  # Alias for annual_income
    "loan_amount": float,
    "employment_type": str,
    "existing_debt": float,
    "age": int,
    "employment_years": int,
    "bank_asset_value": float,
    "residential_assets_value": float,
    "commercial_ assets_value": float,
    "luxury_assets_value": float,
    "gender": str,
    "name": str
}

# Field mappings for insurance applications
INSURANCE_FIELDS = {
    "age": int,
    "bmi": float,
    "height": float,
    "weight": float,
    "smoker": bool,
    "pre_existing_conditions": list,
    "family_history": list,
    "occupation_risk": str,
    "coverage_amount": float,
    "bloodpressure": int,  # Binary: 0=normal, 1=high
    "diabetes": int,  # Binary: 0=no, 1=yes
    "regular_ex": bool,  # Regular exercise
    "hereditary_diseases": bool,
    "cholesterol": float,
    "heart_rate": int,
    "hba1c": float,
    "blood_sugar": float,
    "creatinine": float,
    "gender": str,
    "name": str
}

# Document type enums
LOAN_DOCUMENT_TYPES = [
    "cibil_report",
    "salary_slip",
    "itr_form16",
    "bank_statement",
    "property_document",
    "vehicle_registration",
    "aadhaar_card",
    "pan_card"
]

INSURANCE_DOCUMENT_TYPES = [
    "diagnostic_report",
    "physical_exam",
    "medical_declaration",
    "family_medical_records",
    "ecg_report",
    "prescription_history",
    "discharge_summary",
    "aadhaar_card",
    "pan_card"
]

# Loan type enum
LOAN_TYPES = ["home", "personal", "vehicle", "business"]
