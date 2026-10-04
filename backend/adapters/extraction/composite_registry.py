from __future__ import annotations

from backend.domain.entities import ExtractionFailedError
from backend.domain.ports import InvoiceExtractorPort, ExtractedInvoice
from backend.adapters.extraction.base import ExtractionStrategy, UtilityExtractorRegistry


class CompositeInvoiceExtractor(InvoiceExtractorPort):
    """Adaptador compuesto que implementa InvoiceExtractorPort.

    Orquesta la ejecución priorizando estrategias deterministas (Regex por comercializadora)
    y delegando en la estrategia de contingencia de IA cuando el formato no coincide o falla.
    """

    def __init__(
        self,
        registry: UtilityExtractorRegistry,
        fallback_strategy: ExtractionStrategy | None = None,
    ) -> None:
        self._registry = registry
        self._fallback_strategy = fallback_strategy

    def extract_invoice_data(self, document_text: str) -> ExtractedInvoice | None:
        """Extrae datos de la factura respetando la cascada Regex -> IA."""
        # 1. Intentar estrategia Regex según comercializadora
        strategy = self._registry.find_strategy(document_text)
        if strategy is not None:
            data = strategy.extract(document_text)
            if data is not None:
                return ExtractedInvoice(data=data, strategy_used=strategy.provider_name)

        # 2. Si no hubo coincidencia Regex o falló la extracción, evaluar fallback
        if self._fallback_strategy is None:
            raise ExtractionFailedError(
                "No se pudo extraer la factura con reglas Regex y no hay estrategia de IA configurada."
            )

        fallback_data = self._fallback_strategy.extract(document_text)
        if fallback_data is None:
            raise ExtractionFailedError(
                "La extracción de la factura no pudo completarse ni por Regex ni por IA."
            )

        return ExtractedInvoice(
            data=fallback_data,
            strategy_used=self._fallback_strategy.provider_name,
        )
