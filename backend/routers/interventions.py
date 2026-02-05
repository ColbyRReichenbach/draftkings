"""HITL intervention endpoints."""

from __future__ import annotations

from datetime import datetime
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.hitl import (
    AnalystNoteRequest,
    AnalystNoteResponse,
    AnalystNoteDraftRequest,
    AnalystNoteDraftResponse,
    NudgeLogRequest,
    NudgeLogResponse,
)

router = APIRouter()


@router.post("/notes", response_model=AnalystNoteResponse)
async def submit_notes(
    payload: AnalystNoteRequest, db_path: str = Depends(get_db_path)
) -> AnalystNoteResponse:
    """Store analyst notes for a player.

    Args:
        payload: Analyst note submission payload.
        db_path: DuckDB path injected via dependency.

    Returns:
        Persisted analyst note response.
    """
    created_at = datetime.utcnow().isoformat()
    log_id = str(uuid4())

    execute(
        """
        INSERT INTO rg_analyst_notes_log (
            log_id,
            player_id,
            analyst_id,
            analyst_action,
            analyst_notes,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            payload.player_id,
            payload.analyst_id,
            payload.analyst_action,
            payload.analyst_notes,
            created_at,
        ),
        db_path=db_path,
    )

    return AnalystNoteResponse(
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        analyst_action=payload.analyst_action,
        analyst_notes=payload.analyst_notes,
        created_at=created_at,
    )


@router.post("/notes-draft", response_model=AnalystNoteDraftResponse)
async def submit_notes_draft(
    payload: AnalystNoteDraftRequest, db_path: str = Depends(get_db_path)
) -> AnalystNoteDraftResponse:
    """Upsert analyst draft notes for a player.

    Args:
        payload: Draft note payload.
        db_path: DuckDB path injected via dependency.

    Returns:
        Persisted draft note response.
    """
    updated_at = datetime.utcnow().isoformat()
    execute(
        "DELETE FROM rg_analyst_notes_draft WHERE player_id = ?",
        (payload.player_id,),
        db_path=db_path,
    )
    execute(
        """
        INSERT INTO rg_analyst_notes_draft (
            player_id,
            analyst_id,
            draft_notes,
            draft_action,
            updated_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload.player_id,
            payload.analyst_id,
            payload.draft_notes,
            payload.draft_action,
            updated_at,
        ),
        db_path=db_path,
    )
    return AnalystNoteDraftResponse(
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        draft_notes=payload.draft_notes,
        draft_action=payload.draft_action,
        updated_at=updated_at,
    )


@router.get("/notes/{player_id}", response_model=AnalystNoteResponse)
async def get_latest_notes(
    player_id: str, db_path: str = Depends(get_db_path)
) -> AnalystNoteResponse:
    """Fetch latest analyst notes for a player.

    Args:
        player_id: Player identifier.
        db_path: DuckDB path injected via dependency.

    Returns:
        Latest analyst note response.

    Raises:
        HTTPException: If no notes exist for player.
    """
    rows = query_rows(
        """
        SELECT player_id, analyst_id, analyst_action, analyst_notes, created_at
        FROM rg_analyst_notes_log
        WHERE player_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (player_id,),
        db_path=db_path,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No analyst notes found")

    row = rows[0]
    return AnalystNoteResponse(
        player_id=row["player_id"],
        analyst_id=row["analyst_id"],
        analyst_action=row["analyst_action"],
        analyst_notes=row["analyst_notes"],
        created_at=str(row["created_at"]),
    )


@router.get("/notes-draft/{player_id}", response_model=AnalystNoteDraftResponse)
async def get_latest_notes_draft(
    player_id: str, db_path: str = Depends(get_db_path)
) -> AnalystNoteDraftResponse:
    """Fetch latest analyst draft notes for a player.

    Args:
        player_id: Player identifier.
        db_path: DuckDB path injected via dependency.

    Returns:
        Latest draft note response.

    Raises:
        HTTPException: If no draft exists for player.
    """
    rows = query_rows(
        """
        SELECT player_id, analyst_id, draft_notes, draft_action, updated_at
        FROM rg_analyst_notes_draft
        WHERE player_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (player_id,),
        db_path=db_path,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No draft notes found")

    row = rows[0]
    return AnalystNoteDraftResponse(
        player_id=row["player_id"],
        analyst_id=row["analyst_id"],
        draft_notes=row["draft_notes"] or "",
        draft_action=row.get("draft_action") or "",
        updated_at=str(row["updated_at"]),
    )


@router.post("/nudge", response_model=NudgeLogResponse)
async def submit_nudge(
    payload: NudgeLogRequest, db_path: str = Depends(get_db_path)
) -> NudgeLogResponse:
    """Store analyst-edited nudge and validation results."""
    created_at = datetime.utcnow().isoformat()
    log_id = str(uuid4())
    execute(
        """
        INSERT INTO rg_nudge_log (
            log_id,
            player_id,
            analyst_id,
            draft_nudge,
            final_nudge,
            validation_status,
            validation_violations,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            payload.player_id,
            payload.analyst_id,
            payload.draft_nudge,
            payload.final_nudge,
            payload.validation_status,
            json.dumps(payload.validation_violations),
            created_at,
        ),
        db_path=db_path,
    )

    return NudgeLogResponse(
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        draft_nudge=payload.draft_nudge,
        final_nudge=payload.final_nudge,
        validation_status=payload.validation_status,
        validation_violations=payload.validation_violations,
        created_at=created_at,
    )


@router.get("/nudge/{player_id}", response_model=NudgeLogResponse)
async def get_latest_nudge(
    player_id: str, db_path: str = Depends(get_db_path)
) -> NudgeLogResponse:
    """Fetch latest analyst nudge for a player."""
    rows = query_rows(
        """
        SELECT player_id, analyst_id, draft_nudge, final_nudge, validation_status, validation_violations, created_at
        FROM rg_nudge_log
        WHERE player_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (player_id,),
        db_path=db_path,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No nudge found")

    row = rows[0]
    violations = []
    if row.get("validation_violations"):
        try:
            violations = json.loads(row["validation_violations"])
        except json.JSONDecodeError:
            violations = []

    return NudgeLogResponse(
        player_id=row["player_id"],
        analyst_id=row["analyst_id"],
        draft_nudge=row["draft_nudge"],
        final_nudge=row["final_nudge"],
        validation_status=row["validation_status"],
        validation_violations=violations,
        created_at=str(row["created_at"]),
    )
