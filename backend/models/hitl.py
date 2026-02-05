"""Pydantic models for HITL notes and LLM logs."""

from pydantic import BaseModel, Field


class AnalystNoteRequest(BaseModel):
    """Request body for analyst notes submission."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_id: str = Field(..., min_length=3, max_length=100)
    analyst_action: str = Field(..., min_length=3, max_length=200)
    analyst_notes: str = Field(..., min_length=10, max_length=2000)


class AnalystNoteResponse(BaseModel):
    """Response for analyst notes retrieval."""

    player_id: str
    analyst_id: str
    analyst_action: str
    analyst_notes: str
    created_at: str


class AnalystNoteDraftRequest(BaseModel):
    """Request body for saving analyst draft notes."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_id: str = Field(..., min_length=3, max_length=100)
    draft_action: str = Field(..., min_length=0, max_length=200)
    draft_notes: str = Field(..., min_length=0, max_length=5000)


class AnalystNoteDraftResponse(BaseModel):
    """Response for analyst draft notes retrieval."""

    player_id: str
    analyst_id: str
    draft_action: str
    draft_notes: str
    updated_at: str


class NudgeLogRequest(BaseModel):
    """Request body for storing analyst nudge edits."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_id: str = Field(..., min_length=3, max_length=100)
    draft_nudge: str = Field(..., min_length=5, max_length=2000)
    final_nudge: str = Field(..., min_length=5, max_length=2000)
    validation_status: str = Field(..., min_length=2, max_length=20)
    validation_violations: list[str] = Field(default_factory=list)


class NudgeLogResponse(BaseModel):
    """Response for stored nudge log entries."""

    player_id: str
    analyst_id: str
    draft_nudge: str
    final_nudge: str
    validation_status: str
    validation_violations: list[str]
    created_at: str


class PromptLogEntry(BaseModel):
    """Logged LLM prompt/output for transparency."""

    player_id: str
    analyst_id: str
    prompt_text: str
    response_text: str
    route_type: str | None = None
    tool_used: str | None = None
    created_at: str
