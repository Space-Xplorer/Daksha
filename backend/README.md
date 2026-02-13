# Daksha Backend

Python backend for the Daksha Orchestration System using LangGraph.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment (optional):
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY
   ```

3. Verify installation:
   ```bash
   python -c "import langgraph; print('LangGraph installed successfully')"
   ```

## Running the System

### Basic Usage

```python
from src.schemas.state import create_initial_state
from src.graph.workflow import run_workflow

# Create initial state
state = create_initial_state(
    request_type="loan",
    applicant_data={
        "cibil_score": 750,
        "annual_income": 1200000.0,
        "loan_amount": 500000.0,
        "employment_type": "salaried",
        "existing_debt": 100000.0,
        "age": 32,
        "employment_years": 5
    },
    loan_type="home",
    submitted_name="Rajesh Kumar",
    submitted_dob="1990-05-15"
)

# Run workflow
final_state = run_workflow(state)

# Check results
if final_state["completed"]:
    print("Application processed successfully!")
    if final_state.get("loan_prediction"):
        print(f"Loan approved: {final_state['loan_prediction']['approved']}")
        print(f"Explanation: {final_state['loan_explanation']}")
```

## Testing

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests
pytest tests/test_kyc.py    # Specific test file
```

With coverage:
```bash
pytest --cov=src --cov-report=html
```

## Project Structure

```
backend/
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── kyc.py       # KYC verification
│   │   ├── onboarding.py # Document processing
│   │   ├── compliance.py # Regulatory compliance
│   │   ├── router.py    # Request routing
│   │   ├── underwriting.py # ML model invocation
│   │   ├── verification.py # LLM verification
│   │   ├── transparency.py # Explanation generation
│   │   └── supervisor.py # Workflow orchestration
│   │
│   ├── graph/
│   │   └── workflow.py  # LangGraph workflow definition
│   │
│   ├── schemas/
│   │   └── state.py     # ApplicationState TypedDict
│   │
│   ├── utils/
│   │   ├── logging.py   # Structured logging
│   │   ├── error_handling.py # Error categorization
│   │   ├── validation.py # Input validation
│   │   ├── model_loader.py # ML model loading
│   │   └── ocr_service.py # OCR integration
│   │
│   ├── models/
│   │   └── innovathon/  # Pre-trained EBM models
│   │
│   ├── rules/
│   │   ├── usda_loan_rules.txt
│   │   └── irdai_insurance_rules.txt
│   │
│   └── mock_db.json     # Mock DigiLocker database
│
├── tests/
│   ├── conftest.py      # Pytest fixtures
│   ├── test_kyc.py
│   ├── test_onboarding.py
│   ├── test_compliance.py
│   ├── test_agents.py
│   ├── test_validation.py
│   └── test_workflow.py
│
├── examples/
│   └── documents/       # Sample documents for testing
│
├── .kiro/
│   └── specs/          # Feature specifications
│
├── requirements.txt
├── pytest.ini
└── README.md           # This file
```

## Key Dependencies

- **langgraph**: Multi-agent orchestration framework
- **langchain-groq**: Groq LLM integration
- **interpret**: EBM model support
- **pydantic**: Data validation
- **pytest**: Testing framework

## Environment Variables

Create a `.env` file with:

```bash
# Groq API (for LLM agents)
GROQ_API_KEY=your_api_key_here

# Optional: Bypass compliance for testing
BYPASS_COMPLIANCE=false

# Logging
LOG_LEVEL=INFO
```

## Workflow Execution

The workflow follows this path:

1. **KYC Agent**: Verifies identity against Mock DigiLocker
2. **Onboarding Agent**: Extracts data from uploaded documents
3. **HITL Checkpoint**: Pauses for human review (optional)
4. **Compliance Agent**: Validates against regulatory rules
5. **Router Agent**: Routes to loan/insurance/both
6. **Underwriting Agent**: Invokes ML models
7. **Verification Agent**: LLM sanity check
8. **Transparency Agent**: Generates explanations
9. **Supervisor Agent**: Makes final decision

### Loopback Support

The Supervisor can request more information and loop back to earlier agents:
- Low confidence → Request more documents
- Data quality issues → Re-extract from documents
- Multiple concerns → Manual review

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the backend directory:
```bash
cd backend
python -m pytest  # Use -m flag
```

Or set PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows
```

### Model Loading Errors

If EBM models fail to load:
1. Check that `interpret` library is installed: `pip install interpret`
2. Verify model files exist in `src/models/innovathon/`
3. Check file permissions

### LLM Errors

If Groq LLM calls fail:
1. Verify GROQ_API_KEY is set in `.env`
2. Check API quota/rate limits
3. Agents have fallback logic for LLM failures

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `pytest`
4. Update documentation
5. Submit pull request

## Support

For issues or questions, please check:
- `.kiro/specs/` for design documentation
- `WORKFLOW.md` for workflow details
- `IMPLEMENTATION_STATUS.md` for current status
