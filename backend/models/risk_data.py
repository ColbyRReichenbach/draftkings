"""Pydantic models for live risk data endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskCase(BaseModel):
    """Queue case payload."""

    case_id: str
    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    risk_category: str
    composite_risk_score: float
    score_calculated_at: str
    state_jurisdiction: str | None
    key_evidence: list[str]


class CaseDetail(BaseModel):
    """Case detail payload for analyst review."""

    case_id: str
    player_id: str
    risk_category: str
    composite_risk_score: float
    score_calculated_at: str
    state_jurisdiction: str | None
    evidence_snapshot: dict
    ai_explanation: str
    draft_nudge: str
    regulatory_notes: str
    analyst_actions: list[str]


class AuditTrailEntry(BaseModel):
    """Audit trail entry for the dashboard."""

    audit_id: str
    case_id: str
    player_id: str
    analyst_id: str | None
    action: str
    risk_category: str
    state_jurisdiction: str | None
    timestamp: str
    notes: str


class CaseFileResponse(BaseModel):
    """Aggregated case file response."""

    case_detail: CaseDetail
    latest_note: dict | None
    prompt_logs: list[dict]
    query_logs: list[dict]
    timeline: list[dict]
