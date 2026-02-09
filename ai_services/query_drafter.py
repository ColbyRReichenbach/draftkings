"""Prompt builder for LLM-assisted SQL drafting."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable

from backend.db.duckdb_client import query_rows

SCHEMA_HINTS = """
Available tables (DuckDB dev; Snowflake-compatible names):

STAGING.STG_BET_LOGS
- bet_id, player_id, bet_timestamp, sport_category, market_type, bet_amount,
  odds_american, outcome

STAGING.STG_PLAYER_PROFILES
- player_id, first_name, last_name, email, age, state_jurisdiction, risk_cohort

STAGING.STG_GAMALYZE_SCORES
- assessment_id, player_id, assessment_date, sensitivity_to_reward,
  sensitivity_to_loss, risk_tolerance, decision_consistency,
  overall_risk_rating, loaded_at, gamalyze_version

PROD.RG_RISK_SCORES
- player_id, composite_risk_score, risk_category, calculated_at,
  loss_chase_score, bet_escalation_score, market_drift_score,
  temporal_risk_score, gamalyze_risk_score

PROD.RG_INTERVENTION_QUEUE
- player_id, composite_risk_score, risk_category, primary_driver,
  loss_chase_score, bet_escalation_score, market_drift_score,
  temporal_risk_score, gamalyze_risk_score, calculated_at
"""

_TABLE_ALIASES = [
    ("STAGING.STG_BET_LOGS", "stg_bet_logs"),
    ("STAGING.STG_PLAYER_PROFILES", "stg_player_profiles"),
    ("STAGING.STG_GAMALYZE_SCORES", "stg_gamalyze_scores"),
    ("PROD.RG_RISK_SCORES", "rg_risk_scores"),
    ("PROD.RG_INTERVENTION_QUEUE", "rg_intervention_queue"),
]

_PII_FIELDS = ("first_name", "last_name", "email")

_STAGING_SCHEMA_PREFERENCE = (
    "staging_staging",
    "staging",
    "staging_prod",
    "staging_test_results",
)

_PROD_SCHEMA_PREFERENCE = (
    "prod",
    "staging_prod",
    "staging",
)


def _pick_schema(table_name: str, schema_names: Iterable[str]) -> str:
    preferences = (
        _STAGING_SCHEMA_PREFERENCE
        if table_name.startswith("stg_")
        else _PROD_SCHEMA_PREFERENCE
    )
    for candidate in preferences:
        for schema in schema_names:
            if schema.lower() == candidate.lower():
                return schema
    return next(iter(schema_names))


@lru_cache(maxsize=8)
def _build_live_schema_snapshot(db_path: str) -> str:
    tables = {alias: name for alias, name in _TABLE_ALIASES}
    try:
        rows = query_rows(
            """
            SELECT table_schema, table_name, column_name, ordinal_position
            FROM information_schema.columns
            WHERE LOWER(table_name) IN ({placeholders})
            ORDER BY table_schema, table_name, ordinal_position
            """.format(placeholders=",".join(["?"] * len(tables))),
            tuple(name for name in tables.values()),
            db_path=db_path,
        )
    except Exception:
        return ""
    if not rows:
        return ""

    grouped: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        table_name = row["table_name"].lower()
        table_alias = next(
            (alias for alias, name in _TABLE_ALIASES if name == table_name),
            table_name,
        )
        grouped.setdefault(table_alias, {}).setdefault(row["table_schema"], []).append(
            row["column_name"]
        )

    lines: list[str] = ["Live DuckDB schema snapshot (authoritative):"]
    for alias, table_name in _TABLE_ALIASES:
        schema_map = grouped.get(alias)
        if not schema_map:
            continue
        chosen_schema = _pick_schema(table_name, schema_map.keys())
        columns = schema_map[chosen_schema]
        columns_display = ", ".join(columns)
        lines.append(f"\n{alias} (physical: {chosen_schema}.{table_name})")
        lines.append(f"- {columns_display}")

    lines.append(
        "\nOnly use columns listed above. If a field is missing, it is not available "
        "in the dev DuckDB schema."
    )
    lines.append(
        "Join STAGING.STG_PLAYER_PROFILES for state_jurisdiction and demographics. "
        "Do NOT select PII fields (first_name, last_name, email)."
    )
    return "\n".join(lines)


def _load_data_dictionary() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "claude" / "context" / "data_dictionary.md"
    try:
        content = data_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    lines = content.splitlines()
    trimmed = "\n".join(lines[:160])
    return trimmed.strip()


def build_query_draft_prompt(
    player_id: str, analyst_prompt: str, db_path: str | None = None
) -> str:
    """Build the SQL draft prompt with schema hints."""
    data_dictionary = _load_data_dictionary()
    live_schema = _build_live_schema_snapshot(db_path) if db_path else ""
    schema_context = f"\n{live_schema}\n" if live_schema else ""
    if not live_schema and data_dictionary:
        schema_context += f"\nData Dictionary (excerpt):\n{data_dictionary}\n"
    return f"""You are a responsible gaming analytics assistant.

Task: Draft a SINGLE read-only SQL query (SELECT only) in Snowflake dialect.

Player ID: {player_id}
Analyst request: {analyst_prompt}

Schema hints (Snowflake-style aliases shown; live DuckDB schema used for execution):
{schema_context or SCHEMA_HINTS}

Return JSON only with fields:
{{
  "draft_sql": "SELECT ...",
  "assumptions": ["Assumption 1", "Assumption 2"]
}}

Rules:
- SELECT statements only (no INSERT/UPDATE/DELETE/DDL)
- Use explicit column names (no SELECT *)
- Filter on player_id when relevant
- Prefer LIMIT when analyst requests a sample size
- Use STAGING schema for staging tables (e.g., STAGING.STG_BET_LOGS)
- Use PROD schema for risk marts (e.g., PROD.RG_RISK_SCORES)
- Snowflake-only syntax (DATEADD, DATEDIFF, DATE_TRUNC, ILIKE, QUALIFY)
- Avoid INTERVAL, :: casts, DATE_SUB, REGEXP_MATCH, IFNULL
- Never select PII fields (first_name, last_name, email)
"""


def build_router_prompt(route: str, analyst_prompt: str, player_id: str) -> str:
    """Build prompt routing responses for non-SQL intents."""
    return f"""You are a responsible gaming analyst assistant.

Route: {route}
Player ID: {player_id}
Analyst prompt: {analyst_prompt}

Respond in 3-6 sentences. Be transparent about any limitations:
- If regulatory context is requested, note that production would use an internal compliance knowledge base.
- If external context is requested, state that live web access is not enabled in dev.
- Keep tone professional and supportive.
"""
