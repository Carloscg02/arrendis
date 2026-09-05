"""
Estrategias y Registro de Extracción de Facturas de Suministros (E-02 / F-18).

Implementa el Patrón Estrategia (Strategy Pattern) y el Patrón Registro (Registry)
para garantizar el Principio de Abierto/Cerrado (OCP), además de la capa de
anonimización de datos personales (PrivacyScrubber) conforme al RGPD / GDPR.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal

from backend.domain.entities import ExtractionConfidence, UtilityType
from backend.domain.ports import LLMProviderPort
from backend.domain.value_objects import LLMRequest, UtilityInvoiceData


# ──────────────────────────────────────────────
# Servicio de Dominio: PrivacyScrubber (GDPR)
# ──────────────────────────────────────────────

class PrivacyScrubber:
    """Servicio de dominio para anonimizar datos personales (PII) antes del envío a LLMs.

    Garantiza el principio de minimización de datos del RGPD (Art. 5.1.c) conservando
    intactos los datos técnicos requeridos para la extracción (CUPS, importes, fechas).
    """

    _DNI_REGEX = re.compile(r'\b\d{8}[A-HJ-NP-TV-Z]\b', re.IGNORECASE)
    _NIE_REGEX = re.compile(r'\b[XYZ]\d{7}[A-Z]\b', re.IGNORECASE)
    _CIF_REGEX = re.compile(r'\b[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]\b', re.IGNORECASE)
    _IBAN_REGEX = re.compile(r'\bES\d{2}(?:[\s\-]?\d){20}\b', re.IGNORECASE)
    _MASKED_ACCOUNT_REGEX = re.compile(r'\*{1,}\d{4}')

    _SAFE_KEYWORDS = [
        'cups', 'total factura', 'nº de factura', 'nº de contrato',
        'fecha de emisión', 'periodo de facturación', 'término fijo',
        'energía', 'servicios', 'otros conceptos', 'impuestos', 'consumo',
        'forma de pago', 'fecha de cobro', 'otras vías', 'e-mail',
        'incidencias', 'asistencia', 'portal de consumo', 'información al cliente',
        'peajes de transporte', 'cuota de comercialización', 'potencia contratada',
        'fecha fin de contrato', 'permanencia de contrato', 'distribuidora',
        'peaje de transporte', 'segmentos de cargos', 'nº de contador',
        'nº contrato de acceso', 'tipo de tarifa', 'comercializadora',
        'concepto', 'importe', 'días facturados'
    ]

    _PII_HEADERS = [
        'nombre y apellidos', 'esta es tu factura de', 'titular y datos de pago',
        'dirección de suministro', 'dirección postal', 'cuenta bancaria',
        'localizador de pago', 'dni'
    ]

    @classmethod
    def _apply_inline_redactions(cls, text: str) -> str:
        processed = cls._IBAN_REGEX.sub('[REDACTED_IBAN]', text)
        processed = cls._DNI_REGEX.sub('[REDACTED_NIF]', processed)
        processed = cls._NIE_REGEX.sub('[REDACTED_NIF]', processed)
        processed = cls._CIF_REGEX.sub('[REDACTED_NIF]', processed)
        processed = cls._MASKED_ACCOUNT_REGEX.sub('[REDACTED_IBAN]', processed)
        return processed

    @classmethod
    def scrub(cls, raw_text: str) -> str:
        """Anonimiza PII en el texto respetando los datos técnicos y fiscales."""
        lines = raw_text.splitlines()
        scrubbed_lines: list[str] = []
        redacting_section = False
        last_header: list[str] = []

        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()

            # Si encontramos una palabra clave técnica segura, salimos del modo redacción
            if any(lower.startswith(k) for k in cls._SAFE_KEYWORDS):
                redacting_section = False

            if redacting_section:
                if stripped == '':
                    redacting_section = False
                    scrubbed_lines.append(line)
                else:
                    scrubbed_lines.append('[REDACTED_PII]')
                    # Si el encabezado era de valor de una sola línea, resetear
                    if any(h in ['dni', 'cuenta bancaria'] for h in last_header):
                        redacting_section = False
                continue

            # Comprobar si la línea es un encabezado de PII
            matched_header = [h for h in cls._PII_HEADERS if lower.startswith(h)]
            if matched_header:
                last_header = matched_header
                scrubbed_lines.append(cls._apply_inline_redactions(stripped))
                redacting_section = True
                continue

            scrubbed_lines.append(cls._apply_inline_redactions(stripped))

        return "\n".join(scrubbed_lines)


# ──────────────────────────────────────────────
# Contrato de Estrategia de Extracción
# ──────────────────────────────────────────────

class ExtractionStrategy(ABC):
    """Contrato base para cualquier estrategia de extracción de facturas de suministros."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre canónico del proveedor o estrategia (ej. 'Repsol', 'AI_Fallback')."""
        ...

    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """Determina si esta estrategia reconoce el formato del texto de la factura."""
        ...

    @abstractmethod
    def extract(self, text: str) -> UtilityInvoiceData | None:
        """Extrae los datos estructurados del texto.

        Returns:
            UtilityInvoiceData si todos los campos requeridos se extrajeron correctamente.
            None si la extracción no fue concluyente o falló la validación.
        """
        ...


# ──────────────────────────────────────────────
# Estrategia Regex: Repsol
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Estrategia IA (Fallback Universal)
# ──────────────────────────────────────────────

class AIExtractionStrategy(ExtractionStrategy):
    """Estrategia de extracción resiliente basada en LLM (Gemini Flash vía LLMProviderPort).

    Se invoca cuando:
    - La factura proviene de una comercializadora no registrada en el registry.
    - La estrategia Regex específica falló (diseño del PDF modificado, etc.).
    """

    SYSTEM_PROMPT = (
        "Eres un asistente contable experto en facturas de suministros españoles (luz, gas y agua).\n"
        "Tu objetivo es extraer con máxima precisión los siguientes campos de la factura proporcionada:\n"
        "- cups: Código Unificado de Punto de Suministro (formato español: ES + 16-18 dígitos + caracteres alfanuméricos).\n"
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

            return UtilityInvoiceData(
                cups=data["cups"].strip().upper(),
                amount=Decimal(str(data["amount"])),
                issue_date=date.fromisoformat(data["issue_date"]),
                provider_name=data["provider_name"].strip(),
                utility_type=UtilityType(data["utility_type"].lower()),
                invoice_number=data.get("invoice_number"),
                extraction_confidence=ExtractionConfidence.MEDIUM,
            )
        except Exception:
            return None


# ──────────────────────────────────────────────
# Registro Desacoplado: UtilityExtractorRegistry
# ──────────────────────────────────────────────

class UtilityExtractorRegistry:
    """Registro extensible de estrategias de extracción de facturas (Open/Closed Principle).

    Permite incorporar soporte para nuevas comercializadoras en tiempo de ejecución
    o configuración sin modificar el código del caso de uso.
    """

    def __init__(self, strategies: list[ExtractionStrategy] | None = None) -> None:
        self._strategies: list[ExtractionStrategy] = list(strategies or [])

    def register(self, strategy: ExtractionStrategy) -> None:
        """Añade una nueva estrategia al registro."""
        self._strategies.append(strategy)

    def find_strategy(self, text: str) -> ExtractionStrategy | None:
        """Retorna la primera estrategia cuyo can_handle() devuelva True."""
        for strategy in self._strategies:
            if strategy.can_handle(text):
                return strategy
        return None

    @property
    def registered_providers(self) -> list[str]:
        return [s.provider_name for s in self._strategies]
