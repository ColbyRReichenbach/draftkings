"""HITL intervention endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.hitl import AnalystNoteRequest, AnalystNoteResponse

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
