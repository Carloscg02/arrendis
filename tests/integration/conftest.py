import os
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

os.environ["TESTING"] = "1"

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.main import app
from backend.api.dependencies import get_db

@pytest.fixture
def sqlite_connection():
    """Retorna una conexión SQLite :memory: efímera y la cierra al finalizar."""
    conn = SQLiteConnection(db_path=":memory:")
    yield conn
    conn.close()

@pytest.fixture
def e2e_client(tmp_path, monkeypatch):
    """Proporciona un TestClient E2E aislado con BD en memoria y directorio de imágenes temporal."""
    test_db = SQLiteConnection(":memory:")
    app.dependency_overrides[get_db] = lambda: test_db

    # Isolate image upload directory to tmp_path
    monkeypatch.setattr("backend.api.routes.properties.Path", lambda p: tmp_path if p == "data/images" else Path(p))

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    test_db.close()
