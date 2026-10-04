import json
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from google.genai.errors import APIError

from backend.adapters.valuation import (
    GeminiMarketValuationAdapter,
    MockMarketValuationAdapter,
)

from backend.domain.entities import (
    PropertyType,
    PropertyCondition,
    ValuationConfidence,
    MarketValuationError,
    ValuationRateLimitError,
)
from backend.domain.value_objects import Address


@pytest.fixture
def sample_address() -> Address:
    return Address(
        street="Calle Gran Vía 28",
        city="Madrid",
        postal_code="28013",
        country="España",
    )


# ──────────────────────────────────────────────
# Tests de MockMarketValuationAdapter
# ──────────────────────────────────────────────

def test_mock_adapter_basic_calculation(sample_address: Address):
    adapter = MockMarketValuationAdapter()
    result = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=100,
        property_type=PropertyType.APARTMENT,
        bedrooms=2,
        bathrooms=1,
        floor=3,
        has_elevator=True,
        condition=PropertyCondition.BUEN_ESTADO,
    )

    assert result.confidence == ValuationConfidence.HIGH
    # 100 m2 * 2200 * 1.0 * 1.05 = 231,000 median
    assert result.sale_range.median_price.amount == Decimal("231000")
    assert result.sale_range.min_price.amount == Decimal("207900.00")
    assert result.sale_range.max_price.amount == Decimal("254100.00")

    # 100 m2 * 11 * 1.0 * 1.05 = 1155 -> rounded to nearest 10: 1160
    assert result.rent_range.median_price.amount == Decimal("1160")
    assert len(result.reasoning_factors) >= 1
    assert len(result.sources) >= 1


def test_mock_adapter_condition_variation(sample_address: Address):
    adapter = MockMarketValuationAdapter()
    res_reformado = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=80,
        condition=PropertyCondition.REFORMADO,
    )
    res_a_reformar = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=80,
        condition=PropertyCondition.A_REFORMAR,
    )

    assert res_reformado.sale_range.median_price.amount > res_a_reformar.sale_range.median_price.amount


def test_mock_adapter_no_elevator_penalty(sample_address: Address):
    adapter = MockMarketValuationAdapter()
    res_with_elevator = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=70,
        floor=4,
        has_elevator=True,
    )
    res_without_elevator = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=70,
        floor=4,
        has_elevator=False,
    )

    assert res_with_elevator.sale_range.median_price.amount > res_without_elevator.sale_range.median_price.amount


def test_mock_adapter_invalid_surface_raises(sample_address: Address):
    adapter = MockMarketValuationAdapter()
    with pytest.raises(ValueError, match="positiva"):
        adapter.estimate_valuation(
            address=sample_address,
            surface_m2=0,
        )


# ──────────────────────────────────────────────
# Tests de GeminiMarketValuationAdapter
# ──────────────────────────────────────────────

def test_gemini_adapter_init_missing_key():
    with pytest.raises(MarketValuationError, match="API key is required"):
        GeminiMarketValuationAdapter(api_key="")


@patch("backend.adapters.valuation.adapter.genai.Client")
def test_gemini_adapter_success_flow(mock_client_cls, sample_address: Address):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    payload_data = {
        "sale_range": {"min": 190000, "median": 205000, "max": 220000},
        "rent_range": {"min": 900, "median": 980, "max": 1050},
        "confidence": "HIGH",
        "reasoning_factors": [
            {
                "factor_name": "Ascensor",
                "impact_percent": 8.0,
                "description": "Planta 3 con ascensor en buen estado.",
            }
        ],
        "sources": [
            {
                "title": "Piso similar en Gran Vía",
                "url": "https://www.idealista.com/inmueble/9999",
                "price": 200000,
                "surface_m2": 85,
            }
        ],
        "raw_notes": "Mercado dinámico en la zona centro.",
    }

    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(payload_data)}\n```"
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"

    # Mock grounding chunks
    chunk1 = MagicMock()
    chunk1.web.uri = "https://www.fotocasa.es/es/comprar/vivienda/123"
    chunk1.web.title = "Anuncio en Fotocasa"

    # Chunk with existing url (duplicate)
    chunk2 = MagicMock()
    chunk2.web.uri = "https://www.idealista.com/inmueble/9999"
    chunk2.web.title = "Duplicado"

    # Chunk with missing web or uri
    chunk3 = MagicMock()
    chunk3.web = None

    mock_candidate.grounding_metadata.grounding_chunks = [chunk1, chunk2, chunk3]
    mock_response.candidates = [mock_candidate]

    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiMarketValuationAdapter(api_key="fake-test-key")
    result = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=85,
        property_type=PropertyType.APARTMENT,
        bedrooms=2,
        bathrooms=1,
        floor=3,
        has_elevator=True,
        condition=PropertyCondition.BUEN_ESTADO,
    )

    # Verificaciones de llamada
    call_args = mock_client.models.generate_content.call_args
    assert call_args is not None
    config = call_args.kwargs.get("config")
    assert config is not None
    assert config.temperature == 0.2
    assert len(config.tools) == 1
    # Asegurar que NO se enviaron response_schema ni response_mime_type (incompatibles con search)
    assert not getattr(config, "response_schema", None)
    assert not getattr(config, "response_mime_type", None)

    # Verificaciones de resultado parseado
    assert result.confidence == ValuationConfidence.HIGH
    assert result.sale_range.median_price.amount == Decimal("205000.00")
    assert result.rent_range.median_price.amount == Decimal("980.00")

    # Normalización del impacto porcentual (8.0% -> Decimal("0.0800"))
    assert result.reasoning_factors[0].impact_percent == Decimal("0.0800")

    # Fuentes: 1 del JSON + 1 de grounding (chunk1), chunk2 omitido por duplicado, chunk3 omitido por None
    assert len(result.sources) == 2
    assert result.sources[0].url == "https://www.idealista.com/inmueble/9999"
    assert result.sources[1].url == "https://www.fotocasa.es/es/comprar/vivienda/123"
    assert result.sources[1].title == "Anuncio en Fotocasa"


@patch("backend.adapters.valuation.adapter.genai.Client")
def test_gemini_adapter_rate_limit_error(mock_client_cls, sample_address: Address):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    error_response = MagicMock()
    api_err = APIError(429, {"error": {"message": "Resource has been exhausted"}})
    mock_client.models.generate_content.side_effect = api_err

    adapter = GeminiMarketValuationAdapter(api_key="fake-test-key")
    adapter.INITIAL_BACKOFF_SECONDS = 0.01  # Acelerar test

    with pytest.raises(ValuationRateLimitError):
        adapter.estimate_valuation(
            address=sample_address,
            surface_m2=90,
        )


@patch("backend.adapters.valuation.adapter.genai.Client")
def test_gemini_adapter_safety_blocked_response(mock_client_cls, sample_address: Address):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "SAFETY"
    mock_response.candidates = [mock_candidate]
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiMarketValuationAdapter(api_key="fake-test-key")
    with pytest.raises(MarketValuationError, match="Generación finalizada por motivo no estándar"):
        adapter.estimate_valuation(
            address=sample_address,
            surface_m2=90,
        )


@patch("backend.adapters.valuation.adapter.genai.Client")
def test_gemini_adapter_invalid_json_response(mock_client_cls, sample_address: Address):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = "Lo siento, no puedo estimar el precio de este inmueble."
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.grounding_metadata = None
    mock_response.candidates = [mock_candidate]
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiMarketValuationAdapter(api_key="fake-test-key")
    with pytest.raises(MarketValuationError, match="Fallo al decodificar JSON"):
        adapter.estimate_valuation(
            address=sample_address,
            surface_m2=90,
        )


@patch("backend.adapters.valuation.adapter.genai.Client")
def test_gemini_adapter_search_quota_fallback_to_direct_generation(mock_client_cls, sample_address: Address):
    """Verifica que ante un 429 por agotamiento de cuota de búsqueda, se reintenta sin herramientas y se obtiene la valoración."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    payload_data = {
        "sale_range": {"min": 400000, "median": 450000, "max": 500000},
        "rent_range": {"min": 1500, "median": 1650, "max": 1800},
        "confidence": "HIGH",
        "reasoning_factors": [
            {
                "factor_name": "Ubicación Teatinos",
                "impact_percent": 15.0,
                "description": "Alta demanda residencial.",
            }
        ],
        "sources": [
            {
                "title": "Idealista Teatinos",
                "url": "https://www.idealista.com/venta-viviendas/malaga/teatinos/",
            }
        ],
        "raw_notes": "Mercado dinámico en Málaga.",
    }

    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(payload_data)}\n```"
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.grounding_metadata = None
    mock_response.candidates = [mock_candidate]

    # Primer intento con tools lanza 429, segundo intento sin tools devuelve éxito
    api_429 = APIError(429, {"error": {"message": "Resource has been exhausted"}})
    mock_client.models.generate_content.side_effect = [api_429, mock_response]

    adapter = GeminiMarketValuationAdapter(api_key="fake-test-key")
    result = adapter.estimate_valuation(
        address=sample_address,
        surface_m2=90,
    )

    assert result.confidence == ValuationConfidence.HIGH
    assert result.sale_range.median_price.amount == Decimal("450000.00")
    assert result.rent_range.median_price.amount == Decimal("1650.00")
    assert mock_client.models.generate_content.call_count == 2
    # Comprobar que en el segundo intento no se pasaron herramientas
    second_call_kwargs = mock_client.models.generate_content.call_args_list[1].kwargs
    assert second_call_kwargs["config"].tools is None


def test_sanitize_property_url():
    from backend.adapters.valuation.url_sanitizer import sanitize_property_url as _sanitize_property_url

    # District normalization
    assert _sanitize_property_url("https://www.idealista.com/venta-viviendas/malaga/teatinos-universidad/") == "https://www.idealista.com/venta-viviendas/malaga/teatinos/"
    assert _sanitize_property_url("https://www.idealista.com/venta-viviendas/malaga/teatinos-universidad/hacienda-bizcochero/") == "https://www.idealista.com/venta-viviendas/malaga/teatinos/el-tejar-hacienda-bizcochero/"
    # Bedroom normalization
    assert _sanitize_property_url("https://www.idealista.com/venta-viviendas/malaga/teatinos/con-de-cuatro-dormitorios/") == "https://www.idealista.com/venta-viviendas/malaga/teatinos/con-de-cuatro-cinco-habitaciones-o-mas/"
    # Price filter strip
    assert _sanitize_property_url("https://www.idealista.com/alquiler-viviendas/malaga/teatinos/con-precio-hasta_2000/") == "https://www.idealista.com/alquiler-viviendas/malaga/teatinos/"
    # Street incorrectly nested in regional hierarchy stripped to valid district
    assert _sanitize_property_url("https://www.idealista.com/venta-viviendas/malaga/teatinos/avenida-doctor-manuel-dominguez/") == "https://www.idealista.com/venta-viviendas/malaga/teatinos/"


def test_format_source_title():
    from backend.adapters.valuation.url_sanitizer import format_source_title as _format_source_title

    assert "Venta de pisos en Malaga, Teatinos" in _format_source_title("idealista.com", "https://www.idealista.com/venta-viviendas/malaga/teatinos/")
    assert "Alquiler en Teatinos — Fotocasa" in _format_source_title(None, "https://www.fotocasa.es/es/alquiler/viviendas/teatinos/l")
    assert _format_source_title("Piso luminoso en Paseo Marítimo", "https://www.idealista.com/inmueble/12345/") == "Piso luminoso en Paseo Marítimo"


def test_assemble_sources_replaces_hallucinated_url_with_resolved_grounding():
    from backend.adapters.valuation.url_sanitizer import assemble_sources as _assemble_sources
    from backend.adapters.valuation.schemas import _SourcePayload


    payload_sources = [
        _SourcePayload(
            title="Idealista Teatinos",
            url="https://www.idealista.com/venta-viviendas/malaga/teatinos-universidad/hacienda-bizcochero/",
            price=Decimal("450000"),
            surface_m2=125,
        ),
        _SourcePayload(
            title="Idealista Alquiler",
            url="https://www.idealista.com/alquiler-viviendas/malaga/teatinos-universidad/con-precio-hasta_2000/",
            price=Decimal("1800"),
            surface_m2=125,
        ),
    ]

    resolved_grounding = [
        ("https://www.idealista.com/geo/venta-viviendas/calle-decano-manuel-dominguez-malaga-malaga/", "idealista.com"),
        ("https://www.idealista.com/geo/alquiler-viviendas/calle-juan-del-encina-malaga-malaga/", "idealista.com"),
        ("https://www.fotocasa.es/es/comprar/viviendas/area/calle-decano-manuel-dominguez-malaga-capital/l", "fotocasa.es"),
    ]

    sources = _assemble_sources(payload_sources, resolved_grounding)
    assert len(sources) == 3
    # Venta matched with real geo URL while retaining price and m2
    assert sources[0].url == "https://www.idealista.com/geo/venta-viviendas/calle-decano-manuel-dominguez-malaga-malaga/"
    assert sources[0].price == Decimal("450000")
    assert sources[0].surface_m2 == 125
    # Alquiler matched with real geo URL while retaining price and m2
    assert sources[1].url == "https://www.idealista.com/geo/alquiler-viviendas/calle-juan-del-encina-malaga-malaga/"
    assert sources[1].price == Decimal("1800")
    # Additional Fotocasa source added from grounding
    assert sources[2].url == "https://www.fotocasa.es/es/comprar/viviendas/area/calle-decano-manuel-dominguez-malaga-capital/l"


