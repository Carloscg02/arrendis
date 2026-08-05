import pytest
from datetime import date, timedelta
from decimal import Decimal
from dataclasses import FrozenInstanceError

from backend.domain.entities import (
    Property, PropertyType, Expense, ExpenseCategory, ExpenseSource,
    UtilityType, ExtractionConfidence
)
from backend.domain.value_objects import (
    Address, Money, UtilityInvoiceData
)
from backend.domain.services import FiscalCalculator

def test_ut_f16_01_property_valid_cups():
    address = Address(street="Calle Falsa 123", city="Springfield", postal_code="12345")
    prop = Property(
        name="Test",
        address=address,
        property_type=PropertyType.APARTMENT,
        user_id="user1",
        cups_electricity="ES0031103721971011PR0F"
    )
    assert prop.cups_electricity == "ES0031103721971011PR0F"

def test_ut_f16_02_property_invalid_cups():
    address = Address(street="Calle Falsa 123", city="Springfield", postal_code="12345")
    with pytest.raises(ValueError, match="no tiene formato CUPS válido"):
        Property(
            name="Test",
            address=address,
            property_type=PropertyType.APARTMENT,
            user_id="user1",
            cups_electricity="INVALID"
        )

def test_ut_f16_03_property_none_cups():
    address = Address(street="Calle Falsa 123", city="Springfield", postal_code="12345")
    prop = Property(
        name="Test",
        address=address,
        property_type=PropertyType.APARTMENT,
        user_id="user1",
        cups_electricity=None
    )
    assert prop.cups_electricity is None

def test_ut_f16_04_expense_defaults():
    expense = Expense(
        property_id="prop1",
        amount=Money(Decimal("100")),
        date=date.today(),
        category=ExpenseCategory.REPAIR
    )
    assert expense.is_verified is True
    assert expense.source == ExpenseSource.MANUAL

def test_ut_f16_05_expense_auto_import():
    expense = Expense(
        property_id="prop1",
        amount=Money(Decimal("100")),
        date=date.today(),
        category=ExpenseCategory.UTILITY,
        is_verified=False,
        source=ExpenseSource.AUTO_IMPORT
    )
    assert expense.is_verified is False
    assert expense.source == ExpenseSource.AUTO_IMPORT

def test_ut_f16_06_expense_utility_data():
    utility_data = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("50.0"),
        issue_date=date.today(),
        provider_name="Iberdrola",
        utility_type=UtilityType.ELECTRICITY
    )
    expense = Expense(
        property_id="prop1",
        amount=Money(Decimal("50.0")),
        date=date.today(),
        category=ExpenseCategory.UTILITY,
        is_verified=False,
        source=ExpenseSource.AUTO_IMPORT,
        utility_data=utility_data
    )
    assert expense.utility_data == utility_data

def test_ut_f16_07_utility_data_valid():
    utility_data = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("50.0"),
        issue_date=date.today(),
        provider_name="Iberdrola",
        utility_type=UtilityType.ELECTRICITY,
        invoice_number="INV-001",
        extraction_confidence=ExtractionConfidence.HIGH
    )
    assert utility_data.cups == "ES0031103721971011PR0F"
    assert utility_data.extraction_confidence == ExtractionConfidence.HIGH

def test_ut_f16_08_utility_data_invalid_cups():
    with pytest.raises(ValueError, match="CUPS no tiene formato válido"):
        UtilityInvoiceData(
            cups="INVALID",
            amount=Decimal("50.0"),
            issue_date=date.today(),
            provider_name="Iberdrola",
            utility_type=UtilityType.ELECTRICITY
        )

def test_ut_f16_09_utility_data_negative_amount():
    with pytest.raises(ValueError, match="importe de la factura debe ser positivo"):
        UtilityInvoiceData(
            cups="ES0031103721971011PR0F",
            amount=Decimal("-50.0"),
            issue_date=date.today(),
            provider_name="Iberdrola",
            utility_type=UtilityType.ELECTRICITY
        )

def test_ut_f16_10_utility_data_empty_provider():
    with pytest.raises(ValueError, match="nombre del proveedor no puede estar vacío"):
        UtilityInvoiceData(
            cups="ES0031103721971011PR0F",
            amount=Decimal("50.0"),
            issue_date=date.today(),
            provider_name="",
            utility_type=UtilityType.ELECTRICITY
        )

def test_ut_f16_11_utility_data_immutable():
    utility_data = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("50.0"),
        issue_date=date.today(),
        provider_name="Iberdrola",
        utility_type=UtilityType.ELECTRICITY
    )
    with pytest.raises(FrozenInstanceError):
        utility_data.amount = Decimal("100.0")

def test_ut_f16_12_fiscal_calculator_ignores_unverified():
    from backend.domain.entities import FiscalExpenseCategory
    address = Address(street="Calle Falsa 123", city="Springfield", postal_code="12345")
    prop = Property(
        name="Test",
        address=address,
        property_type=PropertyType.APARTMENT,
        user_id="user1"
    )
    
    # Gasto verificado
    exp1 = Expense(
        property_id=prop.id,
        amount=Money(Decimal("100")),
        date=date(2023, 5, 1),
        category=ExpenseCategory.REPAIR,
        fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION,
        is_verified=True
    )
    
    # Gasto NO verificado
    exp2 = Expense(
        property_id=prop.id,
        amount=Money(Decimal("200")),
        date=date(2023, 6, 1),
        category=ExpenseCategory.REPAIR,
        fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION,
        is_verified=False
    )
    
    report = FiscalCalculator.calculate(
        fiscal_year=2023,
        property=prop,
        incomes=[],
        expenses=[exp1, exp2],
        contracts=[]
    )
    
    # exp2 was ignored
    assert report.expenses_reparacion == Decimal("100")

def test_ut_f16_13_fiscal_calculator_includes_verified():
    from backend.domain.entities import FiscalExpenseCategory
    address = Address(street="Calle Falsa 123", city="Springfield", postal_code="12345")
    prop = Property(
        name="Test",
        address=address,
        property_type=PropertyType.APARTMENT,
        user_id="user1"
    )
    
    exp1 = Expense(
        property_id=prop.id,
        amount=Money(Decimal("100")),
        date=date(2023, 5, 1),
        category=ExpenseCategory.REPAIR,
        fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION,
        is_verified=True
    )
    
    report = FiscalCalculator.calculate(
        fiscal_year=2023,
        property=prop,
        incomes=[],
        expenses=[exp1],
        contracts=[]
    )
    
    assert report.expenses_reparacion == Decimal("100")
