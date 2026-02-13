"""
KYC Agent with Mock DigiLocker integration.

This module implements identity verification using a mock DigiLocker API.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.schemas.state import ApplicationState
from src.utils.logging import log_agent_execution, log_error


class MockDigiLockerAPI:
    """
    Mock DigiLocker API for KYC verification.
    
    This simulates the DigiLocker API for testing purposes.
    In production, this would be replaced with actual DigiLocker integration.
    """
    
    def __init__(self, db_path: str = 'src/mock_db.json'):
        """
        Initialize Mock DigiLocker API.
        
        Args:
            db_path: Path to mock database JSON file
        """
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
    
    def verify_kyc(self, submitted_name: str, submitted_dob: str) -> Dict[str, Any]:
        """
        Verify user against mock DigiLocker database.
        
        Args:
            submitted_name: Name submitted by user
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
        
        # Normalize submitted data
        submitted_name_normalized = submitted_name.strip().lower()
        submitted_dob_normalized = submitted_dob.replace("-", "").replace("/", "")
        
        # Search for matching user in database
        for user_id, user_data in self.db.get("users", {}).items():
            db_name = user_data.get("name", "").strip().lower()
            db_dob = user_data.get("dob", "")
            
            # Check for match
            name_match = submitted_name_normalized == db_name
            dob_match = submitted_dob_normalized == db_dob
            
            if name_match and dob_match:
                return {
                    "status": "SUCCESS",
                    "verified_id": user_data["digilockerid"],
                    "name": user_data["name"],
                    "dob": user_data["dob"],
                    "gender": user_data["gender"]
                }
        
        # No match found
        return {
            "status": "FAILED",
            "reason": "Data mismatch with DigiLocker record. Please verify your name and date of birth."
        }


class KYCAgent:
    """
    KYC Agent for identity verification.
    
    This agent verifies user identity using Mock DigiLocker API before
    allowing application submission.
    """
    
    def __init__(self, db_path: str = 'src/mock_db.json'):
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
            submitted_name = state.get("submitted_name")
            submitted_dob = state.get("submitted_dob")
            
            # Validate inputs
            if not submitted_name or not submitted_dob:
                error_msg = "Missing KYC data: name and date of birth are required"
                state["kyc_verified"] = False
                state["rejected"] = True
                state["rejection_reason"] = f"KYC Failed: {error_msg}"
                state["errors"].append(error_msg)
                
                log_error("validation", error_msg, request_id)
                return state
            
            # Normalize and validate name
            submitted_name = self._normalize_name(submitted_name)
            
            # Normalize and validate DOB
            submitted_dob = self._normalize_dob(submitted_dob)
            if not submitted_dob:
                error_msg = "Invalid date of birth format. Please use YYYY-MM-DD format."
                state["kyc_verified"] = False
                state["rejected"] = True
                state["rejection_reason"] = f"KYC Failed: {error_msg}"
                state["errors"].append(error_msg)
                
                log_error("validation", error_msg, request_id)
                return state
            
            # Call Mock DigiLocker API
            result = self.digilocker.verify_kyc(submitted_name, submitted_dob)
            
            # Process result
            if result["status"] == "SUCCESS":
                state["kyc_verified"] = True
                state["digilocker_id"] = result["verified_id"]
                state["verified_name"] = result["name"]
                state["verified_dob"] = result["dob"]
                state["verified_gender"] = result["gender"]
                
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("KYCAgent", request_id, "completed", duration_ms)
            else:
                state["kyc_verified"] = False
                state["rejected"] = True
                state["rejection_reason"] = self._format_rejection_reason(result["reason"])
                state["errors"].append(result["reason"])
                
                log_error("kyc", result["reason"], request_id)
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("KYCAgent", request_id, "failed", duration_ms)
        
        except Exception as e:
            error_msg = f"KYC verification error: {str(e)}"
            state["kyc_verified"] = False
            state["rejected"] = True
            state["rejection_reason"] = f"KYC Failed: System error"
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
        return f"KYC Verification Failed: {reason}\n\nPlease ensure:\n" \
               "- Your name matches exactly as per your DigiLocker account\n" \
               "- Your date of birth is correct (format: YYYY-MM-DD)\n" \
               "- You have a valid DigiLocker account"
