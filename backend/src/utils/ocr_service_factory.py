"""
OCR Service Factory - switches between mock and production modes.
"""

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_ocr_service() -> Any:
    """
    Get OCR service based on configuration.
    
    Returns:
        OCR service instance (mock or production)
    """
    ocr_mode = os.getenv('OCR_MODE', 'mock').lower()
    
    logger.info(f"Initializing OCR service in {ocr_mode} mode")
    
    if ocr_mode == 'production':
        try:
            from src.utils.ocr_service_production import ProductionOCRService
            return ProductionOCRService()
        except Exception as e:
            logger.error(f"Failed to initialize production OCR service: {e}")
            logger.warning("Falling back to mock OCR service")
            from src.utils.ocr_service_mock import OCRService
            return OCRService()
    else:
        from src.utils.ocr_service_mock import OCRService
        return OCRService()
