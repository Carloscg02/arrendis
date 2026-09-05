"""
Tests unitarios para AIExtractionStrategy (F-18 / LLM Fallback).

Verifica la integración con LLMProviderPort, el paso previo por PrivacyScrubber
y la construcción de UtilityInvoiceData con confianza MEDIUM.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from backend.domain.entities import ExtractionConfidence, UtilityType
from backend.domain.extraction import AIExtractionStrategy
from backend.domain.ports import LLMProviderPort
from backend.domain.value_objects import LLMRequest, LLMResponse


def test_ai_strategy_scrubs_text_before_calling_llm():
    """UT-F18-15: Aplica PrivacyScrubber antes de enviar el prompt al LLM."""
    mock_llm = MagicMock(spec=LLMProviderPort)
    mock_llm.generate.return_value = LLMResponse(
        text='{"cups": "ES0031103721971011PR0F", "amount": 80.50, "issue_date": "2026-08-01", "provider_name": "Endesa", "utility_type": "electricity"}',
        parsed_data={
            "cups": "ES0031103721971011PR0F",
            "amount": 80.50,
            "issue_date": "2026-08-01",
            "provider_name": "Endesa",
            "utility_type": "electricity",
            "invoice_number": "INV-12345",
        },
    )

    strategy = AIExtractionStrategy(llm_provider=mock_llm)
    raw_text = (
        "Factura Endesa\n"
        "Titular: Alvaro Heredia Casado con DNI 53918290B y cuenta *3940\n"
        "CUPS: ES0031103721971011PR0F\n"
        "Total factura: 80,50 €\n"
    )

    strategy.extract(raw_text)

    assert mock_llm.generate.called
    call_args: LLMRequest = mock_llm.generate.call_args[0][0]
    # Comprobar que los datos sensibles NO viajan en el prompt
    assert "53918290B" not in call_args.user_prompt
    assert "*3940" not in call_args.user_prompt
    assert "[REDACTED_NIF]" in call_args.user_prompt
    assert "[REDACTED_IBAN]" in call_args.user_prompt


def test_ai_strategy_parses_valid_structured_data():
    """UT-F18-16: Parsea parsed_data del LLM y asigna ExtractionConfidence.MEDIUM."""
    mock_llm = MagicMock(spec=LLMProviderPort)
    mock_llm.generate.return_value = LLMResponse(
        text="{}",
        parsed_data={
            "cups": "ES0031103721971011PR0F",
            "amount": 80.50,
            "issue_date": "2026-08-01",
            "provider_name": "Endesa Energía",
            "utility_type": "electricity",
            "invoice_number": "INV-12345",
        },
    )

    strategy = AIExtractionStrategy(llm_provider=mock_llm)
    data = strategy.extract("Texto de factura...")

    assert data is not None
    assert data.cups == "ES0031103721971011PR0F"
    assert data.amount == Decimal("80.5")
    assert data.issue_date == date(2026, 8, 1)
    assert data.provider_name == "Endesa Energía"
    assert data.utility_type == UtilityType.ELECTRICITY
    assert data.invoice_number == "INV-12345"
    assert data.extraction_confidence == ExtractionConfidence.MEDIUM


def test_ai_strategy_returns_none_on_invalid_or_missing_fields():
    """UT-F18-17: Retorna None si el LLM no extrae los campos requeridos o hay error."""
    mock_llm = MagicMock(spec=LLMProviderPort)

    # Caso 1: parsed_data vacío o None
    mock_llm.generate.return_value = LLMResponse(text="", parsed_data=None)
    strategy = AIExtractionStrategy(llm_provider=mock_llm)
    assert strategy.extract("Texto...") is None

    # Caso 2: parsed_data con campos nulos
    mock_llm.generate.return_value = LLMResponse(
        text="{}",
        parsed_data={"cups": None, "amount": 50.0},
    )
    assert strategy.extract("Texto...") is None

    # Caso 3: LLM lanza excepción
    mock_llm.generate.side_effect = RuntimeError("Error en conexión con API de IA")
    assert strategy.extract("Texto...") is None
