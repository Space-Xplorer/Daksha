"""
Unit tests for Compliance Agent.

This module contains tests for regulatory compliance checking.
"""

from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.agents.compliance import ComplianceAgent


def _base_state(request_type: str):
	return {
		"request_id": "COMP-TEST",
		"request_type": request_type,
		"applicant_data": {},
		"errors": []
	}


def _force_rule_based(agent: ComplianceAgent) -> None:
	agent.llm = None
	agent.rules_db = None


def test_loan_compliance_low_cibil_critical():
	"""Low CIBIL should trigger a CRITICAL violation and rejection."""
	agent = ComplianceAgent(groq_api_key=None)
	_force_rule_based(agent)

	state = _base_state("loan")
	state["loan_type"] = "home"
	state["applicant_data"] = {
		"cibil_score": 600,
		"annual_income": 800000,
		"loan_amount": 3000000,
		"existing_debt": 0,
		"age": 30,
		"employment_years": 3
	}

	result = agent.check_compliance(state)

	assert result["compliance_checked"] is True
	assert result["compliance_passed"] is False
	assert result.get("rejected", False) is True
	assert len(result.get("compliance_violations", [])) > 0

	violation = result["compliance_violations"][0]
	assert violation["severity"] == "CRITICAL"
	assert "CIBIL" in violation["reason"]


def test_insurance_compliance_high_bmi_high():
	"""High BMI should trigger a HIGH violation but not rejection by itself."""
	agent = ComplianceAgent(groq_api_key=None)
	_force_rule_based(agent)

	state = _base_state("insurance")
	state["applicant_data"] = {
		"age": 40,
		"bmi": 36.5,
		"smoker": False,
		"coverage_amount": 500000
	}

	result = agent.check_compliance(state)

	assert result["compliance_checked"] is True
	assert result["compliance_passed"] is True
	assert result.get("rejected", False) is False
	assert any(v["severity"] == "HIGH" for v in result["compliance_violations"])


def test_compliance_violation_schema():
	"""Violations should include rule, reason, and severity fields."""
	agent = ComplianceAgent(groq_api_key=None)
	_force_rule_based(agent)

	state = _base_state("loan")
	state["loan_type"] = "personal"
	state["applicant_data"] = {
		"cibil_score": 500,
		"annual_income": 500000,
		"loan_amount": 2500000,
		"existing_debt": 100000,
		"age": 25,
		"employment_years": 1
	}

	result = agent.check_compliance(state)
	violations = result.get("compliance_violations", [])

	assert len(violations) > 0
	for violation in violations:
		assert set(["rule", "reason", "severity"]).issubset(violation.keys())
		assert violation["severity"] in ["CRITICAL", "HIGH", "MEDIUM"]
