"""
Tests de integración para adaptadores SQLite.

DB-01 a DB-06: persistencia real con SQLite :memory:.
"""

from datetime import date
from decimal import Decimal

from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
)
from backend.domain.entities import (
    Expense,
    ExpenseCategory,
    Income,
    IncomeCategory,
    Property,
    PropertyStatus,
    PropertyType,
)
from backend.domain.value_objects import Address, Money


def test_save_and_find_property(sqlite_connection):
    """DB-01: Guardar una propiedad y recuperarla por id."""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Centro",
        address=Address("Calle Mayor 15", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT,
        id="prop-db-001",
    )
    repo.save(prop)
    found = repo.find_by_id("prop-db-001")
    assert found is not None
    assert found.name == "Piso Centro"
    assert found.address.street == "Calle Mayor 15"
    assert found.property_type == PropertyType.APARTMENT
    assert found.status == PropertyStatus.AVAILABLE


def test_find_all_properties(sqlite_connection):
    """DB-02: Guardar 3 propiedades y recuperar todas."""
    repo = SQLitePropertyRepository(sqlite_connection)
    for i in range(3):
        prop = Property(
            name=f"Propiedad {i}",
            address=Address(f"Calle {i}", "Madrid", "28001", "ES"),
            property_type=PropertyType.APARTMENT,
            id=f"prop-db-{i}",
        )
        repo.save(prop)
    all_props = repo.find_all()
    assert len(all_props) == 3


def test_delete_property(sqlite_connection):
    """DB-03: Guardar y eliminar una propiedad."""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Para borrar",
        address=Address("Calle Z", "Barcelona", "08001", "ES"),
        property_type=PropertyType.HOUSE,
        id="prop-delete-001",
    )
    repo.save(prop)
    assert repo.find_by_id("prop-delete-001") is not None
    repo.delete("prop-delete-001")
    assert repo.find_by_id("prop-delete-001") is None


def test_save_and_find_income(sqlite_connection):
    """DB-04: Guardar un ingreso y recuperarlo por property_id."""
    # Primero crear la propiedad (FK)
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Ingresos",
        address=Address("Calle A", "Madrid", "28001", "ES"),
        property_type=PropertyType.APARTMENT,
        id="prop-income-001",
    )
    prop_repo.save(prop)

    # Guardar ingreso
    income_repo = SQLiteIncomeRepository(sqlite_connection)
    income = Income(
        property_id="prop-income-001",
        amount=Money(Decimal("750.00"), "EUR"),
        date=date(2026, 7, 1),
        category=IncomeCategory.RENT,
        description="Alquiler julio",
        id="income-001",
    )
    income_repo.save(income)

    # Recuperar
    found = income_repo.find_by_property_id("prop-income-001")
    assert len(found) == 1
    assert found[0].amount.amount == Decimal("750.00")
    assert found[0].category == IncomeCategory.RENT
    assert found[0].date == date(2026, 7, 1)


def test_save_and_find_expense(sqlite_connection):
    """DB-05: Guardar un gasto y recuperarlo por property_id."""
    # Primero crear la propiedad (FK)
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Gastos",
        address=Address("Calle B", "Sevilla", "41001", "ES"),
        property_type=PropertyType.HOUSE,
        id="prop-expense-001",
    )
    prop_repo.save(prop)

    # Guardar gasto
    expense_repo = SQLiteExpenseRepository(sqlite_connection)
    expense = Expense(
        property_id="prop-expense-001",
        amount=Money(Decimal("200.00"), "EUR"),
        date=date(2026, 7, 5),
        category=ExpenseCategory.REPAIR,
        description="Fontanero",
        id="expense-001",
    )
    expense_repo.save(expense)

    # Recuperar
    found = expense_repo.find_by_property_id("prop-expense-001")
    assert len(found) == 1
    assert found[0].amount.amount == Decimal("200.00")
    assert found[0].category == ExpenseCategory.REPAIR


def test_delete_income(sqlite_connection):
    """DB-06: Guardar y eliminar un ingreso."""
    # Crear propiedad (FK)
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Delete Income",
        address=Address("Calle C", "Valencia", "46001", "ES"),
        property_type=PropertyType.APARTMENT,
        id="prop-del-income",
    )
    prop_repo.save(prop)

    # Guardar ingreso
    income_repo = SQLiteIncomeRepository(sqlite_connection)
    income = Income(
        property_id="prop-del-income",
        amount=Money(Decimal("500.00"), "EUR"),
        date=date(2026, 8, 1),
        category=IncomeCategory.DEPOSIT,
        id="income-del-001",
    )
    income_repo.save(income)

    # Verificar que existe
    found = income_repo.find_by_property_id("prop-del-income")
    assert len(found) == 1

    # Eliminar
    income_repo.delete("income-del-001")
    found_after = income_repo.find_by_property_id("prop-del-income")
    assert len(found_after) == 0
