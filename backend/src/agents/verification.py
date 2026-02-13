"""
Verification Agent with LLM-based sanity checking.

This module implements a final verification layer that uses Groq LLM to validate
ML model outputs and reasoning before sending results to the frontend.
"""

import logging
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from src.schemas.state import ApplicationState

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    """Pydantic model for verification results."""
    verified: bool = Field(description="Whether the decision is verified as reasonable")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    concerns: list[str] = Field(default_factory=list, description="List of concerns or red flags")
    recommendation: str = Field(description="Recommendation: APPROVE, REVIEW, REJECT, or ADJUST")


class VerificationAgent:
    """
    Verification agent that performs LLM-based sanity checks on ML model decisions.
    
    This agent:
    - Reviews loan approval decisions for consistency
    - Reviews insurance premium predictions for reasonableness
    - Identifies potential concerns or red flags
    - Returns verification result with confidence score
    """
    
    def __init__(self):
        """Initialize the Verification Agent with Groq LLM."""
        logger.info("Initializing VerificationAgent")
        
        try:
            from langchain_groq import ChatGroq
            from langchain.output_parsers import PydanticOutputParser
            
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.2  # Low temperature for consistent verification
            )
            
            # Initialize Pydantic output parser
            self.parser = PydanticOutputParser(pydantic_object=VerificationResult)
            
            logger.info("VerificationAgent initialized successfully with Pydantic parser")
        except ImportError:
            logger.warning("langchain_groq not available, verification will be limited")
            self.llm = None
            self.parser = None
        except Exception as e:
            logger.warning(f"Failed to initialize Groq LLM: {e}")
            self.llm = None
            self.parser = None
    
    def verify_decision(self, state: ApplicationState) -> ApplicationState:
        """
        Main verification method that routes to loan or insurance verification.
        
        Args:
            state: Current application state with predictions
        
        Returns:
            Updated state with verification_result field
        """
        try:
            request_type = state.get("request_type", "both")
            
            # Verify loan decision if present
            if request_type in ["loan", "both"] and state.get("loan_prediction"):
                loan_verification = self._verify_loan_decision(state)
                state["loan_verification"] = loan_verification
                logger.info(f"Loan verification: {loan_verification.get('verified', False)}")
            
            # Verify insurance decision if present
            if request_type in ["insurance", "both"] and state.get("insurance_prediction"):
                insurance_verification = self._verify_insurance_decision(state)
                state["insurance_verification"] = insurance_verification
                logger.info(f"Insurance verification: {insurance_verification.get('verified', False)}")
            
            return state
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            state.setdefault("errors", []).append(f"Verification: {str(e)}")
            return state
    
    def _verify_loan_decision(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Verify loan decision makes sense given applicant data.
        
        Args:
            state: Application state with loan_prediction and applicant_data
        
        Returns:
            Verification result with verified flag, concerns, and confidence
        """
        if not self.llm or not self.parser:
            # Fallback verification without LLM
            return self._fallback_loan_verification(state)
        
        try:
            prediction = state["loan_prediction"]
            applicant_data = state["applicant_data"]
            
            # Format reasoning for prompt
            reasoning_text = self._format_reasoning(prediction.get("reasoning", {}))
            
            # Get format instructions from parser
            format_instructions = self.parser.get_format_instructions()
            
            prompt = f"""You are a senior loan underwriter reviewing an AI decision.

Applicant Profile:
- CIBIL Score: {applicant_data.get('cibil_score', 'N/A')}
- Annual Income: ₹{applicant_data.get('annual_income', applicant_data.get('income_annum', 'N/A'))}
- Loan Amount: ₹{applicant_data.get('loan_amount', 'N/A')}
- Existing Debt: ₹{applicant_data.get('existing_debt', 'N/A')}
- Age: {applicant_data.get('age', 'N/A')}
- Employment: {applicant_data.get('employment_type', 'N/A')}
- Employment Years: {applicant_data.get('employment_years', 'N/A')}

AI Decision: {"APPROVED" if prediction['approved'] else "REJECTED"}
Confidence: {prediction['probability']:.1%}

Top Contributing Factors:
{reasoning_text}

Task: Verify if this decision is reasonable. Consider:
1. Does the decision align with the applicant's profile?
2. Are the contributing factors logical?
3. Are there any red flags or concerns?

{format_instructions}"""
            
            response = self.llm.invoke(prompt).content
            
            # Parse using Pydantic parser
            try:
                verification = self.parser.parse(response)
                result = verification.model_dump()
                logger.debug(f"Loan verification result: {result}")
                return result
            except ValidationError as e:
                logger.warning(f"Pydantic validation failed, trying manual JSON parse: {e}")
                # Fallback to manual JSON parsing
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()
                verification = json.loads(response)
                return verification
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._fallback_loan_verification(state)
        except Exception as e:
            logger.error(f"Loan verification failed: {e}")
            return self._fallback_loan_verification(state)
    
    def _verify_insurance_decision(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Verify insurance premium makes sense given applicant data.
        
        Args:
            state: Application state with insurance_prediction and applicant_data
        
        Returns:
            Verification result with verified flag, concerns, and confidence
        """
        if not self.llm or not self.parser:
            # Fallback verification without LLM
            return self._fallback_insurance_verification(state)
        
        try:
            prediction = state["insurance_prediction"]
            applicant_data = state["applicant_data"]
            
            # Format reasoning for prompt
            reasoning_text = self._format_reasoning(prediction.get("reasoning", {}))
            
            # Get format instructions from parser
            format_instructions = self.parser.get_format_instructions()
            
            prompt = f"""You are a senior insurance underwriter reviewing an AI premium calculation.

Applicant Profile:
- Age: {applicant_data.get('age', 'N/A')}
- BMI: {applicant_data.get('bmi', 'N/A')}
- Smoker: {applicant_data.get('smoker', 'N/A')}
- Pre-existing Conditions: {applicant_data.get('pre_existing_conditions', [])}
- Blood Pressure: {"High" if applicant_data.get('bloodpressure') else "Normal"}
- Diabetes: {"Yes" if applicant_data.get('diabetes') else "No"}
- Occupation Risk: {applicant_data.get('occupation_risk', 'N/A')}

AI Premium: ₹{prediction['premium']:,.2f}

Top Contributing Factors:
{reasoning_text}

Task: Verify if this premium is reasonable. Consider:
1. Is the premium appropriate for the risk profile?
2. Are the contributing factors logical?
3. Are there any concerns about fairness or accuracy?

{format_instructions}"""
            
            response = self.llm.invoke(prompt).content
            
            # Parse using Pydantic parser
            try:
                verification = self.parser.parse(response)
                result = verification.model_dump()
                logger.debug(f"Insurance verification result: {result}")
                return result
            except ValidationError as e:
                logger.warning(f"Pydantic validation failed, trying manual JSON parse: {e}")
                # Fallback to manual JSON parsing
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()
                verification = json.loads(response)
                return verification
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._fallback_insurance_verification(state)
        except Exception as e:
            logger.error(f"Insurance verification failed: {e}")
            return self._fallback_insurance_verification(state)
    
    def _format_reasoning(self, reasoning: Dict[str, float]) -> str:
        """
        Format feature contributions for prompt.
        
        Args:
            reasoning: Dictionary of feature contributions
        
        Returns:
            Formatted string with top 5 features
        """
        if not reasoning:
            return "No reasoning available"
        
        # Sort by absolute contribution
        sorted_features = sorted(
            reasoning.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # Format top 5 features
        lines = []
        for name, value in sorted_features[:5]:
            lines.append(f"- {name}: {value:+.3f}")
        
        return "\n".join(lines)
    
    def _fallback_loan_verification(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Fallback verification for loan decisions without LLM.
        
        Uses rule-based logic to verify basic consistency.
        
        Args:
            state: Application state
        
        Returns:
            Basic verification result
        """
        prediction = state.get("loan_prediction", {})
        applicant_data = state.get("applicant_data", {})
        
        concerns = []
        
        # Check for basic inconsistencies
        cibil = applicant_data.get('cibil_score', 0)
        approved = prediction.get('approved', False)
        probability = prediction.get('probability', 0.5)
        
        # Very low CIBIL but approved
        if cibil < 600 and approved:
            concerns.append("Low CIBIL score but approved")
        
        # Very high CIBIL but rejected
        if cibil > 800 and not approved:
            concerns.append("High CIBIL score but rejected")
        
        # Low confidence decision
        if 0.4 < probability < 0.6:
            concerns.append("Low confidence decision (near threshold)")
        
        return {
            "verified": len(concerns) == 0,
            "confidence": 0.7 if len(concerns) == 0 else 0.5,
            "concerns": concerns,
            "recommendation": "APPROVE" if len(concerns) == 0 else "REVIEW"
        }
    
    def _fallback_insurance_verification(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Fallback verification for insurance decisions without LLM.
        
        Uses rule-based logic to verify basic consistency.
        
        Args:
            state: Application state
        
        Returns:
            Basic verification result
        """
        prediction = state.get("insurance_prediction", {})
        applicant_data = state.get("applicant_data", {})
        
        concerns = []
        
        # Check for basic inconsistencies
        premium = prediction.get('premium', 0)
        age = applicant_data.get('age', 30)
        
        # Unreasonably low premium
        if premium < 5000:
            concerns.append("Premium seems unusually low")
        
        # Unreasonably high premium
        if premium > 100000:
            concerns.append("Premium seems unusually high")
        
        # Young person with very high premium
        if age < 30 and premium > 50000:
            concerns.append("High premium for young applicant")
        
        return {
            "verified": len(concerns) == 0,
            "confidence": 0.7 if len(concerns) == 0 else 0.5,
            "concerns": concerns,
            "recommendation": "APPROVE" if len(concerns) == 0 else "REVIEW"
        }


def verify_decision(state: ApplicationState) -> ApplicationState:
    """
    Convenience function for workflow integration.
    
    Args:
        state: Current application state
    
    Returns:
        Updated state with verification results
    """
    try:
        agent = VerificationAgent()
        return agent.verify_decision(state)
    except Exception as e:
        logger.error(f"Verification processing failed: {e}")
        state.setdefault("errors", []).append(f"Verification: {str(e)}")
        return state
