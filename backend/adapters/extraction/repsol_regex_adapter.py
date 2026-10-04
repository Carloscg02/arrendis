import re
from datetime import datetime
from decimal import Decimal

from backend.domain.entities import ExtractionConfidence, UtilityType
from backend.domain.value_objects import UtilityInvoiceData
from backend.adapters.extraction.base import ExtractionStrategy


class RepsolExtractionStrategy(ExtractionStrategy):
    """Estrategia de extracción por Regex optimizada para facturas de Repsol.

    Analiza la estructura secuencial etiqueta -> valor que genera PyMuPDF en las
    facturas de Repsol Comercializadora de Electricidad y Gas, S.L.U.
    """

    @property
    def provider_name(self) -> str:
        return "Repsol"

    def can_handle(self, text: str) -> bool:
        """Detecta menciones a Repsol en el texto de la factura."""
        return bool(re.search(r'\bREPSOL\b', text, re.IGNORECASE))

    def extract(self, text: str) -> UtilityInvoiceData | None:
        try:
            # 1. CUPS
            cups_match = re.search(r'CUPS\s*\n\s*(ES\d{16,18}[A-Z0-9]{0,4})', text, re.IGNORECASE)
            if not cups_match:
                return None
            cups = cups_match.group(1).strip().upper()

            # 2. Total Factura
            total_match = re.search(r'Total factura\s*\n\s*([\d.,]+)\s*€', text, re.IGNORECASE)
            if not total_match:
                return None
            amount_str = total_match.group(1).strip().replace('.', '').replace(',', '.')
            amount = Decimal(amount_str)

            # 3. Fecha de emisión
            date_match = re.search(r'Fecha de emisión\s*\n\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if not date_match:
                return None
            issue_date = datetime.strptime(date_match.group(1).strip(), "%d/%m/%Y").date()

            # 4. Número de factura
            inv_match = re.search(r'Nº de factura\s*\n\s*([A-Za-z0-9]+)', text, re.IGNORECASE)
            invoice_number = inv_match.group(1).strip() if inv_match else None

            # 5. Tipo de suministro
            utility_type = UtilityType.ELECTRICITY
            if re.search(r'factura de gas', text, re.IGNORECASE):
                utility_type = UtilityType.GAS

            return UtilityInvoiceData(
                cups=cups,
                amount=amount,
                issue_date=issue_date,
                provider_name="Repsol Comercializadora de Electricidad y Gas, S.L.U.",
                utility_type=utility_type,
                invoice_number=invoice_number,
                extraction_confidence=ExtractionConfidence.HIGH,
            )
        except Exception:
            return None


# Alias semántico
RepsolInvoiceExtractor = RepsolExtractionStrategy
