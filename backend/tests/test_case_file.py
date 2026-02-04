from backend.db.duckdb_client import execute


def test_query_draft_requires_llm_key(client):
    payload = {
        "player_id": "PLR_5678_NJ",
        "analyst_prompt": "Show the last 30 bets for this player."
    }
    response = client.post("/api/ai/query-draft", json=payload)
    assert response.status_code == 503


def test_query_log_create_and_fetch(client):
    payload = {
        "player_id": "PLR_5678_NJ",
        "analyst_id": "Colby Reichenbach",
        "prompt_text": "Show last 30 bets",
        "draft_sql": "SELECT bet_id FROM STAGING.STG_BET_LOGS LIMIT 30",
        "final_sql": "SELECT bet_id FROM STAGING.STG_BET_LOGS LIMIT 30",
        "purpose": "Review latest betting activity",
        "result_summary": "Retrieved 30 recent bets"
    }

    response = client.post("/api/cases/query-log", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == payload["player_id"]

    get_response = client.get("/api/cases/query-log/PLR_5678_NJ")
    assert get_response.status_code == 200
    rows = get_response.json()
    assert len(rows) == 1
    assert rows[0]["purpose"] == payload["purpose"]


def test_case_timeline_merges_events(client):
    execute(
        """
        INSERT INTO rg_analyst_notes_log (log_id, player_id, analyst_id, analyst_action, analyst_notes, created_at)
        VALUES ('log-2', 'PLR_7777_MA', 'Colby Reichenbach', 'Monitor', 'Notes', '2026-02-04T10:00:00Z')
        """
    )
    execute(
        """
        INSERT INTO rg_llm_prompt_log (log_id, player_id, analyst_id, prompt_text, response_text, created_at)
        VALUES ('log-3', 'PLR_7777_MA', 'Colby Reichenbach', 'prompt', 'response', '2026-02-04T10:05:00Z')
        """
    )
    execute(
        """
        INSERT INTO rg_query_log (log_id, player_id, analyst_id, prompt_text, draft_sql, final_sql, purpose, result_summary, created_at)
        VALUES (
            'log-4',
            'PLR_7777_MA',
            'Colby Reichenbach',
            'prompt',
            'SELECT 1',
            'SELECT 1',
            'Check bets',
            'Summary',
            '2026-02-04T10:10:00Z'
        )
        """
    )

    response = client.get("/api/cases/timeline/PLR_7777_MA")
    assert response.status_code == 200
    timeline = response.json()
    event_types = {entry["event_type"] for entry in timeline}
    assert "Analyst note" in event_types
    assert "AI draft" in event_types
    assert "SQL query" in event_types


def test_case_status_start_and_submit(client):
    payload = {
        "case_id": "CASE-9001",
        "player_id": "PLR_1111_MA",
        "analyst_id": "Colby Reichenbach"
    }

    start_resp = client.post("/api/cases/start", json=payload)
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["status"] == "IN_PROGRESS"

    submit_resp = client.post("/api/cases/submit", json=payload)
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert submit_data["status"] == "SUBMITTED"

    status_resp = client.get("/api/cases/status")
    assert status_resp.status_code == 200
    rows = status_resp.json()
    assert any(row["case_id"] == "CASE-9001" for row in rows)
