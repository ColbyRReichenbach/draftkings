import json
from pathlib import Path

import pytest


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_demo_fixture_contract():
    root = Path(__file__).resolve().parents[1]
    demo = root / "frontend" / "public" / "demo"
    if not demo.exists():
        pytest.skip("Static demo fixtures not present in this environment.")

    required = [
        demo / "queue.json",
        demo / "audit-trail.json",
        demo / "analytics-summary.json",
        demo / "cases" / "status.json",
    ]
    for path in required:
        assert path.exists(), f"Missing fixture: {path}"

    queue = _read_json(demo / "queue.json")
    assert isinstance(queue, list)
    assert len(queue) > 0
    queue_expected = {
        "case_id",
        "player_id",
        "risk_category",
        "composite_risk_score",
        "score_calculated_at",
        "state_jurisdiction",
        "key_evidence",
    }
    assert queue_expected.issubset(set(queue[0].keys()))

    player_id = queue[0]["player_id"]

    case_file = _read_json(demo / "case-file" / f"{player_id}.json")
    case_file_expected = {"case_detail", "latest_note", "prompt_logs", "query_logs", "timeline", "trigger_checks"}
    assert case_file_expected.issubset(set(case_file.keys()))

    timeline = _read_json(demo / "cases" / "timeline" / f"{player_id}.json")
    assert isinstance(timeline, list)

    query_log = _read_json(demo / "cases" / "query-log" / f"{player_id}.json")
    assert isinstance(query_log, list)

    trigger = _read_json(demo / "cases" / "trigger-check" / f"{player_id}.json")
    assert isinstance(trigger, list)
