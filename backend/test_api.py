"""
Quick test script for Daksha API.

This script tests the basic API endpoints to ensure everything is working.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health endpoint."""
    print("\n1. Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_register():
    """Test user registration."""
    print("\n2. Testing User Registration...")
    data = {
        "email": "test@example.com",
        "password": "test123",
        "name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code in [201, 409]  # 409 if already exists

def test_login():
    """Test user login."""
    print("\n3. Testing User Login...")
    data = {
        "email": "test@example.com",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   User: {result.get('user', {}).get('email')}")
    
    if response.status_code == 200:
        return result.get('access_token')
    return None

def test_create_application(token):
    """Test application creation."""
    print("\n4. Testing Application Creation...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "request_type": "both",
        "loan_type": "home",
        "submitted_name": "Rajesh Kumar",
        "submitted_dob": "1990-05-15",
        "applicant_data": {
            "cibil_score": 750,
            "annual_income": 1200000,
            "loan_amount": 500000,
            "existing_debt": 100000,
            "employment_type": "salaried",
            "employment_years": 5,
            "age": 32,
            "bmi": 24.5,
            "smoker": False
        }
    }
    response = requests.post(f"{BASE_URL}/applications/", json=data, headers=headers)
    print(f"   Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 201:
        app_id = result.get('application', {}).get('id')
        print(f"   Application ID: {app_id}")
        return app_id
    return None

def test_list_applications(token):
    """Test listing applications."""
    print("\n5. Testing List Applications...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/applications/", headers=headers)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Total Applications: {result.get('count', 0)}")
    return response.status_code == 200

def test_submit_workflow(token, app_id):
    """Test workflow submission."""
    print("\n6. Testing Workflow Submission...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/workflow/submit/{app_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Request ID: {result.get('request_id')}")
    print(f"   Workflow Status: {result.get('status')}")
    return response.status_code == 202

def test_workflow_status(token, app_id):
    """Test workflow status check."""
    print("\n7. Testing Workflow Status...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/workflow/status/{app_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Workflow Status: {result.get('status')}")
    print(f"   KYC Verified: {result.get('kyc_verified')}")
    print(f"   Compliance Passed: {result.get('compliance_passed')}")
    return response.status_code == 200

def main():
    """Run all tests."""
    print("="*60)
    print("DAKSHA API TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Health
        if not test_health():
            print("\n❌ Health check failed!")
            return
        
        # Test 2: Register
        test_register()
        
        # Test 3: Login
        token = test_login()
        if not token:
            print("\n❌ Login failed!")
            return
        
        # Test 4: Create Application
        app_id = test_create_application(token)
        if not app_id:
            print("\n❌ Application creation failed!")
            return
        
        # Test 5: List Applications
        test_list_applications(token)
        
        # Test 6: Submit Workflow
        if test_submit_workflow(token, app_id):
            # Test 7: Check Status
            import time
            time.sleep(2)  # Wait for workflow to process
            test_workflow_status(token, app_id)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server!")
        print("   Make sure the API is running: python run_api.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()
