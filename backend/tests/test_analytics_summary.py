import os

import duckdb


def _seed_risk_table_for_analytics() -> None:
    db_path = os.environ["DUCKDB_PATH"]
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
    conn.close()


def test_analytics_summary_contract(client):
    _seed_risk_table_for_analytics()
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    expected_keys = {
        "total_cases_started",
        "total_cases_submitted",
        "in_progress_count",
        "avg_time_to_submit_hours",
        "avg_time_in_progress_hours",
        "sql_queries_logged",
        "llm_prompts_logged",
        "cases_with_sql_pct",
        "cases_with_llm_pct",
        "risk_mix",
        "trigger_checks_run",
        "nudges_validated",
        "funnel",
    }
    assert expected_keys.issubset(set(data.keys()))

    assert isinstance(data["risk_mix"], dict)
    assert {"critical", "high", "medium", "low"}.issubset(set(data["risk_mix"].keys()))
    assert isinstance(data["funnel"], dict)
    assert {"queued", "started", "submitted"}.issubset(set(data["funnel"].keys()))


def test_analytics_summary_values_are_non_negative(client):
    _seed_risk_table_for_analytics()
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    numeric_fields = [
        "total_cases_started",
        "total_cases_submitted",
        "in_progress_count",
        "avg_time_to_submit_hours",
        "avg_time_in_progress_hours",
        "sql_queries_logged",
        "llm_prompts_logged",
        "cases_with_sql_pct",
        "cases_with_llm_pct",
        "trigger_checks_run",
        "nudges_validated",
    ]
    for field in numeric_fields:
        assert data[field] >= 0
