"""Live data endpoints for queue, case detail, and audit trail."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.db.duckdb_client import get_db_path, query_rows
from backend.models.risk_data import AuditTrailEntry, CaseDetail, CaseFileResponse, RiskCase
from backend.routers.cases import get_case_timeline, get_query_logs
from backend.routers.interventions import get_latest_notes

router = APIRouter()

_ACTION_RECOMMENDATIONS = [
    "Provide Responsible Gaming Resources (RG Center)",
    "Offer Player Limits (Deposit/Wager/Time)",
    "Offer Cool Off Period",
    "Offer Self-Exclusion",
    "Monitor & Document",
]

_REGULATORY_NOTES = {
    "MA": "MA abnormal-play review pending (10x rolling avg check).",
    "NJ": "NJ multi-flag review pending (30-day window).",
    "PA": "PA referral check pending (self-exclusion history).",
}


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


@router.get("/queue", response_model=list[RiskCase])
async def get_queue(limit: int = 200, db_path: str = Depends(get_db_path)) -> list[RiskCase]:
    """Return the analyst queue."""
    rows = query_rows(
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
        FROM PROD.RG_RISK_SCORES r
        LEFT JOIN STAGING.STG_PLAYER_PROFILES p
          ON r.player_id = p.player_id
        ORDER BY r.composite_risk_score DESC, r.score_calculated_at DESC
        LIMIT ?
        """,
        (limit,),
        db_path=db_path,
    )

    return [
        RiskCase(
            case_id=_case_id(row["player_id"]),
            player_id=row["player_id"],
            risk_category=row["risk_category"],
            composite_risk_score=row["composite_risk_score"],
            score_calculated_at=str(row["calculated_at"]),
            state_jurisdiction=row.get("state_jurisdiction"),
            key_evidence=_key_evidence(row),
        )
        for row in rows
    ]


@router.get("/case-detail/{case_id}", response_model=CaseDetail)
async def get_case_detail(
    case_id: str, db_path: str = Depends(get_db_path)
) -> CaseDetail:
    """Return detailed case data for a given case id."""
    player_id = case_id.replace("CASE-", "")
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
        FROM PROD.RG_RISK_SCORES r
        LEFT JOIN STAGING.STG_PLAYER_PROFILES p
          ON r.player_id = p.player_id
        WHERE r.player_id = ?
        """,
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
        FROM STAGING.STG_BET_LOGS
        WHERE player_id = ?
          AND bet_timestamp >= (CURRENT_TIMESTAMP - INTERVAL '7 days')
        """,
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
        analyst_actions=_ACTION_RECOMMENDATIONS,
    )


@router.get("/audit-trail", response_model=list[AuditTrailEntry])
async def get_audit_trail(db_path: str = Depends(get_db_path)) -> list[AuditTrailEntry]:
    """Return audit trail entries."""
    rows = query_rows(
        """
        SELECT
            audit_id,
            player_id,
            risk_category,
            state_jurisdiction,
            analyst_id,
            analyst_action,
            analyst_notes,
            score_calculated_at,
            created_at
        FROM PROD.RG_AUDIT_TRAIL
        ORDER BY created_at DESC
        """,
        db_path=db_path,
    )
    results: list[AuditTrailEntry] = []
    for row in rows:
        timestamp = row["created_at"] or row["score_calculated_at"]
        action = row["analyst_action"] or "Review pending"
        notes = row["analyst_notes"] or "No analyst notes yet."
        results.append(
            AuditTrailEntry(
                audit_id=str(row["audit_id"]),
                case_id=_case_id(row["player_id"]),
                player_id=row["player_id"],
                analyst_id=row.get("analyst_id"),
                action=action,
                risk_category=row["risk_category"],
                state_jurisdiction=row.get("state_jurisdiction"),
                timestamp=str(timestamp),
                notes=notes,
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
    )
