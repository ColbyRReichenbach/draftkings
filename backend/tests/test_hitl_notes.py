from backend.db.duckdb_client import execute


def test_submit_and_get_notes(client):
    payload = {
        "player_id": "PLR_1234_MA",
        "analyst_id": "Colby Reichenbach",
        "analyst_action": "Monitor",
        "analyst_notes": "Reviewed betting activity; monitoring for escalation."
    }

    response = client.post("/api/interventions/notes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == payload["player_id"]
    assert data["analyst_action"] == payload["analyst_action"]

    get_response = client.get("/api/interventions/notes/PLR_1234_MA")
    assert get_response.status_code == 200
    latest = get_response.json()
    assert latest["analyst_notes"] == payload["analyst_notes"]


def test_ai_endpoints_disabled_without_key(client):
    payload = {
        "player_id": "PLR_1234_MA",
        "composite_risk_score": 0.72
    }
    response = client.post("/api/ai/semantic-audit", json=payload)
    assert response.status_code == 503


def test_prompt_logs_endpoint(client):
    execute(
        """
        INSERT INTO rg_llm_prompt_log (log_id, player_id, analyst_id, prompt_text, response_text, created_at)
        VALUES ('log-1', 'PLR_9999_NJ', 'Colby Reichenbach', 'prompt', 'response', '2026-02-04T00:00:00Z')
        """
    )

    response = client.get("/api/ai/logs/PLR_9999_NJ")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["player_id"] == "PLR_9999_NJ"
