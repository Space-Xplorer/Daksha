"""
Generate realistic mock DigiLocker database with 100+ users.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

try:
    from faker import Faker
    fake = Faker('en_IN')  # Indian locale
except ImportError:
    print("Error: Faker library not installed.")
    print("Please install it with: pip install Faker")
    exit(1)


def generate_aadhaar():
    """Generate realistic Aadhaar number (12 digits)."""
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])


def generate_pan():
    """Generate realistic PAN number (5 letters + 4 digits + 1 letter)."""
    pan = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
    pan += ''.join([str(random.randint(0, 9)) for _ in range(4)])
    pan += random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    return pan


def generate_user(user_id: int) -> dict:
    """
    Generate realistic Indian user data.
    
    Args:
        user_id: Unique user ID
        
    Returns:
        Dictionary with user data
    """
    gender = random.choice(['Male', 'Female'])
    
    # Generate name based on gender
    if gender == 'Male':
        first_name = fake.first_name_male()
    else:
        first_name = fake.first_name_female()
    
    last_name = fake.last_name()
    name = f"{first_name} {last_name}"
    
    # Generate DOB (18-70 years old)
    dob = fake.date_of_birth(minimum_age=18, maximum_age=70)
    dob_str = dob.strftime('%Y%m%d')
    
    # Generate document numbers
    aadhaar = generate_aadhaar()
    pan = generate_pan()
    
    # Generate DigiLocker ID
    digilocker_id = f"DL{random.randint(1000, 9999)}{fake.lexify('????').upper()}"
    
    # Generate passport number (optional - 70% have passport)
    passport = f"P{random.randint(1000000, 9999999)}" if random.random() < 0.7 else None
    
    # Generate voter ID
    voter_id = f"{fake.lexify('???').upper()}{random.randint(1000000, 9999999)}"
    
    # Generate address
    address = fake.address().replace('\n', ', ')
    
    return {
        "digilockerid": digilocker_id,
        "name": name,
        "dob": dob_str,
        "gender": gender,
        "address": address,
        "aadhaar_number": aadhaar,
        "aadhaar_last4": aadhaar[-4:],
        "pan": pan,
        "pan_number": pan,
        "passport_number": passport,
        "voter_id_number": voter_id
    }


def generate_edge_case_users() -> dict:
    """Generate edge case users for testing."""
    edge_cases = {}
    
    # User with special characters in name
    edge_cases["user_edge_001"] = {
        "digilockerid": "DL9999EDGE",
        "name": "Ramesh Kumar O'Brien-Patel",
        "dob": "19880722",
        "gender": "Male",
        "address": "123, St. Mary's Road, O'Connor Street, Bangalore-560001",
        "aadhaar_number": "123456789012",
        "aadhaar_last4": "9012",
        "pan": "ABCDE1234F",
        "pan_number": "ABCDE1234F",
        "passport_number": "P1234567",
        "voter_id_number": "ABC1234567"
    }
    
    # User with very long name
    edge_cases["user_edge_002"] = {
        "digilockerid": "DL9998LONG",
        "name": "Srinivasa Ramanujan Iyengar Venkataraman Subramanian",
        "dob": "19921130",
        "gender": "Male",
        "address": "456, Thiruvanmiyur Main Road, Chennai-600041",
        "aadhaar_number": "987654321098",
        "aadhaar_last4": "1098",
        "pan": "FGHIJ5678K",
        "pan_number": "FGHIJ5678K",
        "passport_number": "P9876543",
        "voter_id_number": "DEF9876543"
    }
    
    # User with single name
    edge_cases["user_edge_003"] = {
        "digilockerid": "DL9997SING",
        "name": "Madonna",
        "dob": "19950315",
        "gender": "Female",
        "address": "789, MG Road, Pune-411001",
        "aadhaar_number": "456789012345",
        "aadhaar_last4": "2345",
        "pan": "KLMNO9012P",
        "pan_number": "KLMNO9012P",
        "passport_number": None,
        "voter_id_number": "GHI4567890"
    }
    
    # User with numbers in address
    edge_cases["user_edge_004"] = {
        "digilockerid": "DL9996ADDR",
        "name": "Priya Sharma",
        "dob": "19850320",
        "gender": "Female",
        "address": "Flat 101, Building A-2, Sector 15, Noida-201301",
        "aadhaar_number": "234567890123",
        "aadhaar_last4": "0123",
        "pan": "PQRST3456U",
        "pan_number": "PQRST3456U",
        "passport_number": "P2345678",
        "voter_id_number": "JKL2345678"
    }
    
    # User with common name (for duplicate testing)
    edge_cases["user_edge_005"] = {
        "digilockerid": "DL9995COMM",
        "name": "Rahul Kumar",
        "dob": "19900515",
        "gender": "Male",
        "address": "12, Gandhi Nagar, Delhi-110001",
        "aadhaar_number": "345678901234",
        "aadhaar_last4": "1234",
        "pan": "VWXYZ6789A",
        "pan_number": "VWXYZ6789A",
        "passport_number": "P3456789",
        "voter_id_number": "MNO3456789"
    }
    
    return edge_cases


def generate_test_scenarios() -> dict:
    """Generate comprehensive test scenarios."""
    return {
        "valid_kyc_male": {
            "name": "Rajesh Kumar",
            "dob": "1990-05-15",
            "expected_result": "SUCCESS",
            "description": "Valid KYC for male user"
        },
        "valid_kyc_female": {
            "name": "Priya Sharma",
            "dob": "1985-03-20",
            "expected_result": "SUCCESS",
            "description": "Valid KYC for female user"
        },
        "invalid_name": {
            "name": "John Doe",
            "dob": "1990-05-15",
            "expected_result": "FAILED",
            "reason": "Name not found in database",
            "description": "Invalid name test"
        },
        "invalid_dob": {
            "name": "Rajesh Kumar",
            "dob": "1990-05-16",
            "expected_result": "FAILED",
            "reason": "DOB mismatch",
            "description": "Invalid DOB test"
        },
        "special_characters": {
            "name": "Ramesh Kumar O'Brien-Patel",
            "dob": "1988-07-22",
            "expected_result": "SUCCESS",
            "description": "Name with special characters"
        },
        "long_name": {
            "name": "Srinivasa Ramanujan Iyengar Venkataraman Subramanian",
            "dob": "1992-11-30",
            "expected_result": "SUCCESS",
            "description": "Very long name"
        },
        "single_name": {
            "name": "Madonna",
            "dob": "1995-03-15",
            "expected_result": "SUCCESS",
            "description": "Single name (no surname)"
        },
        "aadhaar_last4_only": {
            "aadhaar": "9012",
            "expected_result": "SUCCESS",
            "note": "Partial Aadhaar match",
            "description": "Match using last 4 digits of Aadhaar"
        },
        "case_insensitive": {
            "name": "RAJESH KUMAR",
            "dob": "1990-05-15",
            "expected_result": "SUCCESS",
            "description": "Case insensitive name matching"
        },
        "whitespace_handling": {
            "name": "  Rajesh   Kumar  ",
            "dob": "1990-05-15",
            "expected_result": "SUCCESS",
            "description": "Name with extra whitespace"
        }
    }


def main():
    """Generate mock database and save to file."""
    print("🔧 Generating realistic mock DigiLocker database...")
    print()
    
    # Generate regular users
    print("📝 Generating 100 regular users...")
    users = {}
    for i in range(1, 101):
        user_key = f"user_{i:04d}"
        users[user_key] = generate_user(i)
        if i % 20 == 0:
            print(f"  Generated {i}/100 users...")
    
    print("✅ Regular users generated")
    print()
    
    # Add edge case users
    print("🔍 Adding edge case users...")
    edge_cases = generate_edge_case_users()
    users.update(edge_cases)
    print(f"✅ Added {len(edge_cases)} edge case users")
    print()
    
    # Generate test scenarios
    print("📋 Generating test scenarios...")
    test_scenarios = generate_test_scenarios()
    print(f"✅ Generated {len(test_scenarios)} test scenarios")
    print()
    
    # Create final database structure
    database = {
        "users": users,
        "test_scenarios": test_scenarios,
        "metadata": {
            "version": "2.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "description": "Enhanced mock DigiLocker database for production testing",
            "total_users": len(users),
            "regular_users": 100,
            "edge_case_users": len(edge_cases),
            "test_scenarios": len(test_scenarios),
            "generated_by": "generate_mock_db.py"
        }
    }
    
    # Save to file
    output_path = Path(__file__).parent.parent / 'src' / 'mock_db.json'
    print(f"💾 Saving to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print("✅ Mock database generated successfully!")
    print()
    print("📊 Summary:")
    print(f"  Total users: {len(users)}")
    print(f"  Regular users: 100")
    print(f"  Edge case users: {len(edge_cases)}")
    print(f"  Test scenarios: {len(test_scenarios)}")
    print(f"  Output file: {output_path}")
    print()
    print("🎉 Done!")


if __name__ == "__main__":
    main()
