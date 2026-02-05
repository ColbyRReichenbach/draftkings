import os
from datetime import datetime, timedelta

import duckdb


def _seed_trigger_tables(db_path: str, player_id: str, state: str) -> None:
    conn = duckdb.connect(db_path)
    conn.execute(
        """
        CREATE TABLE STG_PLAYER_PROFILES (
            player_id VARCHAR,
            state_jurisdiction VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE STG_BET_LOGS (
            player_id VARCHAR,
            bet_amount DOUBLE,
            bet_timestamp TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE RG_RISK_SCORES (
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
        "INSERT INTO STG_PLAYER_PROFILES VALUES (?, ?)",
        (player_id, state),
    )

    now = datetime.utcnow()
    conn.execute(
        "INSERT INTO STG_BET_LOGS VALUES (?, ?, ?)",
        (player_id, 12.0, now - timedelta(days=40)),
    )
    conn.execute(
        "INSERT INTO STG_BET_LOGS VALUES (?, ?, ?)",
        (player_id, 140.0, now - timedelta(days=2)),
    )
    conn.execute(
        "INSERT INTO RG_RISK_SCORES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (player_id, 0.8, "HIGH", now - timedelta(days=5), 0.7, 0.6, 0.5, 0.4, 0.3),
    )
    conn.close()


def test_sql_execute_guardrails(client):
    payload = {"player_id": "PLR_1000_MA", "sql_text": "SELECT 1 AS ok", "purpose": "Test query"}
    response = client.post("/api/sql/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 1
    assert data["columns"] == ["ok"]

    bad_response = client.post(
        "/api/sql/execute",
        json={"player_id": "PLR_1000_MA", "sql_text": "DROP TABLE x", "purpose": "Bad query"},
    )
    assert bad_response.status_code == 400


def test_trigger_check_ma(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2000_MA"
    _seed_trigger_tables(db_path, player_id, "MA")

    response = client.post(f"/api/cases/trigger-check/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["state"] == "MA"
