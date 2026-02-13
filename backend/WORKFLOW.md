# Daksha Orchestration System - Workflow Documentation

## Overview

The Daksha system uses LangGraph to orchestrate a multi-agent workflow for processing loan and insurance applications. The workflow ensures proper validation, compliance checking, and decision-making with full traceability.

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAKSHA WORKFLOW                               │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────┐
                         │   START  │
                         └────┬─────┘
                              │
                              ▼
                      ┌───────────────┐
                      │  KYC Agent    │
                      │  (DigiLocker) │
                      └───────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              [Verified]          [Failed]
                    │                   │
                    ▼                   ▼
            ┌───────────────┐      ┌────────┐
            │  Onboarding   │      │  END   │
            │  Agent (OCR)  │      │(Reject)│
            └───────┬───────┘      └────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Compliance   │
            │  Agent (RAG)  │
            └───────┬───────┘
                    │
          ┌─────────┴─────────┐
          │                   │
    [Passed]            [Violated]
          │                   │
          ▼                   ▼
    ┌──────────┐         ┌────────┐
    │  Router  │         │  END   │
    │  Agent   │         │(Reject)│
    └────┬─────┘         └────────┘
         │
    ┌────┴────┬──────────────┐
    │         │              │
[Loan]  [Insurance]      [Both]
    │         │              │
    ▼         ▼              ▼
┌────────┐ ┌────────┐   ┌────────┐
│ Loan   │ │Insurance│   │ Loan   │
│Underw. │ │Underw.  │   │First   │
└───┬────┘ └───┬────┘   └───┬────┘
    │          │             │
    ▼          ▼             ▼
┌────────┐ ┌────────┐   ┌────────┐
│ Loan   │ │Insurance│   │ Loan   │
│Verify  │ │Verify   │   │Verify  │
└───┬────┘ └───┬────┘   └───┬────┘
    │          │             │
    ▼          ▼             ▼
┌────────┐ ┌────────┐   ┌────────┐
│ Loan   │ │Insurance│   │ Loan   │
│Explain │ │Explain  │   │Explain │
└───┬────┘ └───┬────┘   └───┬────┘
    │          │             │
    │          │             ▼
    │          │        ┌────────┐
    │          │        │Insurance│
    │          │        │Underw.  │
    │          │        └───┬────┘
    │          │            │
    │          │            ▼
    │          │        ┌────────┐
    │          │        │Insurance│
    │          │        │Verify   │
    │          │        └───┬────┘
    │          │            │
    │          │            ▼
    │          │        ┌────────┐
    │          │        │Insurance│
    │          │        │Explain  │
    │          │        └───┬────┘
    │          │            │
    └──────────┴────────────┴────┐
                                 │
                                 ▼
                          ┌──────────┐
                          │ Finalize │
                          └────┬─────┘
                               │
                               ▼
                          ┌────────┐
                          │  END   │
                          └────────┘
```

## Agent Descriptions

### 1. KYC Agent
- **Purpose**: Verify user identity using Mock DigiLocker
- **Input**: submitted_name, submitted_dob
- **Output**: kyc_verified, digilocker_id, verified_name, verified_dob, verified_gender
- **Rejection**: If name/DOB don't match DigiLocker records
- **Duration**: ~1.5 seconds (simulated network delay)

### 2. Onboarding Agent
- **Purpose**: Extract data from uploaded documents using OCR
- **Input**: uploaded_documents
- **Output**: extracted_data, document_verification
- **Processing**: 
  - Document classification
  - Field extraction (CIBIL, income, BMI, BP, etc.)
  - Document freshness verification
- **Status**: Stub implementation (TODO)

### 3. Compliance Agent
- **Purpose**: Validate against regulatory rules (USDA/IRDAI)
- **Input**: applicant_data, request_type
- **Output**: compliance_passed, compliance_violations
- **Rejection**: If CRITICAL or HIGH severity violations found
- **Technology**: RAG with FAISS vector store
- **Status**: Stub implementation (TODO)

### 4. Router Agent
- **Purpose**: Determine processing path based on request_type
- **Input**: request_type
- **Output**: current_agent (next node)
- **Routes**:
  - "loan" → underwriting_loan
  - "insurance" → underwriting_insurance
  - "both" → underwriting_loan (then insurance)

### 5. Underwriting Agents (Loan & Insurance)
- **Purpose**: Invoke ML models for predictions
- **Input**: applicant_data
- **Output**: 
  - Loan: approved, probability, reasoning
  - Insurance: premium, reasoning
- **Models**: Daksha (loan), Health Shield (insurance)
- **Status**: Stub implementation (TODO)

### 6. Verification Agents (Loan & Insurance)
- **Purpose**: LLM-based sanity check of ML predictions
- **Input**: prediction, applicant_data
- **Output**: verified, confidence, concerns
- **Technology**: Groq LLM
- **Status**: Stub implementation (TODO)

### 7. Transparency Agents (Loan & Insurance)
- **Purpose**: Generate human-readable explanations
- **Input**: prediction, reasoning
- **Output**: explanation (natural language)
- **Technology**: Groq LLM
- **Status**: Stub implementation (TODO)

### 8. Finalize
- **Purpose**: Mark workflow as completed
- **Output**: completed = True

## Conditional Routing Logic

### After KYC
```python
if kyc_verified:
    → onboarding
else:
    → end (rejected)
```

### After Compliance
```python
if compliance_passed:
    → router
else:
    → end (rejected)
```

### After Router
```python
if request_type == "loan":
    → underwriting_loan
elif request_type == "insurance":
    → underwriting_insurance
elif request_type == "both":
    → underwriting_loan  # Process loan first
```

### After Loan Explanation
```python
if request_type == "both" and not insurance_prediction:
    → underwriting_insurance  # Continue to insurance
else:
    → end (completed)
```

## Error Handling

All agents are wrapped with `@safe_agent_wrapper` decorator which:
1. Catches all exceptions
2. Logs errors with context
3. Updates state["errors"]
4. Returns state instead of raising
5. Prevents workflow crashes

## State Management

The workflow uses `ApplicationState` TypedDict with fields:
- **Request metadata**: request_id, request_type, loan_type, timestamp
- **KYC data**: kyc_verified, digilocker_id, verified_name, etc.
- **Documents**: uploaded_documents, extracted_data
- **Compliance**: compliance_passed, compliance_violations
- **Predictions**: loan_prediction, insurance_prediction
- **Verifications**: loan_verification, insurance_verification
- **Explanations**: loan_explanation, insurance_explanation
- **Workflow control**: current_agent, errors, completed, rejected

## Usage Example

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
if final_state["completed"] and not final_state["rejected"]:
    print(f"Loan approved: {final_state['loan_prediction']['approved']}")
    print(f"Explanation: {final_state['loan_explanation']}")
else:
    print(f"Rejected: {final_state['rejection_reason']}")
```

## Performance Characteristics

- **KYC**: ~1.5 seconds (simulated network delay)
- **Onboarding**: TBD (depends on OCR and document count)
- **Compliance**: TBD (depends on RAG retrieval)
- **Underwriting**: TBD (depends on model inference)
- **Verification**: TBD (depends on LLM latency)
- **Transparency**: TBD (depends on LLM latency)

**Target**: <5 seconds for loan-only, <8 seconds for both

## Next Steps

1. Implement remaining agent stubs (Onboarding, Compliance, Underwriting, Verification, Transparency)
2. Add model loading and caching
3. Integrate Groq LLM for verification and transparency
4. Add OCR service integration
5. Implement RAG for compliance checking
6. Add comprehensive testing
7. Performance optimization
