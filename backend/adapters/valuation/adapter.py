import os
import re
import json
import time
import random
from decimal import Decimal
from typing import Any
from concurrent.futures import ThreadPoolExecutor

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
    MarketValuationResult,
)
from backend.adapters.valuation.schemas import _GeminiValuationPayload
from backend.adapters.valuation.search_grounding import resolve_real_url
from backend.adapters.valuation.url_sanitizer import assemble_sources
from backend.adapters.valuation.prompts import (
    VALUATION_SYSTEM_INSTRUCTION,
    build_search_prompt,
    build_direct_prompt,
    build_grounded_calculation_prompt,
)


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
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        try:
            self.client = genai.Client(api_key=api_key)
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

        search_prompt = build_search_prompt(address, surface_m2, property_type, bedrooms)
        direct_prompt = build_direct_prompt(
            address, surface_m2, property_type, bedrooms, bathrooms, floor, has_elevator, condition
        )

        config = types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=VALUATION_SYSTEM_INSTRUCTION,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )

        retries = 0
        backoff = self.INITIAL_BACKOFF_SECONDS
        attempted_without_tools = False

        while True:
            try:
                contents = search_prompt if config.tools else direct_prompt

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

                raw_text = getattr(response, "text", "") or ""
                candidate = response.candidates[0] if getattr(response, "candidates", None) else None
                has_json_schema = '"sale_range"' in raw_text

                if config.tools and candidate and not has_json_schema:
                    verified_urls: list[str] = []
                    gm = getattr(candidate, "grounding_metadata", None)
                    if gm and getattr(gm, "grounding_chunks", None):
                        raw_items = [
                            c.web.uri.strip() for c in gm.grounding_chunks
                            if getattr(c, "web", None) and getattr(c.web, "uri", None) and isinstance(c.web.uri, str)
                        ]
                        if raw_items:
                            with ThreadPoolExecutor(max_workers=min(len(raw_items), 5)) as ex:
                                resolved = list(ex.map(resolve_real_url, raw_items))
                            for u in resolved:
                                if u and u.startswith("http") and u not in verified_urls:
                                    verified_urls.append(u)

                    calc_prompt = build_grounded_calculation_prompt(
                        raw_text=raw_text,
                        property_type=property_type,
                        address=address,
                        surface_m2=surface_m2,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        floor=floor,
                        has_elevator=has_elevator,
                        condition=condition,
                        verified_urls=verified_urls,
                    )

                    calc_config = types.GenerateContentConfig(temperature=0.1)
                    calc_response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=calc_prompt,
                        config=calc_config,
                    )
                    return self._parse_response(calc_response, grounding_candidate=candidate)

                return self._parse_response(response)

            except APIError as e:
                if e.code == 429 and config.tools and not attempted_without_tools:
                    config.tools = None
                    attempted_without_tools = True
                    retries = 0
                    continue

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

    def _parse_response(self, response: Any, grounding_candidate: Any = None) -> MarketValuationResult:
        if not response or not getattr(response, "candidates", None):
            raise MarketValuationError("Respuesta vacía o bloqueada por el proveedor", provider=self.PROVIDER_NAME)

        candidate = response.candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        fr_str = getattr(finish_reason, "name", str(finish_reason)).upper() if finish_reason else ""
        if finish_reason and fr_str not in ("STOP", "FINISH_REASON_STOP", "1", "NONE") and "STOP" not in fr_str:
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

        try:
            confidence = ValuationConfidence(payload.confidence.lower())
        except (ValueError, AttributeError):
            confidence = ValuationConfidence.LOW

        reasoning_factors: list[ReasoningFactor] = []
        for f in payload.reasoning_factors:
            impact_dec = Decimal(str(f.impact_percent))
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

        resolved_grounding: list[tuple[str, str]] = []
        target_candidate = grounding_candidate or candidate
        grounding_metadata = getattr(target_candidate, "grounding_metadata", None)
        if grounding_metadata and getattr(grounding_metadata, "grounding_chunks", None):
            raw_grounding_items: list[tuple[str, str]] = []
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
                raw_title = getattr(web, "title", None)
                title = raw_title.strip() if raw_title and isinstance(raw_title, str) else clean_uri
                raw_grounding_items.append((clean_uri, title))

            if raw_grounding_items:
                with ThreadPoolExecutor(max_workers=min(len(raw_grounding_items), 5)) as executor:
                    resolved_urls = list(executor.map(resolve_real_url, [item[0] for item in raw_grounding_items]))
                for (_, title), res_url in zip(raw_grounding_items, resolved_urls):
                    resolved_grounding.append((res_url, title))

        sources = assemble_sources(payload.sources, resolved_grounding)

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
