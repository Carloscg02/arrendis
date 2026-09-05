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
    ProcessBatchUtilityInvoicesUseCase,
)
from backend.domain.entities import (
    DuplicateInvoiceError,
    EmptyPDFTextError,
    Expense,
    ExpenseCategory,
    ExpenseSource,
    ExtractionConfidence,
    ExtractionFailedError,
    FiscalExpenseCategory,
    Money,
    Property,
    PropertyNotFoundForCUPSError,
    PropertyStatus,
    PropertyType,
    UtilityInvoiceData,
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
    assert saved_expense.is_verified is True  # F-20: Contabilización directa por defecto
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


def test_use_case_raises_duplicate_invoice_by_invoice_number(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo, sample_property
):
    """UT-F20-01: Lanza DuplicateInvoiceError si ya existe un gasto con el mismo CUPS y nº de factura."""
    raw_repsol_text = (
        "Factura de luz\n"
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Nº de factura\n"
        "61088387754\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Total factura\n"
        "75,46 €\n"
        "Repsol\n"
    )
    mock_pdf_extractor.extract_text.return_value = raw_repsol_text
    mock_property_repo.find_by_cups.return_value = sample_property

    # Simulamos que ya existe un gasto previo con ese mismo invoice_number
    existing_expense = Expense(
        property_id=sample_property.id,
        amount=Money(Decimal("75.46"), "EUR"),
        date=date(2026, 8, 1),
        category=ExpenseCategory.UTILITY,
        utility_data=UtilityInvoiceData(
            cups="ES0031103721971011PR0F",
            amount=Decimal("75.46"),
            issue_date=date(2026, 8, 1),
            provider_name="Repsol",
            utility_type=UtilityType.ELECTRICITY,
            invoice_number="61088387754",
            extraction_confidence=ExtractionConfidence.HIGH,
        ),
    )
    mock_expense_repo.find_by_property_id.return_value = [existing_expense]

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
    )

    with pytest.raises(DuplicateInvoiceError) as exc_info:
        use_case.execute(pdf_bytes=b"dummy", user_id="user_123")

    assert "ya fue importada previamente" in str(exc_info.value)
    assert exc_info.value.existing_expense == existing_expense
    assert not mock_expense_repo.save.called


def test_use_case_raises_duplicate_invoice_by_date_and_amount_fallback(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo, sample_property
):
    """UT-F20-02: Lanza DuplicateInvoiceError si coinciden CUPS, fecha e importe (sin número de factura)."""
    raw_repsol_text = (
        "Factura de luz\n"
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Total factura\n"
        "75,46 €\n"
        "Repsol\n"
    )
    mock_pdf_extractor.extract_text.return_value = raw_repsol_text
    mock_property_repo.find_by_cups.return_value = sample_property

    # Simulamos gasto existente sin invoice_number pero misma fecha e importe
    existing_expense = Expense(
        property_id=sample_property.id,
        amount=Money(Decimal("75.46"), "EUR"),
        date=date(2026, 8, 1),
        category=ExpenseCategory.UTILITY,
        utility_data=UtilityInvoiceData(
            cups="ES0031103721971011PR0F",
            amount=Decimal("75.46"),
            issue_date=date(2026, 8, 1),
            provider_name="Repsol",
            utility_type=UtilityType.ELECTRICITY,
            invoice_number=None,
            extraction_confidence=ExtractionConfidence.HIGH,
        ),
    )
    mock_expense_repo.find_by_property_id.return_value = [existing_expense]

    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=mock_pdf_extractor,
        registry=registry,
        property_repo=mock_property_repo,
        expense_repo=mock_expense_repo,
    )

    with pytest.raises(DuplicateInvoiceError) as exc_info:
        use_case.execute(pdf_bytes=b"dummy", user_id="user_123")

    assert "Ya existe una factura" in str(exc_info.value)
    assert not mock_expense_repo.save.called


def test_batch_use_case_processes_mixed_files(
    mock_pdf_extractor, mock_property_repo, mock_expense_repo, sample_property
):
    """UT-F20-03: ProcessBatchUtilityInvoicesUseCase procesa múltiples archivos con éxitos, duplicados y errores."""
    single_use_case = MagicMock(spec=ProcessUtilityInvoiceUseCase)

    # 1. Factura exitosa
    mock_exp = Expense(
        property_id=sample_property.id,
        amount=Money(Decimal("80.00"), "EUR"),
        date=date(2026, 7, 1),
        category=ExpenseCategory.UTILITY,
    )
    res_success = ProcessUtilityInvoiceResult(
        expense=mock_exp,
        property=sample_property,
        invoice_data=UtilityInvoiceData(
            cups="ES0031103721971011PR0F",
            amount=Decimal("80.00"),
            issue_date=date(2026, 7, 1),
            provider_name="Repsol",
            utility_type=UtilityType.ELECTRICITY,
        ),
        strategy_used="Repsol",
    )

    # 2. Factura duplicada
    dup_error = DuplicateInvoiceError(
        "Factura duplicada",
        invoice_data=UtilityInvoiceData(
            cups="ES0031103721971011PR0F",
            amount=Decimal("75.46"),
            issue_date=date(2026, 8, 1),
            provider_name="Repsol",
            utility_type=UtilityType.ELECTRICITY,
        ),
    )

    # 3. Factura con error (ej. CUPS no encontrado)
    cups_error = PropertyNotFoundForCUPSError("CUPS no encontrado", cups="ES9999999999999999PR0F")

    single_use_case.execute.side_effect = [res_success, dup_error, cups_error]

    batch_use_case = ProcessBatchUtilityInvoicesUseCase(single_use_case)
    batch_result = batch_use_case.execute(
        files=[
            ("factura1.pdf", b"pdf1"),
            ("factura2.pdf", b"pdf2"),
            ("factura3.pdf", b"pdf3"),
        ],
        user_id="user_123",
    )

    assert batch_result.total_processed == 3
    assert batch_result.successful_count == 1
    assert batch_result.duplicate_count == 1
    assert batch_result.error_count == 1
    assert batch_result.total_amount_imported == Decimal("80.00")

    assert batch_result.items[0].status == "success"
    assert batch_result.items[0].filename == "factura1.pdf"
    assert batch_result.items[0].property_name == sample_property.name

    assert batch_result.items[1].status == "duplicate"
    assert batch_result.items[1].filename == "factura2.pdf"
    assert batch_result.items[1].cups == "ES0031103721971011PR0F"

    assert batch_result.items[2].status == "error"
    assert batch_result.items[2].filename == "factura3.pdf"

