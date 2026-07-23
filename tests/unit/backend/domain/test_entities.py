"""
Tests para Entidades: Property, Tenant, Income, Expense.

EN-01 a EN-12: creación, validación, UUID automático, igualdad por id, defaults.
"""

from datetime import date
from decimal import Decimal

import pytest

from backend.domain.entities import (
    Expense,
    ExpenseCategory,
    Income,
    IncomeCategory,
    Property,
    PropertyStatus,
    PropertyType,
    Tenant,
)
from backend.domain.value_objects import Address, Money


# ──────────────────────────────────────────────
# Property
# ──────────────────────────────────────────────

def test_property_creation():
    """EN-01: Property se crea correctamente con todos los campos."""
    addr = Address(street="Calle Mayor 15", city="Madrid", postal_code="28013")
    prop = Property(
        name="Piso Centro",
        address=addr,
        property_type=PropertyType.APARTMENT,
        id="test-id-001",
    )
    assert prop.name == "Piso Centro"
    assert prop.address == addr
    assert prop.property_type == PropertyType.APARTMENT
    assert prop.id == "test-id-001"


def test_property_auto_uuid():
    """EN-02: Property genera un UUID automáticamente si no se proporciona id."""
    addr = Address(street="Calle A", city="Valencia", postal_code="46001")
    prop = Property(name="Garaje", address=addr, property_type=PropertyType.GARAGE)
    assert prop.id is not None
    assert len(prop.id) == 36  # Formato UUID4: 8-4-4-4-12


def test_property_empty_name_raises():
    """EN-03: Property con nombre vacío lanza ValueError."""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    with pytest.raises(ValueError, match="nombre"):
        Property(name="", address=addr, property_type=PropertyType.APARTMENT)


def test_property_default_status():
    """EN-04: Property tiene status AVAILABLE por defecto."""
    addr = Address(street="Calle B", city="Sevilla", postal_code="41001")
    prop = Property(name="Casa Triana", address=addr, property_type=PropertyType.HOUSE)
    assert prop.status == PropertyStatus.AVAILABLE


def test_property_default_image_filename():
    """T-01: Property se crea con image_filename=None por defecto."""
    addr = Address(street="Calle B", city="Sevilla", postal_code="41001")
    prop = Property(name="Casa Triana", address=addr, property_type=PropertyType.HOUSE)
    assert prop.image_filename is None


def test_property_with_image_filename():
    """T-02: Property acepta image_filename."""
    addr = Address(street="Calle B", city="Sevilla", postal_code="41001")
    prop = Property(name="Casa Triana", address=addr, property_type=PropertyType.HOUSE, image_filename="test.jpg")
    assert prop.image_filename == "test.jpg"


def test_property_equality_by_id():
    """EN-05: Dos Properties con el mismo id son iguales (aunque tengan distinto nombre)."""
    addr = Address(street="Calle X", city="Madrid", postal_code="28013")
    p1 = Property(name="Nombre A", address=addr, property_type=PropertyType.APARTMENT, id="same-id")
    p2 = Property(name="Nombre B", address=addr, property_type=PropertyType.APARTMENT, id="same-id")
    assert p1 == p2


def test_property_inequality_by_id():
    """EN-06: Dos Properties con distinto id NO son iguales."""
    addr = Address(street="Calle X", city="Madrid", postal_code="28013")
    p1 = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, id="id-1")
    p2 = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, id="id-2")
    assert p1 != p2


# ──────────────────────────────────────────────
# Tenant
# ──────────────────────────────────────────────

def test_tenant_creation():
    """EN-07: Tenant se crea correctamente."""
    tenant = Tenant(
        first_name="María",
        last_name="García",
        email="maria@email.com",
        phone="+34 612 345 678",
    )
    assert tenant.first_name == "María"
    assert tenant.last_name == "García"
    assert tenant.email == "maria@email.com"
    assert tenant.phone == "+34 612 345 678"
    assert tenant.id is not None


def test_tenant_invalid_email_raises():
    """EN-08: Tenant con email sin '@' lanza ValueError."""
    with pytest.raises(ValueError, match="email"):
        Tenant(first_name="Juan", last_name="Pérez", email="invalid-email")


def test_tenant_empty_name_raises():
    """EN-09: Tenant con nombre vacío lanza ValueError."""
    with pytest.raises(ValueError, match="nombre"):
        Tenant(first_name="", last_name="García", email="a@b.com")


# ──────────────────────────────────────────────
# Income
# ──────────────────────────────────────────────

def test_income_creation():
    """EN-10: Income se crea correctamente."""
    income = Income(
        property_id="prop-001",
        amount=Money(Decimal("750.00"), "EUR"),
        date=date(2026, 7, 1),
        category=IncomeCategory.RENT,
        description="Alquiler julio",
    )
    assert income.property_id == "prop-001"
    assert income.amount == Money(Decimal("750.00"), "EUR")
    assert income.date == date(2026, 7, 1)
    assert income.category == IncomeCategory.RENT
    assert income.description == "Alquiler julio"


def test_income_empty_property_id_raises():
    """EN-11: Income con property_id vacío lanza ValueError."""
    with pytest.raises(ValueError, match="property_id"):
        Income(
            property_id="",
            amount=Money(Decimal("100.00"), "EUR"),
            date=date(2026, 7, 1),
            category=IncomeCategory.RENT,
        )


# ──────────────────────────────────────────────
# Expense
# ──────────────────────────────────────────────

def test_expense_creation():
    """EN-12: Expense se crea correctamente."""
    expense = Expense(
        property_id="prop-001",
        amount=Money(Decimal("120.00"), "EUR"),
        date=date(2026, 7, 5),
        category=ExpenseCategory.REPAIR,
        description="Reparación caldera",
    )
    assert expense.property_id == "prop-001"
    assert expense.amount == Money(Decimal("120.00"), "EUR")
    assert expense.date == date(2026, 7, 5)
    assert expense.category == ExpenseCategory.REPAIR
    assert expense.description == "Reparación caldera"
