"""
Underwriting Agent with ML model loading.

This module implements loan and insurance underwriting using pre-trained EBM models.
The agent uses Daksha (EBM classifier) for loan approval and Health Shield 
(EBM regressor) for insurance premium prediction.
"""

import logging
import pickle
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path

sys.modules.setdefault("src.agents.underwriting", sys.modules[__name__])

from src.schemas.state import ApplicationState
from src.utils.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class UnderwritingAgent:
    """
    Underwriting agent that invokes pre-trained EBM models for loan and insurance decisions.
    
    This agent:
    - Loads EBM models via ModelLoader singleton
    - Encodes applicant features using pre-trained encoders
    - Invokes Daksha for loan approval prediction
    - Invokes Health Shield for insurance premium prediction
    - Extracts reasoning from EBM explanations
    - Validates monotonicity constraints (logs warnings only)
    """
    
    def __init__(self):
        """Initialize the Underwriting Agent and load all required models."""
        logger.info("Initializing UnderwritingAgent")
        
        # Get ModelLoader singleton
        self.model_loader = ModelLoader()
        
        # Load all 4 models
        self._load_models()
        
        logger.info("UnderwritingAgent initialized successfully")
    
    def _load_models(self):
        """Load all required models (EBMs and encoders)."""
        try:
            # Try to load finance models
            self.credit_model = self.model_loader.load_model("ebm_finance")
            self.credit_encoders = self.model_loader.load_model("fin_encoders")
            
            # Try to load health models
            self.health_model = self.model_loader.load_model("ebm_health")
            self.health_encoders = self.model_loader.load_model("health_encoders")
            
            # Check if models loaded successfully
            models_loaded = all([
                self.credit_model is not None, 
                self.credit_encoders is not None,
                self.health_model is not None, 
                self.health_encoders is not None
            ])
            
            if not models_loaded:
                self._load_models_from_fallback()

            models_loaded = all([
                self.credit_model is not None,
                self.credit_encoders is not None,
                self.health_model is not None,
                self.health_encoders is not None
            ])

            if not models_loaded:
                raise RuntimeError("Required models not available. Cannot proceed.")

            logger.info("All models loaded successfully")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise RuntimeError(f"Underwriting agent initialization failed: {e}")

    def _load_models_from_fallback(self) -> None:
        """Load models directly from the default backend/models directory."""
        fallback_dir = Path(__file__).resolve().parents[2] / "models"

        def _load(path: Path) -> Optional[Any]:
            if not path.exists():
                return None
            try:
                with open(path, "rb") as handle:
                    return pickle.load(handle)
            except Exception as exc:
                logger.error(f"Failed to load model from {path}: {exc}")
                return None

        if self.credit_model is None:
            self.credit_model = _load(fallback_dir / "ebm_finance.pkl")
        if self.credit_encoders is None:
            self.credit_encoders = _load(fallback_dir / "fin_encoders.pkl")
        if self.health_model is None:
            self.health_model = _load(fallback_dir / "ebm_health.pkl")
        if self.health_encoders is None:
            self.health_encoders = _load(fallback_dir / "health_encoders.pkl")
    
    def process_loan(self, state: ApplicationState) -> ApplicationState:
        """
        Process loan application using Daksha EBM model.
        
        Args:
            state: Current application state with applicant_data
        
        Returns:
            Updated state with loan_prediction field populated
        """
        try:
            logger.info("Processing loan application")
            
            # Extract and validate applicant data
            applicant_data = state.get("applicant_data", {})
            if not applicant_data:
                raise ValueError("No applicant_data found in state")
            
            # Encode features
            features = self._encode_finance_features(applicant_data)

            # Get prediction and explanation from EBM
            prediction_proba = self.credit_model.predict_proba(features)[0]
            approval_probability = float(prediction_proba[1])  # Probability of class 1 (Approved)

            # Get local explanation
            explanation = self.credit_model.explain_local(features)
            reasoning = self._extract_reasoning(explanation)

            # Validate monotonicity (log only, don't block)
            self._validate_loan_monotonicity(applicant_data, approval_probability, reasoning)

            # Apply guardrail for very low CIBIL scores
            cibil_score = applicant_data.get("cibil_score")
            if cibil_score is not None:
                try:
                    if float(cibil_score) < 600:
                        approval_probability = min(approval_probability, 0.3)
                except (TypeError, ValueError):
                    pass

            # Update state
            state["loan_prediction"] = {
                "approved": approval_probability > 0.5,
                "probability": approval_probability,
                "reasoning": reasoning
            }

            logger.info(f"Loan prediction complete: {state['loan_prediction']['approved']} "
                       f"(probability: {approval_probability:.2%})")

            return state
            
        except Exception as e:
            logger.error(f"Loan processing failed: {e}")
            state.setdefault("errors", []).append(f"Underwriting (Loan): {str(e)}")
            state["rejected"] = True
            state["rejection_reason"] = "System error during underwriting"
            return state
    
    def process_insurance(self, state: ApplicationState) -> ApplicationState:
        """
        Process insurance application using Health Shield EBM model.
        
        Args:
            state: Current application state with applicant_data
        
        Returns:
            Updated state with insurance_prediction field populated
        """
        try:
            logger.info("Processing insurance application")
            
            # Extract and validate applicant data
            applicant_data = state.get("applicant_data", {})
            if not applicant_data:
                raise ValueError("No applicant_data found in state")
            
            # Encode features
            features = self._encode_health_features(applicant_data)

            # Get prediction and explanation from EBM
            premium = self.health_model.predict(features)[0]
            premium = float(premium)

            # Get local explanation
            explanation = self.health_model.explain_local(features)
            reasoning = self._extract_reasoning(explanation)

            # Validate monotonicity (log only, don't block)
            self._validate_insurance_monotonicity(applicant_data, premium, reasoning)

            # Update state
            state["insurance_prediction"] = {
                "premium": premium,
                "reasoning": reasoning
            }

            logger.info(f"Insurance prediction complete: premium = ₹{premium:,.2f}")

            return state
            
        except Exception as e:
            logger.error(f"Insurance processing failed: {e}")
            state.setdefault("errors", []).append(f"Underwriting (Insurance): {str(e)}")
            state["rejected"] = True
            state["rejection_reason"] = "System error during underwriting"
            return state
    
    def _encode_finance_features(self, applicant_data: Dict[str, Any]) -> np.ndarray:
        """
        Encode finance features using pre-trained encoders.
        
        Args:
            applicant_data: Raw applicant data dictionary
        
        Returns:
            Encoded feature array ready for model prediction
        """
        try:
            # Create DataFrame from applicant data
            df = pd.DataFrame([applicant_data])
            
            # Normalize field names (handle both 'annual_income' and 'income_annum')
            if 'annual_income' in df.columns and 'income_annum' not in df.columns:
                df['income_annum'] = df['annual_income']
            
            # Ensure required fields exist with defaults
            required_fields = ['loan_amount', 'income_annum', 'residential_assets_value', 
                             'commercial_assets_value', 'luxury_assets_value', 'bank_asset_value']
            for field in required_fields:
                if field not in df.columns:
                    df[field] = 0
                    
            # Feature Engineering (CRITICAL: Must match training pipeline)
            # These engineered features MUST be created before encoding
            df['loan_to_income_ratio'] = df['loan_amount'] / (df['income_annum'] + 1)
            
            df['total_assets'] = (
                df['residential_assets_value'].fillna(0) +
                df['commercial_assets_value'].fillna(0) +
                df['luxury_assets_value'].fillna(0) +
                df['bank_asset_value'].fillna(0)
            )
            
            df['asset_to_loan_ratio'] = df['total_assets'] / (df['loan_amount'] + 1)
            
            logger.debug(f"Engineered features: loan_to_income_ratio={df['loan_to_income_ratio'].iloc[0]:.3f}, "
                        f"total_assets={df['total_assets'].iloc[0]:.0f}, "
                        f"asset_to_loan_ratio={df['asset_to_loan_ratio'].iloc[0]:.3f}")
            
            # Apply categorical encoding using pre-trained encoders
            for col, encoder in self.credit_encoders.items():
                if col in df.columns:
                    try:
                        # Transform using fitted encoder
                        # Handle unknown categories by assigning a default value
                        original_values = df[col].astype(str)
                        
                        # Check if value is in encoder's classes
                        encoded_values = []
                        for val in original_values:
                            if val in encoder.classes_:
                                encoded_values.append(encoder.transform([val])[0])
                            else:
                                # Unknown category - use first class as default
                                logger.warning(f"Unknown category '{val}' for column '{col}', using default")
                                encoded_values.append(0)
                        
                        df[col] = encoded_values
                        
                    except Exception as e:
                        logger.warning(f"Failed to encode column {col}: {e}")
                        df[col] = 0  # Default value
            
            # Fill missing values
            df = df.fillna(0)

            # Align to model feature order to avoid shape mismatches
            df = self._align_to_model_features(df, self.credit_model)

            # Convert to numpy array
            features = df.values
            
            logger.debug(f"Encoded finance features shape: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Finance feature encoding failed: {e}")
            raise ValueError(f"Failed to encode finance features: {e}")
    
    def _encode_health_features(self, applicant_data: Dict[str, Any]) -> np.ndarray:
        """
        Encode health features using pre-trained encoders.
        
        Args:
            applicant_data: Raw applicant data dictionary
        
        Returns:
            Encoded feature array ready for model prediction
        """
        try:
            # Normalize known boolean-like fields to numeric values
            normalized = dict(applicant_data)
            boolean_fields = [
                "smoker",
                "diabetes",
                "bloodpressure",
                "regular_ex",
                "blood_pressure_problems",
                "any_transplants",
                "any_chronic_diseases",
                "known_allergies",
                "history_of_cancer_in_family"
            ]

            for field in boolean_fields:
                if field in normalized:
                    value = normalized[field]
                    if isinstance(value, str):
                        value_lower = value.strip().lower()
                        if value_lower in ["yes", "true", "1"]:
                            normalized[field] = 1
                        elif value_lower in ["no", "false", "0"]:
                            normalized[field] = 0
                    elif isinstance(value, bool):
                        normalized[field] = 1 if value else 0

            # Create DataFrame from applicant data
            df = pd.DataFrame([normalized])

            # Ensure boolean-like columns are numeric
            for field in boolean_fields:
                if field in df.columns:
                    df[field] = pd.to_numeric(df[field], errors="coerce")
            
            # Apply categorical encoding using pre-trained encoders
            for col, encoder in self.health_encoders.items():
                if col in df.columns:
                    try:
                        # Transform using fitted encoder
                        original_values = df[col].astype(str)
                        
                        # Check if value is in encoder's classes
                        encoded_values = []
                        for val in original_values:
                            if val in encoder.classes_:
                                encoded_values.append(encoder.transform([val])[0])
                            else:
                                # Unknown category - use first class as default
                                logger.warning(f"Unknown category '{val}' for column '{col}', using default")
                                encoded_values.append(0)
                        
                        df[col] = encoded_values
                        
                    except Exception as e:
                        logger.warning(f"Failed to encode column {col}: {e}")
                        df[col] = 0  # Default value
            
            # Fill missing values
            df = df.fillna(0)

            # Align to model feature order to avoid shape mismatches
            df = self._align_to_model_features(df, self.health_model)

            # Convert to numpy array
            features = df.values
            
            logger.debug(f"Encoded health features shape: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Health feature encoding failed: {e}")
            raise ValueError(f"Failed to encode health features: {e}")
    
    def _extract_reasoning(self, ebm_explanation) -> Dict[str, float]:
        """
        Extract feature contributions from EBM explanation object.
        
        The EBM explanation object from interpret library's explain_local() method
        contains contribution scores for each feature (Shapley-like values).
        
        Args:
            ebm_explanation: EBM local explanation object from explain_local()
        
        Returns:
            Dictionary mapping feature names to contribution values
        """
        try:
            reasoning = {}
            
            # Extract feature names and values
            if hasattr(ebm_explanation, 'data'):
                # interpret library structure: explanation.data(0) returns dict for first sample
                # This is the correct method as shown in test_model.py
                explanation_data = ebm_explanation.data(0)
                
                if 'names' in explanation_data and 'scores' in explanation_data:
                    feature_names = explanation_data['names']
                    feature_scores = explanation_data['scores']
                    
                    for name, score in zip(feature_names, feature_scores):
                        reasoning[name] = float(score)
                    
                    logger.debug(f"Extracted reasoning with {len(reasoning)} features using .data(0) method")
                
            else:
                # Fallback: try direct attribute access
                logger.warning("Using fallback reasoning extraction method")
                if hasattr(ebm_explanation, 'feature_names') and hasattr(ebm_explanation, 'values'):
                    for name, value in zip(ebm_explanation.feature_names, ebm_explanation.values):
                        reasoning[name] = float(value)
            
            if not reasoning:
                logger.warning("No reasoning extracted, returning empty dict")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Reasoning extraction failed: {e}")
            # Return empty dict instead of error dict to avoid breaking downstream processing
            return {}

    def _align_to_model_features(self, df: pd.DataFrame, model: Any) -> pd.DataFrame:
        """Align dataframe columns to model feature order when available."""
        feature_names: Optional[List[str]] = None
        for attr in ("feature_names_", "feature_names", "feature_names_in_"):
            if hasattr(model, attr):
                try:
                    feature_names = list(getattr(model, attr))
                    break
                except Exception:
                    continue

        if not feature_names:
            return df

        for name in feature_names:
            if name not in df.columns:
                df[name] = 0

        return df[feature_names]
    
    def _validate_loan_monotonicity(
        self, 
        applicant_data: Dict[str, Any], 
        probability: float, 
        reasoning: Dict[str, float]
    ) -> None:
        """
        Validate monotonicity constraints for loan approval.
        
        Expected monotonic relationships:
        - Higher CIBIL score → Higher approval probability
        - Higher income → Higher approval probability
        - Higher existing debt → Lower approval probability
        - Higher loan-to-income ratio → Lower approval probability
        
        Args:
            applicant_data: Raw applicant data
            probability: Predicted approval probability
            reasoning: Feature contributions from EBM
        """
        violations = []
        
        # Check CIBIL score (should be positive contributor for high scores)
        cibil_score = applicant_data.get('cibil_score', 0)
        cibil_contribution = reasoning.get('cibil_score', 0)
        if cibil_score > 750 and cibil_contribution < 0:
            violations.append(f"High CIBIL ({cibil_score}) has negative contribution ({cibil_contribution:.3f})")
        
        # Check income (should be positive contributor for high income)
        income = applicant_data.get('income_annum', 0) or applicant_data.get('annual_income', 0)
        income_contribution = reasoning.get('income_annum', 0) or reasoning.get('annual_income', 0)
        if income > 1000000 and income_contribution < 0:
            violations.append(f"High income (₹{income:,}) has negative contribution ({income_contribution:.3f})")
        
        # Check loan-to-income ratio (should be negative contributor for high ratios)
        loan_amount = applicant_data.get('loan_amount', 0)
        if income > 0:
            lti_ratio = loan_amount / income
            lti_contribution = reasoning.get('loan_to_income_ratio', 0)
            if lti_ratio > 5 and lti_contribution > 0:
                violations.append(f"High LTI ratio ({lti_ratio:.2f}) has positive contribution ({lti_contribution:.3f})")
        
        # Log violations (non-blocking)
        if violations:
            logger.warning(f"Monotonicity violations detected for loan approval: {'; '.join(violations)}")
        else:
            logger.debug("No monotonicity violations detected for loan")
    
    def _validate_insurance_monotonicity(
        self,
        applicant_data: Dict[str, Any],
        premium: float,
        reasoning: Dict[str, float]
    ) -> None:
        """
        Validate monotonicity constraints for insurance premium.
        
        Expected monotonic relationships:
        - Higher age → Higher premium
        - Pre-existing conditions → Higher premium
        - Higher BMI (if diabetic/hypertensive) → Higher premium
        
        Args:
            applicant_data: Raw applicant data
            premium: Predicted insurance premium
            reasoning: Feature contributions from EBM
        """
        violations = []
        
        # Check age (should be positive contributor for older applicants)
        age = applicant_data.get('age', 0)
        age_contribution = reasoning.get('age', 0)
        if age > 50 and age_contribution < 0:
            violations.append(f"High age ({age}) has negative contribution ({age_contribution:.3f})")
        
        # Check pre-existing conditions
        conditions = ['diabetes', 'blood_pressure_problems', 'any_transplants', 'any_chronic_diseases']
        for condition in conditions:
            has_condition = applicant_data.get(condition, False)
            condition_contribution = reasoning.get(condition, 0)
            
            # If condition is present, contribution should generally be positive (increase premium)
            if has_condition and condition_contribution < -0.1:  # Allow small negative values
                violations.append(f"Condition '{condition}' has negative contribution ({condition_contribution:.3f})")
        
        # Log violations (non-blocking)
        if violations:
            logger.warning(f"Monotonicity violations detected for insurance premium: {'; '.join(violations)}")
        else:
            logger.debug("No monotonicity violations detected for insurance")


def process_underwriting(state: ApplicationState) -> ApplicationState:
    """
    Convenience function for workflow integration.
    
    Routes to loan or insurance processing based on request_type.
    
    Args:
        state: Current application state
    
    Returns:
        Updated state with predictions
    """
    try:
        agent = UnderwritingAgent()
        request_type = state.get("request_type", "both")
        
        # Process based on request type
        if request_type in ["loan", "both"]:
            state = agent.process_loan(state)
        
        if request_type in ["insurance", "both"]:
            state = agent.process_insurance(state)
        
        return state
        
    except Exception as e:
        logger.error(f"Underwriting processing failed: {e}")
        state.setdefault("errors", []).append(f"Underwriting: {str(e)}")
        return state
