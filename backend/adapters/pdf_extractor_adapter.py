"""
Adaptador de extracción de texto plano desde PDFs usando PyMuPDF (fitz).

Implementa el puerto PDFTextExtractorPort para el subdominio de suministros (E-02 / F-18).
"""

from __future__ import annotations

import fitz  # PyMuPDF
from backend.domain.entities import EmptyPDFTextError, PDFExtractionError
from backend.domain.ports import PDFTextExtractorPort


class PyMuPDFTextExtractorAdapter(PDFTextExtractorPort):
    """Adaptador que implementa PDFTextExtractorPort utilizando PyMuPDF (fitz).

    PyMuPDF realiza la extracción del árbol vectorial de texto en memoria
    con alto rendimiento (motor C++ MuPDF) y sin I/O en disco.
    """

    def extract_text(self, pdf_bytes: bytes) -> str:
        if not pdf_bytes:
            raise EmptyPDFTextError("El archivo PDF recibido está vacío (0 bytes).")

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise PDFExtractionError(f"No se pudo abrir el documento PDF: {e}") from e

        try:
            if doc.is_encrypted:
                raise PDFExtractionError("El documento PDF está protegido con contraseña.")

            pages_text: list[str] = []
            for page in doc:
                text = page.get_text("text")
                if text:
                    pages_text.append(text)

            full_text = "\n".join(pages_text).strip()
            if not full_text:
                raise EmptyPDFTextError(
                    "El documento PDF no contiene capa de texto digital. "
                    "Es probable que sea una imagen escaneada que requiere OCR."
                )

            return full_text
        finally:
            doc.close()
