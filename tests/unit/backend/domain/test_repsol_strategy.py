"""
Tests unitarios para RepsolExtractionStrategy (F-18 / Regex).

Verifica la detección y extracción de facturas de Repsol por expresiones regulares.
"""

from datetime import date
from decimal import Decimal

from backend.domain.entities import ExtractionConfidence, UtilityType
from backend.domain.extraction import RepsolExtractionStrategy


def test_repsol_strategy_can_handle_repsol_text():
    """UT-F18-07: can_handle retorna True si el texto menciona Repsol."""
    strategy = RepsolExtractionStrategy()
    assert strategy.can_handle("Factura emitida por Repsol Comercializadora de Electricidad")
    assert strategy.can_handle("atención al cliente repsol")
    assert strategy.provider_name == "Repsol"


def test_repsol_strategy_cannot_handle_other_providers():
    """UT-F18-08: can_handle retorna False para otras comercializadoras."""
    strategy = RepsolExtractionStrategy()
    assert not strategy.can_handle("Factura de Endesa Energía S.A.")
    assert not strategy.can_handle("Iberdrola Clientes S.A.U.")
    assert not strategy.can_handle("Naturgy Iberia S.A.")


def test_repsol_strategy_extracts_valid_invoice():
    """UT-F18-09: Extrae correctamente todos los campos desde texto de Repsol."""
    strategy = RepsolExtractionStrategy()
    sample_text = (
        "Factura de luz\n"
        "Esta es tu factura de luz,\n"
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Nº de contrato\n"
        "4305565356\n"
        "Nº de factura\n"
        "61088387754\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Total factura\n"
        "75,46 €\n"
        "Repsol Comercializadora de Electricidad y Gas, S.L.U.\n"
    )

    data = strategy.extract(sample_text)
    assert data is not None
    assert data.cups == "ES0031103721971011PR0F"
    assert data.amount == Decimal("75.46")
    assert data.issue_date == date(2026, 8, 1)
    assert data.invoice_number == "61088387754"
    assert data.utility_type == UtilityType.ELECTRICITY
    assert data.provider_name == "Repsol Comercializadora de Electricidad y Gas, S.L.U."


def test_repsol_strategy_assigns_high_confidence():
    """UT-F18-10: Asigna ExtractionConfidence.HIGH."""
    strategy = RepsolExtractionStrategy()
    sample_text = (
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Nº de factura\n"
        "61088387754\n"
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Total factura\n"
        "75,46 €\n"
    )
    data = strategy.extract(sample_text)
    assert data is not None
    assert data.extraction_confidence == ExtractionConfidence.HIGH


def test_repsol_strategy_returns_none_if_missing_required_fields():
    """UT-F18-11: Retorna None si falta el CUPS o el importe."""
    strategy = RepsolExtractionStrategy()

    # Falta CUPS
    text_without_cups = "Total factura\n75,46 €\nFecha de emisión\n01/08/2026\n"
    assert strategy.extract(text_without_cups) is None

    # Falta importe
    text_without_amount = "CUPS\nES0031103721971011PR0F\nFecha de emisión\n01/08/2026\n"
    assert strategy.extract(text_without_amount) is None

    # Importe corrupto / no parseable
    text_invalid_amount = "CUPS\nES0031103721971011PR0F\nTotal factura\nno_es_un_numero €\n"
    assert strategy.extract(text_invalid_amount) is None
