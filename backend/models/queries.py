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
    result_columns: list[str] | None = None
    result_rows: list[list] | None = None
    row_count: int | None = None
    duration_ms: int | None = None


class QueryLogEntry(BaseModel):
    """Logged SQL query entry for a player."""

    player_id: str
    analyst_id: str
    prompt_text: str
    draft_sql: str
    final_sql: str
    purpose: str
    result_summary: str
    result_columns: list[str] | None = None
    result_rows: list[list] | None = None
    row_count: int | None = None
    duration_ms: int | None = None
    created_at: str


class SqlExecuteRequest(BaseModel):
    """Request body for executing read-only SQL."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    sql_text: str = Field(..., min_length=10, max_length=8000)
    purpose: str = Field(..., min_length=5, max_length=500)
    analyst_id: str | None = Field(default=None, max_length=100)
    prompt_text: str | None = Field(default=None, max_length=2000)
    result_summary: str | None = Field(default=None, max_length=1000)
    log: bool = False


class SqlExecuteResponse(BaseModel):
    """Response payload for executed SQL."""

    columns: list[str]
    rows: list[list]
    row_count: int
    duration_ms: int
    result_summary: str


class TriggerCheckResult(BaseModel):
    """State trigger check result payload."""

    state: str
    triggered: bool
    reason: str
    sql_text: str
    row_count: int
    created_at: str | None = None


class CaseTimelineEntry(BaseModel):
    """Unified timeline entry for case activity."""

    event_type: str
    event_detail: str
    created_at: str
