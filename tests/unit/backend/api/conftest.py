import pytest
from fastapi.testclient import TestClient

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.main import app
from backend.api.dependencies import get_db, get_current_user
from backend.domain.entities import User
from backend.domain.value_objects import Email, PasswordHash

@pytest.fixture
def auth_user():
    return User(
        email=Email("test@example.com"),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="testuser",
        id="user-1",
    )

@pytest.fixture
def client(auth_user):
    """Provides a TestClient for the API with an in-memory database."""
    test_db = SQLiteConnection(":memory:")
    
    # Override the dependency to use our in-memory DB
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_current_user] = lambda: auth_user
    
    with TestClient(app) as c:
        yield c
        
    # Teardown
    app.dependency_overrides.clear()
    test_db.close()
