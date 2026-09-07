"""Tests de integración del endpoint /api/llm/health (T-17-16 a T-17-18)."""

import pytest
from fastapi.testclient import TestClient

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.main import app
from backend.api.dependencies import get_db, get_current_user, get_llm_provider


# T-17-16: No LLM configured → 200, status "not_configured"
def test_llm_api_health_not_configured(client, auth_user, token_service):
    app.dependency_overrides[get_llm_provider] = lambda: None

    token = token_service.create_access_token(auth_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/llm/health", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_configured"
    assert data["model"] is None
    assert data["message"] is None

    del app.dependency_overrides[get_llm_provider]


# T-17-17: Mock LLM → 200, status "ok", model name present
def test_llm_api_health_ok(client, auth_user, token_service, fake_llm):
    app.dependency_overrides[get_llm_provider] = lambda: fake_llm

    token = token_service.create_access_token(auth_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/llm/health", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "fake-model"
    assert data["message"] is None

    del app.dependency_overrides[get_llm_provider]


# T-17-18: No auth token → 401
def test_llm_api_health_unauthorized():
    """Sin token de autenticación, el endpoint debe devolver 401."""
    test_db = SQLiteConnection(":memory:")
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_llm_provider] = lambda: None
    # Crucially, do NOT override get_current_user — let the real auth check run
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as c:
        response = c.get("/api/llm/health")

    assert response.status_code == 401

    app.dependency_overrides.clear()
    test_db.close()
