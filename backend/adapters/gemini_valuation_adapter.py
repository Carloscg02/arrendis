"""
Fachada de retrocompatibilidad para backend.adapters.gemini_valuation_adapter.

Este módulo reexporta las clases y utilidades modularizadas en backend.adapters.valuation
para garantizar compatibilidad hacia atrás con tests existentes y decoradores @patch.
"""

from google import genai
from backend.adapters.valuation import (
    GeminiMarketValuationAdapter,
    MockMarketValuationAdapter,
)
from backend.adapters.valuation.schemas import (
    _RangePayload,
    _FactorPayload,
    _SourcePayload,
    _GeminiValuationPayload,
)
from backend.adapters.valuation.search_grounding import (
    resolve_real_url as _resolve_real_url,
    resolve_grounding_urls,
)
from backend.adapters.valuation.url_sanitizer import (
    sanitize_property_url as _sanitize_property_url,
    format_source_title as _format_source_title,
    assemble_sources as _assemble_sources,
)

__all__ = [
    "genai",
    "GeminiMarketValuationAdapter",
    "MockMarketValuationAdapter",
    "_RangePayload",
    "_FactorPayload",
    "_SourcePayload",
    "_GeminiValuationPayload",
    "_resolve_real_url",
    "_sanitize_property_url",
    "_format_source_title",
    "_assemble_sources",
]
