"""
Unit tests for Transparency Agent.

This module contains tests for explanation generation.
"""

from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.agents.transparency import TransparencyAgent


def test_transparency_loan_explanation(monkeypatch):
    """Loan explanation should be generated and non-empty."""
    agent = TransparencyAgent()

    def _mock_llm(_prompt: str, fallback: str) -> str:
        return fallback

    monkeypatch.setattr(agent, "_run_llm_or_fallback", _mock_llm)

    state = {
        "request_id": "TRANS-LOAN",
        "request_type": "loan",
        "loan_prediction": {
            "approved": True,
            "probability": 0.82,
            "reasoning": {"cibil_score": 1.2, "income_annum": 0.6}
        },
        "errors": []
    }

    result = agent.explain_loan_decision(state)

    assert isinstance(result.get("loan_explanation"), str)
    assert len(result["loan_explanation"]) >= 20


def test_transparency_insurance_explanation(monkeypatch):
    """Insurance explanation should be generated and non-empty."""
    agent = TransparencyAgent()

    def _mock_llm(_prompt: str, fallback: str) -> str:
        return fallback

    monkeypatch.setattr(agent, "_run_llm_or_fallback", _mock_llm)

    state = {
        "request_id": "TRANS-INS",
        "request_type": "insurance",
        "insurance_prediction": {
            "premium": 18500.0,
            "reasoning": {"age": 0.8, "bmi": 0.3}
        },
        "errors": []
    }

    result = agent.explain_insurance_premium(state)

    assert isinstance(result.get("insurance_explanation"), str)
    assert len(result["insurance_explanation"]) >= 20
