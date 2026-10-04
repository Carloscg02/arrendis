import logging
from datetime import date
from decimal import Decimal

from backend.domain.entities import ExtractionConfidence, UtilityType
from backend.domain.ports import LLMProviderPort
from backend.domain.value_objects import LLMRequest, UtilityInvoiceData
from backend.adapters.extraction.base import ExtractionStrategy
from backend.adapters.extraction.privacy_scrubber import PrivacyScrubber

logger = logging.getLogger(__name__)


class AIExtractionStrategy(ExtractionStrategy):
    """Estrategia de extracción resiliente basada en LLM (Gemini Flash vía LLMProviderPort).

    Se invoca cuando:
    - La factura proviene de una comercializadora no registrada en el registry.
    - La estrategia Regex específica falló (diseño del PDF modificado, etc.).
    """

    SYSTEM_PROMPT = (
        "Eres un asistente contable experto en facturas de suministros españoles (luz, gas y agua).\n"
        "Tu objetivo es extraer con máxima precisión los siguientes campos de la factura proporcionada:\n"
        "- cups: Código Unificado de Punto de Suministro (formato español: ES + 16-18 dígitos + 2-4 caracteres alfanuméricos, SIN ESPACIOS intermedios ni separadores).\n"
        "- amount: Importe total de la factura a pagar en euros (número decimal positivo).\n"
        "- issue_date: Fecha de emisión de la factura en formato ISO (YYYY-MM-DD).\n"
        "- provider_name: Nombre de la empresa comercializadora o suministradora.\n"
        "- utility_type: Tipo de suministro ('electricity', 'gas' o 'water').\n"
        "- invoice_number: Número identificativo de la factura (opcional).\n\n"
        "Si algún campo no está explícito pero se deduce unívocamente, extráelo. "
        "Si no encuentras el CUPS o el importe total, responde con null en dicho campo."
    )

    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "cups": {"type": "string", "description": "CUPS de la factura"},
            "amount": {"type": "number", "description": "Importe total en euros"},
            "issue_date": {"type": "string", "description": "Fecha de emisión en formato YYYY-MM-DD"},
            "provider_name": {"type": "string", "description": "Nombre de la comercializadora"},
            "utility_type": {"type": "string", "enum": ["electricity", "gas", "water"]},
            "invoice_number": {"type": "string", "description": "Número de factura"},
        },
        "required": ["cups", "amount", "issue_date", "provider_name", "utility_type"],
    }

    def __init__(self, llm_provider: LLMProviderPort) -> None:
        self._llm = llm_provider

    @property
    def provider_name(self) -> str:
        return "AI_Fallback"

    def can_handle(self, text: str) -> bool:
        return True  # Universal

    def extract(self, text: str) -> UtilityInvoiceData | None:
        # 1. Aplicar Scrubbing de Privacidad GDPR
        scrubbed_text = PrivacyScrubber.scrub(text)

        # 2. Petición estructurada al LLM
        request = LLMRequest(
            user_prompt=f"Extrae los datos de esta factura:\n\n{scrubbed_text}",
            system_prompt=self.SYSTEM_PROMPT,
            response_schema=self.RESPONSE_SCHEMA,
            temperature=0.0,
            max_output_tokens=1024,
        )

        try:
            response = self._llm.generate(request)
            data = response.parsed_data
            if not data or not data.get("cups") or data.get("amount") is None:
                return None

            clean_cups = "".join(data["cups"].split()).upper()
            if not clean_cups:
                return None

            return UtilityInvoiceData(
                cups=clean_cups,
                amount=Decimal(str(data["amount"])),
                issue_date=date.fromisoformat(data["issue_date"]),
                provider_name=data["provider_name"].strip(),
                utility_type=UtilityType(data["utility_type"].lower()),
                invoice_number=data.get("invoice_number"),
                extraction_confidence=ExtractionConfidence.MEDIUM,
            )
        except Exception as e:
            logger.warning(f"Error en AIExtractionStrategy al extraer datos con LLM: {e}", exc_info=True)
            return None


# Alias semántico
GeminiInvoiceExtractor = AIExtractionStrategy
