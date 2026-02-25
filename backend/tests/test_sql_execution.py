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


def test_sql_execute_blocks_pii_columns(client):
    response = client.post(
        "/api/sql/execute",
        json={
            "player_id": "PLR_1000_MA",
            "sql_text": "SELECT first_name FROM STAGING.STG_PLAYER_PROFILES",
            "purpose": "PII access attempt",
        },
    )
    assert response.status_code == 400
    assert "PII column" in response.text


def test_trigger_check_ma(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2000_MA"
    _seed_trigger_tables(db_path, player_id, "MA")

    response = client.post(f"/api/cases/trigger-check/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["state"] == "MA"


def test_trigger_check_cache_and_force(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2111_MA"
    _seed_trigger_tables(db_path, player_id, "MA")

    first = client.post(f"/api/cases/trigger-check/{player_id}")
    assert first.status_code == 200

    second = client.post(f"/api/cases/trigger-check/{player_id}")
    assert second.status_code == 200

    conn = duckdb.connect(db_path)
    cached_count = conn.execute(
        "SELECT COUNT(*) FROM rg_trigger_check_log WHERE player_id = ?",
        (player_id,),
    ).fetchone()[0]
    assert cached_count == 1

    forced = client.post(f"/api/cases/trigger-check/{player_id}?force=true")
    assert forced.status_code == 200

    forced_count = conn.execute(
        "SELECT COUNT(*) FROM rg_trigger_check_log WHERE player_id = ?",
        (player_id,),
    ).fetchone()[0]
    conn.close()
    assert forced_count == 2


def test_trigger_check_nj_triggered(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2222_NJ"
    _seed_trigger_tables(db_path, player_id, "NJ")

    conn = duckdb.connect(db_path)
    now = datetime.utcnow()
    conn.execute(
        "INSERT INTO RG_RISK_SCORES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (player_id, 0.9, "CRITICAL", now - timedelta(days=3), 0.8, 0.8, 0.8, 0.8, 0.8),
    )
    conn.execute(
        "INSERT INTO RG_RISK_SCORES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (player_id, 0.85, "HIGH", now - timedelta(days=1), 0.7, 0.7, 0.7, 0.7, 0.7),
    )
    conn.close()

    response = client.post(f"/api/cases/trigger-check/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["state"] == "NJ"
    assert data[0]["triggered"] is True


def test_trigger_check_pa_not_triggered_default(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2333_PA"
    _seed_trigger_tables(db_path, player_id, "PA")

    response = client.post(f"/api/cases/trigger-check/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["state"] == "PA"
    assert data[0]["triggered"] is False
    assert "Self-exclusion history not available" in data[0]["reason"]


def test_sql_execute_unknown_column_returns_hint(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2444_MA"
    _seed_trigger_tables(db_path, player_id, "MA")

    response = client.post(
        "/api/sql/execute",
        json={
            "player_id": player_id,
            "sql_text": "SELECT nonexistent_col FROM STAGING.STG_BET_LOGS",
            "purpose": "unknown column test",
        },
    )
    assert response.status_code == 400
    assert "Unknown column" in response.text
    assert "Candidate bindings" in response.text or "Did you mean" in response.text


def test_sql_execute_applies_result_row_cap(client):
    db_path = os.environ["DUCKDB_PATH"]
    player_id = "PLR_2555_MA"
    _seed_trigger_tables(db_path, player_id, "MA")

    conn = duckdb.connect(db_path)
    now = datetime.utcnow()
    rows = [(player_id, float(i), now - timedelta(minutes=i)) for i in range(250)]
    conn.executemany("INSERT INTO STG_BET_LOGS VALUES (?, ?, ?)", rows)
    conn.close()

    response = client.post(
        "/api/sql/execute",
        json={
            "player_id": player_id,
            "sql_text": f"SELECT player_id, bet_amount FROM STAGING.STG_BET_LOGS WHERE player_id = '{player_id}'",
            "purpose": "row cap test",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 200
