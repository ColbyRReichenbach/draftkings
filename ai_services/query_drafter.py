"""Prompt builder for LLM-assisted SQL drafting."""

from __future__ import annotations

SCHEMA_HINTS = """
Available tables (DuckDB dev):

STAGING.STG_BET_LOGS
- bet_id, player_id, bet_timestamp, bet_amount, sport_category, market_type,
  outcome, payout_amount, market_tier, state_jurisdiction, bet_sequence_num

STAGING.STG_PLAYER_PROFILES
- player_id, account_created_date, state_jurisdiction, age, self_excluded,
  self_exclusion_history, account_status, updated_at

STAGING.STG_GAMALYZE_SCORES
- assessment_id, player_id, assessment_date, sensitivity_to_reward,
  sensitivity_to_loss, risk_tolerance, decision_consistency, overall_risk_rating

PROD.RG_RISK_SCORES
- player_id, composite_risk_score, risk_category, score_calculated_at,
  loss_chase_score, bet_escalation_score, market_drift_score,
  temporal_risk_score, gamalyze_risk_score
"""


def build_query_draft_prompt(player_id: str, analyst_prompt: str) -> str:
    """Build the SQL draft prompt with schema hints."""
    return f"""You are a responsible gaming analytics assistant.

Task: Draft a SINGLE read-only SQL query (SELECT only) in DuckDB dialect.

Player ID: {player_id}
Analyst request: {analyst_prompt}

Schema hints:
{SCHEMA_HINTS}

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
"""
