"""SQL execution endpoints for read-only analyst queries."""

from __future__ import annotations

import re
import time
import json
from difflib import get_close_matches
from functools import lru_cache
from datetime import datetime
from uuid import uuid4

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from ai_services.snowflake_sql import validate_snowflake_sql
from backend.db.duckdb_client import execute, get_connection, get_db_path, query_rows
from backend.models.queries import SqlExecuteRequest, SqlExecuteResponse
from backend.utils.pii import find_pii_column

router = APIRouter()

_DISALLOWED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|MERGE|TRUNCATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

_SCHEMA_CANDIDATES = ("PROD", "staging_prod", "STAGING_PROD", "staging_staging", "STAGING_STAGING")
_ALLOWED_TABLES = (
    "stg_bet_logs",
    "stg_player_profiles",
    "stg_gamalyze_scores",
    "rg_risk_scores",
    "rg_intervention_queue",
)
_COLUMN_ERROR = re.compile(r'Referenced column \"(?P<column>[^\"]+)\" not found', re.IGNORECASE)
_CANDIDATE_BINDINGS = re.compile(r"Candidate bindings: (?P<candidates>.+)", re.IGNORECASE)
_DATEADD_PATTERN = re.compile(
    r"DATEADD\s*\(\s*(?P<unit>'?\w+'?)\s*,\s*(?P<value>[^,]+)\s*,\s*(?P<expr>[^\)]+)\)",
    re.IGNORECASE,
)
_DATEDIFF_PATTERN = re.compile(
    r"DATEDIFF\s*\(\s*(?P<unit>'?\w+'?)\s*,\s*(?P<start>[^,]+)\s*,\s*(?P<end>[^\)]+)\)",
    re.IGNORECASE,
)
_DATETRUNC_PATTERN = re.compile(
    r"DATE_TRUNC\s*\(\s*(?P<unit>'?\w+'?)\s*,\s*(?P<expr>[^\)]+)\)",
    re.IGNORECASE,
)


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


def _rewrite_schema(sql_text: str, db_path: str) -> str:
    staging_schema = _resolve_schema("stg_bet_logs", db_path)
    prod_schema = _resolve_schema("rg_risk_scores", db_path)
    rewritten = re.sub(r"\bSTAGING\.", f"{staging_schema}.", sql_text, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bPROD\.", f"{prod_schema}.", rewritten, flags=re.IGNORECASE)
    return rewritten


def _rewrite_snowflake_functions(sql_text: str) -> str:
    normalized = re.sub(
        r"CURRENT_TIMESTAMP\s*\(\s*\)",
        "CURRENT_TIMESTAMP",
        sql_text,
        flags=re.IGNORECASE,
    )

    def _dateadd(match: re.Match) -> str:
        unit = match.group("unit").strip().strip("'\"").lower()
        value = match.group("value").strip()
        expr = match.group("expr").strip()
        return f"date_add({expr}, INTERVAL '{value} {unit}')"

    def _datediff(match: re.Match) -> str:
        unit = match.group("unit").strip().strip("'\"").lower()
        start = match.group("start").strip()
        end = match.group("end").strip()
        return f"datediff('{unit}', {start}, {end})"

    def _datetrunc(match: re.Match) -> str:
        unit = match.group("unit").strip().strip("'\"").lower()
        expr = match.group("expr").strip()
        return f"date_trunc('{unit}', {expr})"

    rewritten = _DATEADD_PATTERN.sub(_dateadd, normalized)
    rewritten = _DATEDIFF_PATTERN.sub(_datediff, rewritten)
    rewritten = _DATETRUNC_PATTERN.sub(_datetrunc, rewritten)
    rewritten = re.sub(
        r"\bCURRENT_TIMESTAMP\b",
        "CAST(CURRENT_TIMESTAMP AS TIMESTAMP)",
        rewritten,
        flags=re.IGNORECASE,
    )
    return rewritten


def _normalize_sql(sql_text: str) -> str:
    return sql_text.strip().rstrip(";")


def _ensure_select_only(sql_text: str) -> None:
    normalized = _normalize_sql(sql_text)
    if not normalized:
        raise HTTPException(status_code=400, detail="SQL is empty.")
    if _DISALLOWED.search(normalized):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
    head = normalized.lstrip().upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")


def _reject_pii(sql_text: str) -> None:
    column = find_pii_column(sql_text)
    if column:
        raise HTTPException(
            status_code=400,
            detail=(
                f"PII column '{column}' is not allowed in analyst queries. "
                "Use player_id and non-PII fields only."
            ),
        )


def _apply_limit(sql_text: str, limit: int = 200) -> str:
    normalized = _normalize_sql(sql_text)
    return f"SELECT * FROM ({normalized}) AS query_result LIMIT {limit}"


def _default_summary(row_count: int, duration_ms: int, columns: list[str]) -> str:
    columns_preview = ", ".join(columns[:6])
    suffix = "..." if len(columns) > 6 else ""
    return (
        f"Query returned {row_count} rows in {duration_ms}ms. "
        f"Columns: {columns_preview}{suffix}. Notable patterns: ____."
    )


@lru_cache(maxsize=8)
def _column_catalog(db_path: str) -> set[str]:
    rows = query_rows(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE LOWER(table_name) IN ({placeholders})
        """.format(placeholders=",".join(["?"] * len(_ALLOWED_TABLES))),
        tuple(_ALLOWED_TABLES),
        db_path=db_path,
    )
    return {row["column_name"] for row in rows}


def _format_column_error(message: str, db_path: str) -> str | None:
    match = _COLUMN_ERROR.search(message)
    if not match:
        return None
    missing = match.group("column")
    candidates_match = _CANDIDATE_BINDINGS.search(message)
    candidates = candidates_match.group("candidates") if candidates_match else ""
    all_columns = sorted(_column_catalog(db_path))
    suggestions = get_close_matches(missing, all_columns, n=3, cutoff=0.6)
    detail = f"Unknown column '{missing}'."
    if candidates:
        detail += f" Candidate bindings: {candidates}."
    if suggestions:
        detail += f" Did you mean: {', '.join(suggestions)}?"
    detail += (
        " Use columns from STAGING.STG_BET_LOGS, STAGING.STG_PLAYER_PROFILES, "
        "STAGING.STG_GAMALYZE_SCORES, PROD.RG_RISK_SCORES, or PROD.RG_INTERVENTION_QUEUE."
    )
    return detail


@router.post("/sql/execute", response_model=SqlExecuteResponse)
async def execute_sql(
    payload: SqlExecuteRequest, db_path: str = Depends(get_db_path)
) -> SqlExecuteResponse:
    """Execute read-only SQL with guardrails and optional logging."""
    _ensure_select_only(payload.sql_text)
    _reject_pii(payload.sql_text)
    violations = validate_snowflake_sql(payload.sql_text)
    if violations:
        raise HTTPException(status_code=400, detail="; ".join(violations))

    rewritten_sql = _rewrite_schema(payload.sql_text, db_path)
    rewritten_sql = _rewrite_snowflake_functions(rewritten_sql)
    executed_sql = _apply_limit(rewritten_sql)
    start = time.perf_counter()
    try:
        with get_connection(db_path) as conn:
            result = conn.execute(executed_sql)
            columns = [col[0] for col in result.description]
            rows = [list(row) for row in result.fetchall()]
    except duckdb.BinderException as exc:
        detail = _format_column_error(str(exc), db_path)
        if detail:
            raise HTTPException(status_code=400, detail=detail) from exc
        raise
    duration_ms = int((time.perf_counter() - start) * 1000)
    row_count = len(rows)
    result_summary = payload.result_summary or _default_summary(row_count, duration_ms, columns)

    if payload.log:
        created_at = datetime.utcnow().isoformat()
        log_id = str(uuid4())
        analyst_id = payload.analyst_id or "Colby Reichenbach"
        prompt_text = payload.prompt_text or payload.purpose
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
                analyst_id,
                prompt_text,
                payload.sql_text,
                payload.sql_text,
                payload.purpose,
                result_summary,
                json.dumps(columns),
                json.dumps(rows[:10]),
                row_count,
                duration_ms,
                created_at,
            ),
            db_path=db_path,
        )

    return SqlExecuteResponse(
        columns=columns,
        rows=rows,
        row_count=row_count,
        duration_ms=duration_ms,
        result_summary=result_summary,
    )
