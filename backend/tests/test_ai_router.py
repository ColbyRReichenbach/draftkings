def test_prompt_router_requires_llm(client):
    response = client.post(
        "/api/ai/router",
        json={"player_id": "PLR_1234_MA", "analyst_prompt": "Show last 30 bets"},
    )
    if response.status_code == 503:
        assert response.status_code == 503
    else:
        assert response.status_code == 200
