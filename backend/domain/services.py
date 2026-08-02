"""
Servicios de Dominio.

Los servicios de dominio contienen lógica de negocio pura que no pertenece
a ninguna entidad en particular. No tienen identidad ni estado.
"""

from __future__ import annotations

from decimal import Decimal

from backend.domain.entities import (
    Expense,
    Income,
    ExpenseCategory,
    IncomeCategory,
    FiscalExpenseCategory,
    FiscalIncomeCategory,
    Property,
    LeaseContract,
    LeaseType,
)
from backend.domain.value_objects import Money, FiscalReport
import calendar
from datetime import timedelta, date


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


class FiscalCategoryMapper:
    """Servicio de dominio que sugiere categorías fiscales a partir de categorías generales."""

    EXPENSE_SUGGESTIONS: dict[ExpenseCategory, FiscalExpenseCategory] = {
        ExpenseCategory.REPAIR: FiscalExpenseCategory.REPARACION_CONSERVACION,
        ExpenseCategory.TAX: FiscalExpenseCategory.TRIBUTOS,
        ExpenseCategory.INSURANCE: FiscalExpenseCategory.PRIMAS_SEGUROS,
        ExpenseCategory.COMMUNITY_FEE: FiscalExpenseCategory.SERVICIOS_SUMINISTROS,
        ExpenseCategory.MORTGAGE: FiscalExpenseCategory.INTERESES_CAPITAL,
        ExpenseCategory.UTILITY: FiscalExpenseCategory.SERVICIOS_SUMINISTROS,
        ExpenseCategory.OTHER: FiscalExpenseCategory.OTROS_DEDUCIBLES,
    }

    INCOME_SUGGESTIONS: dict[IncomeCategory, FiscalIncomeCategory] = {
        IncomeCategory.RENT: FiscalIncomeCategory.RENDIMIENTO_INTEGRO,
        IncomeCategory.DEPOSIT: FiscalIncomeCategory.OTROS_INGRESOS,
        IncomeCategory.OTHER: FiscalIncomeCategory.OTROS_INGRESOS,
    }

    @classmethod
    def suggest_expense_fiscal_category(cls, category: ExpenseCategory) -> FiscalExpenseCategory:
        return cls.EXPENSE_SUGGESTIONS[category]

    @classmethod
    def suggest_income_fiscal_category(cls, category: IncomeCategory) -> FiscalIncomeCategory:
        return cls.INCOME_SUGGESTIONS[category]


class FiscalCalculator:
    """Motor de cálculo fiscal para Rendimientos del Capital Inmobiliario."""

    AMORTIZATION_RATE = Decimal("0.03")
    VIVIENDA_REDUCTION_RATE = Decimal("0.60")

    @classmethod
    def calculate(
        cls,
        fiscal_year: int,
        property: Property,
        incomes: list[Income],
        expenses: list[Expense],
        contracts: list[LeaseContract],
    ) -> FiscalReport:
        # PASO 1: Filtrar por año fiscal
        incomes_year = [i for i in incomes if i.date.year == fiscal_year]
        expenses_year = [e for e in expenses if e.date.year == fiscal_year]

        # PASO 2: Separar clasificados / no clasificados
        classified_incomes = [i for i in incomes_year if i.fiscal_category is not None]
        classified_expenses = [
            e for e in expenses_year
            if e.fiscal_category is not None
            and e.fiscal_category != FiscalExpenseCategory.NO_DEDUCIBLE
        ]
        unclassified_income_count = sum(1 for i in incomes_year if i.fiscal_category is None)
        unclassified_expense_count = sum(1 for e in expenses_year if e.fiscal_category is None)

        # PASO 3: Rendimientos Íntegros
        gross_rental = sum(
            (i.amount.amount for i in classified_incomes
             if i.fiscal_category == FiscalIncomeCategory.RENDIMIENTO_INTEGRO),
            Decimal("0"),
        )
        other_inc = sum(
            (i.amount.amount for i in classified_incomes
             if i.fiscal_category == FiscalIncomeCategory.OTROS_INGRESOS),
            Decimal("0"),
        )
        total_income = gross_rental + other_inc

        # PASO 4: Ocupación
        total_days = 366 if calendar.isleap(fiscal_year) else 365
        rented_days = cls._merge_rented_intervals(contracts, fiscal_year)
        occupation_ratio = (Decimal(rented_days) / Decimal(total_days)) if total_days > 0 else Decimal("0")

        # PASO 5: Gastos por categoría fiscal (prorrateados)
        def sum_cat(cat):
            return sum(
                (e.amount.amount for e in classified_expenses if e.fiscal_category == cat),
                Decimal("0"),
            )

        raw_intereses = sum_cat(FiscalExpenseCategory.INTERESES_CAPITAL)
        raw_reparacion = sum_cat(FiscalExpenseCategory.REPARACION_CONSERVACION)
        raw_tributos = sum_cat(FiscalExpenseCategory.TRIBUTOS)
        raw_seguros = sum_cat(FiscalExpenseCategory.PRIMAS_SEGUROS)
        raw_suministros = sum_cat(FiscalExpenseCategory.SERVICIOS_SUMINISTROS)
        raw_formalizacion = sum_cat(FiscalExpenseCategory.FORMALIZACION)
        raw_dudoso = sum_cat(FiscalExpenseCategory.DUDOSO_COBRO)
        raw_otros = sum_cat(FiscalExpenseCategory.OTROS_DEDUCIBLES)

        # Intereses y reparación NO se prorratean (son deducibles al 100%)
        exp_intereses = raw_intereses
        exp_reparacion = raw_reparacion
        # El resto se prorratean
        exp_tributos = raw_tributos * occupation_ratio
        exp_seguros = raw_seguros * occupation_ratio
        exp_suministros = raw_suministros * occupation_ratio
        exp_formalizacion = raw_formalizacion * occupation_ratio
        exp_dudoso = raw_dudoso * occupation_ratio
        exp_otros = raw_otros * occupation_ratio

        # PASO 6: Tope reparación + intereses
        repair_interest_raw = exp_intereses + exp_reparacion
        repair_interest_cap = total_income
        repair_interest_applied = min(repair_interest_raw, repair_interest_cap)
        repair_interest_excess = max(Decimal("0"), repair_interest_raw - repair_interest_cap)

        # PASO 7: Amortización
        acq = property.acquisition_cost
        cat = property.cadastral_breakdown
        if acq is None or cat is None:
            amort_base = Decimal("0")
            amort_full = Decimal("0")
            amort_prorated = Decimal("0")
        else:
            construction_acq_expenses = (
                acq.total_acquisition_expenses * acq.construction_portion / acq.purchase_price
            ) if acq.purchase_price > 0 else Decimal("0")
            construction_acq_total = acq.construction_portion + construction_acq_expenses
            construction_cadastral = cat.construction_value

            amort_base = max(construction_acq_total, construction_cadastral)
            amort_full = amort_base * cls.AMORTIZATION_RATE
            amort_prorated = amort_full * occupation_ratio

        # PASO 8: Total gastos deducibles
        total_deductible = (
            repair_interest_applied
            + exp_tributos + exp_seguros + exp_suministros
            + exp_formalizacion + exp_dudoso + exp_otros
            + amort_prorated
        )

        # PASO 9: Rendimiento Neto previo
        net_before = total_income - total_deductible

        # PASO 10: Reducción VH
        vh_contracts = [c for c in contracts if c.lease_type == LeaseType.VIVIENDA_HABITUAL]
        vh_days = cls._merge_rented_intervals(vh_contracts, fiscal_year)
        vh_ratio = (Decimal(vh_days) / Decimal(rented_days)) if rented_days > 0 else Decimal("0")

        if net_before > 0 and vh_days > 0:
            reduction_base = net_before * vh_ratio
            reduction_amount = reduction_base * cls.VIVIENDA_REDUCTION_RATE
        else:
            reduction_base = Decimal("0")
            reduction_amount = Decimal("0")

        # PASO 11: Resultado final
        net_final = net_before - reduction_amount

        return FiscalReport(
            fiscal_year=fiscal_year,
            property_id=property.id,
            gross_rental_income=gross_rental,
            other_income=other_inc,
            total_income=total_income,
            rented_days=rented_days,
            total_days_in_year=total_days,
            occupation_ratio=occupation_ratio,
            expenses_intereses=exp_intereses,
            expenses_reparacion=exp_reparacion,
            expenses_tributos=exp_tributos,
            expenses_seguros=exp_seguros,
            expenses_suministros=exp_suministros,
            expenses_formalizacion=exp_formalizacion,
            expenses_dudoso_cobro=exp_dudoso,
            expenses_otros=exp_otros,
            repair_interest_raw=repair_interest_raw,
            repair_interest_cap=repair_interest_cap,
            repair_interest_applied=repair_interest_applied,
            repair_interest_excess=repair_interest_excess,
            amortization_base=amort_base,
            amortization_rate=cls.AMORTIZATION_RATE,
            amortization_full_year=amort_full,
            amortization_prorated=amort_prorated,
            total_deductible_expenses=total_deductible,
            net_income_before_reduction=net_before,
            vivienda_habitual_days=vh_days,
            vivienda_habitual_ratio=vh_ratio,
            reduction_base=reduction_base,
            reduction_percentage=cls.VIVIENDA_REDUCTION_RATE,
            reduction_amount=reduction_amount,
            net_income_final=net_final,
            unclassified_income_count=unclassified_income_count,
            unclassified_expense_count=unclassified_expense_count,
            has_warnings=(unclassified_income_count + unclassified_expense_count) > 0,
        )

    @staticmethod
    def _merge_rented_intervals(contracts: list[LeaseContract], fiscal_year: int) -> int:
        """Calcula los días totales de alquiler sin contar solapamientos."""
        year_start = date(fiscal_year, 1, 1)
        year_end = date(fiscal_year, 12, 31)
        intervals = []
        for c in contracts:
            eff_start = max(c.start_date, year_start)
            eff_end = min(c.end_date or year_end, year_end)
            if eff_start <= eff_end:
                intervals.append((eff_start, eff_end))
        if not intervals:
            return 0
        intervals.sort()
        merged = [list(intervals[0])]
        for start, end in intervals[1:]:
            if start <= merged[-1][1] + timedelta(days=1):
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return sum((end - start).days + 1 for start, end in merged)
