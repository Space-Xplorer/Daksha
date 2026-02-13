"""
Pytest configuration and shared fixtures.

This module provides fixtures for testing the Daksha system.
"""

import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "models" / "data"
LOAN_DATA_PATH = DATA_DIR / "loan_data.csv"
HEALTH_DATA_PATH = DATA_DIR / "hi.csv"


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    cleaned = str(value).strip()
    if cleaned == "":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    parsed = _parse_float(value)
    if parsed is None:
        return None
    try:
        return int(parsed)
    except (ValueError, TypeError):
        return None


def _load_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _load_loan_rows() -> List[Dict[str, Any]]:
    rows = []
    for row in _load_csv_rows(LOAN_DATA_PATH):
        rows.append({
            "no_of_dependents": _parse_int(row.get("no_of_dependents")),
            "education": (row.get("education") or "").strip(),
            "self_employed": (row.get("self_employed") or "").strip(),
            "income_annum": _parse_float(row.get("income_annum")),
            "loan_amount": _parse_float(row.get("loan_amount")),
            "loan_term": _parse_float(row.get("loan_term")),
            "cibil_score": _parse_float(row.get("cibil_score")),
            "residential_assets_value": _parse_float(row.get("residential_assets_value")) or 0.0,
            "commercial_assets_value": _parse_float(row.get("commercial_assets_value")) or 0.0,
            "luxury_assets_value": _parse_float(row.get("luxury_assets_value")) or 0.0,
            "bank_asset_value": _parse_float(row.get("bank_asset_value")) or 0.0,
            "loan_status": (row.get("loan_status") or "").strip()
        })
    return rows


def _load_health_rows() -> List[Dict[str, Any]]:
    rows = []
    for row in _load_csv_rows(HEALTH_DATA_PATH):
        rows.append({
            "age": _parse_int(row.get("age")),
            "sex": (row.get("sex") or "").strip(),
            "weight": _parse_float(row.get("weight")),
            "bmi": _parse_float(row.get("bmi")),
            "hereditary_diseases": (row.get("hereditary_diseases") or "").strip(),
            "no_of_dependents": _parse_int(row.get("no_of_dependents")),
            "smoker": _parse_int(row.get("smoker")),
            "city": (row.get("city") or "").strip(),
            "bloodpressure": _parse_float(row.get("bloodpressure")),
            "diabetes": _parse_int(row.get("diabetes")),
            "regular_ex": _parse_int(row.get("regular_ex")),
            "job_title": (row.get("job_title") or "").strip(),
            "claim": _parse_float(row.get("claim"))
        })
    return rows


# ============================================================================
# Loan Application Fixtures
# ============================================================================

@pytest.fixture
def valid_loan_application() -> Dict[str, Any]:
    """Valid loan application data."""
    rows = [row for row in _load_loan_rows() if row.get("cibil_score") and row.get("income_annum") and row.get("loan_amount")]
    rows.sort(key=lambda r: r.get("cibil_score") or 0, reverse=True)
    pick = rows[0] if rows else {}
    return {
        "cibil_score": pick.get("cibil_score", 750),
        "income_annum": pick.get("income_annum", 1200000.0),
        "annual_income": pick.get("income_annum", 1200000.0),
        "loan_amount": pick.get("loan_amount", 500000.0),
        "loan_term": pick.get("loan_term", 12),
        "education": pick.get("education", "Graduate"),
        "self_employed": pick.get("self_employed", "No"),
        "no_of_dependents": pick.get("no_of_dependents", 1),
        "residential_assets_value": pick.get("residential_assets_value", 0.0),
        "commercial_assets_value": pick.get("commercial_assets_value", 0.0),
        "luxury_assets_value": pick.get("luxury_assets_value", 0.0),
        "bank_asset_value": pick.get("bank_asset_value", 0.0),
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
    rows = [row for row in _load_loan_rows() if row.get("cibil_score") and row.get("income_annum") and row.get("loan_amount")]
    rows.sort(key=lambda r: r.get("cibil_score") or 9999)
    pick = rows[0] if rows else {}
    return {
        "cibil_score": pick.get("cibil_score", 550),
        "income_annum": pick.get("income_annum", 600000.0),
        "annual_income": pick.get("income_annum", 600000.0),
        "loan_amount": pick.get("loan_amount", 500000.0),
        "loan_term": pick.get("loan_term", 12),
        "education": pick.get("education", "Not Graduate"),
        "self_employed": pick.get("self_employed", "No"),
        "no_of_dependents": pick.get("no_of_dependents", 2),
        "residential_assets_value": pick.get("residential_assets_value", 0.0),
        "commercial_assets_value": pick.get("commercial_assets_value", 0.0),
        "luxury_assets_value": pick.get("luxury_assets_value", 0.0),
        "bank_asset_value": pick.get("bank_asset_value", 0.0),
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
    rows = [row for row in _load_loan_rows() if row.get("cibil_score") and row.get("income_annum") and row.get("loan_amount")]
    rows.sort(key=lambda r: r.get("cibil_score") or 0)
    pick = rows[len(rows) // 2] if rows else {}
    return {
        "cibil_score": pick.get("cibil_score", 650),
        "income_annum": pick.get("income_annum", 800000.0),
        "annual_income": pick.get("income_annum", 800000.0),
        "loan_amount": pick.get("loan_amount", 400000.0),
        "loan_term": pick.get("loan_term", 12),
        "education": pick.get("education", "Graduate"),
        "self_employed": pick.get("self_employed", "No"),
        "no_of_dependents": pick.get("no_of_dependents", 1),
        "residential_assets_value": pick.get("residential_assets_value", 0.0),
        "commercial_assets_value": pick.get("commercial_assets_value", 0.0),
        "luxury_assets_value": pick.get("luxury_assets_value", 0.0),
        "bank_asset_value": pick.get("bank_asset_value", 0.0),
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
    rows = [row for row in _load_health_rows() if row.get("age") and row.get("bmi") is not None and row.get("smoker") is not None]
    rows = [row for row in rows if row.get("smoker") == 0 and (row.get("diabetes") or 0) == 0]
    rows = [row for row in rows if (row.get("age") or 0) < 60]
    pick = rows[0] if rows else {}
    return {
        "age": pick.get("age", 32),
        "bmi": pick.get("bmi", 24.5),
        "smoker": pick.get("smoker", 0),
        "bloodpressure": pick.get("bloodpressure", 0),
        "diabetes": pick.get("diabetes", 0),
        "regular_ex": pick.get("regular_ex", 1),
        "sex": pick.get("sex", "male"),
        "hereditary_diseases": pick.get("hereditary_diseases", "NoDisease"),
        "no_of_dependents": pick.get("no_of_dependents", 0),
        "city": pick.get("city", "Boston"),
        "job_title": pick.get("job_title", "Engineer"),
        "coverage_amount": 1000000.0,
        "name": "Rajesh Kumar"
    }


@pytest.fixture
def invalid_insurance_application_high_risk() -> Dict[str, Any]:
    """Invalid insurance application with high risk factors."""
    rows = [row for row in _load_health_rows() if row.get("age") and row.get("bmi") is not None and row.get("smoker") is not None]
    rows = [row for row in rows if row.get("smoker") == 1 or (row.get("diabetes") or 0) == 1]
    rows.sort(key=lambda r: r.get("bmi") or 0, reverse=True)
    pick = rows[0] if rows else {}
    return {
        "age": pick.get("age", 55),
        "bmi": pick.get("bmi", 32.0),
        "smoker": pick.get("smoker", 1),
        "bloodpressure": pick.get("bloodpressure", 1),
        "diabetes": pick.get("diabetes", 1),
        "regular_ex": pick.get("regular_ex", 0),
        "sex": pick.get("sex", "male"),
        "hereditary_diseases": pick.get("hereditary_diseases", "NoDisease"),
        "no_of_dependents": pick.get("no_of_dependents", 1),
        "city": pick.get("city", "NewYork"),
        "job_title": pick.get("job_title", "Manager"),
        "coverage_amount": 2000000.0,
        "name": "Test User"
    }


@pytest.fixture
def edge_case_insurance_application() -> Dict[str, Any]:
    """Edge case insurance application (borderline premium)."""
    rows = [row for row in _load_health_rows() if row.get("age") and row.get("bmi") is not None and row.get("smoker") is not None]
    rows.sort(key=lambda r: r.get("age") or 0)
    pick = rows[len(rows) // 2] if rows else {}
    return {
        "age": pick.get("age", 40),
        "bmi": pick.get("bmi", 27.0),
        "smoker": pick.get("smoker", 0),
        "bloodpressure": pick.get("bloodpressure", 0),
        "diabetes": pick.get("diabetes", 1),
        "regular_ex": pick.get("regular_ex", 1),
        "sex": pick.get("sex", "female"),
        "hereditary_diseases": pick.get("hereditary_diseases", "NoDisease"),
        "no_of_dependents": pick.get("no_of_dependents", 1),
        "city": pick.get("city", "Boston"),
        "job_title": pick.get("job_title", "Engineer"),
        "coverage_amount": 1500000.0,
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
        submitted_aadhaar="123456789012"
    )


@pytest.fixture
def initial_insurance_state(valid_insurance_application):
    """Initial state for insurance application."""
    from src.schemas.state import create_initial_state
    
    return create_initial_state(
        request_type="insurance",
        applicant_data=valid_insurance_application,
        submitted_aadhaar="123456789012"
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
        submitted_aadhaar="123456789012"
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
