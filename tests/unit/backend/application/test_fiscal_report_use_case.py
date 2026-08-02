import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from backend.application.use_cases import GenerateFiscalReportUseCase
from backend.domain.entities import Property, PropertyType, Address, CadastralBreakdown, AcquisitionCost
from backend.domain.value_objects import FiscalReport

@pytest.fixture
def mock_property_repo():
    return Mock()

@pytest.fixture
def mock_income_repo():
    return Mock()

@pytest.fixture
def mock_expense_repo():
    return Mock()

@pytest.fixture
def mock_contract_repo():
    return Mock()

@pytest.fixture
def use_case(mock_property_repo, mock_income_repo, mock_expense_repo, mock_contract_repo):
    return GenerateFiscalReportUseCase(
        property_repo=mock_property_repo,
        income_repo=mock_income_repo,
        expense_repo=mock_expense_repo,
        contract_repo=mock_contract_repo
    )

def _get_valid_property(user_id="user-123"):
    prop = Property(
        name="Test",
        address=Address("C", "M", "28", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id=user_id
    )
    prop.cadastral_breakdown = CadastralBreakdown(Decimal("10"), Decimal("10"))
    prop.acquisition_cost = AcquisitionCost(Decimal("100"), Decimal("50"), Decimal("50"), Decimal("0"), Decimal("0"), Decimal("0"))
    prop.acquisition_date = date(2020, 1, 1)
    return prop

def test_tu_12_18_generate_report_success(use_case, mock_property_repo, mock_income_repo, mock_expense_repo, mock_contract_repo):
    """T-U-12-18: Genera report con datos completos"""
    prop = _get_valid_property()
    mock_property_repo.find_by_id.return_value = prop
    mock_income_repo.find_by_property_id.return_value = []
    mock_expense_repo.find_by_property_id.return_value = []
    mock_contract_repo.find_by_property_id.return_value = []

    report = use_case.execute("user-123", prop.id, 2025)
    
    assert isinstance(report, FiscalReport)
    assert report.fiscal_year == 2025
    assert report.property_id == prop.id

def test_tu_12_19_error_no_fiscal_data(use_case, mock_property_repo):
    """T-U-12-19: Error si propiedad sin datos fiscales"""
    prop = Property("Test", Address("C", "M", "28", "ES"), PropertyType.APARTMENT, "user-123")
    mock_property_repo.find_by_id.return_value = prop

    with pytest.raises(ValueError, match="La propiedad no tiene datos fiscales completos"):
        use_case.execute("user-123", prop.id, 2025)

def test_tu_12_20_error_wrong_user(use_case, mock_property_repo):
    """T-U-12-20: Error si propiedad no pertenece al usuario"""
    prop = _get_valid_property("user-123")
    mock_property_repo.find_by_id.return_value = prop

    with pytest.raises(ValueError, match="No existe la propiedad con id"):
        use_case.execute("other-user", prop.id, 2025)
