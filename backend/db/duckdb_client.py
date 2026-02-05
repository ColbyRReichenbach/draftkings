"""DuckDB access layer for backend API."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Tuple

import duckdb


def _resolve_path(db_path: str | None = None) -> str:
    """Resolve the DuckDB path from overrides or environment.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Resolved filesystem path for DuckDB.
    """
    return db_path or os.getenv("DUCKDB_PATH", "data/dk_sentinel.duckdb")


def get_db_path() -> str:
    """Return the configured DuckDB path for dependency injection.

    Returns:
        Resolved filesystem path for DuckDB.
    """
    return _resolve_path()


@contextmanager
def get_connection(db_path: str | None = None) -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield a DuckDB connection and ensure it closes.

    Args:
        db_path: Optional explicit database path.

    Yields:
        DuckDBPyConnection: Active connection instance.
    """
    path = _resolve_path(db_path)
    conn = duckdb.connect(path)
    try:
        yield conn
    finally:
        conn.close()


def ensure_tables(db_path: str | None = None) -> None:
    """Ensure HITL and LLM logging tables exist.

    Args:
        db_path: Optional explicit database path.
    """
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_analyst_notes_log (
                log_id VARCHAR,
                player_id VARCHAR,
                analyst_id VARCHAR,
                analyst_action VARCHAR,
                analyst_notes VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_llm_prompt_log (
                log_id VARCHAR,
                player_id VARCHAR,
                analyst_id VARCHAR,
                prompt_text VARCHAR,
                response_text VARCHAR,
                created_at TIMESTAMP,
                route_type VARCHAR,
                tool_used VARCHAR
            )
            """
        )
        conn.execute(
            "ALTER TABLE rg_llm_prompt_log ADD COLUMN IF NOT EXISTS route_type VARCHAR"
        )
        conn.execute(
            "ALTER TABLE rg_llm_prompt_log ADD COLUMN IF NOT EXISTS tool_used VARCHAR"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_query_log (
                log_id VARCHAR,
                player_id VARCHAR,
                analyst_id VARCHAR,
                prompt_text VARCHAR,
                draft_sql VARCHAR,
                final_sql VARCHAR,
                purpose VARCHAR,
                result_summary VARCHAR,
                result_columns VARCHAR,
                result_rows VARCHAR,
                row_count INTEGER,
                duration_ms INTEGER,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            "ALTER TABLE rg_query_log ADD COLUMN IF NOT EXISTS result_columns VARCHAR"
        )
        conn.execute(
            "ALTER TABLE rg_query_log ADD COLUMN IF NOT EXISTS result_rows VARCHAR"
        )
        conn.execute(
            "ALTER TABLE rg_query_log ADD COLUMN IF NOT EXISTS row_count INTEGER"
        )
        conn.execute(
            "ALTER TABLE rg_query_log ADD COLUMN IF NOT EXISTS duration_ms INTEGER"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_case_status_log (
                case_id VARCHAR,
                player_id VARCHAR,
                analyst_id VARCHAR,
                status VARCHAR,
                started_at TIMESTAMP,
                submitted_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_queue_cases (
                case_id VARCHAR,
                player_id VARCHAR,
                risk_category VARCHAR,
                composite_risk_score DOUBLE,
                assigned_at TIMESTAMP,
                batch_id VARCHAR,
                status VARCHAR
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_trigger_check_log (
                player_id VARCHAR,
                state VARCHAR,
                triggered BOOLEAN,
                reason VARCHAR,
                sql_text VARCHAR,
                row_count INTEGER,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_nudge_log (
                log_id VARCHAR,
                player_id VARCHAR,
                analyst_id VARCHAR,
                draft_nudge VARCHAR,
                final_nudge VARCHAR,
                validation_status VARCHAR,
                validation_violations VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rg_analyst_notes_draft (
                player_id VARCHAR,
                analyst_id VARCHAR,
                draft_notes VARCHAR,
                draft_action VARCHAR,
                updated_at TIMESTAMP
            )
            """
        )


def query_rows(
    sql: str, params: Iterable[Any] | None = None, db_path: str | None = None
) -> List[Dict[str, Any]]:
    """Run a query and return rows as dictionaries.

    Args:
        sql: SQL query to execute.
        params: Optional positional parameters.
        db_path: Optional explicit database path.

    Returns:
        List of result rows as dictionaries.
    """
    with get_connection(db_path) as conn:
        if params:
            result = conn.execute(sql, params)
        else:
            result = conn.execute(sql)
        columns = [col[0] for col in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]


def execute(
    sql: str, params: Tuple[Any, ...] | None = None, db_path: str | None = None
) -> None:
    """Execute a statement without returning rows.

    Args:
        sql: SQL statement to execute.
        params: Optional positional parameters.
        db_path: Optional explicit database path.
    """
    with get_connection(db_path) as conn:
        if params:
            conn.execute(sql, params)
        else:
            conn.execute(sql)
