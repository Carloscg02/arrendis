import os
import re
import json
import time
import random
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.domain.ports import MarketValuationPort
from backend.domain.entities import (
    PropertyType,
    PropertyCondition,
    ValuationConfidence,
    MarketValuationError,
    ValuationRateLimitError,
)
from backend.domain.value_objects import (
    Address,
    Money,
    ValuationRange,
    ReasoningFactor,
    ValuationSource,
    MarketValuationResult,
)


class _RangePayload(BaseModel):
    min: Decimal
    median: Decimal
    max: Decimal


class _FactorPayload(BaseModel):
    factor_name: str
    impact_percent: float
    description: str


class _SourcePayload(BaseModel):
    title: str
    url: str
    price: Decimal | None = None
    surface_m2: int | None = None


class _GeminiValuationPayload(BaseModel):
    sale_range: _RangePayload
    rent_range: _RangePayload
    confidence: str
    reasoning_factors: list[_FactorPayload] = Field(default_factory=list)
    sources: list[_SourcePayload] = Field(default_factory=list)
    raw_notes: str | None = None


class GeminiMarketValuationAdapter(MarketValuationPort):
    """Adaptador de infraestructura para estimación de mercado con Gemini Flash y Search Grounding."""

    PROVIDER_NAME = "gemini"
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1.0
    MAX_BACKOFF_SECONDS = 30.0

    def __init__(self, api_key: str, model_name: str | None = None) -> None:
        if not api_key or not api_key.strip():
            raise MarketValuationError("API key is required", provider=self.PROVIDER_NAME)
        self.api_key = api_key
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            self.client = genai.Client(
                api_key=api_key,
                http_options={"api_version": "v1alpha", "timeout": 45.0},
            )
        except Exception as e:
            raise MarketValuationError(f"Failed to initialize Gemini client: {e}", provider=self.PROVIDER_NAME)

    def estimate_valuation(
        self,
        address: Address,
        surface_m2: int,
        property_type: PropertyType = PropertyType.APARTMENT,
        bedrooms: int | None = None,
        bathrooms: int | None = None,
        floor: int | None = None,
        has_elevator: bool | None = None,
        condition: PropertyCondition | None = None,
    ) -> MarketValuationResult:
        if surface_m2 <= 0:
            raise ValueError(f"La superficie construida debe ser positiva: {surface_m2}")

        system_instruction = (
            "Eres un tasador y analista inmobiliario senior experto en el mercado residencial y comercial de España.\n"
            "Tu objetivo es estimar con el mayor rigor y objetividad posible:\n"
            "1. La horquilla de precio de venta en EUR (min, median, max).\n"
            "2. La horquilla de renta mensual de alquiler en EUR (min, median, max).\n"
            "3. El nivel de confianza del análisis ('HIGH', 'MEDIUM', 'LOW').\n"
            "4. Factores explicativos de corrección (porcentaje de impacto cualitativo/cuantitativo y descripción).\n"
            "5. Anuncios y testigos de mercado comparables reales encontrados mediante búsqueda web.\n\n"
            "INSTRUCCIONES DE BÚSQUEDA Y GROUNDING:\n"
            "- Realiza búsquedas precisas en Google sobre portales líderes en España (Idealista, Fotocasa, Habitaclia, Yaencontre) "
            "para la zona, barrio, código postal y municipio indicados.\n"
            "- Extrae los testigos más relevantes y comparables por superficie y tipología.\n\n"
            "FORMATO DE SALIDA:\n"
            "Debes responder EXCLUSIVAMENTE con un objeto JSON válido, sin rodeos ni explicaciones fuera del bloque JSON.\n"
            "Estructura JSON esperada:\n"
            "{\n"
            '  "sale_range": {"min": 180000, "median": 195000, "max": 210000},\n'
            '  "rent_range": {"min": 850, "median": 920, "max": 1000},\n'
            '  "confidence": "HIGH",\n'
            '  "reasoning_factors": [\n'
            '    {"factor_name": "Ascensor", "impact_percent": 7.5, "description": "Tercera planta con ascensor bonifica sobre la media del barrio"}\n'
            "  ],\n"
            '  "sources": [\n'
            '    {"title": "Piso en venta en Calle...", "url": "https://www.idealista.com/...", "price": 190000, "surface_m2": 80}\n'
            "  ],\n"
            '  "raw_notes": "Resumen conciso del mercado de la zona..."\n'
            "}\n"
        )

        user_prompt = (
            f"Por favor, calcula la estimación de venta y alquiler para el siguiente inmueble:\n"
            f"- Tipología: {property_type.value}\n"
            f"- Dirección: {address.street}, {address.city} (CP: {address.postal_code}, País: {address.country})\n"
            f"- Superficie: {surface_m2} m2\n"
            f"- Dormitorios: {bedrooms if bedrooms is not None else 'No especificado'}\n"
            f"- Baños: {bathrooms if bathrooms is not None else 'No especificado'}\n"
            f"- Planta: {floor if floor is not None else 'No especificada'}\n"
            f"- Ascensor: {'Sí' if has_elevator is True else ('No' if has_elevator is False else 'Desconocido')}\n"
            f"- Estado de conservación: {condition.value if condition else 'No especificado'}\n"
        )

        config = types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=system_instruction,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )

        retries = 0
        backoff = self.INITIAL_BACKOFF_SECONDS

        while True:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=config,
                )
                return self._parse_response(response)

            except APIError as e:
                is_retryable = False
                if e.code == 429 or (e.code and e.code >= 500):
                    is_retryable = True

                if is_retryable and retries < self.MAX_RETRIES:
                    jitter = random.uniform(0, 0.1 * backoff)
                    sleep_time = backoff + jitter
                    time.sleep(sleep_time)
                    retries += 1
                    backoff = min(backoff * 2.0, self.MAX_BACKOFF_SECONDS)
                    continue
                else:
                    if e.code == 429:
                        raise ValuationRateLimitError(provider=self.PROVIDER_NAME)
                    raise MarketValuationError(f"API Error ({e.code}): {str(e)}", provider=self.PROVIDER_NAME)
            except ValuationRateLimitError:
                raise
            except MarketValuationError:
                raise
            except Exception as e:
                if retries < self.MAX_RETRIES and ("timeout" in str(e).lower() or "read" in str(e).lower()):
                    jitter = random.uniform(0, 0.1 * backoff)
                    time.sleep(backoff + jitter)
                    retries += 1
                    backoff = min(backoff * 2.0, self.MAX_BACKOFF_SECONDS)
                    continue
                raise MarketValuationError(f"Unexpected error: {str(e)}", provider=self.PROVIDER_NAME)

    def _parse_response(self, response: Any) -> MarketValuationResult:
        if not response or not getattr(response, "candidates", None):
            raise MarketValuationError("Respuesta vacía o bloqueada por el proveedor", provider=self.PROVIDER_NAME)

        candidate = response.candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        if finish_reason and str(finish_reason).upper() not in ("STOP", "FINISH_REASON_STOP", "1", "NONE"):
            raise MarketValuationError(
                f"Generación finalizada por motivo no estándar: {finish_reason}",
                provider=self.PROVIDER_NAME,
            )

        raw_text = response.text or ""
        json_str = self._extract_json_block(raw_text)

        try:
            data = json.loads(json_str)
            payload = _GeminiValuationPayload.model_validate(data)
        except Exception as e:
            raise MarketValuationError(f"Fallo al decodificar JSON de valoración: {e}", provider=self.PROVIDER_NAME)

        # 1. Normalizar Confianza
        try:
            confidence = ValuationConfidence(payload.confidence.lower())
        except (ValueError, AttributeError):
            confidence = ValuationConfidence.LOW

        # 2. Normalizar Factores de Razonamiento
        reasoning_factors: list[ReasoningFactor] = []
        for f in payload.reasoning_factors:
            impact_dec = Decimal(str(f.impact_percent))
            # Normalizar a decimal fraccional (ej: 7.5% -> 0.075) si se proporcionó en escala 0-100
            if abs(impact_dec) > Decimal("1.0"):
                impact_dec = (impact_dec / Decimal("100")).quantize(Decimal("0.0001"))
            try:
                reasoning_factors.append(
                    ReasoningFactor(
                        factor_name=f.factor_name.strip() or "Factor de corrección",
                        impact_percent=impact_dec,
                        description=f.description.strip() or "Ajuste de valor por características del inmueble.",
                    )
                )
            except ValueError:
                continue

        # 3. Extraer Fuentes del payload y Grounding Chunks
        sources: list[ValuationSource] = []
        seen_urls: set[str] = set()

        for s in payload.sources:
            clean_url = s.url.strip()
            if clean_url.startswith("http://") or clean_url.startswith("https://"):
                title = s.title.strip() or clean_url
                try:
                    sources.append(
                        ValuationSource(
                            title=title,
                            url=clean_url,
                            price=s.price,
                            surface_m2=s.surface_m2,
                        )
                    )
                    seen_urls.add(clean_url)
                except ValueError:
                    continue

        # Extraer defensivamente chunks de búsqueda web de grounding_metadata
        grounding_metadata = getattr(candidate, "grounding_metadata", None)
        if grounding_metadata and getattr(grounding_metadata, "grounding_chunks", None):
            for chunk in grounding_metadata.grounding_chunks:
                web = getattr(chunk, "web", None)
                if not web:
                    continue
                uri = getattr(web, "uri", None)
                if not uri or not isinstance(uri, str):
                    continue
                clean_uri = uri.strip()
                if not (clean_uri.startswith("http://") or clean_uri.startswith("https://")):
                    continue
                if clean_uri in seen_urls:
                    continue

                raw_title = getattr(web, "title", None)
                title = raw_title.strip() if raw_title and isinstance(raw_title, str) else clean_uri
                try:
                    sources.append(
                        ValuationSource(
                            title=title,
                            url=clean_uri,
                        )
                    )
                    seen_urls.add(clean_uri)
                except ValueError:
                    continue

        # 4. Construir rangos ordenados
        sale_vals = sorted([payload.sale_range.min, payload.sale_range.median, payload.sale_range.max])
        rent_vals = sorted([payload.rent_range.min, payload.rent_range.median, payload.rent_range.max])

        sale_range = ValuationRange(
            min_price=Money(sale_vals[0].quantize(Decimal("1.00"))),
            median_price=Money(sale_vals[1].quantize(Decimal("1.00"))),
            max_price=Money(sale_vals[2].quantize(Decimal("1.00"))),
        )
        rent_range = ValuationRange(
            min_price=Money(rent_vals[0].quantize(Decimal("1.00"))),
            median_price=Money(rent_vals[1].quantize(Decimal("1.00"))),
            max_price=Money(rent_vals[2].quantize(Decimal("1.00"))),
        )

        # Invariante: Si confianza es LOW o MEDIUM, garantizar nota o factor
        raw_notes = payload.raw_notes
        if confidence in (ValuationConfidence.LOW, ValuationConfidence.MEDIUM):
            if not reasoning_factors and not (raw_notes and raw_notes.strip()):
                raw_notes = "Estimación basada en datos de mercado de la zona con dispersión moderada."

        return MarketValuationResult(
            sale_range=sale_range,
            rent_range=rent_range,
            confidence=confidence,
            reasoning_factors=reasoning_factors,
            sources=sources,
            raw_notes=raw_notes,
        )

    @staticmethod
    def _extract_json_block(text: str) -> str:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()
        return text


class MockMarketValuationAdapter(MarketValuationPort):
    """Adaptador de pruebas con fórmulas heurísticas deterministas sin dependencias externas."""

    def estimate_valuation(
        self,
        address: Address,
        surface_m2: int,
        property_type: PropertyType = PropertyType.APARTMENT,
        bedrooms: int | None = None,
        bathrooms: int | None = None,
        floor: int | None = None,
        has_elevator: bool | None = None,
        condition: PropertyCondition | None = None,
    ) -> MarketValuationResult:
        if surface_m2 <= 0:
            raise ValueError(f"La superficie construida debe ser positiva: {surface_m2}")

        # Multiplicadores por estado de conservación
        condition_factors = {
            PropertyCondition.A_REFORMAR: Decimal("0.80"),
            PropertyCondition.BUEN_ESTADO: Decimal("1.00"),
            PropertyCondition.REFORMADO: Decimal("1.15"),
            PropertyCondition.A_ESTRENAR: Decimal("1.30"),
        }
        factor_cond = condition_factors.get(condition, Decimal("1.00"))

        # Factor ascensor
        elevator_factor = Decimal("0.00")
        if has_elevator is True:
            elevator_factor = Decimal("0.05")
        elif has_elevator is False and floor is not None and floor >= 2:
            elevator_factor = Decimal("-0.07")

        combined_mult = factor_cond * (Decimal("1.00") + elevator_factor)

        # Precio de venta base: 2200 €/m2
        sale_base_m2 = Decimal("2200")
        sale_median_raw = Decimal(surface_m2) * sale_base_m2 * combined_mult
        sale_median = (sale_median_raw / Decimal("100")).quantize(Decimal("1")) * Decimal("100")
        sale_min = (sale_median * Decimal("0.90")).quantize(Decimal("1.00"))
        sale_max = (sale_median * Decimal("1.10")).quantize(Decimal("1.00"))

        # Precio de alquiler base: 11 €/m2
        rent_base_m2 = Decimal("11")
        rent_median_raw = Decimal(surface_m2) * rent_base_m2 * combined_mult
        rent_median = (rent_median_raw / Decimal("10")).quantize(Decimal("1")) * Decimal("10")
        rent_min = (rent_median * Decimal("0.90")).quantize(Decimal("1.00"))
        rent_max = (rent_median * Decimal("1.10")).quantize(Decimal("1.00"))

        factors: list[ReasoningFactor] = []
        if condition:
            factors.append(
                ReasoningFactor(
                    factor_name=f"Estado {condition.value}",
                    impact_percent=Decimal(str((factor_cond - Decimal("1.00")).quantize(Decimal("0.01")))),
                    description=f"Ajuste por estado de conservación {condition.value}.",
                )
            )
        if elevator_factor != Decimal("0.00"):
            factors.append(
                ReasoningFactor(
                    factor_name="Ascensor",
                    impact_percent=elevator_factor,
                    description="Impacto de la presencia o ausencia de ascensor en la planta.",
                )
            )

        sources = [
            ValuationSource(
                title=f"Inmueble comparable en {address.city}",
                url="https://www.idealista.com/inmueble/mock12345",
                price=sale_median,
                surface_m2=surface_m2,
            ),
            ValuationSource(
                title=f"Alquiler similar en {address.street}",
                url="https://www.fotocasa.es/es/alquiler/inmueble/mock67890",
                price=rent_median,
                surface_m2=surface_m2,
            ),
        ]

        return MarketValuationResult(
            sale_range=ValuationRange(
                min_price=Money(sale_min),
                median_price=Money(sale_median),
                max_price=Money(sale_max),
            ),
            rent_range=ValuationRange(
                min_price=Money(rent_min),
                median_price=Money(rent_median),
                max_price=Money(rent_max),
            ),
            confidence=ValuationConfidence.HIGH,
            reasoning_factors=factors,
            sources=sources,
            raw_notes=f"Estimación mock calculada para {surface_m2} m2 en {address.city}.",
        )
