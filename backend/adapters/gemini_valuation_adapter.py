import os
import re
import json
import time
import random
from decimal import Decimal
from typing import Any
import urllib.request
import urllib.error
from urllib.parse import urlparse, urlunparse, urljoin
from concurrent.futures import ThreadPoolExecutor

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


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def _resolve_real_url(url: str, timeout: float = 2.0) -> str:
    """Resuelve redirecciones de Google Search Grounding a sus URLs finales de destino."""
    if not url or "grounding-api-redirect" not in url:
        return url
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with _NO_REDIRECT_OPENER.open(req, timeout=timeout) as resp:
            return resp.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            loc = e.headers.get("Location")
            if loc:
                return urljoin(url, loc)
    except Exception:
        pass
    return url


def _sanitize_property_url(url: str) -> str:
    """Corrige slugs de Idealista alucinados por el LLM hacia rutas canónicas y activas."""
    if not url:
        return url
    clean = url.strip()
    if "idealista.com" in clean:
        clean = clean.replace("/teatinos-universidad/", "/teatinos/")
        clean = clean.replace("/hacienda-bizcochero/", "/el-tejar-hacienda-bizcochero/")
        clean = clean.replace("/carretera-de-cadiz-huelin/", "/carretera-de-cadiz/huelin/")

        clean = re.sub(r"/con-de-(?:cuatro|4)-dormitorios?/?", "/con-de-cuatro-cinco-habitaciones-o-mas/", clean)
        clean = re.sub(r"/con-de-(?:tres|3)-dormitorios?/?", "/con-de-tres-dormitorios/", clean)
        clean = re.sub(r"/con-de-(?:dos|2)-dormitorios?/?", "/con-de-dos-dormitorios/", clean)
        clean = re.sub(r"/con-de-(?:un|1)-dormitorios?/?", "/con-de-un-dormitorio/", clean)

        clean = re.sub(r"/con-precio-hasta_[0-9]+/?", "/", clean)

        # Si se concatenó el slug de una calle dentro de la jerarquía regional (lo que provoca 404 en Idealista)
        # ej. /venta-viviendas/malaga/teatinos/avenida-doctor-manuel-dominguez/ -> /venta-viviendas/malaga/teatinos/
        street_pattern = r"/(?:avenida|avda|calle|paseo|plaza|camino|carrer|via)-[^/]+/?$"
        if re.search(street_pattern, clean) and "/geo/" not in clean:
            clean = re.sub(street_pattern, "/", clean)

        parsed = urlparse(clean)
        clean_path = re.sub(r"/+", "/", parsed.path)
        if not clean_path.endswith("/"):
            clean_path += "/"
        clean = urlunparse(parsed._replace(path=clean_path))

    return clean


def _format_source_title(raw_title: str | None, url: str) -> str:
    """Genera un título legible y representativo para los enlaces de Idealista y Fotocasa."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")

        if raw_title:
            stripped = raw_title.strip()
            if (
                stripped.lower() not in (domain.lower(), "idealista.com", "fotocasa.es", "habitaclia.com")
                and len(stripped) > 8
            ):
                return stripped

        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if "idealista.com" in domain and parts:
            is_alquiler = any("alquiler" in p for p in parts)
            is_venta = any("venta" in p for p in parts)
            action = "Alquiler" if is_alquiler else ("Venta" if is_venta else "Inmuebles")
            loc_parts = [
                p for p in parts
                if p not in (
                    "geo", "venta-viviendas", "alquiler-viviendas", "con-pisos",
                    "inmuebles", "areas", "con-de-cuatro-cinco-habitaciones-o-mas",
                    "con-de-tres-dormitorios", "con-de-dos-dormitorios", "con-de-un-dormitorio",
                )
            ]
            clean_zone = ", ".join([p.replace("-", " ").title() for p in loc_parts])
            return f"{action} de pisos en {clean_zone} — Idealista" if clean_zone else f"{action} de viviendas — Idealista"
        elif "fotocasa.es" in domain and parts:
            is_alquiler = "alquiler" in parts
            action = "Alquiler" if is_alquiler else "Venta"
            loc_parts = [
                p for p in parts
                if p not in ("es", "comprar", "alquiler", "viviendas", "vivienda", "area", "maps", "l", "d")
            ]
            clean_zone = ", ".join([p.replace("-", " ").title() for p in loc_parts if not p.isdigit() and len(p) > 2])
            return f"{action} en {clean_zone} — Fotocasa" if clean_zone else f"{action} de viviendas — Fotocasa"
    except Exception:
        pass
    return raw_title or url


def _assemble_sources(
    payload_sources: list[_SourcePayload],
    resolved_grounding: list[tuple[str, str]],
) -> list[ValuationSource]:
    """Combina fuentes del payload del modelo con URLs reales resueltas desde Google Search Grounding."""
    sources: list[ValuationSource] = []
    used_grounding_indices: set[int] = set()
    seen_urls: set[str] = set()

    for s in payload_sources:
        s_url = _sanitize_property_url(s.url.strip())
        if not (s_url.startswith("http://") or s_url.startswith("https://")):
            continue

        matched_idx = None
        # 1. Coincidencia exacta de URL
        for idx, (g_url, _) in enumerate(resolved_grounding):
            if g_url.rstrip("/") == s_url.rstrip("/"):
                matched_idx = idx
                break

        # 2. Coincidencia por portal y modalidad (venta/alquiler) si no hubo match exacto
        if matched_idx is None and resolved_grounding:
            s_domain = urlparse(s_url).netloc.replace("www.", "")
            s_is_alquiler = "alquiler" in s_url.lower()
            for idx, (g_url, _) in enumerate(resolved_grounding):
                if idx in used_grounding_indices:
                    continue
                g_domain = urlparse(g_url).netloc.replace("www.", "")
                g_is_alquiler = "alquiler" in g_url.lower()
                if s_domain and s_domain == g_domain and s_is_alquiler == g_is_alquiler:
                    matched_idx = idx
                    break

        if matched_idx is not None:
            used_grounding_indices.add(matched_idx)
            g_url, g_title = resolved_grounding[matched_idx]
            final_url = g_url
            final_title = _format_source_title(g_title or s.title, g_url)
        else:
            final_url = s_url
            final_title = _format_source_title(s.title, s_url)

        norm = final_url.rstrip("/")
        if norm not in seen_urls:
            seen_urls.add(norm)
            sources.append(
                ValuationSource(
                    title=final_title,
                    url=final_url,
                    price=s.price,
                    surface_m2=s.surface_m2,
                )
            )

    # Añadir fuentes restantes de búsqueda no emparejadas con el payload
    for idx, (g_url, g_title) in enumerate(resolved_grounding):
        if idx in used_grounding_indices:
            continue
        norm = g_url.rstrip("/")
        if norm not in seen_urls:
            seen_urls.add(norm)
            sources.append(
                ValuationSource(
                    title=_format_source_title(g_title, g_url),
                    url=g_url,
                )
            )

    return sources


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

        system_instruction = (
            "Eres un tasador y analista inmobiliario senior experto en el mercado inmobiliario de España.\n"
            "Tu objetivo es estimar con el mayor rigor, objetividad y actualidad posible (conforme al mercado de 2025-2026):\n"
            "1. La horquilla de precio de venta en EUR (min, median, max).\n"
            "2. La horquilla de renta mensual de alquiler en EUR (min, median, max).\n"
            "3. El nivel de confianza del análisis ('HIGH', 'MEDIUM', 'LOW').\n"
            "4. Factores explicativos de corrección (porcentaje de impacto cualitativo/cuantitativo y descripción detallada).\n"
            "5. Referencias o fuentes de mercado (Idealista, Fotocasa) para la zona, distrito o micro-barrio correspondiente.\n\n"
            "CRITERIOS DE VALORACIÓN CRÍTICOS:\n"
            "- MICRO-LOCALIZACIÓN OBLIGATORIA: Identifica siempre el MICRO-BARRIO o subzona específica a partir del nombre de la calle y el código postal (ej. en Málaga, la calle Salvador Espada Leal en CP 29002 pertenece al barrio de HUELIN, junto al paseo marítimo y Tomás Echeverría; NO debe tasarse con la media del macro-distrito 'Carretera de Cádiz'; en Madrid, determina si es Malasaña, Salamanca, Pacífico, etc.).\n"
            "- NUNCA USAR MEDIAS AGREGADAS DE MACRO-DISTRITOS SI EXISTE DISPERSIÓN: En distritos amplios y heterogéneos (ej. Carretera de Cádiz, Cruz de Humilladero, Fuencarral, Carabanchel), los precios por m² varían drásticamente entre barrios contiguos (ej. Huelin o Pacífico rondan los 4.000 - 4.400 €/m², mientras que barrios interiores como La Luz o San Andrés bajan a 2.300 €/m²). Usar la media genérica del distrito infravalora o sobrevalora gravemente el inmueble.\n"
            "- BÚSQUEDA HIPERLOCAL Y FILTRADA: Al usar Google Search, realiza consultas combinando la calle exacta, el micro-barrio identificado, el número de dormitorios y la superficie (ej. 'pisos 3 dormitorios Salvador Espada Leal Huelin Málaga', 'precio m2 Huelin Málaga venta 2025 2026', 'alquiler 3 dormitorios Huelin').\n"
            "- FUENTES Y ENLACES REPRESENTATIVOS: En el campo 'sources', proporciona URLs acotadas al micro-barrio específico en Idealista y Fotocasa (ej. 'https://www.idealista.com/venta-viviendas/malaga/carretera-de-cadiz/huelin/' o con filtros de dormitorios/precio si procede). NUNCA proporciones únicamente la URL de macro-distrito genérico si existe la sub-ruta del micro-barrio.\n"
            "- PONDERACIÓN DE DORMITORIOS Y ESTADO: Pondera adecuadamente el número de dormitorios, planta y ascensor. Por ejemplo, 3 o 4 dormitorios en zonas familiares o de alta demanda tienen una prima de liquidez y absorción tanto en venta como en alquiler residencial.\n\n"
            "FORMATO DE SALIDA (EXCLUSIVAMENTE JSON):\n"
            "Debes responder EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional fuera del bloque JSON.\n"
            "Estructura JSON esperada:\n"
            "{\n"
            '  "sale_range": {"min": 315000, "median": 345000, "max": 380000},\n'
            '  "rent_range": {"min": 1250, "median": 1400, "max": 1600},\n'
            '  "confidence": "HIGH",\n'
            '  "reasoning_factors": [\n'
            '    {"factor_name": "Micro-ubicación Huelin", "impact_percent": 20.0, "description": "Ubicación en barrio cotizado junto al paseo marítimo con precios significativamente superiores a la media del macro-distrito."}\n'
            "  ],\n"
            '  "sources": [\n'
            '    {"title": "Venta viviendas en Huelin, Málaga - Idealista", "url": "https://www.idealista.com/venta-viviendas/malaga/carretera-de-cadiz/huelin/", "price": 345000, "surface_m2": 80}\n'
            "  ],\n"
            '  "raw_notes": "Análisis específico del micro-barrio..."\n'
            "}\n"
        )

        search_prompt = (
            f"Busca anuncios activos y precios reales en Idealista y Fotocasa de viviendas en venta y alquiler en "
            f"{address.street}, {address.city} (CP: {address.postal_code}, País: {address.country}). "
            f"Detalla los inmuebles comparables encontrados para {property_type.value} de {surface_m2} m2, "
            f"{bedrooms if bedrooms is not None else ''} dormitorios, sus precios de venta y rentas de alquiler, superficies en m2 y características principales."
        )

        direct_prompt = (
            f"Por favor, calcula la estimación de venta y alquiler para el siguiente inmueble:\n"
            f"- Tipología: {property_type.value}\n"
            f"- Dirección: {address.street}, {address.city} (CP: {address.postal_code}, País: {address.country})\n"
            f"- Superficie: {surface_m2} m2\n"
            f"- Dormitorios: {bedrooms if bedrooms is not None else 'No especificado'}\n"
            f"- Baños: {bathrooms if bathrooms is not None else 'No especificado'}\n"
            f"- Planta: {floor if floor is not None else 'No especificada'}\n"
            f"- Ascensor: {'Sí' if has_elevator is True else ('No' if has_elevator is False else 'Desconocido')}\n"
            f"- Estado de conservación: {condition.value if condition else 'No especificado'}\n\n"
            "Instrucciones específicas:\n"
            "1. Determina el micro-barrio exacto o zona de influencia de la dirección indicada.\n"
            "2. Estima los valores de mercado y referencias en Idealista o Fotocasa."
        )

        config = types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=system_instruction,
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

                # Si la llamada incluía herramientas de búsqueda y devolvió texto descriptivo en lugar de JSON estructurado,
                # significa que Gemini realizó la búsqueda web dedicada en directo. Procedemos al cálculo analítico fundamentado.
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
                                resolved = list(ex.map(_resolve_real_url, raw_items))
                            for u in resolved:
                                if u and u.startswith("http") and u not in verified_urls:
                                    verified_urls.append(u)

                    calc_prompt = (
                        "Eres un tasador inmobiliario senior experto en el mercado inmobiliario de España.\n"
                        "Basándote ESTRICTAMENTE en las siguientes ofertas y datos reales de mercado recopilados en directo de la zona:\n\n"
                        "--- TESTIGOS Y ANUNCIOS REALES ENCONTRADOS EN LA ZONA ---\n"
                        f"{raw_text}\n"
                        "---------------------------------------------------------\n\n"
                        "Calcula la tasación y estimación de mercado para este inmueble concreto:\n"
                        f"- Tipología: {property_type.value}\n"
                        f"- Dirección: {address.street}, {address.city} (CP: {address.postal_code}, País: {address.country})\n"
                        f"- Superficie: {surface_m2} m2\n"
                        f"- Dormitorios: {bedrooms if bedrooms is not None else 'No especificado'}\n"
                        f"- Baños: {bathrooms if bathrooms is not None else 'No especificado'}\n"
                        f"- Planta: {floor if floor is not None else 'No especificada'}\n"
                        f"- Ascensor: {'Sí' if has_elevator is True else ('No' if has_elevator is False else 'Desconocido')}\n"
                        f"- Estado de conservación: {condition.value if condition else 'No especificado'}\n\n"
                    )
                    if verified_urls:
                        calc_prompt += (
                            "Enlaces reales verificados de la búsqueda (utiliza estos enlaces en el array 'sources'):\n"
                            + "\n".join(f"- {u}" for u in verified_urls[:6])
                            + "\n\n"
                        )
                    calc_prompt += (
                        "FORMATO DE SALIDA (EXCLUSIVAMENTE JSON):\n"
                        "Debes responder con un objeto JSON válido con la siguiente estructura:\n"
                        "{\n"
                        '  "sale_range": {"min": ..., "median": ..., "max": ...},\n'
                        '  "rent_range": {"min": ..., "median": ..., "max": ...},\n'
                        '  "confidence": "HIGH",\n'
                        '  "reasoning_factors": [\n'
                        '    {"factor_name": "...", "impact_percent": 0.0, "description": "..."}\n'
                        "  ],\n"
                        '  "sources": [\n'
                        '    {"title": "...", "url": "...", "price": ..., "surface_m2": ...}\n'
                        "  ],\n"
                        '  "raw_notes": "..."\n'
                        "}\n"
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
                # Si la cuota de búsqueda de Google Search Grounding está agotada (429) o no disponible en la API key,
                # reintentar inmediatamente sin la herramienta de búsqueda para obtener la valoración analítica de Gemini
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

        # 3. Extraer y resolver Fuentes de búsqueda web y payload
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
                    resolved_urls = list(executor.map(_resolve_real_url, [item[0] for item in raw_grounding_items]))
                for (_, title), res_url in zip(raw_grounding_items, resolved_urls):
                    resolved_grounding.append((res_url, title))

        sources = _assemble_sources(payload.sources, resolved_grounding)

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

        city_slug = address.city.lower().strip().replace(" ", "-") if address.city else "malaga"
        sources = [
            ValuationSource(
                title=f"Búsqueda de mercado residencial en {address.city} (Idealista)",
                url=f"https://www.idealista.com/venta-viviendas/{city_slug}/",
                price=sale_median,
                surface_m2=surface_m2,
            ),
            ValuationSource(
                title=f"Búsqueda de alquileres en {address.city} (Fotocasa)",
                url=f"https://www.fotocasa.es/es/alquiler/viviendas/{city_slug}/l",
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
            raw_notes=(
                f"[MODO SIMULADO / MOCK] Estimación heurística calculada para {surface_m2} m² en {address.city}. "
                "Para obtener tasaciones reales con inteligencia artificial y análisis contextual, verifique su GEMINI_API_KEY."
            ),
        )
