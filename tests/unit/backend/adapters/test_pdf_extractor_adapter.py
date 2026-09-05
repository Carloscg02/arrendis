"""
Tests unitarios para PyMuPDFTextExtractorAdapter (F-18 / Infraestructura).

Verifica la extracción de texto vectorial y la gestión de errores en archivos PDF.
"""

import fitz
import pytest

from backend.adapters.pdf_extractor_adapter import PyMuPDFTextExtractorAdapter
from backend.domain.entities import EmptyPDFTextError, PDFExtractionError


def test_pdf_extractor_adapter_extracts_text_from_valid_pdf():
    """IT-F18-03a: Extrae texto plano de un documento PDF digital válido."""
    # Crear un PDF en memoria usando PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Factura de Luz\nCUPS ES0031103721971011PR0F\nTotal: 75.46 €")
    pdf_bytes = doc.tobytes()
    doc.close()

    adapter = PyMuPDFTextExtractorAdapter()
    text = adapter.extract_text(pdf_bytes)

    assert "Factura de Luz" in text
    assert "ES0031103721971011PR0F" in text
    assert "75.46" in text


def test_pdf_extractor_adapter_raises_empty_pdf_on_zero_bytes():
    """IT-F18-03b: Lanza EmptyPDFTextError ante bytes vacíos (0 bytes)."""
    adapter = PyMuPDFTextExtractorAdapter()
    with pytest.raises(EmptyPDFTextError, match="vacío"):
        adapter.extract_text(b"")


def test_pdf_extractor_adapter_raises_pdf_extraction_error_on_corrupted_bytes():
    """IT-F18-03c: Lanza PDFExtractionError ante bytes corruptos o no-PDF."""
    adapter = PyMuPDFTextExtractorAdapter()
    with pytest.raises(PDFExtractionError, match="No se pudo abrir"):
        adapter.extract_text(b"no es un pdf valido")


def test_pdf_extractor_adapter_raises_empty_pdf_when_no_text_layer():
    """IT-F18-03d: Lanza EmptyPDFTextError si el PDF no tiene capa de texto (página en blanco)."""
    doc = fitz.open()
    doc.new_page()  # Página en blanco sin texto
    pdf_bytes = doc.tobytes()
    doc.close()

    adapter = PyMuPDFTextExtractorAdapter()
    with pytest.raises(EmptyPDFTextError, match="no contiene capa de texto"):
        adapter.extract_text(pdf_bytes)
