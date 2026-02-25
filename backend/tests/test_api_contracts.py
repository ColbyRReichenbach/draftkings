import os
from datetime import datetime, timedelta

import duckdb


def _seed_contract_data(db_path: str) -> str:
    conn = duckdb.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS RG_RISK_SCORES (
            player_id VARCHAR,
            composite_risk_score DOUBLE,
            risk_category VARCHAR,
            calculated_at TIMESTAMP,
            loss_chase_score DOUBLE,
            bet_escalation_score DOUBLE,
            market_drift_score DOUBLE,
            temporal_risk_score DOUBLE,
            gamalyze_risk_score DOUBLE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS STG_PLAYER_PROFILES (
            player_id VARCHAR,
            state_jurisdiction VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS STG_BET_LOGS (
            player_id VARCHAR,
            bet_amount DOUBLE,
            bet_timestamp TIMESTAMP
        )
        """
    )

    player_id = "PLR_8888_MA"
    now = datetime.utcnow()
    conn.execute("INSERT INTO STG_PLAYER_PROFILES VALUES (?, ?)", (player_id, "MA"))
    conn.execute(
        "INSERT INTO RG_RISK_SCORES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (player_id, 0.91, "CRITICAL", now, 0.83, 0.79, 0.58, 0.62, 0.71),
    )
    conn.execute(
        "INSERT INTO STG_BET_LOGS VALUES (?, ?, ?)",
        (player_id, 120.0, now - timedelta(days=2)),
    )
    conn.execute(
        "INSERT INTO STG_BET_LOGS VALUES (?, ?, ?)",
        (player_id, 80.0, now - timedelta(days=20)),
    )
    conn.close()
    return player_id


def test_queue_contract_shape(client):
    db_path = os.environ["DUCKDB_PATH"]
    _seed_contract_data(db_path)

    response = client.get("/api/queue")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    row = data[0]
    expected = {
        "case_id",
        "player_id",
        "risk_category",
        "composite_risk_score",
        "score_calculated_at",
        "state_jurisdiction",
        "key_evidence",
    }
    assert expected.issubset(set(row.keys()))


def test_case_detail_contract_shape(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = _seed_contract_data(db_path)

    response = client.get(f"/api/case-detail/CASE-{player_id}")
    assert response.status_code == 200
    data = response.json()

    expected = {
        "case_id",
        "player_id",
        "risk_category",
        "composite_risk_score",
        "score_calculated_at",
        "state_jurisdiction",
        "evidence_snapshot",
        "ai_explanation",
        "draft_nudge",
        "regulatory_notes",
        "analyst_actions",
    }
    assert expected.issubset(set(data.keys()))
    evidence_expected = {
        "total_bets_7d",
        "total_wagered_7d",
        "loss_chase_score",
        "bet_escalation_score",
        "market_drift_score",
        "temporal_risk_score",
        "gamalyze_risk_score",
    }
    assert evidence_expected.issubset(set(data["evidence_snapshot"].keys()))


def test_case_file_contract_shape(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = _seed_contract_data(db_path)

    response = client.get(f"/api/case-file/{player_id}")
    assert response.status_code == 200
    data = response.json()

    expected = {"case_detail", "latest_note", "prompt_logs", "query_logs", "timeline", "trigger_checks"}
    assert expected.issubset(set(data.keys()))
    assert data["case_detail"]["player_id"] == player_id
    assert isinstance(data["trigger_checks"], list)
