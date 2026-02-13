"""
Health check endpoints for monitoring system status.
"""

from flask import Blueprint, jsonify
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('health', __name__)


@bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON response with system status
    """
    return jsonify({
        "status": "healthy",
        "service": "Daksha API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200


@bp.route('/api/health/models', methods=['GET'])
def check_models():
    """
    Check if all required ML models are loaded.
    
    Returns:
        JSON response with model availability status
    """
    try:
        from src.utils.model_loader import ModelLoader
        
        loader = ModelLoader()
        
        # Check each required model
        status = {
            "ebm_finance": loader.get_model("ebm_finance") is not None,
            "ebm_health": loader.get_model("ebm_health") is not None,
            "fin_encoders": loader.get_model("fin_encoders") is not None,
            "health_encoders": loader.get_model("health_encoders") is not None
        }
        
        all_loaded = all(status.values())
        
        response = {
            "status": "healthy" if all_loaded else "degraded",
            "models": status,
            "timestamp": datetime.now().isoformat()
        }
        
        http_status = 200 if all_loaded else 503
        
        if not all_loaded:
            logger.warning(f"Some models not loaded: {status}")
        
        return jsonify(response), http_status
        
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503


@bp.route('/api/health/ocr', methods=['GET'])
def check_ocr():
    """
    Check OCR service availability.
    
    Returns:
        JSON response with OCR service status
    """
    try:
        ocr_mode = os.getenv('OCR_MODE', 'mock')
        
        status_info = {
            "mode": ocr_mode,
            "available": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # If production mode, check Tesseract
        if ocr_mode == 'production':
            try:
                import pytesseract
                version = pytesseract.get_tesseract_version()
                status_info["tesseract_version"] = str(version)
                status_info["status"] = "healthy"
            except Exception as e:
                status_info["available"] = False
                status_info["status"] = "unhealthy"
                status_info["error"] = f"Tesseract not available: {str(e)}"
                return jsonify(status_info), 503
        else:
            status_info["status"] = "healthy"
            status_info["note"] = "Running in mock mode"
        
        return jsonify(status_info), 200
        
    except Exception as e:
        logger.error(f"OCR health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503


@bp.route('/api/health/llm', methods=['GET'])
def check_llm():
    """
    Check LLM (GROQ) service availability.
    
    Returns:
        JSON response with LLM service status
    """
    try:
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not groq_api_key:
            return jsonify({
                "status": "degraded",
                "available": False,
                "error": "GROQ_API_KEY not configured",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # Try to initialize LLM
        try:
            from langchain_groq import ChatGroq
            
            llm = ChatGroq(
                model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
                temperature=0.0,
                api_key=groq_api_key
            )
            
            # Simple test invocation
            response = llm.invoke("Hello")
            
            return jsonify({
                "status": "healthy",
                "available": True,
                "model": os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
                "timestamp": datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"LLM test invocation failed: {e}")
            return jsonify({
                "status": "unhealthy",
                "available": False,
                "error": f"LLM initialization failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 503
        
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503


@bp.route('/api/health/database', methods=['GET'])
def check_database():
    """
    Check mock database availability.
    
    Returns:
        JSON response with database status
    """
    try:
        import json
        from pathlib import Path
        
        mock_db_path = Path(os.getenv('MOCK_DB_PATH', 'src/mock_db.json'))
        
        if not mock_db_path.exists():
            return jsonify({
                "status": "unhealthy",
                "available": False,
                "error": f"Mock database not found at {mock_db_path}",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # Try to load and validate
        with open(mock_db_path, 'r') as f:
            db_data = json.load(f)
        
        user_count = len(db_data.get('users', {}))
        
        return jsonify({
            "status": "healthy",
            "available": True,
            "path": str(mock_db_path),
            "user_count": user_count,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503


@bp.route('/api/health/all', methods=['GET'])
def check_all():
    """
    Comprehensive health check of all system components.
    
    Returns:
        JSON response with status of all components
    """
    from flask import current_app
    
    components = {}
    overall_healthy = True
    
    # Check models
    try:
        from src.utils.model_loader import ModelLoader
        loader = ModelLoader()
        models_status = {
            "ebm_finance": loader.get_model("ebm_finance") is not None,
            "ebm_health": loader.get_model("ebm_health") is not None,
            "fin_encoders": loader.get_model("fin_encoders") is not None,
            "health_encoders": loader.get_model("health_encoders") is not None
        }
        components["models"] = {
            "status": "healthy" if all(models_status.values()) else "degraded",
            "details": models_status
        }
        if not all(models_status.values()):
            overall_healthy = False
    except Exception as e:
        components["models"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check OCR
    try:
        ocr_mode = os.getenv('OCR_MODE', 'mock')
        ocr_available = True
        if ocr_mode == 'production':
            import pytesseract
            pytesseract.get_tesseract_version()
        components["ocr"] = {
            "status": "healthy",
            "mode": ocr_mode
        }
    except Exception as e:
        components["ocr"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check LLM
    try:
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            components["llm"] = {"status": "healthy", "configured": True}
        else:
            components["llm"] = {"status": "degraded", "configured": False}
            overall_healthy = False
    except Exception as e:
        components["llm"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check database
    try:
        import json
        from pathlib import Path
        mock_db_path = Path(os.getenv('MOCK_DB_PATH', 'src/mock_db.json'))
        with open(mock_db_path, 'r') as f:
            db_data = json.load(f)
        components["database"] = {
            "status": "healthy",
            "user_count": len(db_data.get('users', {}))
        }
    except Exception as e:
        components["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    return jsonify({
        "status": "healthy" if overall_healthy else "degraded",
        "components": components,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200 if overall_healthy else 503
