"""
Error handling and resilience utilities.

This module provides decorators and utilities for robust error handling.
"""

import functools
import time
from typing import Callable, Any
from enum import Enum
from src.schemas.state import ApplicationState
from src.utils.logging import log_error, log_agent_execution


class ErrorCategory(Enum):
    """Error categories for routing and handling."""
    DATA_ERROR = "data"  # Invalid or missing data
    SYSTEM_ERROR = "system"  # System failures (model loading, network, etc.)
    COMPLIANCE_ERROR = "compliance"  # Regulatory compliance violations
    VALIDATION_ERROR = "validation"  # Input validation failures
    TIMEOUT_ERROR = "timeout"  # Operation timeout
    UNKNOWN_ERROR = "unknown"  # Uncategorized errors


def categorize_error(exception: Exception, context: str = "") -> ErrorCategory:
    """
    Categorize an error based on exception type and context.
    
    Args:
        exception: The exception that occurred
        context: Additional context (agent name, operation, etc.)
    
    Returns:
        ErrorCategory enum value
    """
    exception_type = type(exception).__name__
    error_message = str(exception).lower()
    
    # Timeout errors
    if exception_type == "TimeoutError" or "timeout" in error_message:
        return ErrorCategory.TIMEOUT_ERROR
    
    # Data errors
    if exception_type in ["ValueError", "KeyError", "TypeError"]:
        if "missing" in error_message or "not found" in error_message:
            return ErrorCategory.DATA_ERROR
        if "invalid" in error_message or "expected" in error_message:
            return ErrorCategory.VALIDATION_ERROR
    
    # Compliance errors
    if "compliance" in context.lower() or "violation" in error_message:
        return ErrorCategory.COMPLIANCE_ERROR
    
    # System errors
    if exception_type in ["RuntimeError", "IOError", "ConnectionError", "ImportError"]:
        return ErrorCategory.SYSTEM_ERROR
    
    if "model" in error_message or "network" in error_message or "connection" in error_message:
        return ErrorCategory.SYSTEM_ERROR
    
    # Validation errors
    if exception_type in ["ValidationError", "AssertionError"]:
        return ErrorCategory.VALIDATION_ERROR
    
    # Default to unknown
    return ErrorCategory.UNKNOWN_ERROR


def route_error(state: ApplicationState, error_category: ErrorCategory) -> str:
    """
    Determine routing based on error category.
    
    Args:
        state: Current application state
        error_category: Categorized error
    
    Returns:
        Next node to route to ("retry", "reject", "manual_review", "end")
    """
    if error_category == ErrorCategory.COMPLIANCE_ERROR:
        # Compliance errors should reject immediately
        state["rejected"] = True
        return "reject"
    
    elif error_category == ErrorCategory.DATA_ERROR:
        # Data errors might be recoverable with manual review
        return "manual_review"
    
    elif error_category == ErrorCategory.VALIDATION_ERROR:
        # Validation errors should reject with clear message
        state["rejected"] = True
        return "reject"
    
    elif error_category == ErrorCategory.TIMEOUT_ERROR:
        # Timeout errors can be retried
        retry_count = state.get("retry_count", 0)
        if retry_count < 2:
            state["retry_count"] = retry_count + 1
            return "retry"
        else:
            return "reject"
    
    elif error_category == ErrorCategory.SYSTEM_ERROR:
        # System errors should be logged and escalated
        return "manual_review"
    
    else:
        # Unknown errors should be reviewed
        return "manual_review"


def safe_agent_wrapper(agent_func: Callable[[ApplicationState], ApplicationState]) -> Callable[[ApplicationState], ApplicationState]:
    """
    Decorator to catch and log agent errors without crashing the workflow.
    
    This wrapper:
    1. Catches all exceptions from agent execution
    2. Categorizes errors for proper routing
    3. Logs errors with context
    4. Updates state with error information and category
    5. Returns state (possibly incomplete) instead of raising
    
    Args:
        agent_func: Agent function to wrap
        
    Returns:
        Wrapped agent function
    """
    @functools.wraps(agent_func)
    def wrapper(state: ApplicationState) -> ApplicationState:
        agent_name = agent_func.__name__
        request_id = state.get("request_id", "unknown")
        start_time = time.time()
        
        try:
            # Execute agent
            result_state = agent_func(state)
            return result_state
            
        except Exception as e:
            # Categorize error
            error_category = categorize_error(e, context=agent_name)
            
            # Log error with category
            error_msg = f"{agent_name} failed: {str(e)}"
            log_error(
                error_type=error_category.value,
                error_message=error_msg,
                request_id=request_id,
                agent=agent_name,
                exception_type=type(e).__name__
            )
            
            # Update state with error and category
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "message": error_msg,
                "category": error_category.value,
                "agent": agent_name,
                "exception_type": type(e).__name__
            })
            state["completed"] = False
            state["error_category"] = error_category.value
            
            # Determine routing based on error category
            routing = route_error(state, error_category)
            state["error_routing"] = routing
            
            # Log execution failure
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution(agent_name, request_id, "failed", duration_ms)
            
            return state
    
    return wrapper


def timeout_handler(timeout_seconds: float = 5.0):
    """
    Decorator to add timeout handling to functions (for LLM calls).
    
    Note: This is a simple implementation. For production, consider using
    asyncio with timeout or threading with timeout.
    
    Args:
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler_signal(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            
            # Set timeout (Unix-like systems only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler_signal)
                signal.alarm(int(timeout_seconds))
                
                result = func(*args, **kwargs)
                
                signal.alarm(0)  # Cancel alarm
                return result
                
            except AttributeError:
                # Windows doesn't support SIGALRM, just execute normally
                return func(*args, **kwargs)
            except TimeoutError as e:
                log_error("timeout", str(e))
                raise
        
        return wrapper
    return decorator


def format_error_response(state: ApplicationState) -> dict:
    """
    Format state errors into API-ready error response.
    
    Args:
        state: Application state with errors
        
    Returns:
        Dictionary with formatted error response
    """
    return {
        "request_id": state.get("request_id", "unknown"),
        "timestamp": state.get("timestamp", ""),
        "request_type": state.get("request_type", "unknown"),
        "status": "failed",
        "results": {},
        "errors": state.get("errors", []),
        "rejection_reason": state.get("rejection_reason")
    }


def validate_state_transition(state: ApplicationState, required_fields: list) -> bool:
    """
    Validate that state has required fields before proceeding.
    
    Args:
        state: Current application state
        required_fields: List of required field names
        
    Returns:
        True if all required fields are present, False otherwise
    """
    for field in required_fields:
        if field not in state or state[field] is None:
            error_msg = f"State validation failed: missing required field '{field}'"
            log_error("validation", error_msg, state.get("request_id"))
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(error_msg)
            return False
    
    return True
