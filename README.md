# Agentic Shield Orchestration System

A multi-agent platform for financial services that provides automated loan approval decisions and health insurance premium recommendations using LangGraph and pre-trained EBM models.

## Project Structure

```
.
├── frontend/          # React web application (formerly kavach)
│   ├── src/          # React components and pages
│   ├── public/       # Static assets
│   └── package.json  # Frontend dependencies
│
├── backend/          # Python backend with LangGraph agents
│   ├── src/          # Source code
│   │   ├── agents/   # Agent implementations (KYC, Onboarding, etc.)
│   │   ├── graph/    # LangGraph workflow definition
│   │   ├── schemas/  # State and data models
│   │   ├── utils/    # Utilities (logging, error handling, etc.)
│   │   ├── models/   # Pre-trained ML models
│   │   └── rules/    # Regulatory compliance rules
│   ├── tests/        # Test suite
│   ├── examples/     # Example usage and sample documents
│   ├── .kiro/        # Kiro specs and configuration
│   ├── requirements.txt  # Python dependencies
│   └── pytest.ini    # Test configuration
│
└── README.md         # This file
```

## Features

- **Multi-Agent Orchestration**: LangGraph-based workflow with specialized agents
- **KYC Verification**: Mock DigiLocker integration for identity verification
- **Document Processing**: OCR-based extraction from financial and medical documents
- **Compliance Checking**: RAG-based validation against regulatory rules (USDA/IRDAI)
- **ML-Powered Decisions**: EBM models for loan approval and insurance premium prediction
- **Explainable AI**: Natural language explanations using Groq LLM
- **Human-in-the-Loop**: Checkpoint for manual data review and correction
- **Supervisor Agent**: Intelligent routing and loopback for additional information

## Quick Start

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your Groq API key
   ```

4. Run tests:
   ```bash
   pytest
   ```

5. Run example workflow:
   ```bash
   python src/main.py
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open browser to `http://localhost:5173`

## Technology Stack

### Backend
- **Framework**: LangGraph for multi-agent orchestration
- **LLM**: Groq (llama-3.1-70b-versatile)
- **ML Models**: Explainable Boosting Machines (EBM)
- **Language**: Python 3.10+
- **Testing**: pytest

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS
- **Language**: JavaScript/JSX

## Workflow

```
KYC Verification → Document Processing → HITL Checkpoint → 
Compliance Check → Router → Underwriting → Verification → 
Explanation → Supervisor Decision
```

### Agents

1. **KYC Agent**: Verifies identity using Mock DigiLocker
2. **Onboarding Agent**: Extracts data from documents using OCR
3. **Compliance Agent**: Validates against regulatory rules
4. **Router Agent**: Routes to loan/insurance/both processing
5. **Underwriting Agent**: Invokes ML models for predictions
6. **Verification Agent**: LLM-based sanity checking
7. **Transparency Agent**: Generates natural language explanations
8. **Supervisor Agent**: Makes final decisions and handles loopback

## Development

### Running Tests

```bash
cd backend
pytest                    # Run all tests
pytest -m unit           # Run unit tests only
pytest -m integration    # Run integration tests only
pytest -v                # Verbose output
```

### Code Structure

- `backend/src/agents/`: Individual agent implementations
- `backend/src/graph/workflow.py`: Main LangGraph workflow
- `backend/src/schemas/state.py`: Application state definition
- `backend/src/utils/`: Shared utilities
- `backend/tests/`: Test suite with fixtures

## Documentation

- `backend/WORKFLOW.md`: Detailed workflow documentation
- `backend/IMPLEMENTATION_STATUS.md`: Implementation progress
- `backend/.kiro/specs/`: Feature specifications and design docs

## License

[Add your license here]

## Contributors

[Add contributors here]
