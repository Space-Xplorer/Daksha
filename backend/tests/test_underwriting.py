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
    def loan_state(self) -> ApplicationState:
        """Create a sample loan application state."""
        return {
            "request_id": "TEST-001",
            "request_type": "loan",
            "applicant_data": {
                "cibil_score": 750,
                "income_annum": 1200000,
                "loan_amount": 5000000,
                "loan_tenure": 240,
                "residential_assets_value": 2000000,
                "commercial_assets_value": 0,
                "luxury_assets_value": 500000,
                "bank_asset_value": 1000000,
                "age": 35,
                "employment_type": "Salaried",
                "education": "Graduate",
                "no_of_dependents": 2,
                "existing_debt": 500000,
                "loan_to_income_ratio": 4.17
            },
            "errors": []
        }
    
    @pytest.fixture
    def insurance_state(self) -> ApplicationState:
        """Create a sample insurance application state."""
        return {
            "request_id": "TEST-002",
            "request_type": "insurance",
            "applicant_data": {
                "age": 35,
                "gender": "Male",
                "bmi": 24.5,
                "children": 2,
                "smoker": "No",
                "region": "southwest",
                "diabetes": False,
                "blood_pressure_problems": False,
                "any_transplants": False,
                "any_chronic_diseases": False,
                "height": 175,
                "weight": 75,
                "known_allergies": False,
                "history_of_cancer_in_family": False
            },
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
    
    def test_process_underwriting_both(self):
        """Test processing both loan and insurance."""
        state: ApplicationState = {
            "request_id": "TEST-003",
            "request_type": "both",
            "applicant_data": {
                # Loan fields
                "cibil_score": 780,
                "income_annum": 1500000,
                "loan_amount": 3000000,
                "loan_tenure": 180,
                "residential_assets_value": 3000000,
                "commercial_assets_value": 0,
                "luxury_assets_value": 800000,
                "bank_asset_value": 1500000,
                "existing_debt": 200000,
                "loan_to_income_ratio": 2.0,
                # Insurance fields
                "age": 32,
                "gender": "Female",
                "bmi": 22.5,
                "children": 1,
                "smoker": "No",
                "region": "northeast",
                "diabetes": False,
                "blood_pressure_problems": False,
                "any_transplants": False,
                "any_chronic_diseases": False,
                "height": 165,
                "weight": 61,
                "known_allergies": False,
                "history_of_cancer_in_family": False,
                # Common fields
                "employment_type": "Salaried",
                "education": "Graduate",
                "no_of_dependents": 1
            },
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
    
    def test_high_cibil_approval(self, agent):
        """Test that high CIBIL score increases approval probability."""
        # High CIBIL applicant
        high_cibil_state: ApplicationState = {
            "request_id": "TEST-004",
            "request_type": "loan",
            "applicant_data": {
                "cibil_score": 850,
                "income_annum": 2000000,
                "loan_amount": 3000000,
                "loan_tenure": 240,
                "residential_assets_value": 5000000,
                "commercial_assets_value": 0,
                "luxury_assets_value": 1000000,
                "bank_asset_value": 2000000,
                "age": 40,
                "employment_type": "Salaried",
                "education": "Post Graduate",
                "no_of_dependents": 2,
                "existing_debt": 100000,
                "loan_to_income_ratio": 1.5
            },
            "errors": []
        }
        
        result = agent.process_loan(high_cibil_state)
        
        # High CIBIL should have good approval probability
        assert result["loan_prediction"]["probability"] > 0.6
    
    def test_low_cibil_rejection(self, agent):
        """Test that low CIBIL score decreases approval probability."""
        # Low CIBIL applicant
        low_cibil_state: ApplicationState = {
            "request_id": "TEST-005",
            "request_type": "loan",
            "applicant_data": {
                "cibil_score": 550,
                "income_annum": 500000,
                "loan_amount": 5000000,
                "loan_tenure": 300,
                "residential_assets_value": 500000,
                "commercial_assets_value": 0,
                "luxury_assets_value": 0,
                "bank_asset_value": 100000,
                "age": 25,
                "employment_type": "Self Employed",
                "education": "Not Graduate",
                "no_of_dependents": 3,
                "existing_debt": 1000000,
                "loan_to_income_ratio": 10.0
            },
            "errors": []
        }
        
        result = agent.process_loan(low_cibil_state)
        
        # Low CIBIL with high debt should have low approval probability
        assert result["loan_prediction"]["probability"] < 0.5
    
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

    monkeypatch.setattr("src.agents.underwriting.UnderwritingAgent._load_models", _mock_load_models)

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
        "errors": []
    }

    result = agent.process_loan(state)
    assert result["loan_prediction"]["approved"] is True
    assert result["loan_prediction"]["probability"] == 0.8

    result = agent.process_insurance(state)
    assert result["insurance_prediction"]["premium"] == 12345.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
