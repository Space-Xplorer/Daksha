"""
Unit tests for Underwriting Agent.

This module tests the UnderwritingAgent class and its methods.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agents.underwriting import UnderwritingAgent, process_underwriting
from schemas.state import ApplicationState


class TestUnderwritingAgent:
    """Test cases for UnderwritingAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create an UnderwritingAgent instance."""
        return UnderwritingAgent()
    
    @pytest.fixture
    def loan_state(self, valid_loan_application) -> ApplicationState:
        """Create a sample loan application state from dataset-backed fixture."""
        return {
            "request_id": "TEST-001",
            "request_type": "loan",
            "applicant_data": valid_loan_application,
            "declared_data": valid_loan_application,
            "errors": []
        }
    
    @pytest.fixture
    def insurance_state(self, valid_insurance_application) -> ApplicationState:
        """Create a sample insurance application state from dataset-backed fixture."""
        return {
            "request_id": "TEST-002",
            "request_type": "insurance",
            "applicant_data": valid_insurance_application,
            "declared_data": valid_insurance_application,
            "errors": []
        }
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent is not None
        assert agent.credit_model is not None
        assert agent.health_model is not None
        assert agent.credit_encoders is not None
        assert agent.health_encoders is not None
    
    def test_process_loan(self, agent, loan_state):
        """Test loan processing."""
        result = agent.process_loan(loan_state)
        
        # Check that loan_prediction was added
        assert "loan_prediction" in result
        
        prediction = result["loan_prediction"]
        assert "approved" in prediction
        assert "probability" in prediction
        assert "reasoning" in prediction
        
        # Check types
        assert isinstance(prediction["approved"], bool)
        assert isinstance(prediction["probability"], float)
        assert isinstance(prediction["reasoning"], dict)
        
        # Check probability is valid
        assert 0.0 <= prediction["probability"] <= 1.0
        
        # Check reasoning has features
        assert len(prediction["reasoning"]) > 0
    
    def test_process_insurance(self, agent, insurance_state):
        """Test insurance processing."""
        result = agent.process_insurance(insurance_state)
        
        # Check that insurance_prediction was added
        assert "insurance_prediction" in result
        
        prediction = result["insurance_prediction"]
        assert "premium" in prediction
        assert "reasoning" in prediction
        
        # Check types
        assert isinstance(prediction["premium"], float)
        assert isinstance(prediction["reasoning"], dict)
        
        # Check premium is positive
        assert prediction["premium"] > 0
        
        # Check reasoning has features
        assert len(prediction["reasoning"]) > 0
    
    def test_process_underwriting_loan(self, loan_state):
        """Test convenience function for loan."""
        result = process_underwriting(loan_state)
        
        assert "loan_prediction" in result
        assert "approved" in result["loan_prediction"]
    
    def test_process_underwriting_insurance(self, insurance_state):
        """Test convenience function for insurance."""
        result = process_underwriting(insurance_state)
        
        assert "insurance_prediction" in result
        assert "premium" in result["insurance_prediction"]
    
    def test_process_underwriting_both(self, valid_loan_application, valid_insurance_application):
        """Test processing both loan and insurance."""
        combined = {**valid_loan_application, **valid_insurance_application}
        state: ApplicationState = {
            "request_id": "TEST-003",
            "request_type": "both",
            "applicant_data": combined,
            "declared_data": combined,
            "errors": []
        }
        
        result = process_underwriting(state)
        
        # Both predictions should be present
        assert "loan_prediction" in result
        assert "insurance_prediction" in result
        
        # Validate loan prediction
        assert "approved" in result["loan_prediction"]
        assert isinstance(result["loan_prediction"]["approved"], bool)
        
        # Validate insurance prediction
        assert "premium" in result["insurance_prediction"]
        assert result["insurance_prediction"]["premium"] > 0
    
    def test_high_cibil_approval(self, agent, valid_loan_application):
        """Test that high CIBIL score increases approval probability."""
        # High CIBIL applicant
        high_cibil_state: ApplicationState = {
            "request_id": "TEST-004",
            "request_type": "loan",
            "applicant_data": valid_loan_application,
            "declared_data": valid_loan_application,
            "errors": []
        }
        
        result = agent.process_loan(high_cibil_state)
        
        # High CIBIL should have good approval probability
        assert result["loan_prediction"]["probability"] > 0.6
    
    def test_low_cibil_rejection(self, agent, invalid_loan_application_low_cibil):
        """Test that low CIBIL score decreases approval probability."""
        # Low CIBIL applicant
        low_cibil_state: ApplicationState = {
            "request_id": "TEST-005",
            "request_type": "loan",
            "applicant_data": invalid_loan_application_low_cibil,
            "declared_data": invalid_loan_application_low_cibil,
            "errors": []
        }
        
        result = agent.process_loan(low_cibil_state)
        
        # Low CIBIL should have lower approval probability
        assert result["loan_prediction"]["probability"] <= 0.5
    
    def test_error_handling_no_applicant_data(self, agent):
        """Test error handling when applicant_data is missing."""
        empty_state: ApplicationState = {
            "request_id": "TEST-006",
            "request_type": "loan",
            "errors": []
        }
        
        result = agent.process_loan(empty_state)
        
        # Should handle error gracefully
        assert len(result.get("errors", [])) > 0
        assert "loan_prediction" not in result or result.get("loan_prediction") is None


def test_underwriting_with_mock_models(monkeypatch):
    """Use mock models to validate underwriting output structure."""
    class DummyExplanation:
        def data(self):
            return {"names": ["cibil_score", "income_annum"], "scores": [1.5, 0.7]}

    class DummyClassifier:
        def predict_proba(self, _features):
            return [[0.2, 0.8]]

        def explain_local(self, _features):
            return DummyExplanation()

    class DummyRegressor:
        def predict(self, _features):
            return [12345.0]

        def explain_local(self, _features):
            return DummyExplanation()

    def _mock_load_models(self):
        self.credit_model = DummyClassifier()
        self.health_model = DummyRegressor()
        self.credit_encoders = {}
        self.health_encoders = {}

    monkeypatch.setattr("agents.underwriting.UnderwritingAgent._load_models", _mock_load_models)

    agent = UnderwritingAgent()

    state: ApplicationState = {
        "request_id": "TEST-MOCK",
        "request_type": "both",
        "applicant_data": {
            "cibil_score": 720,
            "income_annum": 1200000,
            "loan_amount": 2500000,
            "age": 30
        },
        "declared_data": {
            "cibil_score": 720,
            "income_annum": 1200000,
            "loan_amount": 2500000,
            "age": 30
        },
        "errors": []
    }

    result = agent.process_loan(state)
    assert result["loan_prediction"]["approved"] in [True, False]
    assert 0.0 <= result["loan_prediction"]["probability"] <= 1.0

    result = agent.process_insurance(state)
    assert result["insurance_prediction"]["premium"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
