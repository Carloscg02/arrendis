"""
Tests para FiscalCategoryMapper.
"""

from backend.domain.entities import ExpenseCategory, IncomeCategory, FiscalExpenseCategory, FiscalIncomeCategory
from backend.domain.services import FiscalCategoryMapper

def test_mapper_suggests_reparacion_for_repair():
    """T-U-11-05: FiscalCategoryMapper sugiere REPARACION_CONSERVACION para REPAIR"""
    assert FiscalCategoryMapper.suggest_expense_fiscal_category(ExpenseCategory.REPAIR) == FiscalExpenseCategory.REPARACION_CONSERVACION

def test_mapper_suggests_tributos_for_tax():
    """T-U-11-06: FiscalCategoryMapper sugiere TRIBUTOS para TAX"""
    assert FiscalCategoryMapper.suggest_expense_fiscal_category(ExpenseCategory.TAX) == FiscalExpenseCategory.TRIBUTOS

def test_mapper_suggests_intereses_for_mortgage():
    """T-U-11-07: FiscalCategoryMapper sugiere INTERESES_CAPITAL para MORTGAGE"""
    assert FiscalCategoryMapper.suggest_expense_fiscal_category(ExpenseCategory.MORTGAGE) == FiscalExpenseCategory.INTERESES_CAPITAL

def test_mapper_suggests_suministros_for_community_and_utility():
    """T-U-11-08: FiscalCategoryMapper sugiere SERVICIOS_SUMINISTROS para COMMUNITY_FEE y UTILITY"""
    assert FiscalCategoryMapper.suggest_expense_fiscal_category(ExpenseCategory.COMMUNITY_FEE) == FiscalExpenseCategory.SERVICIOS_SUMINISTROS
    assert FiscalCategoryMapper.suggest_expense_fiscal_category(ExpenseCategory.UTILITY) == FiscalExpenseCategory.SERVICIOS_SUMINISTROS

def test_mapper_suggests_rendimiento_integro_for_rent():
    """T-U-11-09: FiscalCategoryMapper sugiere RENDIMIENTO_INTEGRO para RENT"""
    assert FiscalCategoryMapper.suggest_income_fiscal_category(IncomeCategory.RENT) == FiscalIncomeCategory.RENDIMIENTO_INTEGRO

def test_mapper_suggests_otros_ingresos_for_deposit():
    """T-U-11-10: FiscalCategoryMapper sugiere OTROS_INGRESOS para DEPOSIT"""
    assert FiscalCategoryMapper.suggest_income_fiscal_category(IncomeCategory.DEPOSIT) == FiscalIncomeCategory.OTROS_INGRESOS

def test_mapper_covers_all_expense_categories():
    """T-U-11-11: FiscalCategoryMapper cubre TODOS los valores de ExpenseCategory"""
    for category in ExpenseCategory:
        suggestion = FiscalCategoryMapper.suggest_expense_fiscal_category(category)
        assert isinstance(suggestion, FiscalExpenseCategory)

def test_mapper_covers_all_income_categories():
    """T-U-11-12: FiscalCategoryMapper cubre TODOS los valores de IncomeCategory"""
    for category in IncomeCategory:
        suggestion = FiscalCategoryMapper.suggest_income_fiscal_category(category)
        assert isinstance(suggestion, FiscalIncomeCategory)
