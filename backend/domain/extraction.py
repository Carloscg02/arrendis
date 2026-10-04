"""
Fachada de retrocompatibilidad para backend.domain.extraction.

DEPRECADO: Las estrategias de extracción y el scrubber RGPD pertenecen a la capa de
infraestructura / adaptadores y han sido trasladados a `backend.adapters.extraction`.
Este módulo se conserva para compatibilidad hacia atrás.
"""

from backend.adapters.extraction import (
    PrivacyScrubber,
    ExtractionStrategy,
    RepsolExtractionStrategy,
    AIExtractionStrategy,
    UtilityExtractorRegistry,
)

__all__ = [
    "PrivacyScrubber",
    "ExtractionStrategy",
    "RepsolExtractionStrategy",
    "AIExtractionStrategy",
    "UtilityExtractorRegistry",
]
