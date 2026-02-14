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
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def save_declared_data(
    app_id: str,
    declared_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Persist declared (user-typed) data to storage."""
    payload = {
        "metadata": metadata or {},
        "declared_data": declared_data or {}
    }
    target = get_application_dir(app_id) / "declared_data.json"
    _write_json(target, payload)
    return target


def save_applicant_data(app_id: str, applicant_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Path:
    """Backward-compatible alias for declared data persistence."""
    return save_declared_data(app_id, applicant_data, metadata)


def save_ocr_data(
    app_id: str,
    ocr_extracted_data: Dict[str, Any],
    ocr_documents: Optional[list[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Persist OCR extracted data and document artifacts to storage."""
    payload = {
        "metadata": metadata or {},
        "ocr_extracted_data": ocr_extracted_data or {},
        "ocr_documents": ocr_documents or []
    }
    target = get_application_dir(app_id) / "ocr_extracted_data.json"
    _write_json(target, payload)
    return target


def save_extracted_data(
    app_id: str,
    extracted_data: Dict[str, Any],
    ocr_documents: Optional[list[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Backward-compatible alias for OCR data persistence."""
    return save_ocr_data(app_id, extracted_data, ocr_documents, metadata)


def save_derived_features(
    app_id: str,
    derived_features: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Persist derived features to storage."""
    payload = {
        "metadata": metadata or {},
        "derived_features": derived_features or {}
    }
    target = get_application_dir(app_id) / "derived_features.json"
    _write_json(target, payload)
    return target


def save_validation_report(
    app_id: str,
    validation_report: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Persist validation report to storage."""
    payload = {
        "metadata": metadata or {},
        "validation_report": validation_report or {}
    }
    target = get_application_dir(app_id) / "validation_report.json"
    _write_json(target, payload)
    return target


def save_model_output(
    app_id: str,
    model_output: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Persist model outputs to storage."""
    payload = {
        "metadata": metadata or {},
        "model_output": model_output or {}
    }
    target = get_application_dir(app_id) / "model_output.json"
    _write_json(target, payload)
    return target
