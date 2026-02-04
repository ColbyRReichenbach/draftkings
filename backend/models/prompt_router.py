"""Pydantic models for analyst prompt routing."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PromptRouteRequest(BaseModel):
    """Request body for routing analyst prompts."""

    player_id: str = Field(..., pattern=r"^PLR_\d{4,6}_[A-Z]{2}$")
    analyst_prompt: str = Field(..., min_length=8, max_length=3000)


class PromptRouteResponse(BaseModel):
    """Routing response payload."""

    route: str
    tool: str
    reasoning: str
    model_used: str | None
    response_text: str | None = None
    draft_sql: str | None = None
    assumptions: list[str] | None = None
