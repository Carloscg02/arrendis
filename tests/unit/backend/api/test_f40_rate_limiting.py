"""
Tests unitarios y de integración para F-40:
Protección contra Fuerza Bruta y Rate Limiting en Endpoints de Autenticación.
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.main import app
from backend.api.dependencies import get_db
from backend.api.middleware.rate_limit import InMemoryRateLimiter, default_rate_limiter


@pytest.fixture
def client():
    db = SQLiteConnection(":memory:")
    app.dependency_overrides[get_db] = lambda: db
    default_rate_limiter.reset()
    with TestClient(app) as c:
        yield c
    default_rate_limiter.reset()
    app.dependency_overrides.clear()
    db.close()


def test_in_memory_rate_limiter_allows_under_limit():
    """Verifica que hasta 10 peticiones dentro de la ventana de 60s son permitidas."""
    limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
    for _ in range(10):
        is_limited, retry_after = limiter.is_rate_limited("192.168.1.1", now=1000.0)
        assert is_limited is False
        assert retry_after == 0


def test_in_memory_rate_limiter_blocks_11th_attempt():
    """Verifica que el 11º intento es bloqueado con retry_after positivo."""
    limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
    for i in range(10):
        limiter.is_rate_limited("192.168.1.1", now=1000.0 + i)

    is_limited, retry_after = limiter.is_rate_limited("192.168.1.1", now=1010.0)
    assert is_limited is True
    assert retry_after > 0
    assert retry_after <= 60


def test_in_memory_rate_limiter_resets_after_window_expires():
    """Verifica que tras pasar la ventana (60s), el cupo se restablece."""
    limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
    for i in range(10):
        limiter.is_rate_limited("192.168.1.1", now=1000.0 + i)

    # 11º intento bloqueado en t=1015
    is_limited, _ = limiter.is_rate_limited("192.168.1.1", now=1015.0)
    assert is_limited is True

    # Petición en t=1061 (más de 60s tras el primer intento en 1000)
    is_limited, retry_after = limiter.is_rate_limited("192.168.1.1", now=1061.0)
    assert is_limited is False
    assert retry_after == 0


def test_in_memory_rate_limiter_memory_eviction():
    """Verifica que el almacén desaloja claves al superar max_keys para evitar fugas de memoria."""
    max_keys = 5
    limiter = InMemoryRateLimiter(limit=5, window_seconds=60, max_keys=max_keys)

    # Insertar 10 IPs distintas
    for i in range(10):
        limiter.is_rate_limited(f"10.0.0.{i}", now=1000.0)

    # El tamaño no debe exceder max_keys
    assert len(limiter._records) <= max_keys


def test_in_memory_rate_limiter_reset():
    """Verifica que reset() vacía el almacén."""
    limiter = InMemoryRateLimiter(limit=5, window_seconds=60)
    limiter.is_rate_limited("1.2.3.4", now=1000.0)
    assert len(limiter._records) == 1
    limiter.reset()
    assert len(limiter._records) == 0


def test_auth_login_rate_limiting_http_429(client: TestClient):
    """Verifica que POST /api/auth/login devuelve 429 al superar 10 intentos y cabeceras de seguridad."""
    with patch.dict(os.environ, {"FORCE_RATE_LIMIT": "1"}):
        default_rate_limiter.reset()
        login_payload = {"email": "test@arrendis.com", "password": "WrongPassword123!"}

        # 10 intentos fallidos (401 Unauthorized)
        for _ in range(10):
            res = client.post("/api/auth/login", json=login_payload)
            assert res.status_code == 401

        # El intento 11 debe ser 429 Too Many Requests
        res_blocked = client.post("/api/auth/login", json=login_payload)
        assert res_blocked.status_code == 429
        assert "Retry-After" in res_blocked.headers
        assert int(res_blocked.headers["Retry-After"]) >= 1

        # Verificar cabeceras de seguridad inyectadas en 429
        assert res_blocked.headers.get("X-Content-Type-Options") == "nosniff"
        assert res_blocked.headers.get("X-Frame-Options") == "DENY"

        data = res_blocked.json()
        assert "Demasiados intentos de autenticación" in data["detail"]
        assert data["retry_after"] >= 1


def test_auth_register_rate_limiting_http_429(client: TestClient):
    """Verifica que POST /api/auth/register también aplica rate limiting de 10 peticiones/min."""
    with patch.dict(os.environ, {"FORCE_RATE_LIMIT": "1"}):
        default_rate_limiter.reset()
        register_payload = {
            "email": "invalid-email-format",
            "username": "u",
            "password": "p",
        }

        # 10 peticiones (responderán 400 por validación de email)
        for _ in range(10):
            res = client.post("/api/auth/register", json=register_payload)
            assert res.status_code == 400

        # La 11ª debe ser 429
        res_blocked = client.post("/api/auth/register", json=register_payload)
        assert res_blocked.status_code == 429
        assert "Retry-After" in res_blocked.headers


def test_unprotected_routes_not_rate_limited(client: TestClient):
    """Verifica que rutas no autenticadas o no críticas (ej: /api/health) NO sufren rate limiting."""
    with patch.dict(os.environ, {"FORCE_RATE_LIMIT": "1"}):
        default_rate_limiter.reset()
        for _ in range(15):
            res = client.get("/api/health")
            assert res.status_code == 200


def test_x_forwarded_for_ip_tracking(client: TestClient):
    """Verifica que se rastrea la IP real del cliente usando la cabecera X-Forwarded-For."""
    with patch.dict(os.environ, {"FORCE_RATE_LIMIT": "1"}):
        default_rate_limiter.reset()
        ip_victim = "203.0.113.50"
        ip_other = "198.51.100.77"

        # Agotar cuota para ip_victim
        for _ in range(10):
            res = client.post(
                "/api/auth/login",
                json={"email": "a@b.com", "password": "x"},
                headers={"X-Forwarded-For": f"{ip_victim}, 10.0.0.1"},
            )
            assert res.status_code == 401

        # ip_victim debe estar bloqueada
        res_blocked = client.post(
            "/api/auth/login",
            json={"email": "a@b.com", "password": "x"},
            headers={"X-Forwarded-For": f"{ip_victim}, 10.0.0.1"},
        )
        assert res_blocked.status_code == 429

        # ip_other NO debe estar bloqueada
        res_other = client.post(
            "/api/auth/login",
            json={"email": "a@b.com", "password": "x"},
            headers={"X-Forwarded-For": f"{ip_other}, 10.0.0.1"},
        )
        assert res_other.status_code == 401
