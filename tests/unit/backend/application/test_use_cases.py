"""
Tests para Casos de Uso (Application Layer).

UC-01 a UC-07: crear propiedad, listar, registrar ingreso/gasto, profit report.
Utilizan los repositorios in-memory del conftest.
"""

from datetime import date
from decimal import Decimal

import pytest

from backend.application.use_cases import (
    CreatePropertyUseCase,
    GetPropertyProfitReportUseCase,
    ListPropertiesUseCase,
    RecordExpenseUseCase,
    RecordIncomeUseCase,
)
from backend.domain.entities import PropertyStatus, PropertyType
from backend.domain.value_objects import Money


def test_create_property(property_repo):
    """UC-01: CreatePropertyUseCase crea y persiste una propiedad."""
    uc = CreatePropertyUseCase(property_repo)
    prop = uc.execute(
        name="Piso Centro",
        street="Calle Mayor 15",
        city="Madrid",
        postal_code="28013",
        country="ES",
        property_type="apartment",
    )
    assert prop.name == "Piso Centro"
    assert prop.property_type == PropertyType.APARTMENT
    assert prop.status == PropertyStatus.AVAILABLE
    # Verificar que se persistió
    found = property_repo.find_by_id(prop.id)
    assert found is not None
    assert found.id == prop.id


def test_create_property_duplicate_name(property_repo):
    """UC-01.1: CreatePropertyUseCase impide nombres duplicados."""
    uc = CreatePropertyUseCase(property_repo)
    uc.execute("Unique", "Calle A", "Madrid", "28001", "ES", "apartment")
    
    with pytest.raises(ValueError, match="already exists"):
        uc.execute("Unique", "Calle B", "Madrid", "28001", "ES", "house")


def test_list_properties(property_repo):
    """UC-02: ListPropertiesUseCase retorna todas las propiedades."""
    create_uc = CreatePropertyUseCase(property_repo)
    create_uc.execute("Piso A", "Calle A", "Madrid", "28001", "ES", "apartment")
    create_uc.execute("Casa B", "Calle B", "Sevilla", "41001", "ES", "house")

    list_uc = ListPropertiesUseCase(property_repo)
    props = list_uc.execute()
    assert len(props) == 2


def test_record_income(property_repo, income_repo):
    """UC-03: RecordIncomeUseCase registra un ingreso válido."""
    # Crear propiedad primero
    create_uc = CreatePropertyUseCase(property_repo)
    prop = create_uc.execute("Piso", "Calle X", "Madrid", "28001", "ES", "apartment")

    # Registrar ingreso
    income_uc = RecordIncomeUseCase(property_repo, income_repo)
    income = income_uc.execute(
        property_id=prop.id,
        amount=Decimal("750.00"),
        income_date=date(2026, 7, 1),
        category="rent",
        description="Alquiler julio",
    )
    assert income.property_id == prop.id
    assert income.amount == Money(Decimal("750.00"), "EUR")


def test_record_income_invalid_property(property_repo, income_repo):
    """UC-04: RecordIncomeUseCase lanza ValueError si la propiedad no existe."""
    income_uc = RecordIncomeUseCase(property_repo, income_repo)
    with pytest.raises(ValueError, match="No existe la propiedad"):
        income_uc.execute(
            property_id="non-existent-id",
            amount=Decimal("750.00"),
            income_date=date(2026, 7, 1),
            category="rent",
        )


def test_record_expense(property_repo, expense_repo):
    """UC-05: RecordExpenseUseCase registra un gasto válido."""
    # Crear propiedad primero
    create_uc = CreatePropertyUseCase(property_repo)
    prop = create_uc.execute("Piso", "Calle X", "Madrid", "28001", "ES", "apartment")

    # Registrar gasto
    expense_uc = RecordExpenseUseCase(property_repo, expense_repo)
    expense = expense_uc.execute(
        property_id=prop.id,
        amount=Decimal("120.00"),
        expense_date=date(2026, 7, 5),
        category="repair",
        description="Reparación caldera",
    )
    assert expense.property_id == prop.id
    assert expense.amount == Money(Decimal("120.00"), "EUR")


def test_record_expense_invalid_property(property_repo, expense_repo):
    """UC-06: RecordExpenseUseCase lanza ValueError si la propiedad no existe."""
    expense_uc = RecordExpenseUseCase(property_repo, expense_repo)
    with pytest.raises(ValueError, match="No existe la propiedad"):
        expense_uc.execute(
            property_id="non-existent-id",
            amount=Decimal("120.00"),
            expense_date=date(2026, 7, 5),
            category="repair",
        )


def test_get_profit_report(property_repo, income_repo, expense_repo):
    """UC-07: GetPropertyProfitReportUseCase calcula el beneficio neto."""
    # Crear propiedad
    create_uc = CreatePropertyUseCase(property_repo)
    prop = create_uc.execute("Piso", "Calle X", "Madrid", "28001", "ES", "apartment")

    # Registrar ingresos
    income_uc = RecordIncomeUseCase(property_repo, income_repo)
    income_uc.execute(prop.id, Decimal("750.00"), date(2026, 7, 1), "rent")
    income_uc.execute(prop.id, Decimal("750.00"), date(2026, 8, 1), "rent")

    # Registrar gastos
    expense_uc = RecordExpenseUseCase(property_repo, expense_repo)
    expense_uc.execute(prop.id, Decimal("200.00"), date(2026, 7, 5), "repair")

    # Calcular profit
    profit_uc = GetPropertyProfitReportUseCase(property_repo, income_repo, expense_repo)
    result = profit_uc.execute(prop.id)
    # 750 + 750 - 200 = 1300
    assert result.amount == Decimal("1300.00")
    assert result.currency == "EUR"


def test_in_memory_repo_update_image(property_repo):
    """T-03: InMemoryPropertyRepository.update_image() actualiza el campo correctamente."""
    create_uc = CreatePropertyUseCase(property_repo)
    prop = create_uc.execute("Piso", "Calle X", "Madrid", "28001", "ES", "apartment")
    
    assert prop.image_filename is None
    
    property_repo.update_image(prop.id, "photo.jpg")
    updated = property_repo.find_by_id(prop.id)
    assert updated.image_filename == "photo.jpg"

