"""
System Validation Script for Daksha

This script validates the entire Daksha system before deployment.
Runs all checks from the deployment checklist.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_python_version():
    """Check Python version."""
    print_info("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_dependencies():
    """Check if all dependencies are installed."""
    print_info("Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_cors', 'flask_jwt_extended',
        'langgraph', 'langchain_groq', 'langchain_core',
        'pandas', 'numpy', 'pytest', 'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} missing")
            missing.append(package)
    
    if missing:
        print_warning(f"Missing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """Check if .env file exists and has required variables."""
    print_info("Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print_error(".env file not found")
        print_info("Copy .env.example to .env and configure")
        return False
    
    print_success(".env file exists")
    
    required_vars = [
        'SECRET_KEY', 'JWT_SECRET_KEY', 'GROQ_API_KEY'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print_error(f"{var} not set")
            missing.append(var)
        elif value in ['dev-secret-key-change-in-production', 'jwt-secret-key-change-in-production']:
            print_warning(f"{var} using default value (change for production)")
        else:
            print_success(f"{var} configured")
    
    return len(missing) == 0

def check_required_files():
    """Check if all required files exist."""
    print_info("Checking required files...")
    
    required_files = [
        'src/mock_db.json',
        'src/rules/usda_loan_rules.txt',
        'src/rules/irdai_insurance_rules.txt',
        'main.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} missing")
            all_exist = False
    
    # Check optional model files
    print_info("\nChecking optional model files...")
    model_files = [
        'src/models/innovathon/ebm_finance.pkl',
        'src/models/innovathon/ebm_health.pkl',
        'src/models/innovathon/fin_encoders.pkl',
        'src/models/innovathon/health_encoders.pkl'
    ]
    
    models_exist = True
    for file_path in model_files:
        if os.path.exists(file_path):
            print_success(f"{file_path}")
        else:
            print_warning(f"{file_path} missing (will use mock predictions)")
            models_exist = False
    
    if not models_exist:
        print_info("System will use mock predictions for demo")
    
    return all_exist

def run_unit_tests():
    """Run unit tests."""
    print_info("Running unit tests...")
    
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v', '--ignore=tests/test_workflow.py', '-x'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_success("All unit tests passed")
            return True
        else:
            print_error("Some unit tests failed")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print_error("Unit tests timed out")
        return False
    except Exception as e:
        print_error(f"Failed to run unit tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests."""
    print_info("Running integration tests...")
    
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/test_workflow.py', '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Check if at least 70% passed
        output = result.stdout
        if 'passed' in output:
            # Extract pass/fail counts
            import re
            match = re.search(r'(\d+) passed', output)
            if match:
                passed = int(match.group(1))
                total_match = re.search(r'(\d+) failed', output)
                failed = int(total_match.group(1)) if total_match else 0
                total = passed + failed
                
                pass_rate = (passed / total * 100) if total > 0 else 0
                
                if pass_rate >= 70:
                    print_success(f"Integration tests: {passed}/{total} passed ({pass_rate:.1f}%)")
                    return True
                else:
                    print_warning(f"Integration tests: {passed}/{total} passed ({pass_rate:.1f}%) - below 70% threshold")
                    return False
        
        print_warning("Could not determine test results")
        return False
        
    except subprocess.TimeoutExpired:
        print_error("Integration tests timed out")
        return False
    except Exception as e:
        print_error(f"Failed to run integration tests: {e}")
        return False

def test_api_import():
    """Test if API can be imported."""
    print_info("Testing API import...")
    
    try:
        from main import create_app
        app = create_app()
        print_success("API app created successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create API app: {e}")
        return False

def test_workflow_import():
    """Test if workflow can be imported."""
    print_info("Testing workflow import...")
    
    try:
        from src.graph.workflow import run_workflow
        from src.schemas.state import create_initial_state
        print_success("Workflow modules imported successfully")
        return True
    except Exception as e:
        print_error(f"Failed to import workflow: {e}")
        return False

def check_disk_space():
    """Check available disk space."""
    print_info("Checking disk space...")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        
        free_gb = free // (2**30)
        total_gb = total // (2**30)
        
        if free_gb < 1:
            print_error(f"Low disk space: {free_gb}GB free of {total_gb}GB")
            return False
        elif free_gb < 5:
            print_warning(f"Disk space: {free_gb}GB free of {total_gb}GB")
            return True
        else:
            print_success(f"Disk space: {free_gb}GB free of {total_gb}GB")
            return True
    except Exception as e:
        print_warning(f"Could not check disk space: {e}")
        return True

def generate_report(results):
    """Generate validation report."""
    print_header("VALIDATION REPORT")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"Failed: {Colors.RED}{failed}{Colors.END}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    print("Detailed Results:")
    for check, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"  {status} - {check}")
    
    print()
    
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ SYSTEM READY FOR DEPLOYMENT{Colors.END}")
        return True
    elif passed / total >= 0.8:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ SYSTEM MOSTLY READY (some warnings){Colors.END}")
        return True
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SYSTEM NOT READY FOR DEPLOYMENT{Colors.END}")
        return False

def main():
    """Run all validation checks."""
    print_header("DAKSHA SYSTEM VALIDATION")
    print_info("Running comprehensive system validation...\n")
    
    results = {}
    
    # Environment checks
    print_header("1. ENVIRONMENT CHECKS")
    results['Python Version'] = check_python_version()
    results['Dependencies'] = check_dependencies()
    results['Environment Variables'] = check_env_file()
    results['Required Files'] = check_required_files()
    results['Disk Space'] = check_disk_space()
    
    # Import checks
    print_header("2. IMPORT CHECKS")
    results['API Import'] = test_api_import()
    results['Workflow Import'] = test_workflow_import()
    
    # Test checks
    print_header("3. TEST EXECUTION")
    results['Unit Tests'] = run_unit_tests()
    results['Integration Tests'] = run_integration_tests()
    
    # Generate report
    system_ready = generate_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if system_ready else 1)

if __name__ == "__main__":
    main()
