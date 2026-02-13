"""
Unit tests for KYC Agent.

This module contains tests for KYC verification functionality.
"""

from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(ROOT_DIR))

from src.services.kyc import KYCAgent


@pytest.fixture
def agent():
	"""Create a KYC agent with the mock database."""
	db_path = SRC_DIR / "mock_db.json"
	return KYCAgent(db_path=str(db_path))


def _base_state():
	return {
		"request_id": "KYC-TEST",
		"errors": []
	}


def test_kyc_success(agent, monkeypatch):
	"""Valid name and DOB should verify successfully."""
	monkeypatch.setattr("src.services.kyc.time.sleep", lambda *_: None)

	state = _base_state()
	state.update({
		"submitted_aadhaar": "123456789012"
	})

	result = agent.verify_identity(state)

	assert result["kyc_verified"] is True
	assert result["digilocker_id"] == "DL8899ABCD1234"
	assert result["verified_name"] == "Rajesh Kumar"
	assert result["verified_dob"] == "19900515"
	assert result.get("rejected", False) is False


def test_kyc_success_with_whitespace(agent, monkeypatch):
	"""Name normalization should handle extra whitespace and casing."""
	monkeypatch.setattr("src.services.kyc.time.sleep", lambda *_: None)

	state = _base_state()
	state.update({
		"submitted_aadhaar": "1234 5678 9012"
	})

	result = agent.verify_identity(state)

	assert result["kyc_verified"] is True
	assert result["digilocker_id"] == "DL8899ABCD1234"


def test_kyc_failure_invalid_name(agent, monkeypatch):
	"""Invalid name should fail KYC verification."""
	monkeypatch.setattr("src.services.kyc.time.sleep", lambda *_: None)

	state = _base_state()
	state.update({
		"submitted_aadhaar": "999999999999"
	})

	result = agent.verify_identity(state)

	assert result["kyc_verified"] is False
	assert result.get("rejected", False) is True
	assert "KYC Failed" in result.get("rejection_reason", "")
	assert len(result.get("errors", [])) > 0


def test_kyc_failure_missing_data(agent):
	"""Missing DOB should be handled as a validation failure."""
	state = _base_state()
	state.update({
		"submitted_name": "Rajesh Kumar"
	})

	result = agent.verify_identity(state)

	assert result["kyc_verified"] is False
	assert result.get("rejected", False) is True
	assert "Missing KYC data" in result.get("rejection_reason", "")
