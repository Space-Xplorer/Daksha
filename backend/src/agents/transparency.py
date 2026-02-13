"""
Transparency Agent with Groq integration.

This module implements explanation generation using Groq LLM and
deterministic fallbacks based on feature contributions.
"""

from typing import Dict, Any, List, Tuple
import logging

from langchain_groq import ChatGroq

from src.schemas.state import ApplicationState

logger = logging.getLogger(__name__)


class TransparencyAgent:
	"""
	Generates user-friendly explanations for loan and insurance decisions.
	"""

	LOAN_PROMPT = (
		"You are a finance underwriter writing a clear, empathetic explanation.\n"
		"Use the provided top factors. Avoid policy, legal, or sensitive attributes.\n\n"
		"Decision: {decision}\n"
		"Approval Probability: {probability}\n"
		"Top Factors (name: contribution):\n{factors}\n\n"
		"Write 3-5 short sentences in plain language."
	)

	INSURANCE_PROMPT = (
		"You are a health insurance underwriter writing a clear, empathetic explanation.\n"
		"Use the provided top factors. Avoid policy, legal, or sensitive attributes.\n\n"
		"Premium: {premium}\n"
		"Top Factors (name: contribution):\n{factors}\n\n"
		"Write 3-5 short sentences in plain language."
	)

	def __init__(self) -> None:
		self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

	def explain_loan_decision(self, state: ApplicationState) -> ApplicationState:
		"""Generate explanation for loan decision."""
		prediction = state.get("loan_prediction") or {}
		reasoning = prediction.get("reasoning") or {}

		approved = bool(prediction.get("approved"))
		probability = float(prediction.get("probability", 0.0))

		top_factors = self._format_top_factors(reasoning)
		decision_text = "APPROVED" if approved else "REJECTED"

		prompt = self.LOAN_PROMPT.format(
			decision=decision_text,
			probability=f"{probability:.2%}",
			factors=top_factors
		)

		explanation = self._run_llm_or_fallback(
			prompt,
			fallback=self._fallback_loan_explanation(approved, probability, top_factors)
		)

		explanation = self._validate_explanation(explanation)
		state["loan_explanation"] = explanation
		return state

	def explain_insurance_premium(self, state: ApplicationState) -> ApplicationState:
		"""Generate explanation for insurance premium."""
		prediction = state.get("insurance_prediction") or {}
		reasoning = prediction.get("reasoning") or {}

		premium = float(prediction.get("premium", 0.0))
		top_factors = self._format_top_factors(reasoning)

		prompt = self.INSURANCE_PROMPT.format(
			premium=f"Rs {premium:,.2f}",
			factors=top_factors
		)

		explanation = self._run_llm_or_fallback(
			prompt,
			fallback=self._fallback_insurance_explanation(premium, top_factors)
		)

		explanation = self._validate_explanation(explanation)
		state["insurance_explanation"] = explanation
		return state

	def _run_llm_or_fallback(self, prompt: str, fallback: str) -> str:
		"""Invoke LLM, fallback to deterministic explanation on failure."""
		try:
			response = self.llm.invoke(prompt)
			content = getattr(response, "content", "") if response is not None else ""
			return content.strip() or fallback
		except Exception as exc:
			logger.warning(f"Transparency LLM failed, using fallback: {exc}")
			return fallback

	def _format_top_factors(self, reasoning: Dict[str, float]) -> str:
		"""Sort and format top feature contributions for prompting."""
		top_items = self._top_contributors(reasoning, top_k=5)
		if not top_items:
			return "- No strong factors were identified."

		lines = [f"- {name}: {score:+.3f}" for name, score in top_items]
		return "\n".join(lines)

	def _top_contributors(self, reasoning: Dict[str, float], top_k: int = 5) -> List[Tuple[str, float]]:
		"""Return top contributors by absolute value."""
		items = [(name, float(score)) for name, score in reasoning.items()]
		items.sort(key=lambda x: abs(x[1]), reverse=True)
		return items[:top_k]

	def _fallback_loan_explanation(self, approved: bool, probability: float, factors: str) -> str:
		"""Deterministic fallback for loan explanations."""
		status = "approved" if approved else "not approved"
		return (
			f"Your loan request was {status} based on the information provided. "
			f"The model's confidence was {probability:.2%}. "
			f"Key factors considered were:\n{factors}"
		)

	def _fallback_insurance_explanation(self, premium: float, factors: str) -> str:
		"""Deterministic fallback for insurance explanations."""
		return (
			f"Your estimated premium is Rs {premium:,.2f} based on the information provided. "
			f"Key factors considered were:\n{factors}"
		)

	def _validate_explanation(self, text: str) -> str:
		"""Ensure explanations are non-empty and a reasonable length."""
		cleaned = (text or "").strip()
		if len(cleaned) < 20:
			return cleaned if cleaned else "We could not generate a detailed explanation at this time."
		if len(cleaned) > 800:
			return cleaned[:797].rstrip() + "..."
		return cleaned


def generate_transparency(state: ApplicationState) -> ApplicationState:
	"""
	Convenience function for workflow integration.
	"""
	agent = TransparencyAgent()
	request_type = state.get("request_type", "both")

	if request_type in ["loan", "both"] and state.get("loan_prediction"):
		state = agent.explain_loan_decision(state)

	if request_type in ["insurance", "both"] and state.get("insurance_prediction"):
		state = agent.explain_insurance_premium(state)

	return state
