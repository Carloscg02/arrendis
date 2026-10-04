from unittest.mock import MagicMock
from decimal import Decimal
from datetime import date
import pytest

from backend.domain.entities import ExtractionFailedError, UtilityType, ExtractionConfidence
from backend.domain.value_objects import UtilityInvoiceData
from backend.domain.ports import ExtractedInvoice
from backend.adapters.extraction import (
    CompositeInvoiceExtractor,
    UtilityExtractorRegistry,
    ExtractionStrategy,
)


def test_composite_extractor_success_via_registry():
    mock_strategy = MagicMock(spec=ExtractionStrategy)
    mock_strategy.provider_name = "Repsol"
    mock_strategy.can_handle.return_value = True
    invoice_data = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("50.00"),
        issue_date=date(2026, 8, 1),
        provider_name="Repsol",
        utility_type=UtilityType.ELECTRICITY,
        extraction_confidence=ExtractionConfidence.HIGH,
    )
    mock_strategy.extract.return_value = invoice_data

    registry = UtilityExtractorRegistry([mock_strategy])
    extractor = CompositeInvoiceExtractor(registry=registry, fallback_strategy=None)

    result = extractor.extract_invoice_data("Texto de factura Repsol")
    assert isinstance(result, ExtractedInvoice)
    assert result.data == invoice_data
    assert result.strategy_used == "Repsol"


def test_composite_extractor_fallback_to_ai():
    mock_reg_strategy = MagicMock(spec=ExtractionStrategy)
    mock_reg_strategy.can_handle.return_value = False

    mock_ai = MagicMock(spec=ExtractionStrategy)
    mock_ai.provider_name = "AI_Fallback"
    invoice_data = UtilityInvoiceData(
        cups="ES0031103721971011PR0F",
        amount=Decimal("35.00"),
        issue_date=date(2026, 8, 1),
        provider_name="Aguas de Murcia",
        utility_type=UtilityType.WATER,
        extraction_confidence=ExtractionConfidence.MEDIUM,
    )
    mock_ai.extract.return_value = invoice_data

    registry = UtilityExtractorRegistry([mock_reg_strategy])
    extractor = CompositeInvoiceExtractor(registry=registry, fallback_strategy=mock_ai)

    result = extractor.extract_invoice_data("Texto de factura desconocida")
    assert isinstance(result, ExtractedInvoice)
    assert result.data == invoice_data
    assert result.strategy_used == "AI_Fallback"


def test_composite_extractor_raises_when_no_ai_configured():
    mock_reg_strategy = MagicMock(spec=ExtractionStrategy)
    mock_reg_strategy.can_handle.return_value = False

    registry = UtilityExtractorRegistry([mock_reg_strategy])
    extractor = CompositeInvoiceExtractor(registry=registry, fallback_strategy=None)

    with pytest.raises(ExtractionFailedError, match="no hay estrategia de IA configurada"):
        extractor.extract_invoice_data("Texto de factura")


def test_composite_extractor_raises_when_both_fail():
    mock_reg_strategy = MagicMock(spec=ExtractionStrategy)
    mock_reg_strategy.can_handle.return_value = True
    mock_reg_strategy.extract.return_value = None

    mock_ai = MagicMock(spec=ExtractionStrategy)
    mock_ai.extract.return_value = None

    registry = UtilityExtractorRegistry([mock_reg_strategy])
    extractor = CompositeInvoiceExtractor(registry=registry, fallback_strategy=mock_ai)

    with pytest.raises(ExtractionFailedError, match="no pudo completarse ni por Regex ni por IA"):
        extractor.extract_invoice_data("Texto corrupto")
