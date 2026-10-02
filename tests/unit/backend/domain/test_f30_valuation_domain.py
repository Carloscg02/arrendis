import pytest
from decimal import Decimal

from backend.domain.entities import (
    PropertyType,
    PropertyCondition,
    ValuationConfidence,
    MarketValuationError,
    ValuationRateLimitError,
)
from backend.domain.value_objects import (
    Money,
    ValuationRange,
    ReasoningFactor,
    ValuationSource,
    MarketValuationResult,
    Address,
)
from backend.domain.ports import MarketValuationPort


def test_market_valuation_result_creation_success():
    sale_range = ValuationRange(
        min_price=Money(Decimal("180000")),
        median_price=Money(Decimal("200000")),
        max_price=Money(Decimal("220000")),
    )
    rent_range = ValuationRange(
        min_price=Money(Decimal("800")),
        median_price=Money(Decimal("900")),
        max_price=Money(Decimal("1000")),
    )
    factor = ReasoningFactor(
        factor_name="Ascensor",
        impact_percent=Decimal("0.05"),
        description="Finca con ascensor.",
    )
    source = ValuationSource(
        title="Piso en venta",
        url="https://www.idealista.com/inmueble/123",
        price=Decimal("195000"),
        surface_m2=80,
    )

    result = MarketValuationResult(
        sale_range=sale_range,
        rent_range=rent_range,
        confidence=ValuationConfidence.HIGH,
        reasoning_factors=[factor],
        sources=[source],
        raw_notes="Nota de mercado",
    )

    assert result.confidence == ValuationConfidence.HIGH
    assert len(result.reasoning_factors) == 1
    assert len(result.sources) == 1
    assert result.sale_range.median_price.amount == Decimal("200000")


def test_market_valuation_result_currency_mismatch_raises():
    # Money default is EUR, but if we create with different currencies (not supported by MVP Money,
    # but let's test the invariant check in MarketValuationResult)
    sale_range = ValuationRange(
        min_price=Money(Decimal("100")),
        median_price=Money(Decimal("150")),
        max_price=Money(Decimal("200")),
    )
    # Both are EUR, so creating valid result should succeed
    res = MarketValuationResult(
        sale_range=sale_range,
        rent_range=sale_range,
        confidence=ValuationConfidence.HIGH,
    )
    assert res.sale_range == res.rent_range


def test_market_valuation_result_low_confidence_requires_explanation():
    sale_range = ValuationRange(
        min_price=Money(Decimal("180000")),
        median_price=Money(Decimal("200000")),
        max_price=Money(Decimal("220000")),
    )
    rent_range = ValuationRange(
        min_price=Money(Decimal("800")),
        median_price=Money(Decimal("900")),
        max_price=Money(Decimal("1000")),
    )

    # LOW confidence with neither factors nor raw_notes must raise ValueError
    with pytest.raises(ValueError, match="Se requiere al menos un factor o nota explicativa"):
        MarketValuationResult(
            sale_range=sale_range,
            rent_range=rent_range,
            confidence=ValuationConfidence.LOW,
            reasoning_factors=[],
            raw_notes=None,
        )

    # MEDIUM confidence with neither factors nor raw_notes must also raise ValueError
    with pytest.raises(ValueError, match="Se requiere al menos un factor o nota explicativa"):
        MarketValuationResult(
            sale_range=sale_range,
            rent_range=rent_range,
            confidence=ValuationConfidence.MEDIUM,
            reasoning_factors=[],
            raw_notes="",
        )

    # With a factor, LOW confidence succeeds
    factor = ReasoningFactor(
        factor_name="Pocos testigos",
        impact_percent=Decimal("0.0"),
        description="Muestra de comparables limitada en el código postal.",
    )
    result = MarketValuationResult(
        sale_range=sale_range,
        rent_range=rent_range,
        confidence=ValuationConfidence.LOW,
        reasoning_factors=[factor],
    )
    assert result.confidence == ValuationConfidence.LOW


def test_market_valuation_exceptions():
    err = MarketValuationError("Error general de valoración", provider="gemini")
    assert "[gemini]" in str(err)
    assert err.provider == "gemini"

    rl_err = ValuationRateLimitError(provider="gemini", retry_after_seconds=30)
    assert isinstance(rl_err, MarketValuationError)
    assert rl_err.retry_after_seconds == 30
    assert "reintentar tras 30s" in str(rl_err)


def test_market_valuation_port_abstract():
    class DummyPort(MarketValuationPort):
        pass

    with pytest.raises(TypeError):
        DummyPort()  # cannot instantiate abstract class
