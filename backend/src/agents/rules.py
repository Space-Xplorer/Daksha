"""
Rules Agent for validating uploaded documents against underwriting rule PDFs.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.schemas.state import ApplicationState
from src.utils.llm_helpers import parse_json_response
from src.utils.logging import log_agent_execution, log_error

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


class RulesAgent:
    """
    Validate uploaded documents against official underwriting rules.

    This agent:
    - Loads rule documents (PDF/TXT) from src/rules
    - Summarizes OCR-extracted text from applicant documents
    - Uses LLM to detect rule violations when available
    """

    def __init__(self, rules_dir: str = "src/rules") -> None:
        self.rules_dir = Path(rules_dir)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = None
        if self.groq_api_key and LLM_AVAILABLE:
            try:
                self.llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                    api_key=self.groq_api_key
                )
                logger.info("RulesAgent LLM initialized")
            except Exception as exc:
                logger.warning(f"RulesAgent LLM init failed: {exc}")

    def check_rules(self, state: ApplicationState) -> ApplicationState:
        request_id = state.get("request_id", "unknown")
        log_agent_execution("RulesAgent", request_id, "started")

        try:
            rules_text = self._load_rules_text()
            ocr_documents = state.get("ocr_documents", []) or []

            extracted_snapshots = self._build_text_snapshots(ocr_documents)
            state["rules_extracted_texts"] = extracted_snapshots

            if not rules_text:
                state["rules_checked"] = True
                state["rules_passed"] = True
                state["rules_violations"] = []
                log_agent_execution("RulesAgent", request_id, "completed")
                return state

            if not ocr_documents:
                state["rules_checked"] = True
                state["rules_passed"] = True
                state["rules_violations"] = []
                log_agent_execution("RulesAgent", request_id, "completed")
                return state

            violations = self._evaluate_with_llm(rules_text, extracted_snapshots)

            state["rules_checked"] = True
            state["rules_violations"] = violations
            state["rules_passed"] = len(violations) == 0

            if violations:
                state["rejected"] = True
                state["rejection_reason"] = self._format_rejection_reason(violations)

            log_agent_execution("RulesAgent", request_id, "completed")
            return state

        except Exception as exc:
            error_msg = f"Rules check failed: {exc}"
            state.setdefault("errors", []).append(error_msg)
            log_error("rules", error_msg, request_id)
            state["rules_checked"] = True
            state["rules_passed"] = True
            state["rules_violations"] = []
            log_agent_execution("RulesAgent", request_id, "failed")
            return state

    def _load_rules_text(self) -> str:
        if not self.rules_dir.exists():
            return ""

        parts: List[str] = []

        for path in sorted(self.rules_dir.iterdir()):
            if path.suffix.lower() == ".txt":
                parts.append(self._read_text_file(path))
            elif path.suffix.lower() == ".pdf":
                parts.append(self._read_pdf_file(path))

        return "\n\n".join([p for p in parts if p])

    def _read_text_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to read {path.name}: {exc}")
            return ""

    def _read_pdf_file(self, path: Path) -> str:
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available for PDF rule parsing")
            return ""

        try:
            text_chunks: List[str] = []
            with open(path, "rb") as handle:
                reader = PyPDF2.PdfReader(handle)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    if page_text:
                        text_chunks.append(page_text)
            return "\n".join(text_chunks)
        except Exception as exc:
            logger.warning(f"Failed to read PDF {path.name}: {exc}")
            return ""

    def _build_text_snapshots(self, ocr_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for doc in ocr_documents:
            text = (doc.get("text") or "").strip()
            if not text:
                continue
            snapshots.append({
                "document_type": doc.get("document_type") or doc.get("type"),
                "file_path": doc.get("file_path"),
                "confidence": doc.get("confidence"),
                "text_excerpt": text[:2000]
            })
        return snapshots

    def _evaluate_with_llm(self, rules_text: str, snapshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.llm:
            return []

        prompt = (
            "You are an underwriting rules auditor.\n\n"
            "Rules (authoritative):\n"
            f"{rules_text}\n\n"
            "Applicant document excerpts (OCR):\n"
            f"{snapshots}\n\n"
            "Task: Identify any violations in the applicant documents against the rules.\n"
            "Return JSON array of violations with fields: rule, reason, severity.\n"
            "If no violations, return [].\n"
        )

        response = self.llm.invoke(prompt).content
        violations = parse_json_response(response, default=[])
        if isinstance(violations, list):
            return violations
        return []

    def _format_rejection_reason(self, violations: List[Dict[str, Any]]) -> str:
        reasons = []
        for violation in violations:
            rule = violation.get("rule", "Rule")
            reason = violation.get("reason", "Violation detected")
            reasons.append(f"- {rule}: {reason}")
        return "Application rejected due to rule violations:\n" + "\n".join(reasons)
