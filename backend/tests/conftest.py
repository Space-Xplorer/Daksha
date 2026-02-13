"""
Pytest configuration and shared fixtures.

This module provides fixtures for testing the Daksha system.
"""

import pytest
from typing import Dict, Any
from datetime import datetime


# ============================================================================
# Loan Application Fixtures
# ============================================================================

@pytest.fixture
def valid_loan_application() -> Dict[str, Any]:
    """Valid loan application data."""
    return {
        "cibil_score": 750,
        "annual_income": 1200000.0,
        "loan_amount": 500000.0,
        "employment_type": "salaried",
        "existing_debt": 100000.0,
        "age": 32,
        "employment_years": 5,
        "gender": "M",
        "name": "Rajesh Kumar"
    }


@pytest.fixture
def invalid_loan_application_low_cibil() -> Dict[str, Any]:
    """Invalid loan application with low CIBIL score."""
    return {
        "cibil_score": 550,  # Too low
        "annual_income": 600000.0,
        "loan_amount": 500000.0,
        "employment_type": "salaried",
        "existing_debt": 200000.0,
        "age": 28,
        "employment_years": 2,
        "gender": "M",
        "name": "Test User"
    }


@pytest.fixture
def edge_case_loan_application() -> Dict[str, Any]:
    """Edge case loan application (borderline approval)."""
    return {
        "cibil_score": 650,  # Borderline
        "annual_income": 800000.0,
        "loan_amount": 400000.0,
        "employment_type": "self_employed",
        "existing_debt": 150000.0,
        "age": 45,
        "employment_years": 10,
        "gender": "F",
        "name": "Priya Sharma"
    }


# ============================================================================
# Insurance Application Fixtures
# ============================================================================

@pytest.fixture
def valid_insurance_application() -> Dict[str, Any]:
    """Valid insurance application data."""
    return {
        "age": 32,
        "bmi": 24.5,
        "smoker": False,
        "pre_existing_conditions": [],
        "family_history": [],
        "occupation_risk": "low",
        "coverage_amount": 1000000.0,
        "bloodpressure": 0,  # Normal
        "diabetes": 0,  # No
        "regular_ex": True,
        "gender": "M",
        "name": "Rajesh Kumar"
    }


@pytest.fixture
def invalid_insurance_application_high_risk() -> Dict[str, Any]:
    """Invalid insurance application with high risk factors."""
    return {
        "age": 55,
        "bmi": 32.0,  # Obese
        "smoker": True,
        "pre_existing_conditions": ["diabetes", "hypertension"],
        "family_history": ["heart_disease"],
        "occupation_risk": "high",
        "coverage_amount": 2000000.0,
        "bloodpressure": 1,  # High
        "diabetes": 1,  # Yes
        "regular_ex": False,
        "gender": "M",
        "name": "Test User"
    }


@pytest.fixture
def edge_case_insurance_application() -> Dict[str, Any]:
    """Edge case insurance application (borderline premium)."""
    return {
        "age": 40,
        "bmi": 27.0,  # Slightly overweight
        "smoker": False,
        "pre_existing_conditions": ["diabetes"],
        "family_history": [],
        "occupation_risk": "medium",
        "coverage_amount": 1500000.0,
        "bloodpressure": 0,
        "diabetes": 1,  # Controlled diabetes
        "regular_ex": True,
        "gender": "F",
        "name": "Priya Sharma"
    }


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_response_loan_approved():
    """Mock LLM response for loan approval explanation."""
    return {
        "content": "Your loan application has been approved with high confidence. "
                  "Your excellent credit score of 750 and stable income are the primary "
                  "factors supporting this decision. Your existing debt is manageable "
                  "relative to your income."
    }


@pytest.fixture
def mock_llm_response_insurance_premium():
    """Mock LLM response for insurance premium explanation."""
    return {
        "content": "Your annual health insurance premium is ₹18,500. This rate is "
                  "primarily influenced by your age (32) and healthy lifestyle. "
                  "Your good BMI and non-smoking status help keep the premium reasonable."
    }


@pytest.fixture
def mock_llm_verification_approved():
    """Mock LLM verification response for approved decision."""
    return {
        "verified": True,
        "confidence": 0.9,
        "concerns": [],
        "recommendation": "APPROVE"
    }


@pytest.fixture
def mock_llm_verification_concerns():
    """Mock LLM verification response with concerns."""
    return {
        "verified": False,
        "confidence": 0.6,
        "concerns": ["Low confidence decision", "Borderline CIBIL score"],
        "recommendation": "REVIEW"
    }


@pytest.fixture
def mock_ocr_extraction_cibil():
    """Mock OCR extraction for CIBIL report."""
    return {
        "document_type": "cibil_report",
        "extracted_fields": {
            "cibil_score": 750,
            "name": "RAJESH KUMAR",
            "report_date": "2024-01-15"
        },
        "confidence": 0.95
    }


@pytest.fixture
def mock_ocr_extraction_salary_slip():
    """Mock OCR extraction for salary slip."""
    return {
        "document_type": "salary_slip",
        "extracted_fields": {
            "gross_salary": 100000.0,
            "net_salary": 85000.0,
            "month": "January 2024",
            "employee_name": "Rajesh Kumar"
        },
        "confidence": 0.92
    }


@pytest.fixture
def mock_model_prediction_loan_approved():
    """Mock model prediction for loan approval."""
    return {
        "approved": True,
        "probability": 0.87,
        "reasoning": {
            "cibil_score": 5.07,
            "annual_income": 2.34,
            "existing_debt": -1.23,
            "employment_years": 0.89,
            "age": 0.45
        }
    }


@pytest.fixture
def mock_model_prediction_loan_rejected():
    """Mock model prediction for loan rejection."""
    return {
        "approved": False,
        "probability": 0.32,
        "reasoning": {
            "cibil_score": -4.12,
            "annual_income": -1.56,
            "existing_debt": -2.34,
            "employment_years": -0.67,
            "age": 0.23
        }
    }


@pytest.fixture
def mock_model_prediction_insurance():
    """Mock model prediction for insurance premium."""
    return {
        "premium": 18500.0,
        "reasoning": {
            "age": 2.15,
            "bmi": 0.34,
            "pre_existing_conditions": 3.45,
            "smoker": 0.0,
            "occupation_risk": 0.12
        }
    }


# ============================================================================
# State Fixtures
# ============================================================================

@pytest.fixture
def initial_loan_state(valid_loan_application):
    """Initial state for loan application."""
    from src.schemas.state import create_initial_state
    
    return create_initial_state(
        request_type="loan",
        applicant_data=valid_loan_application,
        loan_type="home",
        submitted_name="Rajesh Kumar",
        submitted_dob="1990-05-15"
    )


@pytest.fixture
def initial_insurance_state(valid_insurance_application):
    """Initial state for insurance application."""
    from src.schemas.state import create_initial_state
    
    return create_initial_state(
        request_type="insurance",
        applicant_data=valid_insurance_application,
        submitted_name="Rajesh Kumar",
        submitted_dob="1990-05-15"
    )


@pytest.fixture
def initial_both_state(valid_loan_application, valid_insurance_application):
    """Initial state for combined loan and insurance application."""
    from src.schemas.state import create_initial_state
    
    # Merge loan and insurance data
    combined_data = {**valid_loan_application, **valid_insurance_application}
    
    return create_initial_state(
        request_type="both",
        applicant_data=combined_data,
        loan_type="home",
        submitted_name="Rajesh Kumar",
        submitted_dob="1990-05-15"
    )


# ============================================================================
# Mock Agent Fixtures
# ============================================================================

@pytest.fixture
def mock_kyc_success():
    """Mock KYC verification success."""
    return {
        "status": "SUCCESS",
        "verified_id": "DL123456789",
        "name": "Rajesh Kumar",
        "dob": "19900515",
        "gender": "M"
    }


@pytest.fixture
def mock_kyc_failure():
    """Mock KYC verification failure."""
    return {
        "status": "FAILED",
        "reason": "Data mismatch with DigiLocker record"
    }


@pytest.fixture
def mock_compliance_passed():
    """Mock compliance check passed."""
    return {
        "compliance_passed": True,
        "compliance_violations": []
    }


@pytest.fixture
def mock_compliance_failed():
    """Mock compliance check failed."""
    return {
        "compliance_passed": False,
        "compliance_violations": [
            {
                "rule": "Minimum CIBIL Score",
                "reason": "CIBIL score 550 is below minimum requirement of 640",
                "severity": "CRITICAL"
            }
        ]
    }
