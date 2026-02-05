"""Pydantic models for analytics summary responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskMix(BaseModel):
    """Risk category mix for analyst workload."""

    critical: int = Field(0, ge=0)
    high: int = Field(0, ge=0)
    medium: int = Field(0, ge=0)
    low: int = Field(0, ge=0)


class FunnelCounts(BaseModel):
    """Case funnel counts for queue throughput."""

    queued: int = Field(0, ge=0)
    started: int = Field(0, ge=0)
    submitted: int = Field(0, ge=0)


class AnalyticsSummary(BaseModel):
    """Summary metrics for analyst performance view."""

    total_cases_started: int = Field(0, ge=0)
    total_cases_submitted: int = Field(0, ge=0)
    in_progress_count: int = Field(0, ge=0)
    avg_time_to_submit_hours: float = Field(0, ge=0)
    avg_time_in_progress_hours: float = Field(0, ge=0)
    sql_queries_logged: int = Field(0, ge=0)
    llm_prompts_logged: int = Field(0, ge=0)
    cases_with_sql_pct: float = Field(0, ge=0, le=1)
    cases_with_llm_pct: float = Field(0, ge=0, le=1)
    risk_mix: RiskMix
    trigger_checks_run: int = Field(0, ge=0)
    nudges_validated: int = Field(0, ge=0)
    funnel: FunnelCounts
