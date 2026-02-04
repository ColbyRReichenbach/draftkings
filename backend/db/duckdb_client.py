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
                created_at TIMESTAMP
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
