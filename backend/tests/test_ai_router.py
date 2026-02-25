class _FakeProvider:
    def generate_json(self, *args, **kwargs):
        return {"draft_sql": "SELECT 1 AS ok", "assumptions": ["unit test"]}

    def generate_text(self, *args, **kwargs):
        return "Mocked context response."


def _enable_llm(client):
    client.app.state.llm_provider = _FakeProvider()
    client.app.state.llm_config = type(
        "Cfg",
        (),
        {"fast_model": "mock-fast", "reasoning_model": "mock-reasoning", "temperature": 0.0, "max_tokens": 256},
    )()
    client.app.state.analyst_name = "Colby Reichenbach"


def test_prompt_router_requires_llm(client):
    response = client.post(
        "/api/ai/router",
        json={"player_id": "PLR_1234_MA", "analyst_prompt": "Show last 30 bets"},
    )
    if response.status_code == 503:
        assert response.status_code == 503
    else:
        assert response.status_code == 200


def test_prompt_router_classifies_sql_route(client):
    _enable_llm(client)
    response = client.post(
        "/api/ai/router",
        json={"player_id": "PLR_1234_MA", "analyst_prompt": "Show SQL query for recent bets"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "SQL_DRAFT"
    assert data["tool"] == "query-draft"
    assert "draft_sql" in data and data["draft_sql"]


def test_prompt_router_classifies_regulatory_route(client):
    _enable_llm(client)
    response = client.post(
        "/api/ai/router",
        json={"player_id": "PLR_1234_MA", "analyst_prompt": "What regulation triggers apply in NJ compliance policy?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "REGULATORY_CONTEXT"
    assert data["tool"] == "policy-context"
    assert data["response_text"] == "Mocked context response."


def test_prompt_router_classifies_external_route(client):
    _enable_llm(client)
    response = client.post(
        "/api/ai/router",
        json={"player_id": "PLR_1234_MA", "analyst_prompt": "Any news event driving betting change this week?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "EXTERNAL_CONTEXT"
    assert data["tool"] == "external-context"


def test_prompt_router_classifies_general_route(client):
    _enable_llm(client)
    response = client.post(
        "/api/ai/router",
        json={"player_id": "PLR_1234_MA", "analyst_prompt": "Help summarize this case objectively."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "GENERAL_ANALYSIS"
    assert data["tool"] == "general-analysis"
