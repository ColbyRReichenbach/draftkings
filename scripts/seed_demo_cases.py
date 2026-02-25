"""Seed deterministic demo case workflow data into runtime DuckDB tables.

This script does not generate model tables. It expects dbt-transformed tables to exist
(e.g., staging_prod.rg_risk_scores and staging_staging.stg_player_profiles), then seeds
runtime workflow tables for demo UX:
- rg_queue_cases
- rg_case_status_log
- rg_query_log
- rg_llm_prompt_log
- rg_nudge_log
- rg_analyst_notes_log
- rg_analyst_notes_draft
- rg_trigger_check_log

Usage:
  python3 scripts/seed_demo_cases.py --completed 20 --in-progress 2
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import duckdb


@dataclass
class CaseCandidate:
    player_id: str
    risk_category: str
    composite_risk_score: float
    state_jurisdiction: str
    loss_chase_score: float
    bet_escalation_score: float
    market_drift_score: float
    temporal_risk_score: float
    gamalyze_risk_score: float
    primary_driver: str


@dataclass
class BehaviorMetrics:
    bets_7d: int
    wager_7d: float
    bets_30d: int
    wager_30d: float
    bets_90d: int
    wager_90d: float
    avg_bet_30d: float
    avg_bet_90d: float
    max_bet_30d: float
    recent_night_ratio_30d: float
    baseline_night_ratio_90d: float
    after_loss_ratio_90d: float


@dataclass
class GamalyzeMetrics:
    sensitivity_to_loss: float
    sensitivity_to_reward: float
    risk_tolerance: float
    decision_consistency: float


@dataclass
class CasePlan:
    case: CaseCandidate
    status: str
    assigned_at: datetime
    started_at: datetime
    submitted_at: datetime | None
    updated_at: datetime
    trigger_at: datetime
    query_times: list[datetime]
    ai_prompt_at: datetime
    nudge_at: datetime | None
    note_at: datetime


def _connect(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path)


def _ensure_runtime_tables(conn: duckdb.DuckDBPyConnection) -> None:
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


def _clear_runtime_tables(conn: duckdb.DuckDBPyConnection) -> None:
    for table in (
        "rg_queue_cases",
        "rg_case_status_log",
        "rg_query_log",
        "rg_llm_prompt_log",
        "rg_trigger_check_log",
        "rg_nudge_log",
        "rg_analyst_notes_log",
        "rg_analyst_notes_draft",
    ):
        conn.execute(f"DELETE FROM {table}")


def _load_candidates(conn: duckdb.DuckDBPyConnection) -> list[CaseCandidate]:
    rows = conn.execute(
        """
        WITH queue AS (
            SELECT player_id, primary_driver
            FROM staging_prod.rg_intervention_queue
        )
        SELECT
            r.player_id,
            r.risk_category,
            r.composite_risk_score,
            p.state_jurisdiction,
            r.loss_chase_score,
            r.bet_escalation_score,
            r.market_drift_score,
            r.temporal_risk_score,
            r.gamalyze_risk_score,
            COALESCE(q.primary_driver, 'LOSS_CHASE') AS primary_driver
        FROM staging_prod.rg_risk_scores r
        JOIN staging_staging.stg_player_profiles p
          ON r.player_id = p.player_id
        LEFT JOIN queue q
          ON q.player_id = r.player_id
        WHERE r.risk_category IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
        ORDER BY
          CASE r.risk_category
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4
          END,
          r.composite_risk_score DESC,
          r.player_id
        """
    ).fetchall()

    return [CaseCandidate(*row) for row in rows]


def _pick_cases(
    candidates: list[CaseCandidate],
    completed: int,
    in_progress: int,
    preferred_player_ids: list[str] | None = None,
) -> tuple[list[CaseCandidate], list[CaseCandidate]]:
    total_needed = completed + in_progress
    quotas = {
        "CRITICAL": min(6, total_needed),
        "HIGH": min(9, max(total_needed - 6, 0)),
        "MEDIUM": max(total_needed - 15, 0),
    }

    by_cat: dict[str, list[CaseCandidate]] = {"CRITICAL": [], "HIGH": [], "MEDIUM": []}
    for candidate in candidates:
        if candidate.risk_category in by_cat:
            by_cat[candidate.risk_category].append(candidate)

    chosen: list[CaseCandidate] = []
    chosen_ids: set[str] = set()
    candidate_by_id = {candidate.player_id: candidate for candidate in candidates}

    if preferred_player_ids:
        for player_id in preferred_player_ids:
            candidate = candidate_by_id.get(player_id)
            if not candidate or candidate.player_id in chosen_ids:
                continue
            chosen.append(candidate)
            chosen_ids.add(candidate.player_id)
            if len(chosen) >= total_needed:
                break

    for category in ("CRITICAL", "HIGH", "MEDIUM"):
        for candidate in by_cat[category]:
            if candidate.player_id in chosen_ids:
                continue
            chosen.append(candidate)
            chosen_ids.add(candidate.player_id)
            if len([c for c in chosen if c.risk_category == category]) >= quotas[category]:
                break
            if len(chosen) >= total_needed:
                break

    if len(chosen) < total_needed:
        used = {c.player_id for c in chosen}
        for candidate in candidates:
            if candidate.player_id in used:
                continue
            chosen.append(candidate)
            if len(chosen) == total_needed:
                break

    if len(chosen) < total_needed:
        raise RuntimeError(
            f"Only found {len(chosen)} eligible cases but need {total_needed}. Run dbt run/test first."
        )

    completed_cases = chosen[:completed]
    in_progress_cases = chosen[completed : completed + in_progress]
    return completed_cases, in_progress_cases


def _load_preferred_player_ids(path: str | None) -> list[str]:
    if not path:
        return []
    file_path = Path(path)
    if not file_path.exists():
        return []
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        ids = payload.get("player_ids", [])
    else:
        ids = payload
    if not isinstance(ids, list):
        return []
    return [str(item).strip() for item in ids if str(item).strip()]


def _player_rng(seed: int, player_id: str) -> random.Random:
    return random.Random(f"{seed}:{player_id}")


def _risk_duration_bounds(risk_category: str) -> tuple[int, int]:
    if risk_category == "CRITICAL":
        return (45, 140)
    if risk_category == "HIGH":
        return (35, 110)
    return (20, 80)


def _build_case_plan(case: CaseCandidate, status: str, idx: int, base_now: datetime, seed: int) -> CasePlan:
    rng = _player_rng(seed, case.player_id)
    days_back = 1 + idx if status == "SUBMITTED" else rng.randint(0, 1)

    start_hour = rng.choice([8, 9, 10, 11, 13, 14, 15, 16, 17])
    start_minute = rng.randint(2, 55)
    started_at = (base_now - timedelta(days=days_back)).replace(
        hour=start_hour,
        minute=start_minute,
        second=rng.randint(4, 57),
        microsecond=0,
    )

    assigned_at = started_at - timedelta(minutes=rng.randint(12, 90))
    min_duration, max_duration = _risk_duration_bounds(case.risk_category)
    total_duration = rng.randint(min_duration, max_duration)

    first_query = started_at + timedelta(minutes=rng.randint(2, 12), seconds=rng.randint(3, 59))
    second_query = first_query + timedelta(minutes=rng.randint(4, 20), seconds=rng.randint(3, 59))

    interruptions = rng.randint(0, 2)
    pause_minutes = sum(rng.randint(6, 22) for _ in range(interruptions))
    third_query = second_query + timedelta(minutes=rng.randint(5, 18) + pause_minutes, seconds=rng.randint(3, 59))

    ai_prompt_at = third_query + timedelta(minutes=rng.randint(3, 18), seconds=rng.randint(3, 59))
    trigger_at = started_at + timedelta(minutes=rng.randint(1, 6), seconds=rng.randint(3, 59))

    if status == "SUBMITTED":
        nudge_at = ai_prompt_at + timedelta(minutes=rng.randint(8, 35), seconds=rng.randint(3, 59))
        note_at = nudge_at + timedelta(minutes=rng.randint(5, 25), seconds=rng.randint(3, 59))
        submitted_at = max(note_at + timedelta(minutes=rng.randint(1, 8)), started_at + timedelta(minutes=total_duration))
        updated_at = submitted_at
    else:
        nudge_at = None
        note_at = ai_prompt_at + timedelta(minutes=rng.randint(8, 18), seconds=rng.randint(3, 59))
        submitted_at = None
        updated_at = max(note_at, started_at + timedelta(minutes=rng.randint(20, 60)))

    timeline_sequence = [trigger_at, first_query, second_query, third_query, ai_prompt_at]
    if nudge_at:
        timeline_sequence.append(nudge_at)
    timeline_sequence.append(note_at)
    for i in range(1, len(timeline_sequence)):
        if timeline_sequence[i] <= timeline_sequence[i - 1]:
            timeline_sequence[i] = timeline_sequence[i - 1] + timedelta(seconds=rng.randint(11, 39))

    trigger_at = timeline_sequence[0]
    query_times = timeline_sequence[1:4]
    ai_prompt_at = timeline_sequence[4]
    if nudge_at:
        nudge_at = timeline_sequence[5]
        note_at = timeline_sequence[6]
    else:
        note_at = timeline_sequence[5]

    return CasePlan(
        case=case,
        status=status,
        assigned_at=assigned_at,
        started_at=started_at,
        submitted_at=submitted_at,
        updated_at=updated_at,
        trigger_at=trigger_at,
        query_times=query_times,
        ai_prompt_at=ai_prompt_at,
        nudge_at=nudge_at,
        note_at=note_at,
    )


def _fetch_behavior_metrics(conn: duckdb.DuckDBPyConnection, player_id: str) -> BehaviorMetrics:
    row = conn.execute(
        """
        WITH ref AS (
            SELECT COALESCE(MAX(bet_timestamp), CAST(CURRENT_TIMESTAMP AS TIMESTAMP)) AS as_of_ts
            FROM staging_staging.stg_bet_logs
        ),
        bets_90d AS (
            SELECT b.*
            FROM staging_staging.stg_bet_logs b, ref
            WHERE b.player_id = ?
              AND b.bet_timestamp <= ref.as_of_ts
              AND b.bet_timestamp >= ref.as_of_ts - INTERVAL '90 days'
        ),
        bets_30d AS (
            SELECT *
            FROM bets_90d, ref
            WHERE bet_timestamp >= ref.as_of_ts - INTERVAL '30 days'
        ),
        bets_7d AS (
            SELECT *
            FROM bets_90d, ref
            WHERE bet_timestamp >= ref.as_of_ts - INTERVAL '7 days'
        ),
        ordered AS (
            SELECT
                bet_timestamp,
                bet_amount,
                outcome,
                LAG(outcome) OVER (ORDER BY bet_timestamp) AS prev_outcome
            FROM bets_90d
        )
        SELECT
            (SELECT COUNT(*) FROM bets_7d) AS bets_7d,
            (SELECT COALESCE(SUM(bet_amount), 0) FROM bets_7d) AS wager_7d,
            (SELECT COUNT(*) FROM bets_30d) AS bets_30d,
            (SELECT COALESCE(SUM(bet_amount), 0) FROM bets_30d) AS wager_30d,
            (SELECT COUNT(*) FROM bets_90d) AS bets_90d,
            (SELECT COALESCE(SUM(bet_amount), 0) FROM bets_90d) AS wager_90d,
            (SELECT COALESCE(AVG(bet_amount), 0) FROM bets_30d) AS avg_bet_30d,
            (SELECT COALESCE(AVG(bet_amount), 0) FROM bets_90d) AS avg_bet_90d,
            (SELECT COALESCE(MAX(bet_amount), 0) FROM bets_30d) AS max_bet_30d,
            (SELECT COALESCE(AVG(CASE WHEN EXTRACT('hour' FROM bet_timestamp) BETWEEN 0 AND 5 THEN 1.0 ELSE 0.0 END), 0) FROM bets_30d) AS recent_night_ratio_30d,
            (SELECT COALESCE(AVG(CASE WHEN EXTRACT('hour' FROM bet_timestamp) BETWEEN 0 AND 5 THEN 1.0 ELSE 0.0 END), 0) FROM bets_90d) AS baseline_night_ratio_90d,
            COALESCE(
                AVG(CASE WHEN prev_outcome = 'loss' THEN bet_amount END) /
                NULLIF(AVG(CASE WHEN prev_outcome = 'win' THEN bet_amount END), 0),
                0
            ) AS after_loss_ratio_90d
        FROM ordered
        """,
        (player_id,),
    ).fetchone()

    return BehaviorMetrics(
        bets_7d=int(row[0] or 0),
        wager_7d=float(row[1] or 0),
        bets_30d=int(row[2] or 0),
        wager_30d=float(row[3] or 0),
        bets_90d=int(row[4] or 0),
        wager_90d=float(row[5] or 0),
        avg_bet_30d=float(row[6] or 0),
        avg_bet_90d=float(row[7] or 0),
        max_bet_30d=float(row[8] or 0),
        recent_night_ratio_30d=float(row[9] or 0),
        baseline_night_ratio_90d=float(row[10] or 0),
        after_loss_ratio_90d=float(row[11] or 0),
    )


def _fetch_gamalyze_metrics(conn: duckdb.DuckDBPyConnection, player_id: str) -> GamalyzeMetrics:
    row = conn.execute(
        """
        SELECT
            COALESCE(sensitivity_to_loss, 0),
            COALESCE(sensitivity_to_reward, 0),
            COALESCE(risk_tolerance, 0),
            COALESCE(decision_consistency, 0)
        FROM staging_staging.stg_gamalyze_scores
        WHERE player_id = ?
        ORDER BY assessment_date DESC
        LIMIT 1
        """,
        (player_id,),
    ).fetchone()
    if not row:
        return GamalyzeMetrics(0.0, 0.0, 0.0, 0.0)
    return GamalyzeMetrics(*[float(v or 0) for v in row])


def _risk_bin(score: float) -> str:
    if score >= 0.8:
        return "CRITICAL"
    if score >= 0.6:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


def _top_signals(case: CaseCandidate) -> list[tuple[str, float]]:
    weighted = [
        ("Loss chase", case.loss_chase_score * 1.15),
        ("Bet escalation", case.bet_escalation_score * 1.1),
        ("Temporal risk", case.temporal_risk_score * 1.0),
        ("Gamalyze", case.gamalyze_risk_score * 1.0),
        ("Market drift", case.market_drift_score * 0.95),
    ]
    weighted.sort(key=lambda item: item[1], reverse=True)
    return weighted[:3]


def _build_findings(case: CaseCandidate, metrics: BehaviorMetrics, gamalyze: GamalyzeMetrics) -> dict[str, object]:
    top = _top_signals(case)
    top_labels = [label for label, _ in top]
    behavior_mean = (
        case.loss_chase_score
        + case.bet_escalation_score
        + case.market_drift_score
        + case.temporal_risk_score
    ) / 4.0

    temporal_delta = metrics.recent_night_ratio_30d - metrics.baseline_night_ratio_90d
    unusual_late_night = metrics.bets_30d >= 8 and temporal_delta >= 0.18 and metrics.recent_night_ratio_30d >= 0.35

    escalation_not_confirmed = case.bet_escalation_score >= 0.7 and metrics.after_loss_ratio_90d < 1.1
    high_model_low_behavior = case.composite_risk_score >= 0.8 and behavior_mean < 0.55
    moderate_model_high_behavior = case.composite_risk_score < 0.6 and behavior_mean >= 0.7

    low_sample = metrics.bets_90d < 25
    gamalyze_high_behavior_low = case.gamalyze_risk_score >= 0.75 and behavior_mean < 0.55
    gamalyze_low_behavior_high = case.gamalyze_risk_score < 0.45 and behavior_mean >= 0.7

    evidence = [
        f"Top signal cluster: {', '.join(top_labels)} (composite {_risk_bin(case.composite_risk_score)} {case.composite_risk_score:.2f}).",
        f"Volume context: {metrics.bets_7d} bets / ${metrics.wager_7d:,.0f} in 7d; {metrics.bets_90d} bets in 90d.",
        f"Escalation corroboration: after-loss ratio {metrics.after_loss_ratio_90d:.2f}, avg bet 30d ${metrics.avg_bet_30d:,.0f} vs 90d ${metrics.avg_bet_90d:,.0f}.",
    ]

    fp_checks: list[str] = []
    fn_checks: list[str] = []

    if unusual_late_night:
        evidence.append(
            f"Late-night behavior appears unusual vs player baseline ({metrics.recent_night_ratio_30d:.1%} recent vs {metrics.baseline_night_ratio_90d:.1%} baseline)."
        )
    else:
        fp_checks.append(
            f"Temporal risk normalized against player baseline ({metrics.recent_night_ratio_30d:.1%} recent vs {metrics.baseline_night_ratio_90d:.1%} baseline); avoid over-weighting night activity alone."
        )

    if escalation_not_confirmed:
        fp_checks.append(
            f"Bet-escalation score is elevated ({case.bet_escalation_score:.2f}) but after-loss ratio is muted ({metrics.after_loss_ratio_90d:.2f}); escalation confidence downgraded."
        )

    if high_model_low_behavior:
        fp_checks.append(
            "High model score with weak behavioral corroboration indicates possible false positive; decision includes tighter follow-up before hard intervention."
        )

    if moderate_model_high_behavior:
        fn_checks.append(
            "Model score is moderate while behavioral indicators are jointly elevated; treat as potential false negative and maintain proactive intervention."
        )

    if gamalyze_high_behavior_low:
        fn_checks.append(
            "Gamalyze is elevated while observed behavioral indicators are softer; treat as neuro-risk lead indicator and monitor for confirmation."
        )

    if gamalyze_low_behavior_high:
        fn_checks.append(
            "Behavioral indicators are elevated despite lower Gamalyze score; decision remains behavior-led for player protection."
        )

    if low_sample:
        fp_checks.append(
            f"Sample adequacy constrained ({metrics.bets_90d} bets in 90d); confidence moderated and reassessment scheduled."
        )

    if not fp_checks:
        fp_checks.append("No dominant false-positive indicators after cross-signal validation.")
    if not fn_checks:
        fn_checks.append("No dominant false-negative indicators after cross-signal validation.")

    if case.risk_category in ("CRITICAL", "HIGH"):
        action = "ESCALATE"
        follow_up_days = 7 if case.risk_category == "CRITICAL" else 10
    else:
        action = "APPROVE"
        follow_up_days = 14

    decision_rationale = (
        f"Decision set to {action} because {top_labels[0]} remains elevated with corroborating signal context; "
        "false-positive and false-negative controls were reviewed before finalizing intervention."
    )

    nudge_focus = top_labels[0]
    if nudge_focus == "Loss chase":
        nudge = (
            "We noticed recent play patterns where wagers increase after losses. "
            "If helpful, you can set wager limits or take a short break in the Responsible Gaming Center."
        )
    elif nudge_focus == "Temporal risk":
        nudge = (
            "We noticed changes in when you usually play, including late-night sessions. "
            "If useful, you can set play-time reminders or take a break in the Responsible Gaming Center."
        )
    elif nudge_focus == "Gamalyze":
        nudge = (
            "We noticed shifts in play behavior that can happen during high-emotion sessions. "
            "You can set limits or take a short pause anytime in the Responsible Gaming Center."
        )
    else:
        nudge = (
            "We noticed recent changes in your play patterns. "
            "You can set limits or take a short break anytime in the Responsible Gaming Center."
        )

    follow_up_plan = (
        f"Reassess within {follow_up_days} days. Confirm trend direction across loss-chasing, escalation, "
        "temporal behavior, and Gamalyze alignment before changing intervention level."
    )

    finding_summary = (
        f"{case.risk_category} profile for {case.player_id}: strongest drivers are {', '.join(top_labels)}; "
        f"composite={case.composite_risk_score:.2f} with 7d activity {metrics.bets_7d} bets / ${metrics.wager_7d:,.0f}."
    )

    return {
        "action": action,
        "finding_summary": finding_summary,
        "evidence_bullets": evidence,
        "false_positive_checks": fp_checks,
        "false_negative_checks": fn_checks,
        "decision_rationale": decision_rationale,
        "nudge_copy": nudge,
        "follow_up_plan": follow_up_plan,
        "gamalyze_context": (
            f"Gamalyze components (loss={gamalyze.sensitivity_to_loss:.0f}, reward={gamalyze.sensitivity_to_reward:.0f}, "
            f"risk_tol={gamalyze.risk_tolerance:.0f}, consistency={gamalyze.decision_consistency:.0f})."
        ),
    }


def _state_query_pack(case: CaseCandidate, metrics: BehaviorMetrics) -> list[tuple[str, str, str, list[str], list[list[object]], bool, str]]:
    """Return (purpose, sql, summary, columns, rows, triggered, reason)."""
    pid = case.player_id
    if case.state_jurisdiction == "MA":
        sql_1 = (
            "WITH avg_90 AS ("
            " SELECT AVG(bet_amount) AS avg_bet FROM STAGING.STG_BET_LOGS "
            " WHERE player_id = '{{player_id}}' AND bet_timestamp >= DATEADD('day', -90, CURRENT_TIMESTAMP)"
            "), recent_max AS ("
            " SELECT MAX(bet_amount) AS max_bet FROM STAGING.STG_BET_LOGS "
            " WHERE player_id = '{{player_id}}' AND bet_timestamp >= DATEADD('day', -30, CURRENT_TIMESTAMP)"
            ") SELECT avg_bet, max_bet FROM avg_90 CROSS JOIN recent_max;"
        )
        triggered_1 = metrics.avg_bet_90d > 0 and metrics.max_bet_30d > metrics.avg_bet_90d * 10
        reason_1 = f"MA abnormal-play check: max ${metrics.max_bet_30d:,.0f} vs 90d avg ${metrics.avg_bet_90d:,.0f}."

        sql_2 = (
            "SELECT COUNT(*) AS late_night_bets_30d, AVG(bet_amount) AS avg_late_night_bet "
            "FROM STAGING.STG_BET_LOGS "
            "WHERE player_id = '{{player_id}}' "
            "  AND bet_timestamp >= DATEADD('day', -30, CURRENT_TIMESTAMP) "
            "  AND EXTRACT('hour' FROM bet_timestamp) BETWEEN 0 AND 5;"
        )
        late_night_bets = int(round(metrics.recent_night_ratio_30d * metrics.bets_30d))
        triggered_2 = metrics.recent_night_ratio_30d - metrics.baseline_night_ratio_90d >= 0.18
        reason_2 = (
            f"Temporal normalization: {metrics.recent_night_ratio_30d:.1%} recent vs {metrics.baseline_night_ratio_90d:.1%} baseline."
        )

        return [
            (
                "Regulatory Trigger Check - MA",
                sql_1,
                reason_1,
                ["avg_bet", "max_bet"],
                [[round(metrics.avg_bet_90d, 2), round(metrics.max_bet_30d, 2)]],
                triggered_1,
                reason_1,
            ),
            (
                "Temporal Corroboration - MA",
                sql_2,
                reason_2,
                ["late_night_bets_30d", "avg_late_night_bet"],
                [[late_night_bets, round(metrics.avg_bet_30d, 2)]],
                triggered_2,
                reason_2,
            ),
        ]

    if case.state_jurisdiction == "NJ":
        sql_1 = (
            "SELECT COUNT(*) AS flag_count FROM PROD.RG_RISK_SCORES "
            "WHERE player_id = '{{player_id}}' "
            "  AND risk_category IN ('HIGH','CRITICAL') "
            "  AND calculated_at >= DATEADD('day', -30, CURRENT_TIMESTAMP);"
        )
        inferred_flags = 3 if case.risk_category in ("HIGH", "CRITICAL") else 1
        triggered_1 = inferred_flags >= 3
        reason_1 = f"NJ multi-flag check: {inferred_flags} high/critical signals in 30 days."

        sql_2 = (
            "WITH ordered AS ("
            " SELECT bet_timestamp, bet_amount, outcome, "
            "        LAG(outcome) OVER (ORDER BY bet_timestamp) AS prev_outcome "
            " FROM STAGING.STG_BET_LOGS WHERE player_id = '{{player_id}}'"
            ") SELECT AVG(CASE WHEN prev_outcome='loss' THEN bet_amount END) AS avg_after_loss, "
            "AVG(CASE WHEN prev_outcome='win' THEN bet_amount END) AS avg_after_win FROM ordered;"
        )
        triggered_2 = metrics.after_loss_ratio_90d >= 1.25
        reason_2 = f"After-loss escalation ratio {metrics.after_loss_ratio_90d:.2f}."

        return [
            (
                "Regulatory Trigger Check - NJ",
                sql_1,
                reason_1,
                ["flag_count"],
                [[inferred_flags]],
                triggered_1,
                reason_1,
            ),
            (
                "Escalation Corroboration - NJ",
                sql_2,
                reason_2,
                ["after_loss_ratio"],
                [[round(metrics.after_loss_ratio_90d, 2)]],
                triggered_2,
                reason_2,
            ),
        ]

    sql_1 = (
        "SELECT 0 AS self_exclusion_reversals_180d, 0 AS operator_referral_count;"
    )
    reversals = 0
    triggered_1 = case.risk_category == "CRITICAL" and metrics.after_loss_ratio_90d >= 1.3
    reason_1 = (
        "PA referral check uses behavioral corroboration in demo dataset; self-exclusion reversal history unavailable."
    )

    sql_2 = (
        "WITH ordered AS ("
        " SELECT bet_timestamp, bet_amount, outcome, "
        "        LAG(outcome) OVER (ORDER BY bet_timestamp) AS prev_outcome "
        " FROM STAGING.STG_BET_LOGS WHERE player_id = '{{player_id}}'"
        ") SELECT AVG(CASE WHEN prev_outcome='loss' THEN bet_amount END) / "
        "NULLIF(AVG(CASE WHEN prev_outcome='win' THEN bet_amount END),0) AS after_loss_ratio "
        "FROM ordered;"
    )
    triggered_2 = metrics.after_loss_ratio_90d >= 1.25
    reason_2 = f"PA behavioral escalation check: after-loss ratio {metrics.after_loss_ratio_90d:.2f}."

    return [
        (
            "Regulatory Trigger Check - PA",
            sql_1,
            reason_1,
            ["self_exclusion_reversals_180d", "operator_referral_count"],
            [[reversals, 0]],
            triggered_1,
            reason_1,
        ),
        (
            "Escalation Corroboration - PA",
            sql_2,
            reason_2,
            ["after_loss_ratio"],
            [[round(metrics.after_loss_ratio_90d, 2)]],
            triggered_2,
            reason_2,
        ),
    ]


def _seed_case_status(conn: duckdb.DuckDBPyConnection, plans: list[CasePlan], analyst_id: str) -> None:
    for plan in plans:
        conn.execute(
            """
            INSERT INTO rg_case_status_log (case_id, player_id, analyst_id, status, started_at, submitted_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"CASE-{plan.case.player_id}",
                plan.case.player_id,
                analyst_id,
                plan.status,
                plan.started_at,
                plan.submitted_at,
                plan.updated_at,
            ),
        )

        conn.execute(
            """
            INSERT INTO rg_queue_cases (case_id, player_id, risk_category, composite_risk_score, assigned_at, batch_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"CASE-{plan.case.player_id}",
                plan.case.player_id,
                plan.case.risk_category,
                plan.case.composite_risk_score,
                plan.assigned_at,
                "DEMO_BATCH",
                plan.status,
            ),
        )


def _seed_logs(conn: duckdb.DuckDBPyConnection, plans: list[CasePlan], analyst_id: str, seed: int) -> None:
    for plan in plans:
        case = plan.case
        metrics = _fetch_behavior_metrics(conn, case.player_id)
        gamalyze = _fetch_gamalyze_metrics(conn, case.player_id)
        findings = _build_findings(case, metrics, gamalyze)
        query_pack = _state_query_pack(case, metrics)

        evidence_line = " ".join(findings["evidence_bullets"])
        fp_line = " ".join(findings["false_positive_checks"])
        fn_line = " ".join(findings["false_negative_checks"])

        note = (
            f"{findings['finding_summary']} "
            f"Evidence: {evidence_line} "
            f"False-positive checks: {fp_line} "
            f"False-negative checks: {fn_line} "
            f"Rationale: {findings['decision_rationale']} "
            f"Follow-up: {findings['follow_up_plan']}"
        )

        conn.execute(
            """
            INSERT INTO rg_analyst_notes_log (log_id, player_id, analyst_id, analyst_action, analyst_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                case.player_id,
                analyst_id,
                findings["action"],
                note,
                plan.note_at,
            ),
        )

        ai_response = (
            f"{findings['finding_summary']} {findings['gamalyze_context']} "
            f"Decision rationale: {findings['decision_rationale']}"
        )
        conn.execute(
            """
            INSERT INTO rg_llm_prompt_log (log_id, player_id, analyst_id, prompt_text, response_text, created_at, route_type, tool_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                case.player_id,
                analyst_id,
                "Summarize top risk signals, contradictions, and recommended analyst action for this case.",
                ai_response,
                plan.ai_prompt_at,
                "GENERAL_RG",
                "semantic_auditor",
            ),
        )

        for idx, (purpose, sql_text, summary, columns, rows, triggered, reason) in enumerate(query_pack):
            created_at = plan.query_times[min(idx, len(plan.query_times) - 1)]
            conn.execute(
                """
                INSERT INTO rg_query_log (
                    log_id, player_id, analyst_id, prompt_text, draft_sql, final_sql, purpose, result_summary,
                    result_columns, result_rows, row_count, duration_ms, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    case.player_id,
                    analyst_id,
                    f"Run {purpose} for case-open triage.",
                    sql_text,
                    sql_text,
                    purpose,
                    summary,
                    json.dumps(columns),
                    json.dumps(rows),
                    len(rows),
                    30 + idx * 9,
                    created_at,
                ),
            )

            if purpose.startswith("Regulatory Trigger Check"):
                conn.execute(
                    """
                    INSERT INTO rg_trigger_check_log (player_id, state, triggered, reason, sql_text, row_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case.player_id,
                        case.state_jurisdiction,
                        triggered,
                        reason,
                        sql_text,
                        len(rows),
                        plan.trigger_at,
                    ),
                )

        supplemental_sql = (
            "SELECT player_id, risk_category, composite_risk_score, loss_chase_score, bet_escalation_score, "
            "market_drift_score, temporal_risk_score, gamalyze_risk_score "
            "FROM PROD.RG_RISK_SCORES WHERE player_id = '{{player_id}}';"
        )
        supplemental_summary = (
            f"Signal ranking validated for {case.player_id}. Top drivers: "
            f"{', '.join(label for label, _ in _top_signals(case))}."
        )
        conn.execute(
            """
            INSERT INTO rg_query_log (
                log_id, player_id, analyst_id, prompt_text, draft_sql, final_sql, purpose, result_summary,
                result_columns, result_rows, row_count, duration_ms, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                case.player_id,
                analyst_id,
                "Validate risk component ranking and contradiction checks.",
                supplemental_sql,
                supplemental_sql,
                "Risk Signal Corroboration",
                supplemental_summary,
                json.dumps([
                    "player_id",
                    "risk_category",
                    "composite_risk_score",
                    "loss_chase_score",
                    "bet_escalation_score",
                    "market_drift_score",
                    "temporal_risk_score",
                    "gamalyze_risk_score",
                ]),
                json.dumps(
                    [[
                        case.player_id,
                        case.risk_category,
                        round(case.composite_risk_score, 4),
                        round(case.loss_chase_score, 4),
                        round(case.bet_escalation_score, 4),
                        round(case.market_drift_score, 4),
                        round(case.temporal_risk_score, 4),
                        round(case.gamalyze_risk_score, 4),
                    ]]
                ),
                1,
                44,
                plan.query_times[-1] + timedelta(minutes=5),
            ),
        )

        if plan.status == "SUBMITTED" and plan.nudge_at is not None:
            nudge_text = findings["nudge_copy"]
            final_nudge = nudge_text + " We are here to support you in staying in control of your play."
            conn.execute(
                """
                INSERT INTO rg_nudge_log (
                    log_id, player_id, analyst_id, draft_nudge, final_nudge, validation_status, validation_violations, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    case.player_id,
                    analyst_id,
                    nudge_text,
                    final_nudge,
                    "PASS",
                    json.dumps([]),
                    plan.nudge_at,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO rg_analyst_notes_draft (player_id, analyst_id, draft_notes, draft_action, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    case.player_id,
                    analyst_id,
                    f"Draft in progress for {case.player_id}. {findings['follow_up_plan']}",
                    "REVIEWING",
                    plan.note_at,
                ),
            )


def _write_manifest(completed_cases: list[CaseCandidate], in_progress_cases: list[CaseCandidate], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "counts": {
            "submitted": len(completed_cases),
            "in_progress": len(in_progress_cases),
        },
        "cases": [],
    }

    for status, cases in (("SUBMITTED", completed_cases), ("IN_PROGRESS", in_progress_cases)):
        for case in cases:
            manifest["cases"].append(
                {
                    "case_id": f"CASE-{case.player_id}",
                    "player_id": case.player_id,
                    "status": status,
                    "risk_category": case.risk_category,
                    "state": case.state_jurisdiction,
                    "driver": case.primary_driver,
                    "composite_risk_score": round(case.composite_risk_score, 4),
                    "doc_path": f"docs/case_reviews/demo/CASE_{case.player_id}.md",
                }
            )

    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def seed_demo_cases(
    db_path: str,
    completed: int,
    in_progress: int,
    analyst_id: str,
    manifest_path: str,
    seed: int,
    preferred_player_ids_path: str | None,
) -> None:
    random.seed(seed)
    base_now = datetime.utcnow().replace(second=0, microsecond=0)
    conn = _connect(db_path)
    try:
        _ensure_runtime_tables(conn)
        _clear_runtime_tables(conn)

        candidates = _load_candidates(conn)
        preferred_ids = _load_preferred_player_ids(preferred_player_ids_path)
        completed_cases, in_progress_cases = _pick_cases(
            candidates, completed, in_progress, preferred_ids
        )

        completed_plans = [
            _build_case_plan(case, "SUBMITTED", idx, base_now, seed)
            for idx, case in enumerate(completed_cases)
        ]
        in_progress_plans = [
            _build_case_plan(case, "IN_PROGRESS", idx, base_now, seed)
            for idx, case in enumerate(in_progress_cases)
        ]

        _seed_case_status(conn, [*completed_plans, *in_progress_plans], analyst_id)
        _seed_logs(conn, [*completed_plans, *in_progress_plans], analyst_id, seed)

        _write_manifest(completed_cases, in_progress_cases, Path(manifest_path))

    finally:
        conn.close()

    print(
        f"Seeded demo runtime data: submitted={completed}, in_progress={in_progress}, db={db_path}"
    )
    print(f"Manifest: {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic demo runtime case data.")
    parser.add_argument("--db-path", default="data/dk_sentinel.duckdb")
    parser.add_argument("--completed", type=int, default=20)
    parser.add_argument("--in-progress", type=int, default=2)
    parser.add_argument("--analyst-id", default="Colby Reichenbach")
    parser.add_argument("--manifest-path", default="docs/case_reviews/CASE_MANIFEST.json")
    parser.add_argument(
        "--preferred-player-ids-path",
        default="docs/case_reviews/LEGACY_CASE_IDS.json",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_demo_cases(
        db_path=args.db_path,
        completed=args.completed,
        in_progress=args.in_progress,
        analyst_id=args.analyst_id,
        manifest_path=args.manifest_path,
        seed=args.seed,
        preferred_player_ids_path=args.preferred_player_ids_path,
    )


if __name__ == "__main__":
    main()
