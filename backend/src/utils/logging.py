"""
Logging configuration.

This module configures structured logging for the Daksha system.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "daksha_system.log",
    log_to_console: bool = True
) -> None:
    """
    Configure structured logging for the Daksha system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, only logs to console
        log_to_console: Whether to also log to console
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # Log initialization
    logging.info(f"Logging initialized at {log_level} level")


def log_request(request_id: str, request_type: str, **kwargs) -> None:
    """
    Log incoming request (without sensitive data).
    
    Args:
        request_id: Unique request identifier
        request_type: Type of request (loan, insurance, both)
        **kwargs: Additional non-sensitive metadata
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Request {request_id}: type={request_type}, "
        f"timestamp={datetime.utcnow().isoformat()}, "
        f"metadata={kwargs}"
    )


def log_agent_execution(agent_name: str, request_id: str, status: str, duration_ms: Optional[float] = None) -> None:
    """
    Log agent execution status.
    
    Args:
        agent_name: Name of the agent
        request_id: Request identifier
        status: Execution status (started, completed, failed)
        duration_ms: Execution duration in milliseconds
    """
    logger = logging.getLogger(__name__)
    
    if duration_ms is not None:
        logger.info(
            f"Agent {agent_name} [{request_id}]: {status} (duration: {duration_ms:.2f}ms)"
        )
    else:
        logger.info(f"Agent {agent_name} [{request_id}]: {status}")


def log_model_prediction(model_name: str, request_id: str, prediction_summary: str) -> None:
    """
    Log model prediction (without sensitive input data).
    
    Args:
        model_name: Name of the ML model
        request_id: Request identifier
        prediction_summary: Summary of prediction (e.g., "approved", "premium=18500")
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Model {model_name} [{request_id}]: {prediction_summary}")


def log_error(error_type: str, error_message: str, request_id: Optional[str] = None, **context) -> None:
    """
    Log error with context.
    
    Args:
        error_type: Type of error (validation, model, llm, system)
        error_message: Error message
        request_id: Optional request identifier
        **context: Additional error context
    """
    logger = logging.getLogger(__name__)
    
    if request_id:
        logger.error(
            f"Error [{request_id}]: type={error_type}, message={error_message}, context={context}"
        )
    else:
        logger.error(f"Error: type={error_type}, message={error_message}, context={context}")


def log_audit_trail(
    request_id: str,
    request_type: str,
    decision: Optional[str] = None,
    premium: Optional[float] = None,
    model_versions: Optional[dict] = None
) -> None:
    """
    Log decision for regulatory compliance audit trail.
    
    Note: Does NOT log raw applicant data (PII protection).
    
    Args:
        request_id: Request identifier
        request_type: Type of request
        decision: Loan decision (approved/rejected)
        premium: Insurance premium amount
        model_versions: Dictionary of model names and versions
    """
    logger = logging.getLogger("audit")
    
    audit_entry = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "request_type": request_type,
        "decision": decision,
        "premium": premium,
        "model_versions": model_versions or {}
    }
    
    logger.info(f"AUDIT: {audit_entry}")
