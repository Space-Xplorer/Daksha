"""
Router Service for request routing.

This module implements routing logic to determine which ML models to invoke.
"""

import time

from src.schemas.state import ApplicationState
from src.utils.logging import log_agent_execution


class RouterAgent:
    """
    Router Agent for determining processing path.
    
    This agent analyzes the request type and routes to appropriate
    underwriting agents (loan, insurance, or both).
    """
    
    def __init__(self):
        """Initialize Router Agent."""
        pass
    
    def route_request(self, state: ApplicationState) -> ApplicationState:
        """
        Route request to appropriate processing path.
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state with routing information
        """
        request_id = state.get("request_id", "unknown")
        start_time = time.time()
        
        log_agent_execution("RouterAgent", request_id, "started")
        
        try:
            request_type = state["request_type"]
            
            # Validate request type
            if request_type not in ["loan", "insurance", "both"]:
                error_msg = f"Invalid request_type: {request_type}"
                state["errors"].append(error_msg)
                state["current_agent"] = "error"
            else:
                # Set current agent based on request type
                if request_type == "loan":
                    state["current_agent"] = "underwriting_loan"
                elif request_type == "insurance":
                    state["current_agent"] = "underwriting_insurance"
                elif request_type == "both":
                    # Process loan first, then insurance
                    state["current_agent"] = "underwriting_loan"
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("RouterAgent", request_id, "completed", duration_ms)
        
        except Exception as e:
            error_msg = f"Router error: {str(e)}"
            state["errors"].append(error_msg)
            state["current_agent"] = "error"
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("RouterAgent", request_id, "failed", duration_ms)
        
        return state
