from backend.adapters.extraction.base import (
    ExtractionStrategy,
    UtilityExtractorRegistry,
)
from backend.adapters.extraction.privacy_scrubber import PrivacyScrubber
from backend.adapters.extraction.repsol_regex_adapter import (
    RepsolExtractionStrategy,
    RepsolInvoiceExtractor,
)
from backend.adapters.extraction.gemini_extractor_adapter import (
    AIExtractionStrategy,
    GeminiInvoiceExtractor,
)
from backend.adapters.extraction.composite_registry import CompositeInvoiceExtractor

__all__ = [
    "ExtractionStrategy",
    "UtilityExtractorRegistry",
    "PrivacyScrubber",
    "RepsolExtractionStrategy",
    "RepsolInvoiceExtractor",
    "AIExtractionStrategy",
    "GeminiInvoiceExtractor",
    "CompositeInvoiceExtractor",
]
