"""Case file endpoints (query logs and timeline)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends

from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.case_status import CaseStatusEntry, CaseStatusRequest
from backend.models.queries import CaseTimelineEntry, QueryLogEntry, QueryLogRequest

router = APIRouter()

STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_SUBMITTED = "SUBMITTED"


@router.post("/query-log", response_model=QueryLogEntry)
async def create_query_log(
    payload: QueryLogRequest, db_path: str = Depends(get_db_path)
) -> QueryLogEntry:
    """Store an analyst-approved SQL query log entry."""
    created_at = datetime.utcnow().isoformat()
    log_id = str(uuid4())

    execute(
        """
        INSERT INTO rg_query_log (
            log_id,
            player_id,
            analyst_id,
            prompt_text,
            draft_sql,
            final_sql,
            purpose,
            result_summary,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            payload.player_id,
            payload.analyst_id,
            payload.prompt_text,
            payload.draft_sql,
            payload.final_sql,
            payload.purpose,
            payload.result_summary,
            created_at,
        ),
        db_path=db_path,
    )

    return QueryLogEntry(
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        prompt_text=payload.prompt_text,
        draft_sql=payload.draft_sql,
        final_sql=payload.final_sql,
        purpose=payload.purpose,
        result_summary=payload.result_summary,
        created_at=created_at,
    )


@router.get("/query-log/{player_id}", response_model=list[QueryLogEntry])
async def get_query_logs(
    player_id: str, db_path: str = Depends(get_db_path)
) -> list[QueryLogEntry]:
    """Return query log entries for a player."""
    rows = query_rows(
        """
        SELECT player_id, analyst_id, prompt_text, draft_sql, final_sql, purpose, result_summary, created_at
        FROM rg_query_log
        WHERE player_id = ?
        ORDER BY created_at DESC
        """,
        (player_id,),
        db_path=db_path,
    )

    return [
        QueryLogEntry(
            player_id=row["player_id"],
            analyst_id=row["analyst_id"],
            prompt_text=row["prompt_text"],
            draft_sql=row["draft_sql"],
            final_sql=row["final_sql"],
            purpose=row["purpose"],
            result_summary=row["result_summary"],
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]


@router.get("/timeline/{player_id}", response_model=list[CaseTimelineEntry])
async def get_case_timeline(
    player_id: str, db_path: str = Depends(get_db_path)
) -> list[CaseTimelineEntry]:
    """Return unified case timeline for a player."""
    notes_rows = query_rows(
        """
        SELECT analyst_action, analyst_notes, created_at
        FROM rg_analyst_notes_log
        WHERE player_id = ?
        """,
        (player_id,),
        db_path=db_path,
    )
    ai_rows = query_rows(
        """
        SELECT prompt_text, created_at
        FROM rg_llm_prompt_log
        WHERE player_id = ?
        """,
        (player_id,),
        db_path=db_path,
    )
    query_rows_data = query_rows(
        """
        SELECT purpose, result_summary, created_at
        FROM rg_query_log
        WHERE player_id = ?
        """,
        (player_id,),
        db_path=db_path,
    )

    timeline: list[CaseTimelineEntry] = []
    for row in notes_rows:
        timeline.append(
            CaseTimelineEntry(
                event_type="Analyst note",
                event_detail=f"{row['analyst_action']}: {row['analyst_notes']}",
                created_at=str(row["created_at"]),
            )
        )
    for row in ai_rows:
        timeline.append(
            CaseTimelineEntry(
                event_type="AI draft",
                event_detail=f"Prompt logged: {row['prompt_text']}",
                created_at=str(row["created_at"]),
            )
        )
    for row in query_rows_data:
        timeline.append(
            CaseTimelineEntry(
                event_type="SQL query",
                event_detail=f"{row['purpose']} — {row['result_summary']}",
                created_at=str(row["created_at"]),
            )
        )

    timeline.sort(key=lambda entry: entry.created_at, reverse=True)
    return timeline


@router.post("/start", response_model=CaseStatusEntry)
async def start_case(
    payload: CaseStatusRequest, db_path: str = Depends(get_db_path)
) -> CaseStatusEntry:
    """Mark a case as in progress."""
    now = datetime.utcnow().isoformat()
    execute(
        "DELETE FROM rg_case_status_log WHERE case_id = ?",
        (payload.case_id,),
        db_path=db_path,
    )
    execute(
        """
        INSERT INTO rg_case_status_log (
            case_id,
            player_id,
            analyst_id,
            status,
            started_at,
            submitted_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.case_id,
            payload.player_id,
            payload.analyst_id,
            STATUS_IN_PROGRESS,
            now,
            None,
            now,
        ),
        db_path=db_path,
    )

    return CaseStatusEntry(
        case_id=payload.case_id,
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        status=STATUS_IN_PROGRESS,
        started_at=now,
        submitted_at=None,
        updated_at=now,
    )


@router.post("/submit", response_model=CaseStatusEntry)
async def submit_case(
    payload: CaseStatusRequest, db_path: str = Depends(get_db_path)
) -> CaseStatusEntry:
    """Mark a case as submitted."""
    now = datetime.utcnow().isoformat()
    execute(
        "DELETE FROM rg_case_status_log WHERE case_id = ?",
        (payload.case_id,),
        db_path=db_path,
    )
    execute(
        """
        INSERT INTO rg_case_status_log (
            case_id,
            player_id,
            analyst_id,
            status,
            started_at,
            submitted_at,
            updated_at
        ) VALUES (
            ?,
            ?,
            ?,
            ?,
            COALESCE(
                (SELECT started_at FROM rg_case_status_log WHERE case_id = ?),
                ?
            ),
            ?,
            ?
        )
        """,
        (
            payload.case_id,
            payload.player_id,
            payload.analyst_id,
            STATUS_SUBMITTED,
            payload.case_id,
            now,
            now,
            now,
        ),
        db_path=db_path,
    )

    started_row = query_rows(
        "SELECT started_at FROM rg_case_status_log WHERE case_id = ?",
        (payload.case_id,),
        db_path=db_path,
    )
    started_at = started_row[0]["started_at"] if started_row else None

    return CaseStatusEntry(
        case_id=payload.case_id,
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        status=STATUS_SUBMITTED,
        started_at=str(started_at) if started_at else None,
        submitted_at=now,
        updated_at=now,
    )


@router.get("/status", response_model=list[CaseStatusEntry])
async def list_case_status(db_path: str = Depends(get_db_path)) -> list[CaseStatusEntry]:
    """Return all case statuses."""
    rows = query_rows(
        """
        SELECT case_id, player_id, analyst_id, status, started_at, submitted_at, updated_at
        FROM rg_case_status_log
        """,
        db_path=db_path,
    )
    return [
        CaseStatusEntry(
            case_id=row["case_id"],
            player_id=row["player_id"],
            analyst_id=row["analyst_id"],
            status=row["status"],
            started_at=str(row["started_at"]) if row["started_at"] else None,
            submitted_at=str(row["submitted_at"]) if row["submitted_at"] else None,
            updated_at=str(row["updated_at"]),
        )
        for row in rows
    ]
