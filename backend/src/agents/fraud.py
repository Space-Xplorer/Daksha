"""
Fraud Agent for OCR document fraud checks.
"""

import logging
from typing import Any, Dict, List

from src.schemas.state import ApplicationState
from src.utils.fraud_detector import FraudDetector
from src.utils.logging import log_agent_execution, log_error

logger = logging.getLogger(__name__)


class FraudAgent:
    """Runs OCR fraud checks and records flags without blocking the flow."""

    def __init__(self) -> None:
        self.detector = FraudDetector()

    def check_fraud(self, state: ApplicationState) -> ApplicationState:
        request_id = state.get("request_id", "unknown")
        log_agent_execution("FraudAgent", request_id, "started")

        try:
            ocr_documents = state.get("ocr_documents", []) or []
            results: List[Dict[str, Any]] = []

            for doc in ocr_documents:
                file_path = doc.get("file_path")
                text = doc.get("text", "")
                doc_type = doc.get("document_type") or doc.get("type") or "unknown"

                if not file_path:
                    continue

                analysis = self.detector.analyze_document(
                    file_path=file_path,
                    extracted_text=text,
                    document_type=doc_type
                )
                analysis["document_type"] = doc_type
                analysis["file_path"] = file_path
                results.append(analysis)

            state["fraud_results"] = results
            log_agent_execution("FraudAgent", request_id, "completed")
            return state

        except Exception as exc:
            error_msg = f"Fraud check failed: {exc}"
            state.setdefault("errors", []).append(error_msg)
            log_error("fraud", error_msg, request_id)
            log_agent_execution("FraudAgent", request_id, "failed")
            return state
