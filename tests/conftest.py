"""
Fixtures compartidos para todos los tests de F-01.

Incluye repositorios in-memory (dict) y conexión SQLite :memory:.
"""

from __future__ import annotations

import pytest

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.domain.entities import Expense, Income, Property
from backend.domain.ports import ExpenseRepository, IncomeRepository, PropertyRepository


# ──────────────────────────────────────────────
# Repositorios In-Memory (implementan los puertos abstractos)
# ──────────────────────────────────────────────

class InMemoryPropertyRepository(PropertyRepository):
    """Implementación in-memory de PropertyRepository para tests."""

    def __init__(self) -> None:
        self._store: dict[str, Property] = {}

    def save(self, property: Property) -> None:
        self._store[property.id] = property

    def find_by_id(self, property_id: str) -> Property | None:
        return self._store.get(property_id)

    def find_all(self) -> list[Property]:
        return list(self._store.values())

    def delete(self, property_id: str) -> None:
        self._store.pop(property_id, None)


class InMemoryIncomeRepository(IncomeRepository):
    """Implementación in-memory de IncomeRepository para tests."""

    def __init__(self) -> None:
        self._store: dict[str, Income] = {}

    def save(self, income: Income) -> None:
        self._store[income.id] = income

    def find_by_property_id(self, property_id: str) -> list[Income]:
        return [i for i in self._store.values() if i.property_id == property_id]

    def delete(self, income_id: str) -> None:
        self._store.pop(income_id, None)


class InMemoryExpenseRepository(ExpenseRepository):
    """Implementación in-memory de ExpenseRepository para tests."""

    def __init__(self) -> None:
        self._store: dict[str, Expense] = {}

    def save(self, expense: Expense) -> None:
        self._store[expense.id] = expense

    def find_by_property_id(self, property_id: str) -> list[Expense]:
        return [e for e in self._store.values() if e.property_id == property_id]

    def delete(self, expense_id: str) -> None:
        self._store.pop(expense_id, None)


# ──────────────────────────────────────────────
# Fixtures de pytest
# ──────────────────────────────────────────────

@pytest.fixture
def property_repo() -> InMemoryPropertyRepository:
    """Retorna un repositorio de propiedades in-memory limpio."""
    return InMemoryPropertyRepository()


@pytest.fixture
def income_repo() -> InMemoryIncomeRepository:
    """Retorna un repositorio de ingresos in-memory limpio."""
    return InMemoryIncomeRepository()


@pytest.fixture
def expense_repo() -> InMemoryExpenseRepository:
    """Retorna un repositorio de gastos in-memory limpio."""
    return InMemoryExpenseRepository()


@pytest.fixture
def sqlite_connection():
    """Retorna una conexión SQLite :memory: y la cierra al finalizar."""
    conn = SQLiteConnection(db_path=":memory:")
    yield conn
    conn.close()
