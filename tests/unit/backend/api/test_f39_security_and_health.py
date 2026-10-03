"""
Tests unitarios y de integración para F-39:
Cabeceras HTTP de Seguridad, Cookies Seguras de Producción y Endpoint de Salud.
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.main import app
from backend.api.dependencies import get_db


@pytest.fixture
def client():
    # Aseguramos BD en memoria para tests
    db = SQLiteConnection(":memory:")
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    db.close()


def test_sqlite_connection_check_health():
    """Verifica que el método check_health() del adaptador SQLite responde True si la BD está sana."""
    db = SQLiteConnection(":memory:")
    assert db.check_health() is True
    db.close()


def test_security_headers_present_on_200_ok(client: TestClient):
    """Verifica que toda respuesta 200 OK contiene las cabeceras HTTP de seguridad OWASP."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers.get("Permissions-Policy", "")


def test_security_headers_present_on_404_error(client: TestClient):
    """Verifica que las cabeceras de seguridad se inyectan también en respuestas de error 404."""
    response = client.get("/api/ruta_completamente_inexistente_12345")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_hsts_header_in_production_environment(client: TestClient):
    """Verifica que HSTS solo se inyecta en producción o con FORCE_HSTS=1."""
    # En desarrollo / test no debe aparecer
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "FORCE_HSTS": "0"}):
        res_dev = client.get("/api/health")
        assert "Strict-Transport-Security" not in res_dev.headers

    # Con FORCE_HSTS="1" debe aparecer
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "FORCE_HSTS": "1"}):
        res_hsts = client.get("/api/health")
        assert res_hsts.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"

    # En entorno producción debe aparecer
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        res_prod = client.get("/api/health")
        assert res_prod.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"


def test_health_endpoint_healthy_without_auth(client: TestClient):
    """Verifica que /api/health es accesible públicamente sin token y retorna 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["version"] == "0.1.0"


def test_health_endpoint_degraded_when_db_fails(client: TestClient):
    """Verifica que /api/health retorna 503 Service Unavailable si la BD falla."""
    with patch.object(SQLiteConnection, "check_health", return_value=False):
        response = client.get("/api/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"
        assert "Database connectivity check failed" in data["error"]


def test_auth_cookie_secure_dev_vs_prod(client: TestClient):
    """Verifica que la cookie refresh_token lleva el flag Secure según el entorno."""
    user_payload = {
        "email": "seguridad@arrendis.com",
        "username": "seguridad_user",
        "password": "Password123!",
    }

    # En entorno dev / test -> secure=False (no lleva directiva Secure)
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "COOKIE_SECURE": "0"}):
        res_dev = client.post("/api/auth/register", json=user_payload)
        assert res_dev.status_code == 201
        cookie_dev = res_dev.headers.get("set-cookie", "")
        assert "refresh_token=" in cookie_dev
        assert "HttpOnly" in cookie_dev
        assert "Secure" not in cookie_dev

    # Login con COOKIE_SECURE=true -> secure=True (lleva directiva Secure)
    with patch.dict(os.environ, {"ENVIRONMENT": "production", "COOKIE_SECURE": "1"}):
        res_prod = client.post(
            "/api/auth/login",
            json={"email": "seguridad@arrendis.com", "password": "Password123!"},
        )
        assert res_prod.status_code == 200
        cookie_prod = res_prod.headers.get("set-cookie", "")
        assert "refresh_token=" in cookie_prod
        assert "Secure" in cookie_prod
        assert "HttpOnly" in cookie_prod


def test_auth_logout_cookie_attributes(client: TestClient):
    """Verifica que /api/auth/logout invalida la cookie con las opciones de seguridad adecuadas."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json() == {"message": "Sesión cerrada"}
        cookie = response.headers.get("set-cookie", "")
        assert "refresh_token=" in cookie
        assert "Secure" in cookie
        assert "HttpOnly" in cookie
        assert "Path=/api/auth" in cookie or "path=/api/auth" in cookie
