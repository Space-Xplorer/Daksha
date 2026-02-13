"""
Configuration validator for production deployment.
"""

import os
import sys
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_production_config() -> bool:
    """
    Validate all required configuration for production.
    
    Returns:
        True if validation passes, False otherwise
    """
    errors = []
    warnings = []
    
    print("\n" + "="*60)
    print("🔍 Validating Production Configuration")
    print("="*60 + "\n")
    
    # Required environment variables
    required_vars = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'GROQ_API_KEY'
    ]
    
    print("📋 Checking required environment variables...")
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
            print(f"  ❌ {var}: NOT SET")
        else:
            print(f"  ✅ {var}: SET")
    
    # Validate OCR mode
    print("\n🔧 Checking OCR configuration...")
    ocr_mode = os.getenv('OCR_MODE', 'mock')
    print(f"  OCR_MODE: {ocr_mode}")
    
    if ocr_mode == 'production':
        if not os.getenv('TESSERACT_PATH'):
            warnings.append("OCR_MODE=production but TESSERACT_PATH not set. Will use system default.")
            print(f"  ⚠️  TESSERACT_PATH: NOT SET (will use system default)")
        else:
            tesseract_path = Path(os.getenv('TESSERACT_PATH', ''))
            if not tesseract_path.exists():
                errors.append(f"Tesseract not found at: {tesseract_path}")
                print(f"  ❌ TESSERACT_PATH: {tesseract_path} (NOT FOUND)")
            else:
                print(f"  ✅ TESSERACT_PATH: {tesseract_path}")
    
    # Validate models directory
    print("\n📦 Checking ML models...")
    models_dir = Path(os.getenv('MODELS_DIR', 'models'))
    if not models_dir.exists():
        errors.append(f"Models directory not found: {models_dir}")
        print(f"  ❌ Models directory: {models_dir} (NOT FOUND)")
    else:
        print(f"  ✅ Models directory: {models_dir}")
        
        required_models = [
            'ebm_finance.pkl',
            'ebm_health.pkl',
            'fin_encoders.pkl',
            'health_encoders.pkl'
        ]
        
        for model in required_models:
            model_path = models_dir / model
            if not model_path.exists():
                errors.append(f"Required model not found: {model_path}")
                print(f"  ❌ {model}: NOT FOUND")
            else:
                print(f"  ✅ {model}: FOUND")
    
    # Validate mock database
    print("\n💾 Checking mock database...")
    mock_db_path = Path(os.getenv('MOCK_DB_PATH', 'src/mock_db.json'))
    if not mock_db_path.exists():
        errors.append(f"Mock database not found: {mock_db_path}")
        print(f"  ❌ Mock database: {mock_db_path} (NOT FOUND)")
    else:
        print(f"  ✅ Mock database: {mock_db_path}")
        
        # Validate JSON format
        try:
            with open(mock_db_path, 'r') as f:
                db_data = json.load(f)
                user_count = len(db_data.get('users', {}))
                print(f"  ℹ️  Users in database: {user_count}")
                
                if user_count < 5:
                    warnings.append(f"Mock database has only {user_count} users. Consider expanding for better testing.")
        except json.JSONDecodeError as e:
            errors.append(f"Mock database is not valid JSON: {e}")
            print(f"  ❌ Invalid JSON format: {e}")
    
    # Validate fraud detection configuration
    print("\n🛡️  Checking fraud detection configuration...")
    fraud_enabled = os.getenv('FRAUD_DETECTION_ENABLED', 'false').lower() == 'true'
    print(f"  FRAUD_DETECTION_ENABLED: {fraud_enabled}")
    
    if fraud_enabled:
        fraud_threshold = os.getenv('FRAUD_DETECTION_THRESHOLD', '40')
        fraud_auto_reject = os.getenv('FRAUD_AUTO_REJECT_THRESHOLD', '70')
        print(f"  FRAUD_DETECTION_THRESHOLD: {fraud_threshold}")
        print(f"  FRAUD_AUTO_REJECT_THRESHOLD: {fraud_auto_reject}")
    
    # Print results
    print("\n" + "="*60)
    if errors:
        print("❌ Configuration validation FAILED")
        print("="*60)
        print("\nErrors:")
        for error in errors:
            print(f"  • {error}")
        
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        print("\n" + "="*60)
        return False
    
    if warnings:
        print("⚠️  Configuration validation PASSED with warnings")
        print("="*60)
        print("\nWarnings:")
        for warning in warnings:
            print(f"  • {warning}")
    else:
        print("✅ Configuration validation PASSED")
        print("="*60)
    
    print()
    return True


def validate_or_exit():
    """
    Validate configuration and exit if validation fails.
    """
    if not validate_production_config():
        print("\n⛔ Cannot start application with invalid configuration.")
        print("Please fix the errors above and try again.\n")
        sys.exit(1)


if __name__ == "__main__":
    # Allow running as standalone script
    validate_or_exit()
