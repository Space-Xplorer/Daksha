"""
OCR Service Factory - uses production OCR service.
"""

import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def get_ocr_service(groq_api_key: Optional[str] = None) -> Any:
    """
    Get OCR service based on configuration.
    
    Returns:
        OCR service instance
    """
    ocr_mode = os.getenv('OCR_MODE', 'production').lower()
    
    logger.info(f"Initializing OCR service in {ocr_mode} mode")
    
    if ocr_mode in ["mock", "development", "dev", "test"]:
        from src.utils.ocr_service_mock import OCRService
        return OCRService(groq_api_key=groq_api_key)

    if ocr_mode != 'production':
        raise RuntimeError(f"Unsupported OCR_MODE: {ocr_mode}. Set OCR_MODE=production or OCR_MODE=mock.")

    try:
        from src.utils.ocr_service_production import ProductionOCRService
        return ProductionOCRService(groq_api_key=groq_api_key)
    except Exception as e:
        logger.error(f"Failed to initialize production OCR service: {e}")
        raise
