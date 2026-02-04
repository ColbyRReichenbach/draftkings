"""AI endpoints for semantic audit and nudge validation."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

import re

from ai_services.query_drafter import build_query_draft_prompt, build_router_prompt
from ai_services.snowflake_sql import validate_snowflake_sql
from ai_services.semantic_auditor import BehavioralSemanticAuditor
from ai_services.schemas import (
    NudgeValidationRequest,
    NudgeValidationResult,
    RiskExplanationRequest,
    RiskExplanationResponse,
)
from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.hitl import PromptLogEntry
from backend.models.prompt_router import PromptRouteRequest, PromptRouteResponse
from backend.models.queries import QueryDraftRequest, QueryDraftResponse

router = APIRouter()
_PROHIBITED_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE)\b",
    re.IGNORECASE,
)


@router.post("/semantic-audit", response_model=RiskExplanationResponse)
async def semantic_audit(
    payload: RiskExplanationRequest,
    request: Request,
    reasoning: bool = True,
    db_path: str = Depends(get_db_path),
) -> RiskExplanationResponse:
    """
    Generate a semantic risk explanation for a player.

    Args:
        payload: RiskExplanationRequest payload.
        request: FastAPI request (for app state access).
        reasoning: Whether to use reasoning model.
        db_path: DuckDB path injected via dependency.

    Returns:
        RiskExplanationResponse.
    """
    auditor = request.app.state.semantic_auditor
    analyst_name = request.app.state.analyst_name

    if auditor is None:
        raise HTTPException(status_code=503, detail="LLM provider not configured.")

    result = auditor.generate_risk_explanation(payload, reasoning=reasoning)

    try:
        prompt_text = BehavioralSemanticAuditor._build_prompt(payload)
        execute(
            """
            INSERT INTO rg_llm_prompt_log (
                log_id,
                player_id,
                analyst_id,
                prompt_text,
                response_text,
                created_at,
                route_type,
                tool_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                payload.player_id,
                analyst_name,
                prompt_text,
                result.model_dump_json(),
                datetime.utcnow().isoformat(),
                "SEMANTIC_AUDIT",
                "semantic-audit",
            ),
            db_path=db_path,
        )
    except Exception:
        # Logging failure should not block response
        pass

    return result


@router.post("/query-draft", response_model=QueryDraftResponse)
async def query_draft(
    payload: QueryDraftRequest, request: Request
) -> QueryDraftResponse:
    """
    Draft a SQL query for analyst review.

    Args:
        payload: QueryDraftRequest payload.
        request: FastAPI request (for app state access).

    Returns:
        QueryDraftResponse with draft SQL and assumptions.
    """
    provider = request.app.state.llm_provider
    config = request.app.state.llm_config
    if provider is None:
        raise HTTPException(status_code=503, detail="LLM provider not configured.")

    prompt = build_query_draft_prompt(payload.player_id, payload.analyst_prompt)
    raw = provider.generate_json(
        prompt=prompt,
        model=config.fast_model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        system_prompt=(
            "You are a responsible gaming analytics assistant. "
            "Draft safe, read-only SQL queries only."
        ),
    )

    response = QueryDraftResponse.model_validate(raw)
    draft_sql = response.draft_sql.strip()
    if not draft_sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Draft SQL must be a SELECT statement.")
    if _PROHIBITED_SQL_PATTERN.search(draft_sql):
        raise HTTPException(status_code=400, detail="Draft SQL contains prohibited keywords.")
    if validate_snowflake_sql(draft_sql):
        raise HTTPException(
            status_code=400,
            detail="Draft SQL contains non-Snowflake syntax. Please use Snowflake functions only.",
        )
    return response


@router.post("/validate-nudge", response_model=NudgeValidationResult)
async def validate_nudge(
    payload: NudgeValidationRequest, request: Request
) -> NudgeValidationResult:
    """
    Validate a customer nudge for compliance.

    Args:
        payload: NudgeValidationRequest payload.
        request: FastAPI request (for app state access).

    Returns:
        NudgeValidationResult with violations.
    """
    validator = request.app.state.nudge_validator
    if validator is None:
        raise HTTPException(status_code=503, detail="LLM provider not configured.")
    return validator.validate_nudge(payload.nudge_text)


@router.post("/router", response_model=PromptRouteResponse)
async def route_prompt(
    payload: PromptRouteRequest,
    request: Request,
    db_path: str = Depends(get_db_path),
) -> PromptRouteResponse:
    """Route analyst prompts to the appropriate tool."""
    provider = request.app.state.llm_provider
    config = request.app.state.llm_config
    analyst_name = request.app.state.analyst_name
    if provider is None:
        raise HTTPException(status_code=503, detail="LLM provider not configured.")

    prompt_text = payload.analyst_prompt.strip()
    lower_prompt = prompt_text.lower()

    if any(keyword in lower_prompt for keyword in ["sql", "query", "select", "last", "bets"]):
        route = "SQL_DRAFT"
        tool = "query-draft"
    elif any(keyword in lower_prompt for keyword in ["regulation", "regulatory", "trigger", "responsible gaming"]):
        route = "REGULATORY_CONTEXT"
        tool = "policy-context"
    elif any(keyword in lower_prompt for keyword in ["news", "event", "game", "headline", "week of"]):
        route = "EXTERNAL_CONTEXT"
        tool = "external-context"
    else:
        route = "GENERAL_ANALYSIS"
        tool = "general-analysis"

    response_text = None
    draft_sql = None
    assumptions: list[str] | None = None

    if route == "SQL_DRAFT":
        raw = provider.generate_json(
            prompt=build_query_draft_prompt(payload.player_id, prompt_text),
            model=config.fast_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=(
                "You are a responsible gaming analytics assistant. "
                "Draft Snowflake-compatible, read-only SQL queries only."
            ),
        )
        response = QueryDraftResponse.model_validate(raw)
        draft_sql = response.draft_sql.strip()
        assumptions = response.assumptions
        if not draft_sql.upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400, detail="Draft SQL must be a SELECT statement."
            )
        if _PROHIBITED_SQL_PATTERN.search(draft_sql):
            raise HTTPException(
                status_code=400, detail="Draft SQL contains prohibited keywords."
            )
        if validate_snowflake_sql(draft_sql):
            raise HTTPException(
                status_code=400,
                detail="Draft SQL contains non-Snowflake syntax. Please use Snowflake functions only.",
            )
    else:
        routed_prompt = build_router_prompt(route, prompt_text, payload.player_id)
        raw_text = provider.generate_text(
            prompt=routed_prompt,
            model=config.reasoning_model,
            temperature=0.2,
            max_tokens=config.max_tokens,
            system_prompt=(
                "You are a responsible gaming analyst assistant. "
                "Be concise, supportive, and transparent about data limits."
            ),
        )
        response_text = raw_text.strip()

    execute(
        """
        INSERT INTO rg_llm_prompt_log (
            log_id,
            player_id,
            analyst_id,
            prompt_text,
            response_text,
            created_at,
            route_type,
            tool_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            payload.player_id,
            analyst_name,
            prompt_text,
            response_text or draft_sql or "",
            datetime.utcnow().isoformat(),
            route,
            tool,
        ),
        db_path=db_path,
    )

    return PromptRouteResponse(
        route=route,
        tool=tool,
        reasoning="Routed based on prompt intent keywords.",
        model_used=config.reasoning_model if route != "SQL_DRAFT" else config.fast_model,
        response_text=response_text,
        draft_sql=draft_sql,
        assumptions=assumptions,
    )


@router.get("/logs/{player_id}", response_model=list[PromptLogEntry])
async def get_prompt_logs(
    player_id: str, db_path: str = Depends(get_db_path)
) -> list[PromptLogEntry]:
    """Return prompt/response logs for a player.

    Args:
        player_id: Player identifier.
        db_path: DuckDB path injected via dependency.

    Returns:
        List of prompt log entries.
    """
    rows = query_rows(
        """
        SELECT player_id, analyst_id, prompt_text, response_text, created_at, route_type, tool_used
        FROM rg_llm_prompt_log
        WHERE player_id = ?
        ORDER BY created_at DESC
        """,
        (player_id,),
        db_path=db_path,
    )

    return [
        PromptLogEntry(
            player_id=row["player_id"],
            analyst_id=row["analyst_id"],
            prompt_text=row["prompt_text"],
            response_text=row["response_text"],
            route_type=row.get("route_type"),
            tool_used=row.get("tool_used"),
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]
