"""
KYC Service with Mock DigiLocker integration.

This module implements identity verification using a mock DigiLocker API.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.schemas.state import ApplicationState
from src.utils.logging import log_agent_execution, log_error


class MockDigiLockerAPI:
    """
    Mock DigiLocker API for KYC verification.
    
    This simulates the DigiLocker API for testing purposes.
    In production, this would be replaced with actual DigiLocker integration.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Mock DigiLocker API.
        
        Args:
            db_path: Path to mock database JSON file
        """
        if db_path is None:
            self.db_path = Path(__file__).resolve().parents[1] / "mock_db.json"
        else:
            self.db_path = Path(db_path)
        self.db = self._load_database()
    
    def _load_database(self) -> Dict[str, Any]:
        """Load mock database from JSON file."""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            log_error("system", f"Mock database not found at {self.db_path}")
            return {"users": {}}
        except json.JSONDecodeError as e:
            log_error("system", f"Invalid JSON in mock database: {e}")
            return {"users": {}}
    
    def verify_kyc(
        self,
        submitted_aadhaar: Optional[str] = None,
        submitted_name: Optional[str] = None,
        submitted_dob: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify user against mock DigiLocker database.
        
        Args:
            submitted_aadhaar: Aadhaar number submitted by user (12 digits)
            submitted_name: Name submitted by user (fallback)
            submitted_dob: Date of birth submitted by user (format: YYYY-MM-DD or YYYYMMDD)
            
        Returns:
            Dictionary with verification result:
            - status: "SUCCESS" or "FAILED"
            - verified_id: DigiLocker ID (if success)
            - name: Verified name (if success)
            - dob: Verified DOB (if success)
            - gender: Verified gender (if success)
            - reason: Failure reason (if failed)
        """
        # Simulate network delay
        time.sleep(1.5)
        
        submitted_name_normalized = submitted_name.strip().lower() if submitted_name else ""
        submitted_dob_normalized = submitted_dob.replace("-", "").replace("/", "") if submitted_dob else ""
        submitted_aadhaar_normalized = ""
        if submitted_aadhaar:
            # Extract only digits from Aadhaar (remove spaces, dashes, etc.)
            submitted_aadhaar_normalized = re.sub(r"\D", "", submitted_aadhaar)
        
        # Debug logging
        print(f"[KYC DEBUG] Submitted Aadhaar (raw): '{submitted_aadhaar}'")
        print(f"[KYC DEBUG] Submitted Aadhaar (normalized): '{submitted_aadhaar_normalized}'")
        print(f"[KYC DEBUG] Submitted Aadhaar length: {len(submitted_aadhaar_normalized) if submitted_aadhaar_normalized else 0}")
        print(f"[KYC DEBUG] Submitted Name (normalized): '{submitted_name_normalized}'")
        print(f"[KYC DEBUG] Submitted DOB (normalized): '{submitted_dob_normalized}'")
        
        # Search for matching user in database
        for user_id, user_data in self.db.get("users", {}).items():
            db_name = user_data.get("name", "").strip().lower()
            db_dob = user_data.get("dob", "")
            db_aadhaar = user_data.get("aadhaar_number", "")
            db_aadhaar_last4 = user_data.get("aadhaar_last4", "")
            
            # Debug logging
            print(f"[KYC DEBUG] Checking DB user: {user_id}")
            print(f"[KYC DEBUG]   DB Aadhaar: '{db_aadhaar}' (last 4: '{db_aadhaar_last4}')")
            print(f"[KYC DEBUG]   DB Name: '{db_name}'")
            print(f"[KYC DEBUG]   DB DOB: '{db_dob}'")

            aadhaar_match = False
            if submitted_aadhaar_normalized:
                if len(submitted_aadhaar_normalized) == 4:
                    aadhaar_match = submitted_aadhaar_normalized == db_aadhaar_last4
                    print(f"[KYC DEBUG]   Last 4 match: {aadhaar_match}")
                else:
                    aadhaar_match = submitted_aadhaar_normalized == db_aadhaar
                    print(f"[KYC DEBUG]   Full Aadhaar match: {aadhaar_match}")

            name_match = submitted_name_normalized == db_name if submitted_name_normalized else False
            dob_match = submitted_dob_normalized == db_dob if submitted_dob_normalized else False
            
            print(f"[KYC DEBUG]   Name match: {name_match}, DOB match: {dob_match}")

            if aadhaar_match or (name_match and dob_match):
                print(f"[KYC DEBUG] ✓ MATCH FOUND for user {user_id}")
                return {
                    "status": "SUCCESS",
                    "verified_id": user_data.get("digilockerid"),
                    "name": user_data.get("name"),
                    "dob": user_data.get("dob"),
                    "gender": user_data.get("gender"),
                    "aadhaar_number": user_data.get("aadhaar_number"),
                    "pan_number": user_data.get("pan_number", user_data.get("pan")),
                    "passport_number": user_data.get("passport_number"),
                    "voter_id_number": user_data.get("voter_id_number"),
                    "address": user_data.get("address"),
                    "cibil_score": user_data.get("cibil_score")
                }
        
        # No match found
        print(f"[KYC DEBUG] ✗ NO MATCH FOUND in database")
        print(f"[KYC DEBUG] Available Aadhaar numbers in DB:")
        for user_id, user_data in self.db.get("users", {}).items():
            print(f"[KYC DEBUG]   - {user_data.get('name')}: {user_data.get('aadhaar_number')}")
        
        return {
            "status": "FAILED",
            "reason": "Data mismatch with DigiLocker record. Please verify your Aadhaar number."
        }


class KYCAgent:
    """
    KYC Agent for identity verification.
    
    This agent verifies user identity using Mock DigiLocker API before
    allowing application submission.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize KYC Agent.
        
        Args:
            db_path: Path to mock DigiLocker database
        """
        self.digilocker = MockDigiLockerAPI(db_path)
    
    def verify_identity(self, state: ApplicationState) -> ApplicationState:
        """
        Verify user identity via Mock DigiLocker.
        
        This method:
        1. Extracts submitted name and DOB from state
        2. Calls Mock DigiLocker API for verification
        3. Updates state with verification result
        4. Marks application as rejected if KYC fails
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state
        """
        request_id = state.get("request_id", "unknown")
        start_time = time.time()
        
        log_agent_execution("KYCAgent", request_id, "started")
        
        try:
            # Mark KYC as attempted
            state["kyc_attempted"] = True
            
            # Extract submitted data from state
            submitted_aadhaar = state.get("submitted_aadhaar")
            submitted_name = state.get("submitted_name")
            submitted_dob = state.get("submitted_dob")
            
            # Validate inputs
            if submitted_aadhaar:
                submitted_aadhaar = self._normalize_aadhaar(submitted_aadhaar)
                if not submitted_aadhaar:
                    error_msg = "Invalid Aadhaar format. Please enter a 12-digit number."
                    state["kyc_verified"] = False
                    state["rejected"] = True
                    state["rejection_reason"] = f"KYC Failed: {error_msg}"
                    state["kyc_rejection_reason"] = state["rejection_reason"]
                    state["errors"].append(error_msg)

                    log_error("validation", error_msg, request_id)
                    return state
            else:
                if not submitted_name or not submitted_dob:
                    error_msg = "Missing KYC data: Aadhaar number is required"
                    state["kyc_verified"] = False
                    state["rejected"] = True
                    state["rejection_reason"] = f"KYC Failed: {error_msg}"
                    state["kyc_rejection_reason"] = state["rejection_reason"]
                    state["errors"].append(error_msg)

                    log_error("validation", error_msg, request_id)
                    return state
            
            # Call Mock DigiLocker API
            result = self.digilocker.verify_kyc(
                submitted_aadhaar=submitted_aadhaar,
                submitted_name=self._normalize_name(submitted_name) if submitted_name else None,
                submitted_dob=self._normalize_dob(submitted_dob) if submitted_dob else None
            )
            
            # Process result
            if result["status"] == "SUCCESS":
                state["kyc_verified"] = True
                state["digilocker_id"] = result["verified_id"]
                state["verified_name"] = result["name"]
                state["verified_dob"] = result["dob"]
                state["verified_gender"] = result["gender"]
                state["verified_aadhaar"] = result.get("aadhaar_number")
                state["verified_pan"] = result.get("pan_number")
                state["verified_passport"] = result.get("passport_number")
                state["verified_voter_id"] = result.get("voter_id_number")
                state["verified_address"] = result.get("address")
                
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("KYCAgent", request_id, "completed", duration_ms)
            else:
                state["kyc_verified"] = False
                state["rejected"] = True
                state["rejection_reason"] = self._format_rejection_reason(result["reason"])
                state["kyc_rejection_reason"] = state["rejection_reason"]
                state["errors"].append(result["reason"])
                
                log_error("kyc", result["reason"], request_id)
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("KYCAgent", request_id, "failed", duration_ms)
        
        except Exception as e:
            error_msg = f"KYC verification error: {str(e)}"
            state["kyc_verified"] = False
            state["rejected"] = True
            state["rejection_reason"] = f"KYC Failed: System error"
            state["kyc_rejection_reason"] = state["rejection_reason"]
            state["errors"].append(error_msg)
            
            log_error("system", error_msg, request_id)
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("KYCAgent", request_id, "failed", duration_ms)
        
        return state
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison.
        
        Args:
            name: Raw name string
            
        Returns:
            Normalized name (trimmed, title case)
        """
        # Remove extra whitespace
        name = " ".join(name.split())
        # Convert to title case for consistency
        name = name.title()
        return name

    def _normalize_aadhaar(self, aadhaar: str) -> str:
        """
        Normalize Aadhaar number for comparison.

        Args:
            aadhaar: Raw Aadhaar string

        Returns:
            Normalized Aadhaar with digits only, or empty string if invalid
        """
        digits = re.sub(r"\D", "", aadhaar or "")
        if len(digits) != 12:
            return ""
        return digits
    
    def _normalize_dob(self, dob: str) -> str:
        """
        Normalize date of birth for comparison.
        
        Accepts formats: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD
        
        Args:
            dob: Raw DOB string
            
        Returns:
            Normalized DOB in YYYYMMDD format, or empty string if invalid
        """
        try:
            # Remove separators
            dob_clean = dob.replace("-", "").replace("/", "").strip()
            
            # Validate length
            if len(dob_clean) != 8:
                return ""
            
            # Validate it's all digits
            if not dob_clean.isdigit():
                return ""
            
            # Validate date components
            year = int(dob_clean[:4])
            month = int(dob_clean[4:6])
            day = int(dob_clean[6:8])
            
            # Basic validation
            if not (1900 <= year <= 2010):  # Reasonable birth year range
                return ""
            if not (1 <= month <= 12):
                return ""
            if not (1 <= day <= 31):
                return ""
            
            return dob_clean
        
        except (ValueError, IndexError):
            return ""
    
    def _format_rejection_reason(self, reason: str) -> str:
        """
        Format rejection reason for user display.
        
        Args:
            reason: Raw rejection reason
            
        Returns:
            Formatted rejection message
        """
        return f"KYC Failed: {reason}\n\nPlease ensure:\n" \
               "- Your name matches exactly as per your DigiLocker account\n" \
               "- Your date of birth is correct (format: YYYY-MM-DD)\n" \
               "- You have a valid DigiLocker account"
