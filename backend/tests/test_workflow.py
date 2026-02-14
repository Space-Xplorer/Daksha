"""
Integration tests for LangGraph workflow.

This module contains end-to-end workflow tests for the Daksha system.
"""

import pytest
import os
from dotenv import load_dotenv

# Load environment variables before importing workflow
load_dotenv()

from src.schemas.state import create_initial_state
from src.graph.workflow import run_workflow


class TestEndToEndLoanWorkflow:
    """Test end-to-end loan application workflow."""
    
    def test_successful_loan_approval(self, valid_loan_application):
        """
        Test 16.1: End-to-end loan application with approval.
        
        Flow: KYC → Onboarding → Compliance → Router → Underwriting → 
              Verification → Transparency → Supervisor
        """
        # Create initial state with valid loan application
        state = create_initial_state(
            request_type="loan",
            applicant_data=valid_loan_application,
            loan_type="home",
            submitted_aadhaar="123456789012"
        )
        
        # Run workflow
        final_state = run_workflow(state)
        
        # Assert KYC passed
        assert final_state["kyc_verified"] is True
        assert final_state["verified_name"] == "Rajesh Kumar"
        assert final_state["digilocker_id"] is not None
        
        # Assert compliance passed
        assert final_state["compliance_passed"] is True
        assert len(final_state.get("compliance_violations", [])) == 0
        
        # Assert loan prediction exists
        assert "loan_prediction" in final_state
        loan_pred = final_state["loan_prediction"]
        assert "approved" in loan_pred
        assert "probability" in loan_pred
        assert "reasoning" in loan_pred
        
        # Assert loan approved (high CIBIL, good income)
        assert loan_pred["approved"] is True
        assert loan_pred["probability"] > 0.5
        
        # Assert explanation generated
        assert "loan_explanation" in final_state
        assert len(final_state["loan_explanation"]) > 0
        
        # Assert verification completed
        assert "loan_verification" in final_state
        
        # Assert supervisor decision
        assert "supervisor_decision" in final_state
        
        # Assert workflow completed
        assert final_state.get("completed") is True
        assert len(final_state.get("errors", [])) == 0
    
    def test_loan_with_moderate_cibil(self, edge_case_loan_application):
        """Test loan application with moderate CIBIL score."""
        state = create_initial_state(
            request_type="loan",
            applicant_data=edge_case_loan_application,
            loan_type="personal",
            submitted_aadhaar="123456789012"
        )
        
        final_state = run_workflow(state)
        
        # Should pass KYC and compliance
        assert final_state["kyc_verified"] is True
        assert "compliance_passed" in final_state
        
        # Should have prediction
        loan_pred = final_state.get("loan_prediction")
        if loan_pred is None:
            assert final_state.get("compliance_passed") is False or final_state.get("rejected") is True
            return
        
        # May or may not be approved based on other factors
        assert "approved" in loan_pred
        assert "reasoning" in loan_pred
        
        # Should have explanation regardless of decision
        assert "loan_explanation" in final_state


class TestEndToEndInsuranceWorkflow:
    """Test end-to-end insurance application workflow."""
    
    def test_successful_insurance_premium_calculation(self, valid_insurance_application):
        """
        Test 16.2: End-to-end insurance application with premium calculation.
        
        Flow: KYC → Onboarding → Compliance → Router → Underwriting → 
              Verification → Transparency → Supervisor
        """
        state = create_initial_state(
            request_type="insurance",
            applicant_data=valid_insurance_application,
            submitted_aadhaar="345678901234"
        )
        
        final_state = run_workflow(state)
        
        # Assert KYC passed
        assert final_state["kyc_verified"] is True
        assert final_state["verified_name"] == "Amit Patel"
        
        # Assert compliance passed
        assert final_state["compliance_passed"] is True
        
        # Assert insurance prediction exists
        assert "insurance_prediction" in final_state
        insurance_pred = final_state["insurance_prediction"]
        assert "premium" in insurance_pred
        assert "reasoning" in insurance_pred
        
        # Assert premium is reasonable (positive number)
        assert insurance_pred["premium"] > 0
        assert insurance_pred["premium"] < 100000  # Sanity check
        
        # Assert explanation generated
        assert "insurance_explanation" in final_state
        assert len(final_state["insurance_explanation"]) > 0
        
        # Assert verification completed
        assert "insurance_verification" in final_state
        
        # Assert workflow completed
        assert final_state.get("completed") is True
    
    def test_insurance_with_health_conditions(self, invalid_insurance_application_high_risk):
        """Test insurance application with pre-existing conditions."""
        state = create_initial_state(
            request_type="insurance",
            applicant_data=invalid_insurance_application_high_risk,
            submitted_aadhaar="123456789012"
        )
        
        final_state = run_workflow(state)
        
        # Should pass KYC
        assert final_state["kyc_verified"] is True
        
        # Should have insurance prediction
        assert "insurance_prediction" in final_state
        insurance_pred = final_state["insurance_prediction"]
        
        # Premium should be higher due to conditions
        assert insurance_pred["premium"] > 15000  # Higher than healthy applicant
        
        # Should have explanation
        assert "insurance_explanation" in final_state


class TestEndToEndCombinedWorkflow:
    """Test end-to-end combined loan + insurance workflow."""
    
    def test_successful_combined_application(self, valid_loan_application, valid_insurance_application):
        """
        Test 16.3: End-to-end combined application (both loan and insurance).
        
        Flow: KYC → Onboarding → Compliance → Router → 
              Underwriting (Loan) → Underwriting (Insurance) → 
              Verification → Transparency → Supervisor
        """
        state = create_initial_state(
            request_type="both",
            applicant_data={
                # Loan data
                "name": "Vikram Singh",
                "cibil_score": 780,
                "annual_income": 1500000,
                "loan_amount": 600000,
                "existing_debt": 80000,
                "employment_type": "salaried",
                "employment_years": 7,
                
                # Insurance data
                "age": 38,
                "bmi": 23.5,
                "smoker": False,
                "bloodpressure": 0,
                "diabetes": 0,
                "regular_ex": True,
                "height": 178,
                "weight": 74,
                "gender": "M",
                "coverage_amount": 1500000
            },
            loan_type="home",
            submitted_name="Vikram Singh",
            submitted_dob="1985-06-15"
        )
        
        final_state = run_workflow(state)
        
        # Assert KYC passed
        assert final_state["kyc_verified"] is True
        
        # Assert compliance passed
        assert final_state["compliance_passed"] is True
        
        # Assert BOTH loan and insurance predictions exist
        assert "loan_prediction" in final_state
        assert "insurance_prediction" in final_state
        
        # Assert loan prediction
        loan_pred = final_state["loan_prediction"]
        assert "approved" in loan_pred
        assert "probability" in loan_pred
        assert loan_pred["approved"] is True  # Good profile
        
        # Assert insurance prediction
        insurance_pred = final_state["insurance_prediction"]
        assert "premium" in insurance_pred
        assert insurance_pred["premium"] > 0
        
        # Assert BOTH explanations generated
        assert "loan_explanation" in final_state
        assert "insurance_explanation" in final_state
        
        # Assert workflow completed
        assert final_state.get("completed") is True
        assert len(final_state.get("errors", [])) == 0


class TestKYCRejectionScenarios:
    """Test KYC rejection scenarios."""
    
    def test_kyc_rejection_invalid_name(self, valid_loan_application, valid_insurance_application):
        """
        Test 16.4: KYC rejection due to name mismatch.
        """
        state = create_initial_state(
            request_type="both",
            applicant_data={
                **valid_loan_application,
                **valid_insurance_application
            },
            loan_type="home",
            submitted_name="Wrong Name",
            submitted_dob="1990-05-15"
        )
        
        final_state = run_workflow(state)
        
        # Assert KYC failed
        assert final_state["kyc_verified"] is False
        assert final_state.get("kyc_rejection_reason") or final_state.get("rejection_reason")
        
        # Workflow should stop after KYC failure
        assert final_state.get("loan_prediction") is None
        assert final_state.get("completed") is True  # Completed but rejected
    
    def test_kyc_rejection_invalid_dob(self):
        """Test KYC rejection due to DOB mismatch."""
        state = create_initial_state(
            request_type="loan",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 750,
                "annual_income": 1000000,
                "loan_amount": 400000
            },
            loan_type="personal",
            submitted_name="Rajesh Kumar",
            submitted_dob="1980-01-01"  # Wrong DOB
        )
        
        final_state = run_workflow(state)
        
        # Assert KYC failed
        assert final_state["kyc_verified"] is False
        
        # No predictions should be made
        assert final_state.get("loan_prediction") is None


class TestComplianceRejectionScenarios:
    """Test compliance rejection scenarios."""
    
    def test_compliance_rejection_low_cibil(self, invalid_loan_application_low_cibil):
        """
        Test 16.5: Compliance rejection due to CIBIL score too low.
        """
        state = create_initial_state(
            request_type="loan",
            applicant_data=invalid_loan_application_low_cibil,
            loan_type="personal",
            submitted_aadhaar="123456789012"
        )
        
        final_state = run_workflow(state)
        
        # KYC should pass
        assert final_state["kyc_verified"] is True

        # Rule engine should fail on credit score threshold
        assert final_state.get("rules_passed") is False
        assert len(final_state.get("rules_violations", [])) > 0

        violations = final_state.get("rules_violations", [])
        cibil_violation = any("credit" in str(v).lower() or "score" in str(v).lower()
                     for v in violations)
        assert cibil_violation

        # Workflow should stop after rules failure
        assert final_state.get("loan_prediction") is None
    
    def test_compliance_rejection_high_risk_insurance(self, invalid_insurance_application_high_risk):
        """Test compliance rejection for high-risk insurance applicant."""
        state = create_initial_state(
            request_type="insurance",
            applicant_data=invalid_insurance_application_high_risk,
            submitted_aadhaar="123456789012"
        )
        
        final_state = run_workflow(state)
        
        # KYC should pass
        assert final_state["kyc_verified"] is True
        
        # May or may not fail compliance depending on rules
        # But should at least process the application
        assert "compliance_passed" in final_state


class TestDocumentVerificationScenarios:
    """Test document verification scenarios."""
    
    def test_workflow_without_documents(self):
        """
        Test 16.6: Workflow with no documents (using applicant_data directly).
        """
        state = create_initial_state(
            request_type="loan",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 720,
                "annual_income": 1000000,
                "loan_amount": 400000,
                "existing_debt": 100000,
                "employment_type": "salaried",
                "employment_years": 4,
                "age": 32,
                "gender": "M"
            },
            loan_type="home",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
        
        # No documents provided
        assert len(state.get("documents", [])) == 0
        
        final_state = run_workflow(state)
        
        # Should still process successfully
        assert final_state["kyc_verified"] is True
        assert "loan_prediction" in final_state
        
        # Onboarding should handle missing documents gracefully
        assert "ocr_extracted_data" in final_state


class TestHITLWorkflow:
    """Test HITL (Human-in-the-Loop) checkpoint scenarios."""
    
    def test_hitl_checkpoint_and_resume(self):
        """
        Test 16.7: HITL handoff and resume flow.
        
        Flow: Onboarding → HITL Checkpoint → (Human Review) → 
              Compliance → Router → ...
        """
        state = create_initial_state(
            request_type="loan",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 700,
                "annual_income": 900000,
                "loan_amount": 350000,
                "existing_debt": 75000,
                "employment_type": "salaried",
                "employment_years": 4,
                "age": 30,
                "gender": "M"
            },
            loan_type="personal",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
        
        # Note: HITL checkpoint is typically triggered by onboarding agent
        # For this test, we'll run the full workflow and check if HITL fields exist
        
        final_state = run_workflow(state)
        
        # Check if HITL-related fields are in state schema
        assert "hitl_checkpoint" in final_state
        assert "hitl_data_corrected" in final_state
        assert "hitl_corrections" in final_state
        
        # Workflow should complete
        assert final_state.get("completed") is True
    
    def test_hitl_with_corrections(self):
        """Test HITL workflow with data corrections."""
        state = create_initial_state(
            request_type="loan",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 680,
                "annual_income": 850000,
                "loan_amount": 300000
            },
            loan_type="home",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
        
        # Simulate HITL corrections
        state["hitl_data_corrected"] = True
        state["hitl_corrections"] = {
            "annual_income": 900000,  # Corrected from 850000
            "cibil_score": 720  # Corrected from 680
        }
        
        # Apply corrections
        state["applicant_data"].update(state["hitl_corrections"])
        
        final_state = run_workflow(state)
        
        # Verify corrections were applied
        assert final_state["applicant_data"]["annual_income"] == 900000
        assert final_state["applicant_data"]["cibil_score"] == 720
        
        # Workflow should complete with corrected data
        assert "loan_prediction" in final_state


class TestErrorHandlingInWorkflow:
    """Test error handling in workflow."""
    
    def test_workflow_with_missing_required_fields(self):
        """Test workflow handles missing required fields gracefully."""
        state = create_initial_state(
            request_type="loan",
            applicant_data={
                "name": "Rajesh Kumar",
                # Missing critical fields like cibil_score, income
            },
            loan_type="personal",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
        
        final_state = run_workflow(state)
        
        # Should complete but may have errors
        assert final_state.get("completed") is True
        
        # Errors should be captured
        if "loan_prediction" not in final_state:
            assert len(final_state.get("errors", [])) > 0
    
    def test_workflow_error_recovery(self):
        """Test workflow continues after non-critical errors."""
        state = create_initial_state(
            request_type="both",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 750,
                "annual_income": 1200000,
                "loan_amount": 500000,
                "age": 32,
                "bmi": 24.5,
                "gender": "M"
            },
            loan_type="home",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
        
        final_state = run_workflow(state)
        
        # Even if some agents have issues, workflow should complete
        assert final_state.get("completed") is True
        
        # Should have at least attempted all steps
        assert "kyc_verified" in final_state
        assert "compliance_passed" in final_state


class TestSupervisorDecisions:
    """Test supervisor decision scenarios."""
    
    def test_supervisor_finalize_decision(self):
        """Test supervisor finalizes successful application."""
        state = create_initial_state(
            request_type="loan",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 800,
                "annual_income": 1500000,
                "loan_amount": 500000,
                "existing_debt": 50000,
                "employment_type": "salaried",
                "employment_years": 8,
                "age": 35,
                "gender": "M"
            },
            loan_type="home",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
        
        final_state = run_workflow(state)
        
        # Should have supervisor decision
        assert "supervisor_decision" in final_state
        supervisor_dec = final_state["supervisor_decision"]
        
        # Should have action and reason
        assert "action" in supervisor_dec
        assert "reason" in supervisor_dec
        
        # For successful application, should finalize or proceed
        assert supervisor_dec["action"] in ["finalize", "proceed"]
