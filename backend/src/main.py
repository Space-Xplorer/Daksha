"""
Main entry point for the Daksha Orchestration System.

This module provides example usage and testing functionality.
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.schemas.state import create_initial_state
from src.graph.workflow import run_workflow
from src.utils.logging import setup_logging


def main():
    """Main entry point for testing the Daksha system."""
    
    # Setup logging
    setup_logging("INFO", "daksha_system.log", True)
    
    print("=" * 70)
    print("Daksha Orchestration System")
    print("=" * 70)
    print()
    
    # Example 1: Loan Application
    print("Example 1: Loan Application")
    print("-" * 70)
    
    loan_state = create_initial_state(
        request_type="loan",
        applicant_data={
            "cibil_score": 750,
            "annual_income": 1200000.0,
            "loan_amount": 500000.0,
            "employment_type": "salaried",
            "existing_debt": 100000.0,
            "age": 32,
            "employment_years": 5
        },
        loan_type="home",
        submitted_name="Rajesh Kumar",
        submitted_dob="1990-05-15"
    )
    
    print(f"Request ID: {loan_state['request_id']}")
    print(f"Request Type: {loan_state['request_type']}")
    print(f"Loan Type: {loan_state['loan_type']}")
    print()
    
    # Run workflow
    final_state = run_workflow(loan_state)
    
    # Display results
    print("Results:")
    print(f"  KYC Verified: {final_state['kyc_verified']}")
    print(f"  Compliance Passed: {final_state['compliance_passed']}")
    print(f"  Loan Approved: {final_state.get('loan_prediction', {}).get('approved', 'N/A')}")
    print(f"  Approval Probability: {final_state.get('loan_prediction', {}).get('probability', 0):.1%}")
    print(f"  Explanation: {final_state.get('loan_explanation', 'N/A')}")
    print(f"  Errors: {len(final_state['errors'])}")
    print()
    
    # Example 2: Insurance Application
    print("Example 2: Insurance Application")
    print("-" * 70)
    
    insurance_state = create_initial_state(
        request_type="insurance",
        applicant_data={
            "age": 32,
            "bmi": 24.5,
            "smoker": False,
            "coverage_amount": 1000000.0
        },
        submitted_name="Priya Sharma",
        submitted_dob="1985-03-20"
    )
    
    print(f"Request ID: {insurance_state['request_id']}")
    print(f"Request Type: {insurance_state['request_type']}")
    print()
    
    # Run workflow
    final_state = run_workflow(insurance_state)
    
    # Display results
    print("Results:")
    print(f"  KYC Verified: {final_state['kyc_verified']}")
    print(f"  Compliance Passed: {final_state['compliance_passed']}")
    print(f"  Premium: ₹{final_state.get('insurance_prediction', {}).get('premium', 'N/A'):,.2f}")
    print(f"  Explanation: {final_state.get('insurance_explanation', 'N/A')}")
    print(f"  Errors: {len(final_state['errors'])}")
    print()
    
    # Example 3: Combined Application
    print("Example 3: Combined Loan + Insurance Application")
    print("-" * 70)
    
    combined_state = create_initial_state(
        request_type="both",
        applicant_data={
            "cibil_score": 750,
            "annual_income": 1200000.0,
            "loan_amount": 500000.0,
            "employment_type": "salaried",
            "existing_debt": 100000.0,
            "age": 32,
            "employment_years": 5,
            "bmi": 24.5,
            "smoker": False,
            "coverage_amount": 1000000.0
        },
        loan_type="home",
        submitted_name="Amit Patel",
        submitted_dob="1992-07-10"
    )
    
    print(f"Request ID: {combined_state['request_id']}")
    print(f"Request Type: {combined_state['request_type']}")
    print()
    
    # Run workflow
    final_state = run_workflow(combined_state)
    
    # Display results
    print("Results:")
    print(f"  KYC Verified: {final_state['kyc_verified']}")
    print(f"  Compliance Passed: {final_state['compliance_passed']}")
    print(f"  Loan Approved: {final_state.get('loan_prediction', {}).get('approved', 'N/A')}")
    print(f"  Loan Probability: {final_state.get('loan_prediction', {}).get('probability', 0):.1%}")
    print(f"  Insurance Premium: ₹{final_state.get('insurance_prediction', {}).get('premium', 'N/A'):,.2f}")
    print(f"  Loan Explanation: {final_state.get('loan_explanation', 'N/A')}")
    print(f"  Insurance Explanation: {final_state.get('insurance_explanation', 'N/A')}")
    print(f"  Errors: {len(final_state['errors'])}")
    print()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

