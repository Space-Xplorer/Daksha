"""
Storage helpers for application artifacts.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


def get_storage_root() -> Path:
    """Return the storage root directory."""
    backend_dir = Path(__file__).resolve().parents[2]
    return backend_dir / "storage"


def get_application_dir(app_id: str) -> Path:
    """Return per-application storage directory."""
    return get_storage_root() / app_id


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def save_applicant_data(app_id: str, applicant_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Path:
    """Persist applicant input data to storage."""
    payload = {
        "metadata": metadata or {},
        "applicant_data": applicant_data or {}
    }
    target = get_application_dir(app_id) / "applicant.json"
    _write_json(target, payload)
    return target


def save_extracted_data(
    app_id: str,
    extracted_data: Dict[str, Any],
    ocr_documents: Optional[list[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Persist OCR extracted data and document artifacts to storage."""
    payload = {
        "metadata": metadata or {},
        "extracted_data": extracted_data or {},
        "ocr_documents": ocr_documents or []
    }
    target = get_application_dir(app_id) / "extracted.json"
    _write_json(target, payload)
    return target
