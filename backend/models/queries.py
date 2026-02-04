"""Pydantic models for SQL draft and query logging."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryDraftRequest(BaseModel):
    """Request body for drafting SQL via LLM."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_prompt: str = Field(..., min_length=10, max_length=2000)


class QueryDraftResponse(BaseModel):
    """Response payload for drafted SQL."""

    draft_sql: str
    assumptions: list[str]


class QueryLogRequest(BaseModel):
    """Request body for logging analyst-approved SQL."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_id: str = Field(..., min_length=3, max_length=100)
    prompt_text: str = Field(..., min_length=10, max_length=2000)
    draft_sql: str = Field(..., min_length=10, max_length=8000)
    final_sql: str = Field(..., min_length=10, max_length=8000)
    purpose: str = Field(..., min_length=5, max_length=500)
    result_summary: str = Field(..., min_length=5, max_length=1000)


class QueryLogEntry(BaseModel):
    """Logged SQL query entry for a player."""

    player_id: str
    analyst_id: str
    prompt_text: str
    draft_sql: str
    final_sql: str
    purpose: str
    result_summary: str
    created_at: str


class CaseTimelineEntry(BaseModel):
    """Unified timeline entry for case activity."""

    event_type: str
    event_detail: str
    created_at: str
