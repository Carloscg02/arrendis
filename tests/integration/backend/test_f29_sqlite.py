from datetime import date
from decimal import Decimal

from backend.adapters.sqlite_adapter import (
    SQLiteConnection,
    SQLitePropertyRepository,
    SQLitePropertyValuationRepository,
)
from backend.domain.entities import (
    Property,
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


def test_sqlite_f29_01_property_physical_columns_persisted():
    """TEST-F29-06: Persistencia y recuperación de atributos físicos en SQLite."""
    db = SQLiteConnection(":memory:")
    repo = SQLitePropertyRepository(db)

    prop = Property(
        name="Chamberí Clásico",
        address=Address("Calle Fuencarral 120", "Madrid", "28010"),
        property_type=PropertyType.APARTMENT,
        user_id="user-1",
        surface_m2=110,
        bedrooms=3,
        bathrooms=2,
        floor=4,
        has_elevator=True,
        condition=PropertyCondition.BUEN_ESTADO,
    )

    repo.save(prop)

    fetched = repo.find_by_id(prop.id)
    assert fetched is not None
    assert fetched.surface_m2 == 110
    assert fetched.bedrooms == 3
    assert fetched.bathrooms == 2
    assert fetched.floor == 4
    assert fetched.has_elevator is True
    assert fetched.condition == PropertyCondition.BUEN_ESTADO

    props = repo.list_properties("user-1")
    assert len(props) == 1
    assert props[0].surface_m2 == 110


def test_sqlite_f29_02_property_update_physical_attributes():
    """TEST-F29-07: Actualización exclusiva de atributos físicos con update_physical_attributes."""
    db = SQLiteConnection(":memory:")
    repo = SQLitePropertyRepository(db)

    prop = Property(
        name="Piso Moncloa",
        address=Address("Calle Princesa 40", "Madrid", "28008"),
        property_type=PropertyType.APARTMENT,
        user_id="user-1",
    )
    repo.save(prop)

    # Actualizar solo atributos físicos
    repo.update_physical_attributes(
        property_id=prop.id,
        surface_m2=75,
        bedrooms=2,
        bathrooms=1,
        floor=2,
        has_elevator=False,
        condition=PropertyCondition.A_REFORMAR,
    )

    updated = repo.find_by_id(prop.id)
    assert updated is not None
    assert updated.surface_m2 == 75
    assert updated.bedrooms == 2
    assert updated.bathrooms == 1
    assert updated.floor == 2
    assert updated.has_elevator is False
    assert updated.condition == PropertyCondition.A_REFORMAR


def test_sqlite_f29_03_property_valuation_repository_crud():
    """TEST-F29-08: CRUD completo del repositorio de valoraciones de mercado."""
    db = SQLiteConnection(":memory:")
    prop_repo = SQLitePropertyRepository(db)
    val_repo = SQLitePropertyValuationRepository(db)

    prop = Property(
        name="Piso Goya",
        address=Address("Calle Goya 25", "Madrid", "28001"),
        property_type=PropertyType.APARTMENT,
        user_id="user-1",
    )
    prop_repo.save(prop)

    # Valoración 1 (más antigua)
    val1 = PropertyValuation(
        property_id=prop.id,
        valuation_date=date(2026, 1, 15),
        sale_range=ValuationRange(Money(Decimal("300000")), Money(Decimal("320000")), Money(Decimal("350000"))),
        rent_range=ValuationRange(Money(Decimal("1200")), Money(Decimal("1300")), Money(Decimal("1450"))),
        confidence=ValuationConfidence.MEDIUM,
        reasoning_factors=[ReasoningFactor("Zona Barrio Salamanca", Decimal("0.15"), "Ubicación premium")],
        sources=[ValuationSource("Anuncio Goya 20", "https://idealista.com/1", Decimal("1350"), 70)],
        raw_notes="Primera tasación",
    )
    val_repo.save(val1)

    # Valoración 2 (más reciente)
    val2 = PropertyValuation(
        property_id=prop.id,
        valuation_date=date(2026, 9, 20),
        sale_range=ValuationRange(Money(Decimal("310000")), Money(Decimal("335000")), Money(Decimal("360000"))),
        rent_range=ValuationRange(Money(Decimal("1250")), Money(Decimal("1350")), Money(Decimal("1500"))),
        confidence=ValuationConfidence.HIGH,
        reasoning_factors=[
            ReasoningFactor("Zona Barrio Salamanca", Decimal("0.15"), "Ubicación premium"),
            ReasoningFactor("Alza de rentas", Decimal("0.05"), "Incremento interanual"),
        ],
        sources=[
            ValuationSource("Anuncio Goya 20", "https://idealista.com/1", Decimal("1350"), 70),
            ValuationSource("Anuncio Serrano 15", "https://fotocasa.es/2", Decimal("1400"), 75),
        ],
        raw_notes="Actualización tras 8 meses",
    )
    val_repo.save(val2)

    # find_by_id
    fetched = val_repo.find_by_id(val1.id)
    assert fetched is not None
    assert fetched.sale_range.min_price.amount == Decimal("300000")
    assert fetched.confidence == ValuationConfidence.MEDIUM
    assert len(fetched.reasoning_factors) == 1
    assert fetched.reasoning_factors[0].factor_name == "Zona Barrio Salamanca"

    # find_latest_by_property_id (debe ser val2 por ser del 2026-09-20)
    latest = val_repo.find_latest_by_property_id(prop.id)
    assert latest is not None
    assert latest.id == val2.id
    assert latest.valuation_date == date(2026, 9, 20)
    assert latest.confidence == ValuationConfidence.HIGH
    assert len(latest.reasoning_factors) == 2
    assert len(latest.sources) == 2

    # list_by_property_id (ordenadas descendente por fecha)
    history = val_repo.list_by_property_id(prop.id)
    assert len(history) == 2
    assert history[0].id == val2.id
    assert history[1].id == val1.id
