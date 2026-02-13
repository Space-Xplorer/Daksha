"""
Daksha - Main Entry Point

This is the unified entry point for the Daksha Orchestration System.
It provides a CLI interface to run different components of the system.

Usage:
    python daksha.py api          # Start Flask API server
    python daksha.py demo         # Run interactive demo
    python daksha.py demo-auto    # Run automated demo
    python daksha.py test         # Run all tests
    python daksha.py validate     # Validate system
    python daksha.py workflow     # Run workflow with custom data
    python daksha.py --help       # Show help
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
    """Print Daksha banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║                    DAKSHA SYSTEM                         ║
    ║          AI-Powered Loan & Insurance Platform            ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_api(args):
    """Start the Flask API server."""
    print("🚀 Starting Daksha API Server...\n")
    
    from main import create_app
    
    app = create_app()
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', args.port))
    debug = args.debug or os.getenv('FLASK_ENV') == 'development'
    
    print(f"""
    Server Configuration:
    - Host: {host}
    - Port: {port}
    - Debug: {debug}
    - Health Check: http://{host}:{port}/api/health
    
    Default Admin Credentials:
    - Email: admin@daksha.com
    - Password: admin123
    
    Press CTRL+C to stop the server
    """)
    
    app.run(host=host, port=port, debug=debug, threaded=True)


def run_demo(args):
    """Run the interactive demo."""
    print("🎬 Starting Interactive Demo...\n")
    
    if args.auto:
        # Run automated demo
        import demo_script_auto
    else:
        # Run interactive demo
        import demo_script


def run_tests(args):
    """Run tests."""
    import subprocess
    
    print("🧪 Running Tests...\n")
    
    if args.unit:
        print("Running unit tests...")
        result = subprocess.run([
            'python', '-m', 'pytest', 'tests/', '-v',
            '--ignore=tests/test_workflow.py'
        ])
    elif args.integration:
        print("Running integration tests...")
        result = subprocess.run([
            'python', '-m', 'pytest', 'tests/test_workflow.py', '-v'
        ])
    elif args.api:
        print("Running API tests...")
        result = subprocess.run(['python', 'test_api.py'])
    else:
        print("Running all tests...")
        result = subprocess.run([
            'python', '-m', 'pytest', 'tests/', '-v'
        ])
    
    sys.exit(result.returncode)


def run_validation(args):
    """Run system validation."""
    print("✓ Running System Validation...\n")
    
    import subprocess
    result = subprocess.run(['python', 'validate_system.py'])
    sys.exit(result.returncode)


def run_workflow(args):
    """Run workflow with custom data."""
    print("⚙️  Running Workflow...\n")
    
    from src.schemas.state import create_initial_state
    from src.graph.workflow import run_workflow
    import json
    
    # Load data from file or use defaults
    if args.data_file:
        with open(args.data_file, 'r') as f:
            data = json.load(f)
        
        state = create_initial_state(
            request_type=data.get('request_type', 'both'),
            applicant_data=data.get('applicant_data', {}),
            loan_type=data.get('loan_type'),
            submitted_name=data.get('submitted_name'),
            submitted_dob=data.get('submitted_dob')
        )
    else:
        # Use default test data
        state = create_initial_state(
            request_type="both",
            applicant_data={
                "name": "Rajesh Kumar",
                "cibil_score": 750,
                "annual_income": 1200000,
                "loan_amount": 500000,
                "existing_debt": 100000,
                "employment_type": "salaried",
                "employment_years": 5,
                "age": 32,
                "bmi": 24.5,
                "smoker": False,
                "gender": "M"
            },
            loan_type="home",
            submitted_name="Rajesh Kumar",
            submitted_dob="1990-05-15"
        )
    
    print(f"Request ID: {state['request_id']}")
    print(f"Request Type: {state['request_type']}")
    print("\nRunning workflow...\n")
    
    final_state = run_workflow(state)
    
    # Print results
    print("\n" + "="*70)
    print("WORKFLOW RESULTS")
    print("="*70 + "\n")
    
    print(f"✓ KYC Verified: {final_state.get('kyc_verified')}")
    print(f"✓ Compliance Passed: {final_state.get('compliance_passed')}")
    
    if 'loan_prediction' in final_state:
        loan = final_state['loan_prediction']
        print(f"\n💰 Loan Decision: {'APPROVED' if loan.get('approved') else 'REJECTED'}")
        print(f"   Probability: {loan.get('probability', 0):.1%}")
    
    if 'insurance_prediction' in final_state:
        insurance = final_state['insurance_prediction']
        print(f"\n🏥 Insurance Premium: ₹{insurance.get('premium', 0):,.2f}/year")
    
    print(f"\n✓ Completed: {final_state.get('completed')}")
    print(f"✗ Errors: {len(final_state.get('errors', []))}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json_state = {k: v for k, v in final_state.items() if not callable(v)}
            json.dump(json_state, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")


def show_info(args):
    """Show system information."""
    print_banner()
    
    print("""
    Daksha Orchestration System
    Version: 1.0.0
    
    Components:
    - Flask REST API (18 endpoints)
    - LangGraph Workflow (8 agents)
    - JWT Authentication
    - HITL Checkpoint
    - Mock Predictions
    
    Documentation:
    - API: backend/API_DOCUMENTATION.md
    - Demo: backend/DEMO_USE_CASE.md
    - Deployment: backend/DEPLOYMENT_CHECKLIST.md
    
    Quick Start:
    1. python daksha.py validate    # Validate system
    2. python daksha.py api         # Start API server
    3. python daksha.py demo-auto   # Run demo
    
    For help: python daksha.py --help
    """)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Daksha Orchestration System - Unified Entry Point',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python daksha.py api                    # Start API server
  python daksha.py api --port 8000        # Start on custom port
  python daksha.py demo                   # Run interactive demo
  python daksha.py demo --auto            # Run automated demo
  python daksha.py test                   # Run all tests
  python daksha.py test --unit            # Run unit tests only
  python daksha.py validate               # Validate system
  python daksha.py workflow               # Run workflow with defaults
  python daksha.py workflow --data data.json  # Run with custom data
  python daksha.py info                   # Show system info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start Flask API server')
    api_parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    api_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demo')
    demo_parser.add_argument('--auto', action='store_true', help='Run automated demo')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    test_parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    test_parser.add_argument('--api', action='store_true', help='Run API tests only')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate system')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run workflow')
    workflow_parser.add_argument('--data-file', help='JSON file with application data')
    workflow_parser.add_argument('--output', default='workflow_results.json', help='Output file for results')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Route to appropriate function
    if args.command == 'api':
        run_api(args)
    elif args.command == 'demo':
        run_demo(args)
    elif args.command == 'test':
        run_tests(args)
    elif args.command == 'validate':
        run_validation(args)
    elif args.command == 'workflow':
        run_workflow(args)
    elif args.command == 'info':
        show_info(args)
    else:
        parser.print_help()
        print("\nFor more information, run: python daksha.py <command> --help")


if __name__ == '__main__':
    main()
