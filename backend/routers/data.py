"""Live data endpoints for queue, case detail, and audit trail."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from backend.db.duckdb_client import execute, get_db_path, query_rows
from backend.models.analytics import AnalyticsSummary, FunnelCounts, RiskMix
from backend.models.risk_data import AuditTrailEntry, CaseDetail, CaseFileResponse, RiskCase
from backend.routers.cases import get_case_timeline, get_query_logs, trigger_check
from backend.routers.interventions import get_latest_notes

router = APIRouter()

def _action_recommendations(risk_category: str, state: str | None) -> list[str]:
    base = ["Provide Responsible Gaming Resources (RG Center)"]
    if risk_category == "CRITICAL":
        base += [
            "Immediate analyst review (within 2 hours)",
            "Supportive nudge + timeout offer",
            "Escalate for senior review (manual limits/exclusion)",
        ]
    elif risk_category == "HIGH":
        base += [
            "Supportive nudge (within 24 hours)",
            "Offer Player Limits (Deposit/Wager/Time)",
            "Offer Cool Off Period",
        ]
    elif risk_category == "MEDIUM":
        base += [
            "Watchlist + weekly check-in",
            "Optional check-in message",
        ]
    else:
        base += [
            "Monitor only (no intervention)",
            "Document only (optional)",
        ]

    if state == "NJ":
        base.append("Refer for mandatory 24-hour timeout + commission notification (if NJ trigger)")
    elif state == "PA":
        base.append("Refer to PA Problem Gambling Council + 72-hour cooling period (if PA trigger)")
    elif state == "MA":
        base.append("Internal documentation + analyst review (if MA trigger)")

    return base

_REGULATORY_NOTES = {
    "MA": "MA abnormal-play review pending (10x rolling avg check).",
    "NJ": "NJ multi-flag review pending (30-day window).",
    "PA": "PA referral check pending (self-exclusion history).",
}

_SCHEMA_CANDIDATES = ("PROD", "staging_prod", "STAGING_PROD", "staging_staging", "STAGING_STAGING")
_QUEUE_TARGET = 50
_QUEUE_REFILL_AT = 20
_QUEUE_BATCH = 30
_QUEUE_MIX = (
    ("CRITICAL", 6),
    ("HIGH", 12),
    ("MEDIUM", 20),
    ("LOW", 5),
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


def _case_id(player_id: str) -> str:
    return f"CASE-{player_id}"


def _key_evidence(row: dict) -> list[str]:
    scores = {
        "Loss chase": row.get("loss_chase_score", 0.0),
        "Bet escalation": row.get("bet_escalation_score", 0.0),
        "Market drift": row.get("market_drift_score", 0.0),
        "Temporal risk": row.get("temporal_risk_score", 0.0),
        "Gamalyze": row.get("gamalyze_risk_score", 0.0),
    }
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    return [f"{label} {value:.2f}" for label, value in ranked]


def _queued_count(db_path: str) -> int:
    rows = query_rows(
        "SELECT COUNT(*) AS total FROM rg_queue_cases WHERE status = 'QUEUED'",
        db_path=db_path,
    )
    return int(rows[0]["total"]) if rows else 0


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _fetch_analytics_summary(db_path: str) -> AnalyticsSummary:
    status_rows = query_rows(
        """
        SELECT
            COUNT(*) AS started,
            SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 'SUBMITTED' THEN 1 ELSE 0 END) AS submitted
        FROM rg_case_status_log
        """,
        db_path=db_path,
    )
    status = status_rows[0] if status_rows else {"started": 0, "in_progress": 0, "submitted": 0}

    avg_submit_rows = query_rows(
        """
        SELECT
            AVG(DATE_DIFF('minute', started_at, submitted_at)) / 60.0 AS avg_hours
        FROM rg_case_status_log
        WHERE status = 'SUBMITTED'
          AND started_at IS NOT NULL
          AND submitted_at IS NOT NULL
        """,
        db_path=db_path,
    )
    avg_submit = avg_submit_rows[0]["avg_hours"] if avg_submit_rows else 0.0
    if avg_submit is None or avg_submit < 0:
        avg_submit = 0.0

    avg_progress_rows = query_rows(
        """
        SELECT
            AVG(DATE_DIFF('minute', started_at, CAST(CURRENT_TIMESTAMP AS TIMESTAMP))) / 60.0 AS avg_hours
        FROM rg_case_status_log
        WHERE status = 'IN_PROGRESS'
          AND started_at IS NOT NULL
        """,
        db_path=db_path,
    )
    avg_progress = avg_progress_rows[0]["avg_hours"] if avg_progress_rows else 0.0
    if avg_progress is None or avg_progress < 0:
        avg_progress = 0.0

    sql_rows = query_rows("SELECT COUNT(*) AS total FROM rg_query_log", db_path=db_path)
    sql_total = int(sql_rows[0]["total"]) if sql_rows else 0

    llm_rows = query_rows("SELECT COUNT(*) AS total FROM rg_llm_prompt_log", db_path=db_path)
    llm_total = int(llm_rows[0]["total"]) if llm_rows else 0

    case_count_rows = query_rows(
        "SELECT COUNT(DISTINCT player_id) AS total FROM rg_case_status_log", db_path=db_path
    )
    total_cases_distinct = int(case_count_rows[0]["total"]) if case_count_rows else 0

    sql_case_rows = query_rows(
        "SELECT COUNT(DISTINCT player_id) AS total FROM rg_query_log", db_path=db_path
    )
    sql_cases = int(sql_case_rows[0]["total"]) if sql_case_rows else 0

    llm_case_rows = query_rows(
        "SELECT COUNT(DISTINCT player_id) AS total FROM rg_llm_prompt_log", db_path=db_path
    )
    llm_cases = int(llm_case_rows[0]["total"]) if llm_case_rows else 0

    risk_schema = _resolve_schema("rg_risk_scores", db_path)
    risk_rows = query_rows(
        """
        SELECT r.risk_category, COUNT(*) AS total
        FROM rg_case_status_log s
        LEFT JOIN {risk_schema}.RG_RISK_SCORES r
          ON s.player_id = r.player_id
        GROUP BY r.risk_category
        """.format(risk_schema=risk_schema),
        db_path=db_path,
    )
    risk_mix = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for row in risk_rows:
        category = (row.get("risk_category") or "").upper()
        if category in risk_mix:
            risk_mix[category] = int(row["total"])

    queue_rows = query_rows(
        "SELECT COUNT(*) AS total FROM rg_queue_cases WHERE status = 'QUEUED'", db_path=db_path
    )
    queued_total = int(queue_rows[0]["total"]) if queue_rows else 0

    trigger_rows = query_rows(
        "SELECT COUNT(*) AS total FROM rg_trigger_check_log", db_path=db_path
    )
    trigger_total = int(trigger_rows[0]["total"]) if trigger_rows else 0

    nudge_rows = query_rows("SELECT COUNT(*) AS total FROM rg_nudge_log", db_path=db_path)
    nudge_total = int(nudge_rows[0]["total"]) if nudge_rows else 0

    return AnalyticsSummary(
        total_cases_started=int(status.get("started") or 0),
        total_cases_submitted=int(status.get("submitted") or 0),
        in_progress_count=int(status.get("in_progress") or 0),
        avg_time_to_submit_hours=float(avg_submit or 0.0),
        avg_time_in_progress_hours=float(avg_progress or 0.0),
        sql_queries_logged=sql_total,
        llm_prompts_logged=llm_total,
        cases_with_sql_pct=_safe_ratio(sql_cases, total_cases_distinct),
        cases_with_llm_pct=_safe_ratio(llm_cases, total_cases_distinct),
        risk_mix=RiskMix(
            critical=risk_mix["CRITICAL"],
            high=risk_mix["HIGH"],
            medium=risk_mix["MEDIUM"],
            low=risk_mix["LOW"],
        ),
        trigger_checks_run=trigger_total,
        nudges_validated=nudge_total,
        funnel=FunnelCounts(
            queued=queued_total,
            started=int(status.get("started") or 0),
            submitted=int(status.get("submitted") or 0),
        ),
    )


def _fetch_candidates(
    *,
    category: str | None,
    limit: int,
    db_path: str,
    risk_schema: str,
) -> list[dict]:
    category_filter = "AND r.risk_category = ?" if category else ""
    params = [category] if category else []
    params.append(limit)
    return query_rows(
        """
        SELECT
            r.player_id,
            r.composite_risk_score,
            r.risk_category,
            r.calculated_at,
            r.loss_chase_score,
            r.bet_escalation_score,
            r.market_drift_score,
            r.temporal_risk_score,
            r.gamalyze_risk_score
        FROM {risk_schema}.RG_RISK_SCORES r
        LEFT JOIN rg_queue_cases q
          ON r.player_id = q.player_id AND q.status = 'QUEUED'
        LEFT JOIN rg_case_status_log s
          ON r.player_id = s.player_id
        WHERE q.player_id IS NULL
          AND s.player_id IS NULL
          {category_filter}
        ORDER BY r.composite_risk_score DESC, r.calculated_at DESC
        LIMIT ?
        """.format(risk_schema=risk_schema, category_filter=category_filter),
        tuple(params),
        db_path=db_path,
    )


def _insert_queue_entries(rows: list[dict], batch_id: str, db_path: str) -> None:
    assigned_at = datetime.utcnow().isoformat()
    for row in rows:
        execute(
            """
            INSERT INTO rg_queue_cases (
                case_id,
                player_id,
                risk_category,
                composite_risk_score,
                assigned_at,
                batch_id,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _case_id(row["player_id"]),
                row["player_id"],
                row["risk_category"],
                row["composite_risk_score"],
                assigned_at,
                batch_id,
                "QUEUED",
            ),
            db_path=db_path,
        )


def _refill_queue_if_needed(db_path: str) -> None:
    current_count = _queued_count(db_path)
    if current_count >= _QUEUE_REFILL_AT:
        return

    risk_schema = _resolve_schema("rg_risk_scores", db_path)
    target_add = _QUEUE_TARGET if current_count == 0 else _QUEUE_BATCH
    batch_id = str(uuid4())
    selected: list[dict] = []
    selected_ids: set[str] = set()

    for category, limit in _QUEUE_MIX:
        if len(selected) >= target_add:
            break
        added_for_category = 0
        candidates = _fetch_candidates(
            category=category,
            limit=limit * 2,
            db_path=db_path,
            risk_schema=risk_schema,
        )
        for row in candidates:
            if row["player_id"] in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row["player_id"])
            added_for_category += 1
            if added_for_category >= limit or len(selected) >= target_add:
                break

    remaining = target_add - len(selected)
    if remaining > 0:
        fallback_limit = max(remaining * 10, _QUEUE_TARGET)
        candidates = _fetch_candidates(
            category=None,
            limit=fallback_limit,
            db_path=db_path,
            risk_schema=risk_schema,
        )
        for row in candidates:
            if row["player_id"] in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row["player_id"])
            if len(selected) >= target_add:
                break

    if selected:
        _insert_queue_entries(selected, batch_id, db_path)


@router.get("/queue", response_model=list[RiskCase])
async def get_queue(limit: int = 200, db_path: str = Depends(get_db_path)) -> list[RiskCase]:
    """Return the analyst queue."""
    _refill_queue_if_needed(db_path)
    risk_schema = _resolve_schema("rg_risk_scores", db_path)
    rows = query_rows(
        """
        SELECT
            q.case_id,
            q.player_id,
            q.assigned_at,
            r.composite_risk_score,
            r.risk_category,
            r.calculated_at,
            r.loss_chase_score,
            r.bet_escalation_score,
            r.market_drift_score,
            r.temporal_risk_score,
            r.gamalyze_risk_score,
            p.state_jurisdiction
        FROM rg_queue_cases q
        LEFT JOIN {schema}.RG_RISK_SCORES r
          ON q.player_id = r.player_id
        LEFT JOIN {staging}.STG_PLAYER_PROFILES p
          ON q.player_id = p.player_id
        WHERE q.status = 'QUEUED'
        ORDER BY q.assigned_at DESC
        LIMIT ?
        """.format(schema=risk_schema, staging=_resolve_schema("stg_player_profiles", db_path)),
        (limit,),
        db_path=db_path,
    )

    return [
        RiskCase(
            case_id=row.get("case_id") or _case_id(row["player_id"]),
            player_id=row["player_id"],
            risk_category=row["risk_category"],
            composite_risk_score=row["composite_risk_score"],
            score_calculated_at=str(row["calculated_at"]),
            state_jurisdiction=row.get("state_jurisdiction"),
            key_evidence=_key_evidence(row),
        )
        for row in rows
    ]


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db_path: str = Depends(get_db_path)) -> AnalyticsSummary:
    """Return analyst performance summary metrics."""
    return _fetch_analytics_summary(db_path)


@router.get("/case-detail/{case_id}", response_model=CaseDetail)
async def get_case_detail(
    case_id: str, db_path: str = Depends(get_db_path)
) -> CaseDetail:
    """Return detailed case data for a given case id."""
    player_id = case_id.replace("CASE-", "")
    risk_schema = _resolve_schema("rg_risk_scores", db_path)
    score_rows = query_rows(
        """
        SELECT
            r.player_id,
            r.composite_risk_score,
            r.risk_category,
            r.calculated_at,
            r.loss_chase_score,
            r.bet_escalation_score,
            r.market_drift_score,
            r.temporal_risk_score,
            r.gamalyze_risk_score,
            p.state_jurisdiction
        FROM {schema}.RG_RISK_SCORES r
        LEFT JOIN {staging}.STG_PLAYER_PROFILES p
          ON r.player_id = p.player_id
        WHERE r.player_id = ?
        """.format(schema=risk_schema, staging=_resolve_schema("stg_player_profiles", db_path)),
        (player_id,),
        db_path=db_path,
    )
    if not score_rows:
        raise HTTPException(status_code=404, detail="Case not found")

    row = score_rows[0]
    bet_rows = query_rows(
        """
        SELECT
            COUNT(*) AS total_bets_7d,
            COALESCE(SUM(bet_amount), 0) AS total_wagered_7d
        FROM {staging}.STG_BET_LOGS
        WHERE player_id = ?
          AND bet_timestamp >= CAST(CURRENT_TIMESTAMP AS TIMESTAMP) - INTERVAL '7 days'
        """.format(staging=_resolve_schema("stg_bet_logs", db_path)),
        (player_id,),
        db_path=db_path,
    )
    bets = bet_rows[0] if bet_rows else {"total_bets_7d": 0, "total_wagered_7d": 0}

    state = row.get("state_jurisdiction")
    regulatory_notes = _REGULATORY_NOTES.get(state or "", "Regulatory review pending.")

    return CaseDetail(
        case_id=_case_id(player_id),
        player_id=player_id,
        risk_category=row["risk_category"],
        composite_risk_score=row["composite_risk_score"],
        score_calculated_at=str(row["calculated_at"]),
        state_jurisdiction=state,
        evidence_snapshot={
            "total_bets_7d": int(bets["total_bets_7d"]),
            "total_wagered_7d": float(bets["total_wagered_7d"]),
            "loss_chase_score": float(row["loss_chase_score"]),
            "bet_escalation_score": float(row["bet_escalation_score"]),
            "market_drift_score": float(row["market_drift_score"]),
            "temporal_risk_score": float(row["temporal_risk_score"]),
            "gamalyze_risk_score": float(row["gamalyze_risk_score"]),
        },
        ai_explanation="",
        draft_nudge="",
        regulatory_notes=regulatory_notes,
        analyst_actions=_action_recommendations(row["risk_category"], state),
    )


@router.get("/audit-trail", response_model=list[AuditTrailEntry])
async def get_audit_trail(
    limit: int = 200, db_path: str = Depends(get_db_path)
) -> list[AuditTrailEntry]:
    """Return analyst-driven audit trail entries."""
    risk_schema = _resolve_schema("rg_risk_scores", db_path)
    staging_schema = _resolve_schema("stg_player_profiles", db_path)
    rows = query_rows(
        """
        WITH latest_notes AS (
            SELECT
                player_id,
                analyst_action,
                analyst_notes,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY player_id
                    ORDER BY created_at DESC
                ) AS rn
            FROM rg_analyst_notes_log
        ),
        latest_nudge AS (
            SELECT
                player_id,
                final_nudge,
                validation_status,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY player_id
                    ORDER BY created_at DESC
                ) AS rn
            FROM rg_nudge_log
        )
        SELECT
            s.case_id,
            s.player_id,
            s.analyst_id,
            s.status,
            s.started_at,
            s.submitted_at,
            s.updated_at,
            r.risk_category,
            p.state_jurisdiction,
            n.analyst_action,
            n.analyst_notes,
            n.created_at AS note_created_at,
            ng.final_nudge AS nudge_text,
            ng.validation_status AS nudge_status,
            ng.created_at AS nudge_created_at
        FROM rg_case_status_log s
        LEFT JOIN {risk_schema}.RG_RISK_SCORES r
          ON s.player_id = r.player_id
        LEFT JOIN {staging_schema}.STG_PLAYER_PROFILES p
          ON s.player_id = p.player_id
        LEFT JOIN latest_notes n
          ON s.player_id = n.player_id AND n.rn = 1
        LEFT JOIN latest_nudge ng
          ON s.player_id = ng.player_id AND ng.rn = 1
        ORDER BY s.updated_at DESC
        LIMIT ?
        """.format(risk_schema=risk_schema, staging_schema=staging_schema),
        (limit,),
        db_path=db_path,
    )

    results: list[AuditTrailEntry] = []
    for row in rows:
        status = row["status"]
        action = row.get("analyst_action")
        if not action:
            action = "Submitted decision" if status == "SUBMITTED" else "Case review started"
        notes = row.get("analyst_notes") or "No analyst notes yet."
        timestamp = row.get("note_created_at") or row.get("updated_at")
        nudge_text = row.get("nudge_text")
        nudge_excerpt = None
        if nudge_text:
            nudge_excerpt = nudge_text[:80]
            if len(nudge_text) > 80:
                nudge_excerpt += "…"
        results.append(
            AuditTrailEntry(
                audit_id=str(row["case_id"]),
                case_id=row["case_id"],
                player_id=row["player_id"],
                analyst_id=row.get("analyst_id"),
                action=action,
                risk_category=row.get("risk_category") or "HIGH",
                state_jurisdiction=row.get("state_jurisdiction"),
                timestamp=str(timestamp),
                notes=notes,
                nudge_status=row.get("nudge_status"),
                nudge_excerpt=nudge_excerpt,
            )
        )
    return results


@router.get("/case-file/{player_id}", response_model=CaseFileResponse)
async def get_case_file(
    player_id: str, db_path: str = Depends(get_db_path)
) -> CaseFileResponse:
    """Return aggregated case file payload."""
    case_detail = await get_case_detail(_case_id(player_id), db_path)
    try:
        latest_note = await get_latest_notes(player_id, db_path)
    except HTTPException:
        latest_note = None

    prompt_logs = query_rows(
        """
        SELECT player_id, analyst_id, prompt_text, response_text, route_type, tool_used, created_at
        FROM rg_llm_prompt_log
        WHERE player_id = ?
        ORDER BY created_at DESC
        """,
        (player_id,),
        db_path=db_path,
    )
    query_logs = await get_query_logs(player_id, db_path)
    timeline = await get_case_timeline(player_id, db_path)
    trigger_checks = await trigger_check(player_id, db_path=db_path)

    return CaseFileResponse(
        case_detail=case_detail,
        latest_note=latest_note.model_dump() if latest_note else None,
        prompt_logs=[
            {
                "player_id": row["player_id"],
                "analyst_id": row["analyst_id"],
                "prompt_text": row["prompt_text"],
                "response_text": row["response_text"],
                "route_type": row.get("route_type"),
                "tool_used": row.get("tool_used"),
                "created_at": str(row["created_at"]),
            }
            for row in prompt_logs
        ],
        query_logs=[log.model_dump() for log in query_logs],
        timeline=[entry.model_dump() for entry in timeline],
        trigger_checks=[check.model_dump() for check in trigger_checks],
    )
