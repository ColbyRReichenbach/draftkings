"""AI endpoints for semantic audit and nudge validation."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from ai_services.semantic_auditor import BehavioralSemanticAuditor
from ai_services.schemas import (
    NudgeValidationRequest,
    NudgeValidationResult,
    RiskExplanationRequest,
    RiskExplanationResponse,
)
from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.hitl import PromptLogEntry

router = APIRouter()


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
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                payload.player_id,
                analyst_name,
                prompt_text,
                result.model_dump_json(),
                datetime.utcnow().isoformat(),
            ),
            db_path=db_path,
        )
    except Exception:
        # Logging failure should not block response
        pass

    return result


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
        SELECT player_id, analyst_id, prompt_text, response_text, created_at
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
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]
