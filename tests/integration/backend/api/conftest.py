import pytest
from fastapi.testclient import TestClient

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.main import app
from backend.api.dependencies import get_db

@pytest.fixture
def client():
    """Provides a TestClient for the API with an in-memory database."""
    test_db = SQLiteConnection(":memory:")
    
    # Override the dependency to use our in-memory DB
    app.dependency_overrides[get_db] = lambda: test_db
    
    with TestClient(app) as c:
        yield c
        
    # Teardown
    app.dependency_overrides.clear()
    test_db.close()
