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


class PromptLogEntry(BaseModel):
    """Logged LLM prompt/output for transparency."""

    player_id: str
    analyst_id: str
    prompt_text: str
    response_text: str
    created_at: str
