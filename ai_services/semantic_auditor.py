"""Behavioral semantic auditor for RG risk explanations."""

from ai_services.config import LLMConfig
from ai_services.provider_base import LLMProvider
from ai_services.schemas import RiskExplanationRequest, RiskExplanationResponse


class BehavioralSemanticAuditor:
    """Generate human-readable risk explanations using an LLM provider."""

    def __init__(self, provider: LLMProvider, config: LLMConfig) -> None:
        """
        Initialize the auditor.

        Args:
            provider: LLM provider implementation.
            config: LLM configuration.
        """
        self.provider = provider
        self.config = config

    def generate_risk_explanation(
        self, request: RiskExplanationRequest, reasoning: bool = True
    ) -> RiskExplanationResponse:
        """
        Generate a structured risk explanation for a player.

        Args:
            request: RiskExplanationRequest payload.
            reasoning: Use reasoning model if True, fast model if False.

        Returns:
            RiskExplanationResponse.
        """
        prompt = self._build_prompt(request)
        model = self.config.reasoning_model if reasoning else self.config.fast_model

        raw = self.provider.generate_json(
            prompt=prompt,
            model=model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            system_prompt=(
                "You are a responsible gaming analyst assistant at DraftKings. "
                "Provide clear, compliant, and audit-ready explanations."
            ),
        )
        return RiskExplanationResponse.model_validate(raw)

    @staticmethod
    def _build_prompt(request: RiskExplanationRequest) -> str:
        """Build the LLM prompt from request data."""
        return f"""Analyze this player's responsible gaming risk profile.

PLAYER ID: {request.player_id}
COMPOSITE RISK SCORE: {request.composite_risk_score:.2f}/1.00
RISK CATEGORY: {request.risk_category or 'N/A'}
STATE: {request.state_jurisdiction or 'N/A'}

BEHAVIORAL EVIDENCE (Past 7 Days):
- Total Bets: {request.total_bets_7d if request.total_bets_7d is not None else 'N/A'}
- Total Wagered: {request.total_wagered_7d if request.total_wagered_7d is not None else 'N/A'}
- Loss Chase Score: {request.loss_chase_score if request.loss_chase_score is not None else 'N/A'}
- Bet Escalation Score: {request.bet_escalation_score if request.bet_escalation_score is not None else 'N/A'}
- Market Drift Score: {request.market_drift_score if request.market_drift_score is not None else 'N/A'}
- Temporal Risk Score: {request.temporal_risk_score if request.temporal_risk_score is not None else 'N/A'}
- Gamalyze Risk Score: {request.gamalyze_risk_score if request.gamalyze_risk_score is not None else 'N/A'}

Provide response in JSON format:
{{
  "risk_verdict": "CRITICAL | HIGH | MEDIUM | LOW",
  "explanation": "2-3 sentence explanation of WHY this player is flagged",
  "key_evidence": ["Evidence 1", "Evidence 2", "Evidence 3"],
  "recommended_action": "Specific intervention recommendation",
  "draft_customer_nudge": "Supportive 2-3 sentence message to player",
  "regulatory_notes": "State-specific reporting requirements if applicable"
}}

CRITICAL REQUIREMENTS for draft_customer_nudge:
- Supportive, non-judgmental tone (never "irresponsible", "addicted")
- Include link to Responsible Gaming Center (rg.draftkings.com)
- Emphasize player autonomy ("you can choose" not "you must")
- NO specific dollar amounts
- NO medical/clinical language
"""
