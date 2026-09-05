"""
Tests unitarios para ProcessUtilityInvoiceUseCase (F-18 / Capa de Aplicación).

Verifica la orquestación completa del pipeline de extracción de facturas de suministros:
- Vía A (Regex)
- Fallback a Vía B (IA)
- Matching CUPS con propiedades del usuario (aislamiento multi-tenant)
- Creación del gasto en estado is_verified=False
- Manejo exhaustivo de errores
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.application.use_cases import (
    ProcessUtilityInvoiceUseCase,
    ProcessUtilityInvoiceResult,
)
from backend.domain.entities import (
    EmptyPDFTextError,
    Expense,
    ExpenseCategory,
    ExpenseSource,
    ExtractionConfidence,
    ExtractionFailedError,
    FiscalExpenseCategory,
    Property,
    PropertyNotFoundForCUPSError,
    PropertyStatus,
    PropertyType,
    UtilityType,
)
from backend.domain.extraction import (
    ExtractionStrategy,
    RepsolExtractionStrategy,
    UtilityExtractorRegistry,
)
from backend.domain.ports import (
    ExpenseRepository,
    PDFTextExtractorPort,
    PropertyRepository,
)
from backend.domain.value_objects import Address, UtilityInvoiceData


@pytest.fixture
def mock_pdf_extractor():
    return MagicMock(spec=PDFTextExtractorPort)


@pytest.fixture
def mock_property_repo():
    return MagicMock(spec=PropertyRepository)


@pytest.fixture
def mock_expense_repo():
    return MagicMock(spec=ExpenseRepository)


@pytest.fixture
def sample_property():
    return Property(
        name="Piso Frank Capra",
        address=Address("CL Frank Capra 4", "Málaga", "29010", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id="user_123",
        status=PropertyStatus.AVAILABLE,
        cups_electricity="ES0031103721971011PR0F",
    )


def test_use_case_via_a_regex_success(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo, sample_property
):
    """UT-F18-18: Vía A exitosa — Regex de Repsol crea Expense no verificado."""
    raw_repsol_text = (
        "Factura de luz\n"
        "Esta es tu factura de luz,\n"
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Nº de factura\n"
        "61088387754\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Total factura\n"
        "75,46 €\n"
        "Repsol Comercializadora de Electricidad y Gas, S.L.U.\n"
    )
    mock_pdf_extractor.extract_text.return_value = raw_repsol_text
    mock_property_repo.find_by_cups.return_value = sample_property

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
        fallback_strategy=None,
    )

    result = use_case.execute(pdf_bytes=b"dummy_bytes", user_id="user_123")

    assert isinstance(result, ProcessUtilityInvoiceResult)
    assert result.strategy_used == "Repsol"
    assert result.property.id == sample_property.id
    assert result.invoice_data.cups == "ES0031103721971011PR0F"
    assert result.invoice_data.amount == Decimal("75.46")
    assert result.invoice_data.extraction_confidence == ExtractionConfidence.HIGH

    # Verificar que el gasto creado se guardó y tiene las propiedades correctas
    assert mock_expense_repo.save.called
    saved_expense: Expense = mock_expense_repo.save.call_args[0][0]
    assert saved_expense.property_id == sample_property.id
    assert saved_expense.amount.amount == Decimal("75.46")
    assert saved_expense.date == date(2026, 8, 1)
    assert saved_expense.category == ExpenseCategory.UTILITY
    assert saved_expense.fiscal_category == FiscalExpenseCategory.SERVICIOS_SUMINISTROS
    assert saved_expense.is_verified is False  # Regla crítica: pendiente de validación
    assert saved_expense.source == ExpenseSource.AUTO_IMPORT
    assert saved_expense.utility_data is not None


def test_use_case_fallback_to_ai_when_regex_fails(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo, sample_property
):
    """UT-F18-19: Fallback a Vía B cuando la estrategia Regex falla."""
    # Texto de Repsol pero sin el total (regex fallará)
    broken_text = (
        "Repsol factura\n"
        "CUPS\n"
        "ES0031103721971011PR0F\n"
    )
    mock_pdf_extractor.extract_text.return_value = broken_text
    mock_property_repo.find_by_cups.return_value = sample_property

    mock_ai_strategy = MagicMock(spec=ExtractionStrategy)
    mock_ai_strategy.provider_name = "AI_Fallback"
    mock_ai_strategy.extract.return_value = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("90.00"),
        issue_date=date(2026, 8, 1),
        provider_name="Repsol",
        utility_type=UtilityType.ELECTRICITY,
        extraction_confidence=ExtractionConfidence.MEDIUM,
    )

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
        fallback_strategy=mock_ai_strategy,
    )

    result = use_case.execute(pdf_bytes=b"dummy", user_id="user_123")

    assert result.strategy_used == "AI_Fallback"
    assert result.invoice_data.extraction_confidence == ExtractionConfidence.MEDIUM
    assert mock_expense_repo.save.called


def test_use_case_fallback_to_ai_when_provider_unknown(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo, sample_property
):
    """UT-F18-20: Fallback a Vía B cuando el proveedor no está en el registry."""
    unknown_text = "Factura de Aguas de Murcia..."
    mock_pdf_extractor.extract_text.return_value = unknown_text
    mock_property_repo.find_by_cups.return_value = sample_property

    mock_ai_strategy = MagicMock(spec=ExtractionStrategy)
    mock_ai_strategy.provider_name = "AI_Fallback"
    mock_ai_strategy.extract.return_value = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("35.20"),
        issue_date=date(2026, 8, 1),
        provider_name="Aguas de Murcia",
        utility_type=UtilityType.WATER,
        extraction_confidence=ExtractionConfidence.MEDIUM,
    )

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
        fallback_strategy=mock_ai_strategy,
    )

    result = use_case.execute(pdf_bytes=b"dummy", user_id="user_123")

    assert result.strategy_used == "AI_Fallback"
    assert result.invoice_data.utility_type == UtilityType.WATER


def test_use_case_raises_when_regex_fails_and_no_ai_strategy(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo
):
    """UT-F18-21: Lanza ExtractionFailedError si Regex falla y no hay IA configurada."""
    mock_pdf_extractor.extract_text.return_value = "Texto desconocido sin coincidencia"

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
        fallback_strategy=None,
    )

    with pytest.raises(ExtractionFailedError, match="no hay estrategia de IA configurada"):
        use_case.execute(pdf_bytes=b"dummy", user_id="user_123")


def test_use_case_raises_when_both_regex_and_ai_fail(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo
):
    """UT-F18-22: Lanza ExtractionFailedError si tanto Regex como IA fallan."""
    mock_pdf_extractor.extract_text.return_value = "Texto corrupto..."
    mock_ai_strategy = MagicMock(spec=ExtractionStrategy)
    mock_ai_strategy.extract.return_value = None

    registry = UtilityExtractorRegistry([])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
        fallback_strategy=mock_ai_strategy,
    )

    with pytest.raises(ExtractionFailedError, match="no pudo completarse ni por Regex ni por IA"):
        use_case.execute(pdf_bytes=b"dummy", user_id="user_123")


def test_use_case_raises_when_cups_not_found_for_user(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo
):
    """UT-F18-23: Lanza PropertyNotFoundForCUPSError si el CUPS no está asignado."""
    raw_repsol_text = (
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Total factura\n"
        "75,46 €\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Repsol\n"
    )
    mock_pdf_extractor.extract_text.return_value = raw_repsol_text
    # El repositorio no encuentra ninguna propiedad con ese CUPS
    mock_property_repo.find_by_cups.return_value = None

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
    )

    with pytest.raises(PropertyNotFoundForCUPSError) as exc_info:
        use_case.execute(pdf_bytes=b"dummy", user_id="user_123")

    assert exc_info.value.cups == "ES0031103721971011PR0F"
    assert exc_info.value.invoice_data is not None
    assert exc_info.value.invoice_data.amount == Decimal("75.46")
    # Asegurar que NO se guardó ningún gasto huérfano
    assert not mock_expense_repo.save.called


def test_use_case_respects_multi_tenancy(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo
):
    """UT-F18-24: Multi-tenancy — find_by_cups se invoca con el user_id de la sesión."""
    raw_repsol_text = (
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Total factura\n"
        "75,46 €\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Repsol\n"
    )
    mock_pdf_extractor.extract_text.return_value = raw_repsol_text
    mock_property_repo.find_by_cups.return_value = None

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
    )

    with pytest.raises(PropertyNotFoundForCUPSError):
        use_case.execute(pdf_bytes=b"dummy", user_id="tenant_user_abc")

    mock_property_repo.find_by_cups.assert_called_once_with(
        "ES0031103721971011PR0F", user_id="tenant_user_abc"
    )


def test_use_case_raises_empty_pdf_when_extractor_raises(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo
):
    """UT-F18-25: Propaga EmptyPDFTextError si el extractor lo lanza."""
    mock_pdf_extractor.extract_text.side_effect = EmptyPDFTextError("PDF vacío")

    registry = UtilityExtractorRegistry([])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
    )

    with pytest.raises(EmptyPDFTextError):
        use_case.execute(pdf_bytes=b"", user_id="user_123")
