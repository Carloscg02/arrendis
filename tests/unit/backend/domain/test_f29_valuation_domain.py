import pytest
from datetime import date
from decimal import Decimal

from backend.domain.entities import (
    Property,
    PropertyStatus,
    PropertyType,
    PropertyCondition,
    ValuationConfidence,
    PropertyValuation,
)
from backend.domain.value_objects import (
    Address,
    Money,
    ValuationRange,
    ReasoningFactor,
    ValuationSource,
)


def test_f29_01_property_physical_attributes_instantiation():
    """TEST-F29-01: Instanciación válida de Property con atributos físicos."""
    prop = Property(
        name="Ático Retiro",
        address=Address("Calle Menéndez Pelayo 10", "Madrid", "28009"),
        property_type=PropertyType.APARTMENT,
        user_id="user-123",
        surface_m2=95,
        bedrooms=3,
        bathrooms=2,
        floor=6,
        has_elevator=True,
        condition=PropertyCondition.REFORMADO,
    )
    assert prop.surface_m2 == 95
    assert prop.bedrooms == 3
    assert prop.bathrooms == 2
    assert prop.floor == 6
    assert prop.has_elevator is True
    assert prop.condition == PropertyCondition.REFORMADO


def test_f29_02_property_physical_attributes_validation_errors():
    """TEST-F29-02: Validaciones de invariantes físicos en Property."""
    addr = Address("Calle Mayor 1", "Madrid", "28013")

    with pytest.raises(ValueError, match="estrictamente positiva"):
        Property(
            name="Piso Inválido",
            address=addr,
            property_type=PropertyType.APARTMENT,
            user_id="u1",
            surface_m2=0,
        )

    with pytest.raises(ValueError, match="estrictamente positiva"):
        Property(
            name="Piso Inválido",
            address=addr,
            property_type=PropertyType.APARTMENT,
            user_id="u1",
            surface_m2=-15,
        )

    with pytest.raises(ValueError, match="no puede ser negativo"):
        Property(
            name="Piso Inválido",
            address=addr,
            property_type=PropertyType.APARTMENT,
            user_id="u1",
            bedrooms=-1,
        )

    with pytest.raises(ValueError, match="no puede ser negativo"):
        Property(
            name="Piso Inválido",
            address=addr,
            property_type=PropertyType.APARTMENT,
            user_id="u1",
            bathrooms=-2,
        )


def test_f29_03_valuation_range_invariants():
    """TEST-F29-03: Invariantes y validaciones de ValuationRange."""
    vr = ValuationRange(
        min_price=Money(Decimal("1000")),
        median_price=Money(Decimal("1150")),
        max_price=Money(Decimal("1300")),
    )
    assert vr.min_price.amount == Decimal("1000")
    assert vr.median_price.amount == Decimal("1150")
    assert vr.max_price.amount == Decimal("1300")

    with pytest.raises(ValueError, match="no puede ser mayor que el precio mediano"):
        ValuationRange(
            min_price=Money(Decimal("1200")),
            median_price=Money(Decimal("1100")),
            max_price=Money(Decimal("1300")),
        )

    with pytest.raises(ValueError, match="no puede ser mayor que el precio máximo"):
        ValuationRange(
            min_price=Money(Decimal("1000")),
            median_price=Money(Decimal("1400")),
            max_price=Money(Decimal("1300")),
        )


def test_f29_04_reasoning_factor_and_source_value_objects():
    """TEST-F29-04: Value Objects ReasoningFactor y ValuationSource."""
    factor = ReasoningFactor(
        factor_name="Presencia de ascensor",
        impact_percent=Decimal("0.05"),
        description="Planta intermedia con ascensor",
    )
    assert factor.factor_name == "Presencia de ascensor"
    assert factor.impact_percent == Decimal("0.05")

    with pytest.raises(ValueError, match="no puede estar vacío"):
        ReasoningFactor(factor_name="", impact_percent=Decimal("0.05"), description="ok")

    source = ValuationSource(
        title="Piso en Almagro",
        url="https://idealista.com/inmueble/123",
        price=Decimal("1250"),
        surface_m2=85,
        date_found=date(2026, 9, 20),
    )
    assert source.title == "Piso en Almagro"
    assert source.price == Decimal("1250")

    with pytest.raises(ValueError, match="http:// o https://"):
        ValuationSource(title="Fuente inválida", url="ftp://inmueble.es")


def test_f29_05_property_valuation_entity_identity():
    """TEST-F29-05: Entidad PropertyValuation e identidad."""
    sale_range = ValuationRange(
        min_price=Money(Decimal("250000")),
        median_price=Money(Decimal("280000")),
        max_price=Money(Decimal("310000")),
    )
    rent_range = ValuationRange(
        min_price=Money(Decimal("1100")),
        median_price=Money(Decimal("1250")),
        max_price=Money(Decimal("1400")),
    )
    factor = ReasoningFactor("Estado reformado", Decimal("0.10"), "Cocina y baños a estrenar")
    source = ValuationSource("Testigo Calle Mayor", "https://idealista.com/123", Decimal("1300"), 80)

    val1 = PropertyValuation(
        property_id="prop-abc",
        valuation_date=date(2026, 9, 26),
        sale_range=sale_range,
        rent_range=rent_range,
        confidence=ValuationConfidence.HIGH,
        reasoning_factors=[factor],
        sources=[source],
        raw_notes="Zona de alta demanda",
    )

    assert val1.property_id == "prop-abc"
    assert val1.confidence == ValuationConfidence.HIGH
    assert len(val1.reasoning_factors) == 1
    assert len(val1.sources) == 1

    # Igualdad por identidad id
    val2 = PropertyValuation(
        id=val1.id,
        property_id="prop-otro",
        valuation_date=date(2026, 9, 26),
        sale_range=sale_range,
        rent_range=rent_range,
        confidence=ValuationConfidence.LOW,
    )
    assert val1 == val2
    assert hash(val1) == hash(val2)

    with pytest.raises(ValueError, match="property_id no puede estar vacío"):
        PropertyValuation(
            property_id="",
            valuation_date=date(2026, 9, 26),
            sale_range=sale_range,
            rent_range=rent_range,
            confidence=ValuationConfidence.LOW,
        )
