"""Pydantic models for case lifecycle status."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CaseStatusRequest(BaseModel):
    """Request body for starting or submitting a case."""

    case_id: str = Field(..., min_length=3, max_length=50)
    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_id: str = Field(..., min_length=3, max_length=100)


class CaseStatusEntry(BaseModel):
    """Status entry for audit trail cases."""

    case_id: str
    player_id: str
    analyst_id: str
    status: str
    started_at: str | None
    submitted_at: str | None
    updated_at: str
