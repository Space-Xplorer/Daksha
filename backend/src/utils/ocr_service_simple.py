"""
Compatibility shim for tests and older imports.

Exposes `OCRService` name expected by some modules/tests and delegates
to the configured OCR service from the factory (mock or production).
"""
from src.utils.ocr_service_factory import get_ocr_service


def OCRService(*args, **kwargs):
    """Return an OCR service instance (mock or production based on OCR_MODE)."""
    return get_ocr_service()
