import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from backend.application.use_cases import UpdatePropertyFiscalDataUseCase
from backend.domain.entities import Property, PropertyType
from backend.domain.value_objects import Address

def test_update_property_fiscal_data_use_case():
    """T-U-09-16: UpdatePropertyFiscalDataUseCase persiste datos correctamente"""
    repo = MagicMock()
    
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    prop = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u1", id="prop-01")
    repo.find_by_id.return_value = prop
    
    use_case = UpdatePropertyFiscalDataUseCase(repo)
    use_case.execute(
        user_id="u1",
        property_id="prop-01",
        cadastral_ref="1234567AB1234C0001XY",
        land_value=Decimal("40000"),
        construction_value=Decimal("80000"),
        purchase_price=Decimal("200000"),
        construction_portion=Decimal("120000"),
        land_portion=Decimal("80000"),
        transfer_tax=Decimal("16000"),
        notary_fees=Decimal("800"),
        registry_fees=Decimal("400"),
        acquisition_date=date(2020, 1, 1),
    )
    
    repo.update_fiscal_data.assert_called_once()
    kwargs = repo.update_fiscal_data.call_args.kwargs
    assert kwargs["property_id"] == "prop-01"
    assert kwargs["cadastral_ref"] == "1234567AB1234C0001XY"
    assert kwargs["cadastral_breakdown"].land_value == Decimal("40000")
    assert kwargs["acquisition_cost"].purchase_price == Decimal("200000")
    assert kwargs["acquisition_date"] == date(2020, 1, 1)

def test_update_property_fiscal_data_rejects_missing_property():
    """T-U-09-17: UpdatePropertyFiscalDataUseCase rechaza propiedad inexistente"""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    
    use_case = UpdatePropertyFiscalDataUseCase(repo)
    with pytest.raises(ValueError, match="No existe la propiedad"):
        use_case.execute(
            user_id="u1", property_id="prop-01", cadastral_ref=None,
            land_value=None, construction_value=None, purchase_price=None,
            construction_portion=None, land_portion=None, transfer_tax=None,
            notary_fees=None, registry_fees=None, acquisition_date=None
        )

def test_update_property_fiscal_data_rejects_wrong_user():
    """T-U-09-18: UpdatePropertyFiscalDataUseCase rechaza propiedad de otro usuario"""
    repo = MagicMock()
    addr = Address(street="Calle A", city="Madrid", postal_code="28013")
    prop = Property(name="Piso", address=addr, property_type=PropertyType.APARTMENT, user_id="u2", id="prop-01")
    repo.find_by_id.return_value = prop
    
    use_case = UpdatePropertyFiscalDataUseCase(repo)
    with pytest.raises(ValueError, match="No existe la propiedad"):
        use_case.execute(
            user_id="u1", property_id="prop-01", cadastral_ref=None,
            land_value=None, construction_value=None, purchase_price=None,
            construction_portion=None, land_portion=None, transfer_tax=None,
            notary_fees=None, registry_fees=None, acquisition_date=None
        )

from backend.application.use_cases import (
    RecordExpenseUseCase,
    RecordIncomeUseCase,
    UpdateFiscalCategoryUseCase,
    SuggestFiscalCategoriesUseCase,
)
from backend.domain.entities import (
    Expense,
    ExpenseCategory,
    FiscalExpenseCategory,
    Income,
    IncomeCategory,
    FiscalIncomeCategory,
    PropertyStatus,
)
from backend.domain.value_objects import Money

@pytest.fixture
def test_property(property_repo):
    prop = Property(
        name="Test Prop",
        address=Address(street="Calle A", city="Madrid", postal_code="28001"),
        property_type=PropertyType.APARTMENT,
        user_id="user123",
        id="prop123"
    )
    property_repo.save(prop)
    return prop

def test_record_expense_with_fiscal_category(property_repo, expense_repo, test_property):
    """T-U-11-13: RecordExpenseUseCase acepta fiscal_category"""
    uc = RecordExpenseUseCase(property_repo, expense_repo)
    expense = uc.execute(
        user_id="user123",
        property_id="prop123",
        amount=Decimal("100"),
        expense_date=date.today(),
        category="repair",
        fiscal_category="reparacion_conservacion"
    )
    assert expense.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION
    
    saved = expense_repo.find_by_property_id("prop123")[0]
    assert saved.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION

def test_record_income_with_fiscal_category(property_repo, income_repo, test_property):
    """T-U-11-14: RecordIncomeUseCase acepta fiscal_category"""
    uc = RecordIncomeUseCase(property_repo, income_repo)
    income = uc.execute(
        user_id="user123",
        property_id="prop123",
        amount=Decimal("1000"),
        income_date=date.today(),
        category="rent",
        fiscal_category="rendimiento_integro"
    )
    assert income.fiscal_category == FiscalIncomeCategory.RENDIMIENTO_INTEGRO
    
    saved = income_repo.find_by_property_id("prop123")[0]
    assert saved.fiscal_category == FiscalIncomeCategory.RENDIMIENTO_INTEGRO

def test_update_fiscal_category_use_case(property_repo, income_repo, expense_repo, test_property):
    """T-U-11-15: UpdateFiscalCategoryUseCase actualiza gasto e ingreso"""
    expense = Expense(
        property_id="prop123",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=ExpenseCategory.REPAIR,
        id="exp1"
    )
    expense_repo.save(expense)
    
    uc = UpdateFiscalCategoryUseCase(property_repo, income_repo, expense_repo)
    updated = uc.execute("user123", "exp1", "expense", "reparacion_conservacion")
    
    assert updated.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION
    
    saved = expense_repo.find_by_property_id("prop123")[0]
    assert saved.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION

def test_update_fiscal_category_rejects_other_user(property_repo, income_repo, expense_repo, test_property):
    """T-U-11-16: UpdateFiscalCategoryUseCase rechaza propiedad ajena"""
    expense = Expense(
        property_id="prop123",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=ExpenseCategory.REPAIR,
        id="exp1"
    )
    expense_repo.save(expense)
    
    uc = UpdateFiscalCategoryUseCase(property_repo, income_repo, expense_repo)
    with pytest.raises(ValueError, match="Registro no encontrado o no pertenece al usuario."):
        uc.execute("other_user", "exp1", "expense", "reparacion_conservacion")

def test_suggest_fiscal_categories_use_case(property_repo, income_repo, expense_repo, test_property):
    """T-U-11-17: SuggestFiscalCategoriesUseCase retorna sugerencias"""
    expense = Expense(
        property_id="prop123",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=ExpenseCategory.REPAIR,
        id="exp1"
    )
    expense_repo.save(expense)
    
    income = Income(
        property_id="prop123",
        amount=Money(Decimal("1000"), "EUR"),
        date=date.today(),
        category=IncomeCategory.RENT,
        id="inc1"
    )
    income_repo.save(income)
    
    uc = SuggestFiscalCategoriesUseCase(property_repo, income_repo, expense_repo)
    suggestions = uc.execute("user123", "prop123")
    
    assert suggestions["total_unclassified"] == 2
    assert len(suggestions["unclassified_expenses"]) == 1
    assert suggestions["unclassified_expenses"][0]["suggested_fiscal_category"] == "reparacion_conservacion"
    
    assert len(suggestions["unclassified_incomes"]) == 1
    assert suggestions["unclassified_incomes"][0]["suggested_fiscal_category"] == "rendimiento_integro"

def test_suggest_fiscal_categories_ignores_classified(property_repo, income_repo, expense_repo, test_property):
    """T-U-11-18: SuggestFiscalCategoriesUseCase ignora ya clasificados"""
    expense = Expense(
        property_id="prop123",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=ExpenseCategory.REPAIR,
        fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION,
        id="exp1"
    )
    expense_repo.save(expense)
    
    uc = SuggestFiscalCategoriesUseCase(property_repo, income_repo, expense_repo)
    suggestions = uc.execute("user123", "prop123")
    
    assert suggestions["total_unclassified"] == 0
    assert len(suggestions["unclassified_expenses"]) == 0
