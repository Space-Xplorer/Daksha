"""
Unit tests for Verification Agent.

This module contains tests for verification logic.
"""

from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.agents.verification import VerificationAgent


def test_verification_loan_fallback():
    """Fallback path should return a valid verification result for loans."""
    agent = VerificationAgent()
    agent.llm = None
    agent.parser = None

    state = {
        "request_id": "VERIFY-LOAN",
        "request_type": "loan",
        "loan_prediction": {
            "approved": True,
            "probability": 0.9,
            "reasoning": {"cibil_score": 1.2}
        },
        "applicant_data": {
            "cibil_score": 720,
            "annual_income": 1200000,
            "loan_amount": 2000000,
            "existing_debt": 0,
            "age": 30,
            "employment_type": "salaried",
            "employment_years": 3
        },
        "errors": []
    }

    result = agent.verify_decision(state)

    verification = result.get("loan_verification")
    assert verification is not None
    assert "verified" in verification
    assert "confidence" in verification
    assert "concerns" in verification
    assert "recommendation" in verification


def test_verification_insurance_fallback():
    """Fallback path should return a valid verification result for insurance."""
    agent = VerificationAgent()
    agent.llm = None
    agent.parser = None

    state = {
        "request_id": "VERIFY-INS",
        "request_type": "insurance",
        "insurance_prediction": {
            "premium": 120000.0,
            "reasoning": {"age": 1.1}
        },
        "applicant_data": {
            "age": 25,
            "bmi": 22.0,
            "smoker": False,
            "occupation_risk": "low"
        },
        "errors": []
    }

    result = agent.verify_decision(state)

    verification = result.get("insurance_verification")
    assert verification is not None
    assert "verified" in verification
    assert "confidence" in verification
    assert "concerns" in verification
    assert "recommendation" in verification
