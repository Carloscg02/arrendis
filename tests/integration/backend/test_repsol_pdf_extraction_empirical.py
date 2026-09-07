"""
Test de integración empírico: Extracción sobre la muestra real de Repsol (F-18).

Procesa directamente el archivo PDF 'specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf'
utilizando el adaptador PyMuPDFTextExtractorAdapter y la estrategia RepsolExtractionStrategy.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from backend.adapters.pdf_extractor_adapter import PyMuPDFTextExtractorAdapter
from backend.domain.entities import ExtractionConfidence, UtilityType
from backend.domain.extraction import RepsolExtractionStrategy


def test_empirical_extraction_repsol_sample_pdf():
    """IT-F18-01: Extrae con 100% de precisión la factura real de Repsol disponible."""
    sample_path = Path("specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf")
    assert sample_path.exists(), f"El archivo de muestra no existe en {sample_path}"

    pdf_bytes = sample_path.read_bytes()
    assert len(pdf_bytes) > 0

    # 1. Extracción con PyMuPDF
    extractor = PyMuPDFTextExtractorAdapter()
    raw_text = extractor.extract_text(pdf_bytes)

    assert len(raw_text) > 0
    assert "REPSOL" in raw_text.upper()

    # 2. Extracción con RepsolExtractionStrategy
    strategy = RepsolExtractionStrategy()
    assert strategy.can_handle(raw_text) is True

    invoice_data = strategy.extract(raw_text)
    assert invoice_data is not None

    # 3. Comprobación exacta de los campos del documento real
    assert invoice_data.cups == "ES0031103721971011PR0F"
    assert invoice_data.amount == Decimal("75.46")
    assert invoice_data.issue_date == date(2026, 8, 1)
    assert invoice_data.invoice_number == "61088387754"
    assert invoice_data.utility_type == UtilityType.ELECTRICITY
    assert invoice_data.extraction_confidence == ExtractionConfidence.HIGH
    assert "Repsol" in invoice_data.provider_name
