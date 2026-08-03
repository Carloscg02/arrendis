import os
import pytest

os.environ["TESTING"] = "1"

from backend.adapters.sqlite_adapter import SQLiteConnection


@pytest.fixture
def sqlite_connection():
    """Retorna una conexión SQLite :memory: y la cierra al finalizar."""
    conn = SQLiteConnection(db_path=":memory:")
    yield conn
    conn.close()
