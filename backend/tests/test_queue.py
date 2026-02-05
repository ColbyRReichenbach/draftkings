import os
from datetime import datetime, timedelta

import duckdb


def _seed_queue_data(db_path: str) -> None:
    conn = duckdb.connect(db_path)
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
        """
        CREATE TABLE STG_PLAYER_PROFILES (
            player_id VARCHAR,
            state_jurisdiction VARCHAR
        )
        """
    )

    categories = (
        ("CRITICAL", 10),
        ("HIGH", 20),
        ("MEDIUM", 40),
        ("LOW", 30),
    )
    now = datetime.utcnow()
    player_index = 1
    states = ["NJ", "PA", "MA"]
    for category, count in categories:
        for idx in range(count):
            state = states[player_index % len(states)]
            player_id = f"PLR_{player_index:04d}_{state}"
            score = 0.95 - (idx * 0.005)
            conn.execute(
                """
                INSERT INTO RG_RISK_SCORES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player_id,
                    max(score, 0.1),
                    category,
                    now - timedelta(hours=idx),
                    0.8,
                    0.7,
                    0.6,
                    0.5,
                    0.4,
                ),
            )
            conn.execute(
                """
                INSERT INTO STG_PLAYER_PROFILES VALUES (?, ?)
                """,
                (player_id, state),
            )
            player_index += 1
    conn.close()


def test_queue_refill_and_start_case(client):
    db_path = os.environ["DUCKDB_PATH"]
    _seed_queue_data(db_path)

    response = client.get("/api/queue")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 50

    category_counts = {}
    for row in data:
        category_counts[row["risk_category"]] = category_counts.get(row["risk_category"], 0) + 1

    assert category_counts.get("CRITICAL", 0) >= 6
    assert category_counts.get("HIGH", 0) >= 12
    assert category_counts.get("MEDIUM", 0) >= 20
    assert category_counts.get("LOW", 0) >= 5

    first_case = data[0]
    start_payload = {
        "case_id": first_case["case_id"],
        "player_id": first_case["player_id"],
        "analyst_id": "Colby Reichenbach",
    }
    start_response = client.post("/api/cases/start", json=start_payload)
    assert start_response.status_code == 200

    response_after = client.get("/api/queue")
    assert response_after.status_code == 200
    data_after = response_after.json()
    assert len(data_after) == 49
    assert all(row["case_id"] != first_case["case_id"] for row in data_after)
