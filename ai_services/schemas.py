"""Pydantic models for LLM input/output schemas."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class RiskExplanationRequest(BaseModel):
    """Input schema for semantic risk explanation generation."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    composite_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_category: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None

    total_bets_7d: Optional[int] = Field(None, ge=0)
    total_wagered_7d: Optional[float] = Field(None, ge=0)

    loss_chase_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    bet_escalation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    market_drift_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    temporal_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    gamalyze_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    state_jurisdiction: Optional[Literal["MA", "NJ", "PA"]] = None


class RiskExplanationResponse(BaseModel):
    """Output schema for semantic risk explanation generation."""

    risk_verdict: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    explanation: str
    key_evidence: List[str]
    recommended_action: str
    draft_customer_nudge: str
    regulatory_notes: Optional[str] = None


class NudgeValidationResult(BaseModel):
    """Result schema for safety validation of customer nudges."""

    is_valid: bool
    violations: List[str]


class NudgeValidationRequest(BaseModel):
    """Input schema for nudge validation."""

    nudge_text: str = Field(..., min_length=10, max_length=2000)
