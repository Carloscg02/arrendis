import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from backend.application.use_cases import DownloadFiscalReportPdfUseCase
from backend.domain.entities import Property, PropertyType, Address, CadastralBreakdown, AcquisitionCost
from backend.domain.ports import FiscalReportRendererPort


class FakeRenderer(FiscalReportRendererPort):
    def render(self, report, property_name, property_address) -> bytes:
        return b"%PDF-1.4 Fake PDF Content"

    def content_type(self) -> str:
        return "application/pdf"

    def file_extension(self) -> str:
        return "pdf"


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
def fake_renderer():
    return FakeRenderer()


@pytest.fixture
def use_case(mock_property_repo, mock_income_repo, mock_expense_repo, mock_contract_repo, fake_renderer):
    return DownloadFiscalReportPdfUseCase(
        property_repo=mock_property_repo,
        income_repo=mock_income_repo,
        expense_repo=mock_expense_repo,
        contract_repo=mock_contract_repo,
        renderer=fake_renderer,
    )


def _get_valid_property(user_id="user-123", name="Piso Test"):
    prop = Property(
        name=name,
        address=Address("Calle Gran Via 1", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id=user_id,
    )
    prop.cadastral_breakdown = CadastralBreakdown(Decimal("40000"), Decimal("60000"))
    prop.acquisition_cost = AcquisitionCost(
        purchase_price=Decimal("150000"),
        construction_portion=Decimal("90000"),
        land_portion=Decimal("60000"),
        transfer_tax=Decimal("15000"),
        notary_fees=Decimal("1000"),
        registry_fees=Decimal("500"),
    )
    prop.acquisition_date = date(2020, 1, 1)
    return prop


def test_tu_13_09_execute_returns_pdf_tuple(use_case, mock_property_repo, mock_income_repo, mock_expense_repo, mock_contract_repo):
    """T-U-13-09: execute() retorna la tupla (bytes, content_type, filename)."""
    prop = _get_valid_property()
    mock_property_repo.find_by_id.return_value = prop
    mock_income_repo.find_by_property_id.return_value = []
    mock_expense_repo.find_by_property_id.return_value = []
    mock_contract_repo.find_by_property_id.return_value = []

    pdf_bytes, content_type, filename = use_case.execute("user-123", prop.id, 2026)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert content_type == "application/pdf"
    assert filename.endswith(".pdf")


def test_tu_13_10_execute_wrong_user_raises(use_case, mock_property_repo):
    """T-U-13-10: Error (ValueError) si la propiedad no pertenece al usuario."""
    prop = _get_valid_property("user-123")
    mock_property_repo.find_by_id.return_value = prop

    with pytest.raises(ValueError, match="No existe la propiedad con id"):
        use_case.execute("other-user", prop.id, 2026)


def test_tu_13_11_execute_no_fiscal_data_raises(use_case, mock_property_repo):
    """T-U-13-11: Error (ValueError) si la propiedad no tiene datos fiscales."""
    prop = Property(
        name="Piso Sin Datos",
        address=Address("Calle A", "Madrid", "28001", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id="user-123",
    )
    mock_property_repo.find_by_id.return_value = prop

    with pytest.raises(ValueError, match="La propiedad no tiene datos fiscales completos"):
        use_case.execute("user-123", prop.id, 2026)


def test_tu_13_12_filename_contains_name_and_year(use_case, mock_property_repo, mock_income_repo, mock_expense_repo, mock_contract_repo):
    """T-U-13-12: El filename generado contiene el nombre de la propiedad y el año fiscal."""
    prop = _get_valid_property(name="Piso Sol")
    mock_property_repo.find_by_id.return_value = prop
    mock_income_repo.find_by_property_id.return_value = []
    mock_expense_repo.find_by_property_id.return_value = []
    mock_contract_repo.find_by_property_id.return_value = []

    _, _, filename = use_case.execute("user-123", prop.id, 2026)

    assert "Piso_Sol" in filename
    assert "2026" in filename
