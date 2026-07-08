"""
Tests para Servicios de Dominio: ProfitCalculator.

SV-01 a SV-04: cálculo de beneficio neto con distintas combinaciones.
"""

from datetime import date
from decimal import Decimal

from backend.domain.entities import (
    Expense,
    ExpenseCategory,
    Income,
    IncomeCategory,
)
from backend.domain.services import ProfitCalculator
from backend.domain.value_objects import Money


def _make_income(amount: Decimal) -> Income:
    """Helper: crea un Income con un monto dado."""
    return Income(
        property_id="prop-001",
        amount=Money(amount, "EUR"),
        date=date(2026, 7, 1),
        category=IncomeCategory.RENT,
    )


def _make_expense(amount: Decimal) -> Expense:
    """Helper: crea un Expense con un monto dado."""
    return Expense(
        property_id="prop-001",
        amount=Money(amount, "EUR"),
        date=date(2026, 7, 1),
        category=ExpenseCategory.REPAIR,
    )


def test_profit_with_incomes_and_expenses():
    """SV-01: 3x750 - (200+100) = 1950.00 EUR."""
    incomes = [
        _make_income(Decimal("750.00")),
        _make_income(Decimal("750.00")),
        _make_income(Decimal("750.00")),
    ]
    expenses = [
        _make_expense(Decimal("200.00")),
        _make_expense(Decimal("100.00")),
    ]
    result = ProfitCalculator.calculate_net_profit(incomes, expenses)
    assert result.amount == Decimal("1950.00")
    assert result.currency == "EUR"


def test_profit_no_data():
    """SV-02: Sin ingresos ni gastos → Money(0.00, EUR)."""
    result = ProfitCalculator.calculate_net_profit([], [])
    assert result.amount == Decimal("0.00")
    assert result.currency == "EUR"


def test_profit_only_expenses():
    """SV-03: Solo gastos → resultado negativo."""
    expenses = [
        _make_expense(Decimal("200.00")),
        _make_expense(Decimal("150.00")),
    ]
    result = ProfitCalculator.calculate_net_profit([], expenses)
    assert result.amount == Decimal("-350.00")
    assert result.currency == "EUR"


def test_profit_only_incomes():
    """SV-04: Solo ingresos → resultado positivo."""
    incomes = [
        _make_income(Decimal("500.00")),
        _make_income(Decimal("300.00")),
    ]
    result = ProfitCalculator.calculate_net_profit(incomes, [])
    assert result.amount == Decimal("800.00")
    assert result.currency == "EUR"
