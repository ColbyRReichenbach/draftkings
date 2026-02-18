"""Case file endpoints (query logs and timeline)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4
import json

from fastapi import APIRouter, Depends, HTTPException

from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.case_status import CaseStatusEntry, CaseStatusRequest
from backend.models.queries import (
    CaseTimelineEntry,
    QueryLogEntry,
    QueryLogRequest,
    TriggerCheckResult,
)
from backend.utils.pii import find_pii_column, redact_text
from backend.utils.supabase_client import insert_audit

router = APIRouter()

STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_SUBMITTED = "SUBMITTED"
_SCHEMA_CANDIDATES = ("PROD", "staging_prod", "STAGING_PROD", "staging_staging", "STAGING_STAGING")


@router.post("/query-log", response_model=QueryLogEntry)
async def create_query_log(
    payload: QueryLogRequest, db_path: str = Depends(get_db_path)
) -> QueryLogEntry:
    """Store an analyst-approved SQL query log entry."""
    pii_column = find_pii_column(payload.final_sql or "")
    if pii_column:
        raise HTTPException(
            status_code=400,
            detail=(
                f"PII column '{pii_column}' is not allowed in analyst queries. "
                "Use player_id and non-PII fields only."
            ),
        )
    created_at = datetime.utcnow().isoformat()
    log_id = str(uuid4())
    safe_prompt = redact_text(payload.prompt_text)

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
            result_columns,
            result_rows,
            row_count,
            duration_ms,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            payload.player_id,
            payload.analyst_id,
            safe_prompt,
            payload.draft_sql,
            payload.final_sql,
            payload.purpose,
            payload.result_summary,
            json.dumps(payload.result_columns) if payload.result_columns else None,
            json.dumps(payload.result_rows) if payload.result_rows else None,
            payload.row_count,
            payload.duration_ms,
            created_at,
        ),
        db_path=db_path,
    )

    return QueryLogEntry(
        player_id=payload.player_id,
        analyst_id=payload.analyst_id,
        prompt_text=safe_prompt,
        draft_sql=payload.draft_sql,
        final_sql=payload.final_sql,
        purpose=payload.purpose,
        result_summary=payload.result_summary,
        result_columns=payload.result_columns,
        result_rows=payload.result_rows,
        row_count=payload.row_count,
        duration_ms=payload.duration_ms,
        created_at=created_at,
    )


@router.get("/query-log/{player_id}", response_model=list[QueryLogEntry])
async def get_query_logs(
    player_id: str, db_path: str = Depends(get_db_path)
) -> list[QueryLogEntry]:
    """Return query log entries for a player."""
    rows = query_rows(
        """
        SELECT player_id, analyst_id, prompt_text, draft_sql, final_sql, purpose, result_summary,
               result_columns, result_rows, row_count, duration_ms, created_at
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
            result_columns=json.loads(row["result_columns"]) if row["result_columns"] else None,
            result_rows=json.loads(row["result_rows"]) if row["result_rows"] else None,
            row_count=row["row_count"],
            duration_ms=row["duration_ms"],
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


def _resolve_schema(table_name: str, db_path: str) -> str:
    rows = query_rows(
        """
        SELECT table_schema
        FROM information_schema.tables
        WHERE LOWER(table_name) = LOWER(?)
        """,
        (table_name,),
        db_path=db_path,
    )
    available = {row["table_schema"] for row in rows}
    for candidate in _SCHEMA_CANDIDATES:
        if candidate in available:
            return candidate
    return rows[0]["table_schema"] if rows else "PROD"


def _log_trigger_query(
    *,
    player_id: str,
    analyst_id: str,
    sql_text: str,
    purpose: str,
    result_summary: str,
    db_path: str,
) -> str:
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
            result_columns,
            result_rows,
            row_count,
            duration_ms,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            player_id,
            analyst_id,
            purpose,
            sql_text,
            sql_text,
            purpose,
            result_summary,
            None,
            None,
            None,
            None,
            created_at,
        ),
        db_path=db_path,
    )
    return created_at


def _get_state_for_player(player_id: str, db_path: str) -> str | None:
    staging_schema = _resolve_schema("stg_player_profiles", db_path)
    rows = query_rows(
        f"""
        SELECT state_jurisdiction
        FROM {staging_schema}.STG_PLAYER_PROFILES
        WHERE player_id = ?
        """,
        (player_id,),
        db_path=db_path,
    )
    return rows[0]["state_jurisdiction"] if rows else None


@router.post("/trigger-check/{player_id}", response_model=list[TriggerCheckResult])
async def trigger_check(
    player_id: str, force: bool = False, db_path: str = Depends(get_db_path)
) -> list[TriggerCheckResult]:
    """Run state-specific trigger checks and log results."""
    cached = query_rows(
        """
        SELECT state, triggered, reason, sql_text, row_count, created_at
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY state
                    ORDER BY created_at DESC
                ) AS rn
            FROM rg_trigger_check_log
            WHERE player_id = ?
        ) latest
        WHERE rn = 1
        ORDER BY created_at DESC
        """,
        (player_id,),
        db_path=db_path,
    )
    if cached and not force:
        return [
            TriggerCheckResult(
                state=row["state"],
                triggered=bool(row["triggered"]),
                reason=row["reason"],
                sql_text=row["sql_text"],
                row_count=int(row["row_count"]),
                created_at=str(row["created_at"]),
            )
            for row in cached
        ]

    state = _get_state_for_player(player_id, db_path)
    analyst_id = "Colby Reichenbach"
    results: list[TriggerCheckResult] = []

    if state == "MA":
        staging_schema = _resolve_schema("stg_bet_logs", db_path)
        sql_text = f"""
        WITH avg_90 AS (
            SELECT AVG(bet_amount) AS avg_bet
            FROM {staging_schema}.STG_BET_LOGS
            WHERE player_id = ?
              AND bet_timestamp >= CAST(CURRENT_TIMESTAMP AS TIMESTAMP) - INTERVAL '90 days'
        ),
        recent_max AS (
            SELECT MAX(bet_amount) AS max_bet
            FROM {staging_schema}.STG_BET_LOGS
            WHERE player_id = ?
              AND bet_timestamp >= CAST(CURRENT_TIMESTAMP AS TIMESTAMP) - INTERVAL '30 days'
        )
        SELECT
            avg_90.avg_bet,
            recent_max.max_bet
        FROM avg_90
        CROSS JOIN recent_max
        """
        rows = query_rows(sql_text, (player_id, player_id), db_path=db_path)
        avg_bet = float(rows[0]["avg_bet"]) if rows and rows[0]["avg_bet"] is not None else 0.0
        max_bet = float(rows[0]["max_bet"]) if rows and rows[0]["max_bet"] is not None else 0.0
        triggered = avg_bet > 0 and max_bet > avg_bet * 10
        reason = (
            f"Max bet ${max_bet:,.2f} vs 90d avg ${avg_bet:,.2f}."
            if avg_bet > 0
            else "No 90-day betting history available."
        )
        summary = f"MA abnormal play check: {'TRIGGERED' if triggered else 'Not triggered'}. {reason}"
        created_at = _log_trigger_query(
            player_id=player_id,
            analyst_id=analyst_id,
            sql_text=sql_text.strip(),
            purpose="Regulatory Trigger Check - MA",
            result_summary=summary,
            db_path=db_path,
        )
        execute(
            """
            INSERT INTO rg_trigger_check_log (
                player_id,
                state,
                triggered,
                reason,
                sql_text,
                row_count,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (player_id, "MA", triggered, reason, sql_text.strip(), 1, created_at),
            db_path=db_path,
        )
        results.append(
            TriggerCheckResult(
                state="MA",
                triggered=triggered,
                reason=reason,
                sql_text=sql_text.strip(),
                row_count=1,
                created_at=created_at,
            )
        )

    if state == "NJ":
        risk_schema = _resolve_schema("rg_risk_scores", db_path)
        sql_text = f"""
        SELECT COUNT(*) AS flag_count
        FROM {risk_schema}.RG_RISK_SCORES
        WHERE player_id = ?
          AND risk_category IN ('HIGH', 'CRITICAL')
          AND CAST(calculated_at AS TIMESTAMP) >= CAST(CURRENT_TIMESTAMP AS TIMESTAMP) - INTERVAL '30 days'
        """
        rows = query_rows(sql_text, (player_id,), db_path=db_path)
        flag_count = int(rows[0]["flag_count"]) if rows else 0
        triggered = flag_count >= 3
        reason = f"{flag_count} high/critical flags in last 30 days."
        summary = f"NJ multi-flag check: {'TRIGGERED' if triggered else 'Not triggered'}. {reason}"
        created_at = _log_trigger_query(
            player_id=player_id,
            analyst_id=analyst_id,
            sql_text=sql_text.strip(),
            purpose="Regulatory Trigger Check - NJ",
            result_summary=summary,
            db_path=db_path,
        )
        execute(
            """
            INSERT INTO rg_trigger_check_log (
                player_id,
                state,
                triggered,
                reason,
                sql_text,
                row_count,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (player_id, "NJ", triggered, reason, sql_text.strip(), 1, created_at),
            db_path=db_path,
        )
        results.append(
            TriggerCheckResult(
                state="NJ",
                triggered=triggered,
                reason=reason,
                sql_text=sql_text.strip(),
                row_count=1,
                created_at=created_at,
            )
        )

    if state == "PA":
        sql_text = "SELECT 0 AS self_exclusion_reversals"
        rows = query_rows(sql_text, db_path=db_path)
        reversals = int(rows[0]["self_exclusion_reversals"]) if rows else 0
        triggered = reversals >= 3
        reason = (
            "Self-exclusion history not available in dataset."
            if reversals == 0
            else f"{reversals} reversals detected in 6 months."
        )
        summary = f"PA referral check: {'TRIGGERED' if triggered else 'Not triggered'}. {reason}"
        created_at = _log_trigger_query(
            player_id=player_id,
            analyst_id=analyst_id,
            sql_text=sql_text.strip(),
            purpose="Regulatory Trigger Check - PA",
            result_summary=summary,
            db_path=db_path,
        )
        execute(
            """
            INSERT INTO rg_trigger_check_log (
                player_id,
                state,
                triggered,
                reason,
                sql_text,
                row_count,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (player_id, "PA", triggered, reason, sql_text.strip(), 1, created_at),
            db_path=db_path,
        )
        results.append(
            TriggerCheckResult(
                state="PA",
                triggered=triggered,
                reason=reason,
                sql_text=sql_text.strip(),
                row_count=1,
                created_at=created_at,
            )
        )

    return results


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
    execute(
        """
        UPDATE rg_queue_cases
        SET status = 'REMOVED'
        WHERE case_id = ?
        """,
        (payload.case_id,),
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
    execute(
        """
        UPDATE rg_queue_cases
        SET status = 'REMOVED'
        WHERE case_id = ?
        """,
        (payload.case_id,),
        db_path=db_path,
    )

    started_row = query_rows(
        "SELECT started_at FROM rg_case_status_log WHERE case_id = ?",
        (payload.case_id,),
        db_path=db_path,
    )
    started_at = started_row[0]["started_at"] if started_row else None

    # Persist audit trail to Supabase (best-effort; non-blocking)
    try:
        audit_entry = {
            "audit_id": f"AUD-{payload.case_id}-{now}",
            "case_id": payload.case_id,
            "player_id": payload.player_id,
            "analyst_id": payload.analyst_id,
            "action": STATUS_SUBMITTED,
            "notes": None,
            "created_at": now,
        }
        insert_audit(audit_entry)
    except Exception:
        # insert_audit logs internally; do not block response on failure
        pass

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
