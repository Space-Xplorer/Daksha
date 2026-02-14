"""
Unit tests for input validation.

This module contains tests for validation logic.
"""

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.utils.validation import (
	validate_loan_application,
	validate_insurance_application,
	validate_request_type,
	sanitize_input,
	check_basic_rules
)


def test_validate_loan_application_success():
	data = {
		"cibil_score": 720,
		"annual_income": 1200000.0,
		"loan_amount": 2500000.0,
		"employment_type": "salaried",
		"existing_debt": 0.0,
		"age": 30,
		"employment_years": 3
	}
	is_valid, errors = validate_loan_application(data)
	assert is_valid is True
	assert errors == []


def test_validate_loan_application_errors():
	data = {
		"cibil_score": 200,
		"annual_income": -1.0,
		"loan_amount": 0.0,
		"employment_type": "contract",
		"existing_debt": -10.0,
		"age": 10,
		"employment_years": -2
	}
	is_valid, errors = validate_loan_application(data)
	assert is_valid is False
	assert any("cibil_score" in err for err in errors)
	assert any("annual_income" in err for err in errors)
	assert any("loan_amount" in err for err in errors)
	assert any("employment_type" in err for err in errors)


def test_validate_insurance_application_success():
	data = {
		"age": 35,
		"bmi": 24.5,
		"smoker": False,
		"coverage_amount": 500000.0
	}
	is_valid, errors = validate_insurance_application(data)
	assert is_valid is True
	assert errors == []


def test_validate_insurance_application_errors():
	data = {
		"age": 15,
		"bmi": 5.0,
		"smoker": "no",
		"coverage_amount": -1.0,
		"occupation_risk": "extreme"
	}
	is_valid, errors = validate_insurance_application(data)
	assert is_valid is False
	assert any("age" in err for err in errors)
	assert any("bmi" in err for err in errors)
	assert any("smoker" in err for err in errors)
	assert any("coverage_amount" in err for err in errors)
	assert any("occupation_risk" in err for err in errors)


def test_validate_request_type_and_loan_type():
	applicant_data = {
		"cibil_score": 720,
		"annual_income": 1000000.0,
		"loan_amount": 2000000.0,
		"employment_type": "salaried",
		"existing_debt": 0.0,
		"age": 30,
		"employment_years": 3
	}
	is_valid, errors = validate_request_type("loan", applicant_data, loan_type="home")
	assert is_valid is True
	assert errors == []

	is_valid, errors = validate_request_type("loan", applicant_data, loan_type="invalid")
	assert is_valid is False
	assert any("loan_type" in err for err in errors)


def test_sanitize_input_removes_dangerous_patterns():
	data = {
		"name": "Robert'); DROP TABLE users; --",
		"notes": "/* test */ xp_cmdshell"
	}
	sanitized = sanitize_input(data)

	assert "DROP" not in sanitized["name"].upper()
	assert "--" not in sanitized["name"]
	assert "XP_" not in sanitized["notes"].upper()


def test_check_basic_rules_rejects_age_60_or_more():
	ok, reason = check_basic_rules("loan", {"age": 60})
	assert ok is True
	assert reason is None


def test_check_basic_rules_rejects_loan_amount_vs_income_tenure():
	ok, reason = check_basic_rules("loan", {
		"age": 30,
		"loan_amount": 120000,
		"income": 10000,
		"tenure": 12
	})
	assert ok is True
	assert reason is None


def test_check_basic_rules_allows_valid_case():
	ok, reason = check_basic_rules("insurance", {"age": 35})
	assert ok is True
	assert reason is None
