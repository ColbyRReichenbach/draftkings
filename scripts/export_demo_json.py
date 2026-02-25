"""Export static frontend demo JSON snapshots from live backend endpoints.

Uses FastAPI TestClient against local app and DuckDB path, then writes fixtures into
frontend/public/demo for static hosting mode (VITE_DATA_MODE=static).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _get(client: TestClient, path: str) -> object:
    response = client.get(path)
    if response.status_code >= 400:
        raise RuntimeError(f"GET {path} failed: {response.status_code} {response.text}")
    return response.json()


def _post(client: TestClient, path: str) -> object:
    response = client.post(path)
    if response.status_code >= 400:
        raise RuntimeError(f"POST {path} failed: {response.status_code} {response.text}")
    return response.json()


def _extract(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.I | re.M)
    return match.group(1).strip() if match else default


def _find_doc_for_player(project_root: Path, player_id: str) -> Path | None:
    preferred = [
        project_root / "docs" / "case_reviews" / f"CASE_{player_id}.md",
        project_root / "docs" / "case_reviews" / "demo" / f"CASE_{player_id}.md",
    ]
    for path in preferred:
        if path.exists():
            return path
    return None


def _legacy_case_payload(player_id: str, project_root: Path) -> dict[str, object] | None:
    doc_path = _find_doc_for_player(project_root, player_id)
    if not doc_path:
        return None

    text = doc_path.read_text(encoding="utf-8")
    state = _extract(r"Jurisdiction:\*\*\s*([A-Z]{2})", text, player_id.split("_")[-1])
    risk = _extract(r"Risk Category:\*\*\s*([A-Z]+)", text, "MEDIUM").upper()
    composite_raw = _extract(r"Composite Risk Score:\*\*\s*([0-9.]+)", text, "0.58")
    composite = float(composite_raw)
    decision = _extract(r"\*\*Decision:\*\*\s*(.+)", text, "Decision documented after evidence review.")
    action = _extract(r"\*\*Action:\*\*\s*(.+)", text, "Supportive outreach and monitoring.")
    nudge = _extract(r"##\s*7\)\s*Nudge Copy.*?[\n\r]+[\"“](.+?)[\"”]", text)
    if not nudge:
        nudge = (
            "We noticed recent changes in play patterns. If useful, you can set limits or "
            "take a short break anytime in the Responsible Gaming Center."
        )
    sql_blocks = re.findall(r"```sql\n(.*?)```", text, flags=re.S | re.I)
    if not sql_blocks:
        sql_blocks = [
            "SELECT player_id, risk_category, composite_risk_score FROM PROD.RG_RISK_SCORES WHERE player_id = '{{player_id}}';"
        ]

    now = datetime.utcnow().replace(microsecond=0)
    base = now - timedelta(days=2)
    query_logs = []
    timeline = []
    for index, sql in enumerate(sql_blocks[:3]):
        ts = base + timedelta(minutes=8 + index * 11, seconds=7 + index * 9)
        query_logs.append(
            {
                "player_id": player_id,
                "analyst_id": "Colby Reichenbach",
                "prompt_text": f"Legacy evidence query {index + 1} for case review.",
                "draft_sql": sql.strip(),
                "final_sql": sql.strip(),
                "purpose": f"Legacy Evidence Query {index + 1}",
                "result_summary": "Query executed and reviewed during analyst assessment.",
                "result_columns": ["player_id", "risk_category", "composite_risk_score"],
                "result_rows": [[player_id, risk, round(composite, 4)]],
                "row_count": 1,
                "duration_ms": 40 + (index * 8),
                "created_at": ts.isoformat(sep=" "),
            }
        )
        timeline.append(
            {
                "event_type": "SQL query",
                "event_detail": f"Legacy Evidence Query {index + 1} — Query executed and reviewed during analyst assessment.",
                "created_at": ts.isoformat(sep=" "),
            }
        )

    ai_ts = base + timedelta(minutes=50, seconds=15)
    note_ts = base + timedelta(minutes=77, seconds=33)
    nudge_ts = base + timedelta(minutes=64, seconds=12)
    timeline.append(
        {
            "event_type": "AI draft",
            "event_detail": "Prompt logged: Legacy case narrative harmonized with current workflow.",
            "created_at": ai_ts.isoformat(sep=" "),
        }
    )
    timeline.append(
        {
            "event_type": "Analyst note",
            "event_detail": f"{'ESCALATE' if risk in {'CRITICAL', 'HIGH'} else 'APPROVE'}: {decision} {action}",
            "created_at": note_ts.isoformat(sep=" "),
        }
    )
    timeline.sort(key=lambda row: row["created_at"], reverse=True)

    evidence_defaults = {
        "CRITICAL": {
            "total_bets_7d": 36,
            "total_wagered_7d": 17250.0,
            "loss_chase_score": 0.9,
            "bet_escalation_score": 0.86,
            "market_drift_score": 0.7,
            "temporal_risk_score": 0.79,
            "gamalyze_risk_score": 0.78,
        },
        "HIGH": {
            "total_bets_7d": 24,
            "total_wagered_7d": 8600.0,
            "loss_chase_score": 0.73,
            "bet_escalation_score": 0.71,
            "market_drift_score": 0.62,
            "temporal_risk_score": 0.67,
            "gamalyze_risk_score": 0.69,
        },
        "MEDIUM": {
            "total_bets_7d": 15,
            "total_wagered_7d": 2400.0,
            "loss_chase_score": 0.55,
            "bet_escalation_score": 0.53,
            "market_drift_score": 0.49,
            "temporal_risk_score": 0.52,
            "gamalyze_risk_score": 0.54,
        },
        "LOW": {
            "total_bets_7d": 8,
            "total_wagered_7d": 720.0,
            "loss_chase_score": 0.26,
            "bet_escalation_score": 0.24,
            "market_drift_score": 0.22,
            "temporal_risk_score": 0.21,
            "gamalyze_risk_score": 0.23,
        },
    }

    case_id = f"CASE-{player_id}"
    note_text = f"{decision} {action}".strip()
    final_nudge = f"{nudge} We are here to support you in staying in control of your play."
    action_tag = "ESCALATE" if risk in {"CRITICAL", "HIGH"} else "APPROVE"
    trigger_reason = f"{state} legacy case trigger replayed from documented analyst evidence."

    return {
        "case_id": case_id,
        "player_id": player_id,
        "risk_category": risk,
        "state": state,
        "composite": composite,
        "case_detail": {
            "case_id": case_id,
            "player_id": player_id,
            "risk_category": risk,
            "composite_risk_score": composite,
            "score_calculated_at": (base - timedelta(hours=2)).isoformat(sep=" ") + "-05:00",
            "state_jurisdiction": state,
            "evidence_snapshot": evidence_defaults.get(risk, evidence_defaults["MEDIUM"]),
            "ai_explanation": "",
            "draft_nudge": "",
            "regulatory_notes": f"{state} legacy case review synchronized for static demo.",
            "analyst_actions": [
                "Provide Responsible Gaming Resources (RG Center)",
                "Document evidence-driven rationale",
                "Apply state-specific follow-up controls",
            ],
        },
        "case_file": {
            "case_detail": None,  # set below
            "latest_note": {
                "player_id": player_id,
                "analyst_id": "Colby Reichenbach",
                "analyst_action": action_tag,
                "analyst_notes": note_text,
                "created_at": note_ts.isoformat(sep=" "),
            },
            "prompt_logs": [
                {
                    "player_id": player_id,
                    "analyst_id": "Colby Reichenbach",
                    "prompt_text": "Legacy case narrative harmonization for static replay.",
                    "response_text": "Legacy evidence translated into structured workflow artifacts.",
                    "route_type": "GENERAL_RG",
                    "tool_used": "semantic_auditor",
                    "created_at": ai_ts.isoformat(sep=" "),
                }
            ],
            "query_logs": query_logs,
            "timeline": timeline,
            "trigger_checks": [
                {
                    "state": state,
                    "triggered": risk in {"CRITICAL", "HIGH"},
                    "reason": trigger_reason,
                    "sql_text": "SELECT 1 AS legacy_trigger_check",
                    "row_count": 1,
                    "created_at": (base + timedelta(minutes=4, seconds=30)).isoformat(sep=" "),
                }
            ],
        },
        "notes": {
            "player_id": player_id,
            "analyst_id": "Colby Reichenbach",
            "analyst_action": action_tag,
            "analyst_notes": note_text,
            "created_at": note_ts.isoformat(sep=" "),
        },
        "nudge": {
            "player_id": player_id,
            "analyst_id": "Colby Reichenbach",
            "draft_nudge": nudge,
            "final_nudge": final_nudge,
            "validation_status": "PASS",
            "validation_violations": [],
            "created_at": nudge_ts.isoformat(sep=" "),
        },
        "query_logs": query_logs,
        "timeline": timeline,
        "trigger_checks": [
            {
                "state": state,
                "triggered": risk in {"CRITICAL", "HIGH"},
                "reason": trigger_reason,
                "sql_text": "SELECT 1 AS legacy_trigger_check",
                "row_count": 1,
                "created_at": (base + timedelta(minutes=4, seconds=30)).isoformat(sep=" "),
            }
        ],
    }


def export_demo_json(db_path: str, output_dir: str, manifest_path: str, queue_cap: int) -> None:
    os.environ["DUCKDB_PATH"] = db_path
    root_dir = Path(__file__).resolve().parents[1]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    logging.getLogger("httpx").setLevel(logging.WARNING)

    from backend.main import app

    out = Path(output_dir)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    with TestClient(app) as client:
        queue = _get(client, "/api/queue")
        audit_trail = _get(client, "/api/audit-trail")
        analytics = _get(client, "/api/analytics/summary")
        case_status = _get(client, "/api/cases/status")

        _write_json(out / "queue.json", queue)
        _write_json(out / "audit-trail.json", audit_trail)
        _write_json(out / "analytics-summary.json", analytics)
        _write_json(out / "cases" / "status.json", case_status)

        players = {row["player_id"] for row in manifest["cases"]}
        legacy_ids_path = root_dir / "docs" / "case_reviews" / "LEGACY_CASE_IDS.json"
        if legacy_ids_path.exists():
            legacy_payload = json.loads(legacy_ids_path.read_text(encoding="utf-8"))
            legacy_ids = (
                legacy_payload.get("player_ids", [])
                if isinstance(legacy_payload, dict)
                else legacy_payload
            )
            if isinstance(legacy_ids, list):
                for player_id in legacy_ids:
                    if isinstance(player_id, str) and player_id.strip():
                        players.add(player_id.strip())
        for row in queue[:queue_cap]:
            players.add(row["player_id"])

        legacy_docs_root = root_dir

        for player_id in sorted(players):
            case_id = f"CASE-{player_id}"
            case_detail_resp = client.get(f"/api/case-detail/{case_id}")
            if case_detail_resp.status_code == 404:
                legacy_payload = _legacy_case_payload(player_id, legacy_docs_root)
                if not legacy_payload:
                    raise RuntimeError(f"GET /api/case-detail/{case_id} failed: 404 and no legacy doc found")
                case_detail = legacy_payload["case_detail"]
                case_file = legacy_payload["case_file"]
                case_file["case_detail"] = case_detail
                _write_json(out / "case-detail" / f"{case_id}.json", case_detail)
                _write_json(out / "case-file" / f"{player_id}.json", case_file)
                _write_json(out / "cases" / "timeline" / f"{player_id}.json", legacy_payload["timeline"])
                _write_json(out / "cases" / "query-log" / f"{player_id}.json", legacy_payload["query_logs"])
                _write_json(out / "ai" / "logs" / f"{player_id}.json", case_file["prompt_logs"])
                _write_json(out / "interventions" / "notes" / f"{player_id}.json", legacy_payload["notes"])
                _write_json(out / "interventions" / "notes-draft" / f"{player_id}.json", None)
                _write_json(out / "interventions" / "nudge" / f"{player_id}.json", legacy_payload["nudge"])
                _write_json(out / "cases" / "trigger-check" / f"{player_id}.json", legacy_payload["trigger_checks"])

                case_status.append(
                    {
                        "case_id": legacy_payload["case_id"],
                        "player_id": player_id,
                        "analyst_id": "Colby Reichenbach",
                        "status": "SUBMITTED",
                        "started_at": (
                            datetime.fromisoformat(legacy_payload["notes"]["created_at"]) - timedelta(minutes=50)
                        ).isoformat(sep=" "),
                        "submitted_at": legacy_payload["notes"]["created_at"],
                        "updated_at": legacy_payload["notes"]["created_at"],
                    }
                )
                audit_trail.append(
                    {
                        "audit_id": legacy_payload["case_id"],
                        "case_id": legacy_payload["case_id"],
                        "player_id": player_id,
                        "analyst_id": "Colby Reichenbach",
                        "action": legacy_payload["notes"]["analyst_action"],
                        "risk_category": legacy_payload["risk_category"],
                        "state_jurisdiction": legacy_payload["state"],
                        "timestamp": legacy_payload["notes"]["created_at"],
                        "notes": legacy_payload["notes"]["analyst_notes"],
                        "nudge_status": "PASS",
                        "nudge_excerpt": legacy_payload["nudge"]["final_nudge"][:80] + (
                            "…" if len(legacy_payload["nudge"]["final_nudge"]) > 80 else ""
                        ),
                    }
                )
                continue
            if case_detail_resp.status_code >= 400:
                raise RuntimeError(
                    f"GET /api/case-detail/{case_id} failed: {case_detail_resp.status_code} {case_detail_resp.text}"
                )
            case_detail = case_detail_resp.json()
            _write_json(out / "case-detail" / f"{case_id}.json", case_detail)

            case_file = _get(client, f"/api/case-file/{player_id}")
            _write_json(out / "case-file" / f"{player_id}.json", case_file)

            timeline = _get(client, f"/api/cases/timeline/{player_id}")
            _write_json(out / "cases" / "timeline" / f"{player_id}.json", timeline)

            query_log = _get(client, f"/api/cases/query-log/{player_id}")
            _write_json(out / "cases" / "query-log" / f"{player_id}.json", query_log)

            prompt_logs = _get(client, f"/api/ai/logs/{player_id}")
            _write_json(out / "ai" / "logs" / f"{player_id}.json", prompt_logs)

            notes_resp = client.get(f"/api/interventions/notes/{player_id}")
            if notes_resp.status_code == 404:
                _write_json(out / "interventions" / "notes" / f"{player_id}.json", None)
            else:
                _write_json(out / "interventions" / "notes" / f"{player_id}.json", notes_resp.json())

            draft_resp = client.get(f"/api/interventions/notes-draft/{player_id}")
            if draft_resp.status_code == 404:
                _write_json(out / "interventions" / "notes-draft" / f"{player_id}.json", None)
            else:
                _write_json(out / "interventions" / "notes-draft" / f"{player_id}.json", draft_resp.json())

            nudge_resp = client.get(f"/api/interventions/nudge/{player_id}")
            if nudge_resp.status_code == 404:
                _write_json(out / "interventions" / "nudge" / f"{player_id}.json", None)
            else:
                _write_json(out / "interventions" / "nudge" / f"{player_id}.json", nudge_resp.json())

            trigger_checks = _post(client, f"/api/cases/trigger-check/{player_id}")
            _write_json(out / "cases" / "trigger-check" / f"{player_id}.json", trigger_checks)

        dedup_status = {}
        for row in case_status:
            dedup_status[row["case_id"]] = row
        dedup_audit = {}
        for row in audit_trail:
            dedup_audit[row["case_id"]] = row
        case_status = sorted(dedup_status.values(), key=lambda row: row["updated_at"], reverse=True)
        audit_trail = sorted(dedup_audit.values(), key=lambda row: row["timestamp"], reverse=True)
        _write_json(out / "audit-trail.json", audit_trail)
        _write_json(out / "cases" / "status.json", case_status)

    print(f"Exported static demo fixtures to: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export static frontend demo fixtures.")
    parser.add_argument("--db-path", default="data/dk_sentinel.duckdb")
    parser.add_argument("--output-dir", default="frontend/public/demo")
    parser.add_argument("--manifest-path", default="docs/case_reviews/CASE_MANIFEST.json")
    parser.add_argument("--queue-cap", type=int, default=12)
    args = parser.parse_args()

    export_demo_json(
        db_path=args.db_path,
        output_dir=args.output_dir,
        manifest_path=args.manifest_path,
        queue_cap=args.queue_cap,
    )


if __name__ == "__main__":
    main()
