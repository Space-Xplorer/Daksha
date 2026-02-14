"""
Unit tests for Onboarding Agent.

This module contains tests for document processing and OCR functionality.
"""

from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.agents.onboarding import OnboardingAgent
from src.utils.ocr_service_mock import OCRService


@pytest.fixture
def agent():
	return OnboardingAgent()


def _base_state(request_type: str):
	return {
		"request_id": "ONBOARD-TEST",
		"request_type": request_type,
		"uploaded_documents": [],
		"declared_data": {},
		"ocr_extracted_data": {},
		"applicant_data": {},
		"errors": []
	}


def test_document_classification_cibil_salary_diagnostic():
	"""OCRService should classify common document types correctly."""
	ocr = OCRService()

	text_cibil = "CIBIL CREDIT REPORT\nCIBIL Score: 750"
	assert ocr.classify_document(text_cibil, filename="cibil_report.pdf") == "cibil_report"

	text_salary = "SALARY SLIP\nGross Salary: Rs 100,000"
	assert ocr.classify_document(text_salary, filename="salary_slip.pdf") == "salary_slip"

	text_diag = "DIAGNOSTIC REPORT\nHbA1c: 5.8%"
	assert ocr.classify_document(text_diag, filename="diagnostic_report.pdf") == "diagnostic_report"


def test_onboarding_extracts_loan_fields(agent):
	"""Loan documents should yield expected financial fields."""
	state = _base_state("loan")
	state["uploaded_documents"] = [
		{"file_path": "cibil_report.pdf"},
		{"file_path": "salary_slip.pdf"},
		{"file_path": "bank_statement.pdf"}
	]

	result = agent.process_documents(state)

	extracted = result.get("ocr_extracted_data", {})
	assert extracted.get("cibil_score") == 750
	assert extracted.get("income_annum") == 1200000.0
	assert extracted.get("bank_asset_value") == 250000.0

	assert result.get("onboarding_completed") is True
	assert result.get("document_verification") is not None
	assert result["declared_data"].get("cibil_score") is None


def test_onboarding_extracts_health_fields(agent):
	"""Health documents should yield expected medical fields."""
	state = _base_state("insurance")
	state["uploaded_documents"] = [
		{"file_path": "diagnostic_report.pdf"},
		{"file_path": "physical_exam.pdf"}
	]

	result = agent.process_documents(state)

	extracted = result.get("ocr_extracted_data", {})
	assert extracted.get("hba1c") == 5.8
	assert extracted.get("diabetes") == 0
	assert extracted.get("cholesterol") == 180.0
	assert extracted.get("blood_sugar") == 95.0

	assert extracted.get("height_cm") == 175.0
	assert extracted.get("weight_kg") == 75.0
	assert extracted.get("bmi") == pytest.approx(24.49, rel=1e-2)
	assert extracted.get("systolic_bp") == 120
	assert extracted.get("diastolic_bp") == 80
	assert extracted.get("bloodpressure") == 0
	assert extracted.get("heart_rate") == 72

	assert result.get("onboarding_completed") is True
	assert result.get("document_verification") is not None


def test_onboarding_handles_no_documents(agent):
	"""No uploaded documents should still complete onboarding."""
	state = _base_state("loan")

	result = agent.process_documents(state)

	assert result.get("onboarding_completed") is True
	assert result.get("ocr_extracted_data") == {}
	assert result.get("document_verification") == {}
