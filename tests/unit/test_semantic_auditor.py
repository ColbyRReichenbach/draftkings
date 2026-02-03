"""Unit tests for BehavioralSemanticAuditor."""

from ai_services.config import LLMConfig
from ai_services.provider_base import LLMProvider
from ai_services.schemas import RiskExplanationRequest
from ai_services.semantic_auditor import BehavioralSemanticAuditor


class FakeProvider(LLMProvider):
    """Fake provider for unit tests."""

    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def generate_json(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None = None,
    ) -> dict:
        return self.payload


def test_generate_risk_explanation_returns_valid_response() -> None:
    payload = {
        "risk_verdict": "HIGH",
        "explanation": "Loss-chasing and escalation are elevated.",
        "key_evidence": ["Loss-chase score high", "Escalation ratio high"],
        "recommended_action": "Apply limits",
        "draft_customer_nudge": "You can choose tools at rg.draftkings.com.",
        "regulatory_notes": "NJ timeout if 3+ flags in 30 days.",
    }
    provider = FakeProvider(payload)
    auditor = BehavioralSemanticAuditor(provider=provider, config=LLMConfig())

    request = RiskExplanationRequest(
        player_id="PLR_1234_MA",
        composite_risk_score=0.75,
        risk_category="HIGH",
        total_bets_7d=25,
        total_wagered_7d=1500.0,
    )

    result = auditor.generate_risk_explanation(request)
    assert result.risk_verdict == "HIGH"
    assert "loss" in result.explanation.lower()
