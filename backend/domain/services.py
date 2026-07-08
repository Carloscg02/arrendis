"""
Servicios de Dominio.

Los servicios de dominio contienen lógica de negocio pura que no pertenece
a ninguna entidad en particular. No tienen identidad ni estado.
"""

from __future__ import annotations

from decimal import Decimal

from backend.domain.entities import Expense, Income
from backend.domain.value_objects import Money


class ProfitCalculator:
    """Calcula el beneficio neto de una propiedad.

    Es un Servicio de Dominio: no tiene identidad ni estado.
    Solo contiene lógica pura que opera sobre entidades.
    """

    @staticmethod
    def calculate_net_profit(incomes: list[Income], expenses: list[Expense]) -> Money:
        """Calcula el beneficio neto: Σ income.amount − Σ expense.amount.

        - Si no hay ingresos ni gastos, retorna Money(0, "EUR").
        - El resultado PUEDE ser negativo (se pierde dinero).
        """
        # Sumar todos los ingresos
        total_income = Decimal("0.00")
        for income in incomes:
            total_income += income.amount.amount

        # Sumar todos los gastos
        total_expense = Decimal("0.00")
        for expense in expenses:
            total_expense += expense.amount.amount

        # Calcular beneficio neto (puede ser negativo)
        net = total_income - total_expense

        if net < 0:
            return Money._create_allowing_negative(net, "EUR")
        return Money(net, "EUR")
