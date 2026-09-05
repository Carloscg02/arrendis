"""
Tests unitarios para UtilityExtractorRegistry (F-18 / OCP Registry).

Verifica el desacoplamiento del registro de estrategias de extracción.
"""

from backend.domain.extraction import (
    ExtractionStrategy,
    RepsolExtractionStrategy,
    UtilityExtractorRegistry,
)
from backend.domain.value_objects import UtilityInvoiceData


class DummyEndesaStrategy(ExtractionStrategy):
    @property
    def provider_name(self) -> str:
        return "Endesa"

    def can_handle(self, text: str) -> bool:
        return "ENDESA" in text.upper()

    def extract(self, text: str) -> UtilityInvoiceData | None:
        return None


def test_registry_register_and_list_providers():
    """UT-F18-12: register() añade estrategias y actualiza registered_providers."""
    registry = UtilityExtractorRegistry()
    assert registry.registered_providers == []

    repsol_strategy = RepsolExtractionStrategy()
    registry.register(repsol_strategy)
    assert registry.registered_providers == ["Repsol"]

    endesa_strategy = DummyEndesaStrategy()
    registry.register(endesa_strategy)
    assert registry.registered_providers == ["Repsol", "Endesa"]


def test_registry_find_strategy_matches_can_handle():
    """UT-F18-13: find_strategy() selecciona la estrategia correspondiente."""
    registry = UtilityExtractorRegistry([
        RepsolExtractionStrategy(),
        DummyEndesaStrategy(),
    ])

    repsol_text = "Factura emitida por Repsol Luz y Gas."
    found_repsol = registry.find_strategy(repsol_text)
    assert found_repsol is not None
    assert found_repsol.provider_name == "Repsol"

    endesa_text = "Factura de suministro Endesa Energía XXI."
    found_endesa = registry.find_strategy(endesa_text)
    assert found_endesa is not None
    assert found_endesa.provider_name == "Endesa"


def test_registry_find_strategy_returns_none_when_no_match():
    """UT-F18-14: find_strategy() retorna None si ninguna estrategia la reconoce."""
    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])

    unknown_text = "Factura de Aguas de Torremolinos S.A."
    assert registry.find_strategy(unknown_text) is None
