import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))
    monkeypatch.setenv("ANALYST_NAME", "Colby Reichenbach")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client
