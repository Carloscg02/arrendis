import pytest

from backend.domain.entities import Expense, Income, Property
from backend.domain.ports import ExpenseRepository, IncomeRepository, PropertyRepository


class InMemoryPropertyRepository(PropertyRepository):
    """Implementación in-memory de PropertyRepository para tests unitarios."""

    def __init__(self) -> None:
        self._store: dict[str, Property] = {}

    def save(self, property: Property) -> None:
        self._store[property.id] = property

    def find_by_id(self, property_id: str) -> Property | None:
        return self._store.get(property_id)

    def find_by_name(self, name: str) -> Property | None:
        for p in self._store.values():
            if p.name == name:
                return p
        return None

    def find_all(self) -> list[Property]:
        return list(self._store.values())

    def delete(self, property_id: str) -> None:
        self._store.pop(property_id, None)

    def update_image(self, property_id: str, image_filename: str | None) -> None:
        for prop in self._store.values():
            if prop.id == property_id:
                prop.image_filename = image_filename
                return


class InMemoryIncomeRepository(IncomeRepository):
    """Implementación in-memory de IncomeRepository para tests unitarios."""

    def __init__(self) -> None:
        self._store: dict[str, Income] = {}

    def save(self, income: Income) -> None:
        self._store[income.id] = income

    def find_by_property_id(self, property_id: str) -> list[Income]:
        return [i for i in self._store.values() if i.property_id == property_id]

    def delete(self, income_id: str) -> None:
        self._store.pop(income_id, None)


class InMemoryExpenseRepository(ExpenseRepository):
    """Implementación in-memory de ExpenseRepository para tests unitarios."""

    def __init__(self) -> None:
        self._store: dict[str, Expense] = {}

    def save(self, expense: Expense) -> None:
        self._store[expense.id] = expense

    def find_by_property_id(self, property_id: str) -> list[Expense]:
        return [e for e in self._store.values() if e.property_id == property_id]

    def delete(self, expense_id: str) -> None:
        self._store.pop(expense_id, None)


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
