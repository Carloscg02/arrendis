import pytest
from datetime import date
from decimal import Decimal
from backend.domain.entities import (
    Property, PropertyType, Address, CadastralBreakdown, AcquisitionCost,
    Income, Expense, LeaseContract, LeaseType, IncomeCategory, ExpenseCategory,
    FiscalIncomeCategory, FiscalExpenseCategory
)
from backend.domain.value_objects import Money, FiscalReport
from backend.domain.services import FiscalCalculator

@pytest.fixture
def sample_property():
    address = Address("Calle Falsa 123", "Madrid", "28080", "ES")
    prop = Property(
        name="Piso Madrid",
        address=address,
        property_type=PropertyType.APARTMENT,
        user_id="user-123"
    )
    prop.cadastral_breakdown = CadastralBreakdown(Decimal("40000"), Decimal("60000"))
    prop.acquisition_cost = AcquisitionCost(
        purchase_price=Decimal("150000"),
        construction_portion=Decimal("90000"),
        land_portion=Decimal("60000"),
        transfer_tax=Decimal("15000"),
        notary_fees=Decimal("1000"),
        registry_fees=Decimal("500")
    )
    prop.acquisition_date = date(2020, 1, 1)
    return prop

def test_tu_12_01_base_case(sample_property):
    # 1 contrato VH todo el año, datos completos
    contracts = [
        LeaseContract(
            property_id=sample_property.id,
            tenant_name="Juan",
            tenant_nif="12345678A",
            start_date=date(2024, 1, 1),
            monthly_rent=Money(Decimal("1000")),
            lease_type=LeaseType.VIVIENDA_HABITUAL,
            end_date=date(2024, 12, 31)
        )
    ]
    incomes = [
        Income(
            property_id=sample_property.id,
            amount=Money(Decimal("12000")),
            date=date(2024, 6, 1),
            category=IncomeCategory.RENT,
            fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO
        )
    ]
    expenses = [
        Expense(
            property_id=sample_property.id,
            amount=Money(Decimal("500")),
            date=date(2024, 6, 1),
            category=ExpenseCategory.TAX,
            fiscal_category=FiscalExpenseCategory.TRIBUTOS
        )
    ]
    
    report = FiscalCalculator.calculate(2024, sample_property, incomes, expenses, contracts)
    
    assert report.total_income == Decimal("12000")
    assert report.rented_days == 366  # 2024 es bisiesto
    assert report.occupation_ratio == Decimal("1")
    assert report.expenses_tributos == Decimal("500")
    # Amortización: (90000 + (16500 * 90000 / 150000)) = 90000 + 9900 = 99900. 99900 * 0.03 = 2997
    assert report.amortization_base == Decimal("99900")
    assert report.amortization_prorated == Decimal("2997")
    assert report.total_deductible_expenses == Decimal("3497")
    assert report.net_income_before_reduction == Decimal("8503")
    assert report.vivienda_habitual_ratio == Decimal("1")
    assert report.reduction_amount == Decimal("5101.8")
    assert report.net_income_final == Decimal("3401.2")

def test_tu_12_02_no_contracts(sample_property):
    incomes = []
    expenses = [
        Expense(
            property_id=sample_property.id,
            amount=Money(Decimal("500")),
            date=date(2024, 6, 1),
            category=ExpenseCategory.TAX,
            fiscal_category=FiscalExpenseCategory.TRIBUTOS
        )
    ]
    report = FiscalCalculator.calculate(2024, sample_property, incomes, expenses, [])
    assert report.rented_days == 0
    assert report.occupation_ratio == Decimal("0")
    assert report.expenses_tributos == Decimal("0")
    assert report.amortization_prorated == Decimal("0")

def test_tu_12_03_partial_contract(sample_property):
    contracts = [
        LeaseContract(
            property_id=sample_property.id,
            tenant_name="Juan",
            tenant_nif="12345678A",
            start_date=date(2025, 1, 1),
            monthly_rent=Money(Decimal("1000")),
            lease_type=LeaseType.VIVIENDA_HABITUAL,
            end_date=date(2025, 7, 2)  # 183 days, exactly 50% (approx) for non-leap year (183/365 = 0.50136986...)
        )
    ]
    report = FiscalCalculator.calculate(2025, sample_property, [], [], contracts)
    assert report.rented_days == 183
    
def test_tu_12_04_repair_interest_cap_exceeded(sample_property):
    incomes = [
        Income(sample_property.id, Money(Decimal("1000")), date(2025, 6, 1), IncomeCategory.RENT, fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO)
    ]
    expenses = [
        Expense(sample_property.id, Money(Decimal("800")), date(2025, 6, 1), ExpenseCategory.REPAIR, fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION),
        Expense(sample_property.id, Money(Decimal("300")), date(2025, 6, 1), ExpenseCategory.MORTGAGE, fiscal_category=FiscalExpenseCategory.INTERESES_CAPITAL)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, incomes, expenses, [])
    assert report.repair_interest_raw == Decimal("1100")
    assert report.repair_interest_cap == Decimal("1000")
    assert report.repair_interest_applied == Decimal("1000")
    assert report.repair_interest_excess == Decimal("100")

def test_tu_12_05_repair_interest_cap_not_exceeded(sample_property):
    incomes = [
        Income(sample_property.id, Money(Decimal("2000")), date(2025, 6, 1), IncomeCategory.RENT, fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO)
    ]
    expenses = [
        Expense(sample_property.id, Money(Decimal("800")), date(2025, 6, 1), ExpenseCategory.REPAIR, fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, incomes, expenses, [])
    assert report.repair_interest_raw == Decimal("800")
    assert report.repair_interest_applied == Decimal("800")
    assert report.repair_interest_excess == Decimal("0")

def test_tu_12_06_amortization_max_adq(sample_property):
    report = FiscalCalculator.calculate(2025, sample_property, [], [], [])
    assert report.amortization_base == Decimal("99900")

def test_tu_12_07_amortization_max_cadastral(sample_property):
    sample_property.cadastral_breakdown = CadastralBreakdown(Decimal("40000"), Decimal("110000"))
    report = FiscalCalculator.calculate(2025, sample_property, [], [], [])
    assert report.amortization_base == Decimal("110000")

def test_tu_12_08_reduction_60(sample_property):
    # Ya testeado en base_case, verify here with basic data
    contracts = [
        LeaseContract(sample_property.id, "Juan", "12345678A", date(2025, 1, 1), Money(Decimal("1000")), LeaseType.VIVIENDA_HABITUAL, date(2025, 12, 31))
    ]
    incomes = [
        Income(sample_property.id, Money(Decimal("10000")), date(2025, 6, 1), IncomeCategory.RENT, fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, incomes, [], contracts)
    net_before = report.net_income_before_reduction
    assert report.reduction_amount == net_before * Decimal("0.60")

def test_tu_12_09_no_reduction_negative_net(sample_property):
    contracts = [
        LeaseContract(sample_property.id, "Juan", "12345678A", date(2025, 1, 1), Money(Decimal("1000")), LeaseType.VIVIENDA_HABITUAL, date(2025, 12, 31))
    ]
    incomes = [
        Income(sample_property.id, Money(Decimal("100")), date(2025, 6, 1), IncomeCategory.RENT, fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO)
    ]
    expenses = [
        Expense(sample_property.id, Money(Decimal("5000")), date(2025, 6, 1), ExpenseCategory.TAX, fiscal_category=FiscalExpenseCategory.TRIBUTOS)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, incomes, expenses, contracts)
    assert report.net_income_before_reduction < 0
    assert report.reduction_amount == Decimal("0")

def test_tu_12_10_no_reduction_not_vh(sample_property):
    contracts = [
        LeaseContract(sample_property.id, "Juan", "12345678A", date(2025, 1, 1), Money(Decimal("1000")), LeaseType.TEMPORAL, date(2025, 12, 31))
    ]
    incomes = [
        Income(sample_property.id, Money(Decimal("10000")), date(2025, 6, 1), IncomeCategory.RENT, fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, incomes, [], contracts)
    assert report.vivienda_habitual_days == 0
    assert report.reduction_amount == Decimal("0")

def test_tu_12_11_mix_contracts(sample_property):
    contracts = [
        LeaseContract(sample_property.id, "Juan", "12345678A", date(2025, 1, 1), Money(Decimal("1000")), LeaseType.VIVIENDA_HABITUAL, date(2025, 6, 30)),
        LeaseContract(sample_property.id, "Maria", "87654321B", date(2025, 7, 1), Money(Decimal("1000")), LeaseType.TEMPORAL, date(2025, 12, 31))
    ]
    report = FiscalCalculator.calculate(2025, sample_property, [], [], contracts)
    assert report.rented_days == 365
    assert report.vivienda_habitual_days == 181
    
def test_tu_12_12_no_deducible_excluded(sample_property):
    expenses = [
        Expense(sample_property.id, Money(Decimal("500")), date(2025, 6, 1), ExpenseCategory.OTHER, fiscal_category=FiscalExpenseCategory.NO_DEDUCIBLE)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, [], expenses, [])
    assert report.total_deductible_expenses == Decimal("0")  # (except amortization, which is also prorated to 0 as rented_days=0)

def test_tu_12_13_unclassified_warnings(sample_property):
    incomes = [
        Income(sample_property.id, Money(Decimal("1000")), date(2025, 6, 1), IncomeCategory.RENT, fiscal_category=None)
    ]
    expenses = [
        Expense(sample_property.id, Money(Decimal("500")), date(2025, 6, 1), ExpenseCategory.TAX, fiscal_category=None)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, incomes, expenses, [])
    assert report.unclassified_income_count == 1
    assert report.unclassified_expense_count == 1
    assert report.has_warnings is True

def test_tu_12_14_overlapping_contracts(sample_property):
    contracts = [
        LeaseContract(sample_property.id, "Juan", "12345678A", date(2025, 1, 1), Money(Decimal("1000")), LeaseType.TEMPORAL, date(2025, 1, 10)),
        LeaseContract(sample_property.id, "Maria", "87654321B", date(2025, 1, 5), Money(Decimal("1000")), LeaseType.TEMPORAL, date(2025, 1, 15))
    ]
    report = FiscalCalculator.calculate(2025, sample_property, [], [], contracts)
    assert report.rented_days == 15

def test_tu_12_15_leap_year(sample_property):
    report = FiscalCalculator.calculate(2024, sample_property, [], [], [])
    assert report.total_days_in_year == 366

def test_tu_12_16_exclude_other_years(sample_property):
    expenses = [
        Expense(sample_property.id, Money(Decimal("500")), date(2024, 6, 1), ExpenseCategory.TAX, fiscal_category=FiscalExpenseCategory.TRIBUTOS)
    ]
    report = FiscalCalculator.calculate(2025, sample_property, [], expenses, [])
    assert report.expenses_tributos == Decimal("0")

def test_tu_12_17_amortization_expenses_proportion(sample_property):
    # 90k construction / 150k total = 0.6
    # 16.5k expenses * 0.6 = 9.9k
    report = FiscalCalculator.calculate(2025, sample_property, [], [], [])
    assert report.amortization_base == Decimal("99900")
