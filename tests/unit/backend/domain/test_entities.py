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
    FiscalExpenseCategory,
    Income,
    IncomeCategory,
    FiscalIncomeCategory,
    Property,
    PropertyStatus,
    PropertyType,
    Tenant,
    LeaseContract,
    LeaseType,
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
        user_id="u1",
        id="test-id-001",
    )
    assert prop.name == "Piso Centro"
    assert prop.address == addr
    assert prop.property_type == PropertyType.APARTMENT
    assert prop.id == "test-id-001"


def test_property_auto_uuid():
    """EN-02: Property genera un UUID automáticamente si no se proporciona id."""
    addr = Address(street="Calle A", city="Valencia", postal_code="46001")
    prop = Property(name="Garaje", address=addr, property_type=PropertyType.GARAGE, user_id="u1")
    assert prop.id is not None
    assert len(prop.id) == 36  # Formato UUID4: 8-4-4-4-12


def test_property_empty_name_raises():
    """EN-03: Property con nombre vacío lanza ValueError."""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    with pytest.raises(ValueError, match="nombre"):
        Property(name="", address=addr, property_type=PropertyType.APARTMENT, user_id="u1")

def test_property_empty_user_id_raises():
    """EN-03.1: Property con user_id vacío lanza ValueError."""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    with pytest.raises(ValueError, match="user_id"):
        Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="")


def test_property_default_status():
    """EN-04: Property tiene status AVAILABLE por defecto."""
    addr = Address(street="Calle B", city="Sevilla", postal_code="41001")
    prop = Property(name="Casa Triana", address=addr, property_type=PropertyType.HOUSE, user_id="u1")
    assert prop.status == PropertyStatus.AVAILABLE


def test_property_default_image_filename():
    """T-01: Property se crea con image_filename=None por defecto."""
    addr = Address(street="Calle B", city="Sevilla", postal_code="41001")
    prop = Property(name="Casa Triana", address=addr, property_type=PropertyType.HOUSE, user_id="u1")
    assert prop.image_filename is None


def test_property_with_image_filename():
    """T-02: Property acepta image_filename."""
    addr = Address(street="Calle B", city="Sevilla", postal_code="41001")
    prop = Property(name="Casa Triana", address=addr, property_type=PropertyType.HOUSE, image_filename="test.jpg", user_id="u1")
    assert prop.image_filename == "test.jpg"


def test_property_equality_by_id():
    """EN-05: Dos Properties con el mismo id son iguales (aunque tengan distinto nombre)."""
    addr = Address(street="Calle X", city="Madrid", postal_code="28013")
    p1 = Property(name="Nombre A", address=addr, property_type=PropertyType.APARTMENT, user_id="u1", id="same-id")
    p2 = Property(name="Nombre B", address=addr, property_type=PropertyType.APARTMENT, user_id="u2", id="same-id")
    assert p1 == p2


def test_property_inequality_by_id():
    """EN-06: Dos Properties con distinto id NO son iguales."""
    addr = Address(street="Calle X", city="Madrid", postal_code="28013")
    p1 = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1", id="id-1")
    p2 = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1", id="id-2")
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


def test_income_with_fiscal_category():
    """T-U-11-03: Income acepta fiscal_category válida."""
    income = Income(
        property_id="prop-001",
        amount=Money(Decimal("750.00"), "EUR"),
        date=date(2026, 7, 1),
        category=IncomeCategory.RENT,
        fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO,
    )
    assert income.fiscal_category == FiscalIncomeCategory.RENDIMIENTO_INTEGRO


def test_income_without_fiscal_category():
    """T-U-11-04: Income funciona sin fiscal_category (None por defecto)."""
    income = Income(
        property_id="prop-001",
        amount=Money(Decimal("750.00"), "EUR"),
        date=date(2026, 7, 1),
        category=IncomeCategory.RENT,
    )
    assert income.fiscal_category is None


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


def test_expense_with_fiscal_category():
    """T-U-11-01: Expense acepta fiscal_category válida."""
    expense = Expense(
        property_id="prop-001",
        amount=Money(Decimal("120.00"), "EUR"),
        date=date(2026, 7, 5),
        category=ExpenseCategory.REPAIR,
        fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION,
    )
    assert expense.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION


def test_expense_without_fiscal_category():
    """T-U-11-02: Expense funciona sin fiscal_category (None por defecto)."""
    expense = Expense(
        property_id="prop-001",
        amount=Money(Decimal("120.00"), "EUR"),
        date=date(2026, 7, 5),
        category=ExpenseCategory.REPAIR,
    )
    assert expense.fiscal_category is None


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────

from backend.domain.value_objects import Email, PasswordHash
from backend.domain.entities import User

def test_user_creation():
    user = User(
        email=Email("test@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234"),
        username="testuser",
    )
    assert user.email.value == "test@example.com"
    assert user.username == "testuser"

def test_user_empty_username_raises():
    with pytest.raises(ValueError):
        User(
            email=Email("test@example.com"),
            password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234"),
            username="",
        )

def test_user_equality_by_id():
    u1 = User(email=Email("a@b.com"), password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234"), username="a", id="same")
    u2 = User(email=Email("x@y.com"), password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234"), username="b", id="same")
    assert u1 == u2


from backend.domain.value_objects import CadastralBreakdown, AcquisitionCost

def test_property_creation_without_fiscal_data():
    """T-U-09-12: Property se crea sin datos fiscales (compatibilidad F-01–F-08)"""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    prop = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1")
    assert prop.cadastral_ref is None
    assert prop.cadastral_breakdown is None
    assert prop.acquisition_cost is None
    assert prop.acquisition_date is None
    assert prop.has_fiscal_data is False


def test_property_creation_with_fiscal_data():
    """T-U-09-13: Property se crea con datos fiscales completos"""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    cadastral = CadastralBreakdown(Decimal("40000"), Decimal("80000"))
    acquisition = AcquisitionCost(Decimal("200000"), Decimal("120000"), Decimal("80000"), Decimal("16000"), Decimal("800"), Decimal("400"))
    prop = Property(
        name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1",
        cadastral_ref="1234567AB1234C0001XY",
        cadastral_breakdown=cadastral,
        acquisition_cost=acquisition,
        acquisition_date=date(2020, 1, 1)
    )
    assert prop.has_fiscal_data is True


def test_property_has_fiscal_data_only_with_complete_data():
    """T-U-09-14: Property.has_fiscal_data retorna True solo con datos completos"""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    prop = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1")
    assert prop.has_fiscal_data is False
    
    prop.cadastral_breakdown = CadastralBreakdown(Decimal("40000"), Decimal("80000"))
    assert prop.has_fiscal_data is False
    
    prop.acquisition_cost = AcquisitionCost(Decimal("200000"), Decimal("120000"), Decimal("80000"), Decimal("16000"), Decimal("800"), Decimal("400"))
    assert prop.has_fiscal_data is False
    
    prop.acquisition_date = date(2020, 1, 1)
    assert prop.has_fiscal_data is True


def test_property_validates_cadastral_ref_length():
    """T-U-09-15: Property valida cadastral_ref de 20 caracteres"""
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    with pytest.raises(ValueError, match="20 caracteres"):
        Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1", cadastral_ref="123")


# ──────────────────────────────────────────────
# LeaseContract
# ──────────────────────────────────────────────

def test_lease_contract_creation():
    """T-U-10-01: LeaseContract se crea correctamente con todos los campos"""
    contract = LeaseContract(
        property_id="p1",
        tenant_name="Juan Perez",
        tenant_nif="12345678A",
        start_date=date(2025, 1, 1),
        monthly_rent=Money(Decimal("1000"), "EUR"),
        lease_type=LeaseType.VIVIENDA_HABITUAL
    )
    assert contract.property_id == "p1"
    assert contract.tenant_name == "Juan Perez"
    assert contract.tenant_nif == "12345678A"
    assert contract.start_date == date(2025, 1, 1)
    assert contract.monthly_rent == Money(Decimal("1000"), "EUR")
    assert contract.lease_type == LeaseType.VIVIENDA_HABITUAL
    assert contract.end_date is None
    assert contract.id is not None

def test_lease_contract_empty_property_id():
    """T-U-10-02: LeaseContract rechaza property_id vacío"""
    with pytest.raises(ValueError, match="property_id no puede estar vacío"):
        LeaseContract("", "Juan Perez", "12345678A", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL)

def test_lease_contract_empty_tenant_name():
    """T-U-10-03: LeaseContract rechaza tenant_name vacío"""
    with pytest.raises(ValueError, match="nombre del inquilino no puede estar vacío"):
        LeaseContract("p1", "", "12345678A", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL)

def test_lease_contract_empty_tenant_nif():
    """T-U-10-04: LeaseContract rechaza tenant_nif vacío"""
    with pytest.raises(ValueError, match="NIF del inquilino no puede estar vacío"):
        LeaseContract("p1", "Juan Perez", "", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL)

def test_lease_contract_end_date_before_start_date():
    """T-U-10-05: LeaseContract rechaza end_date anterior a start_date"""
    with pytest.raises(ValueError, match="no puede ser anterior a la fecha de inicio"):
        LeaseContract("p1", "Juan Perez", "12345678A", date(2025, 1, 2), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL, end_date=date(2025, 1, 1))

def test_lease_contract_is_active_no_end_date():
    """T-U-10-06: is_active retorna True si end_date es None"""
    contract = LeaseContract("p1", "Juan Perez", "12345678A", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL)
    assert contract.is_active is True

def test_lease_contract_is_active_future_end_date():
    """T-U-10-07: is_active retorna True si end_date es futura"""
    future_date = date(date.today().year + 1, 1, 1)
    contract = LeaseContract("p1", "Juan Perez", "12345678A", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL, end_date=future_date)
    assert contract.is_active is True

def test_lease_contract_is_active_past_end_date():
    """T-U-10-08: is_active retorna False si end_date es pasada"""
    past_date = date(1999, 1, 1)
    contract = LeaseContract("p1", "Juan Perez", "12345678A", past_date, Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL, end_date=past_date)
    assert contract.is_active is False

def test_lease_contract_rented_days_full_year():
    """T-U-10-09: rented_days_in_year con contrato completo en el año"""
    contract = LeaseContract("p1", "Juan Perez", "12345678A", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL, end_date=date(2025, 12, 31))
    assert contract.rented_days_in_year(2025) == 365

def test_lease_contract_rented_days_partial_year():
    """T-U-10-10: rented_days_in_year con contrato parcial (empieza mitad de año)"""
    contract = LeaseContract("p1", "Juan Perez", "12345678A", date(2025, 7, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL, end_date=date(2025, 12, 31))
    assert contract.rented_days_in_year(2025) == 184

def test_lease_contract_rented_days_outside_year():
    """T-U-10-11: rented_days_in_year con contrato fuera del año fiscal → 0"""
    contract = LeaseContract("p1", "Juan Perez", "12345678A", date(2024, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL, end_date=date(2024, 12, 31))
    assert contract.rented_days_in_year(2025) == 0

def test_lease_contract_rented_days_indefinite():
    """T-U-10-12: rented_days_in_year con contrato indefinido (end_date=None)"""
    contract = LeaseContract("p1", "Juan Perez", "12345678A", date(2025, 1, 1), Money(Decimal("1000"), "EUR"), LeaseType.VIVIENDA_HABITUAL)
    assert contract.rented_days_in_year(2025) == 365

