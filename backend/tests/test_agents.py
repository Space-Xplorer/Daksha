"""
Unit tests for all agents.

This module contains general agent tests.
"""

from pathlib import Path
import sys
import pickle

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.agents.router import RouterAgent
from src.utils.model_loader import ModelLoader


def _base_state(request_type: str):
	return {
		"request_id": "AGENT-TEST",
		"request_type": request_type,
		"errors": []
	}


def test_router_invalid_request_type():
	agent = RouterAgent()
	state = _base_state("invalid")

	result = agent.route_request(state)

	assert result["current_agent"] == "error"
	assert len(result["errors"]) > 0


def test_router_both_routes_to_loan_first():
	agent = RouterAgent()
	state = _base_state("both")

	result = agent.route_request(state)

	assert result["current_agent"] == "underwriting_loan"


def test_model_loader_singleton_and_cache(tmp_path):
	ModelLoader._instance = None
	ModelLoader._models = {}

	dummy_path = tmp_path / "dummy.pkl"
	with open(dummy_path, "wb") as f:
		pickle.dump({"name": "dummy"}, f)

	loader_one = ModelLoader(models_dir=str(tmp_path))
	loaded = loader_one.load_model("dummy")

	assert loaded == {"name": "dummy"}
	assert loader_one.get_model("dummy") == {"name": "dummy"}

	loader_two = ModelLoader(models_dir=str(tmp_path / "other"))

	assert loader_one is loader_two
	assert loader_two.get_model("dummy") == {"name": "dummy"}
