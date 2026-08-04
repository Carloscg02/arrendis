import pytest
from backend.api.main import app
from backend.api.dependencies import get_current_user

@pytest.fixture(autouse=True)
def unmock_auth(client):
    app.dependency_overrides.pop(get_current_user, None)
    yield

def _register_user(client, email="test@example.com", username="testuser", password="password123"):
    return client.post("/api/auth/register", json={
        "email": email, "username": username, "password": password
    })

def test_register_success(client):
    res = _register_user(client)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["username"] == "testuser"
    # Check refresh cookie is set
    assert "refresh_token" in res.cookies

def test_register_duplicate_email(client):
    _register_user(client)
    res = _register_user(client)  # same email again
    assert res.status_code == 400

def test_login_success(client):
    _register_user(client)
    res = client.post("/api/auth/login", json={
        "email": "test@example.com", "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"

def test_login_wrong_password(client):
    _register_user(client)
    res = client.post("/api/auth/login", json={
        "email": "test@example.com", "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_refresh_success(client):
    reg = _register_user(client)
    # The refresh cookie should be set
    res = client.post("/api/auth/refresh")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

def test_refresh_no_cookie(client):
    # Fresh client, no cookie
    res = client.post("/api/auth/refresh")
    assert res.status_code == 401

def test_me_authenticated(client):
    reg = _register_user(client)
    token = reg.json()["access_token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"

def test_me_no_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

def test_logout(client):
    _register_user(client)
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    assert res.json()["message"] == "Sesión cerrada"
