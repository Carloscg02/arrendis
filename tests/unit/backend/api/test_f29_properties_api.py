from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.adapters.sqlite_adapter import SQLitePropertyValuationRepository
from backend.domain.entities import (
    PropertyValuation,
    ValuationConfidence,
)
from backend.domain.value_objects import (
    Money,
    ValuationRange,
    ReasoningFactor,
    ValuationSource,
)


def test_api_f29_01_create_property_with_physical_attributes(client: TestClient):
    """TEST-F29-09: POST /api/properties con atributos físicos."""
    payload = {
        "name": "Piso Salamanca",
        "address": {
            "street": "Calle Serrano 50",
            "city": "Madrid",
            "postal_code": "28001",
            "country": "ES",
        },
        "property_type": "apartment",
        "surface_m2": 120,
        "bedrooms": 3,
        "bathrooms": 2,
        "floor": 4,
        "has_elevator": True,
        "condition": "reformado",
    }
    response = client.post("/api/properties", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["surface_m2"] == 120
    assert data["bedrooms"] == 3
    assert data["bathrooms"] == 2
    assert data["floor"] == 4
    assert data["has_elevator"] is True
    assert data["condition"] == "reformado"


def test_api_f29_02_patch_physical_attributes(client: TestClient):
    """TEST-F29-10: PATCH /api/properties/{id}/physical-attributes."""
    create_res = client.post(
        "/api/properties",
        json={
            "name": "Piso Chamberí",
            "address": {
                "street": "Calle Santa Engracia 10",
                "city": "Madrid",
                "postal_code": "28010",
                "country": "ES",
            },
            "property_type": "apartment",
        },
    )
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/properties/{prop_id}/physical-attributes",
        json={
            "surface_m2": 80,
            "bedrooms": 2,
            "bathrooms": 1,
            "floor": 3,
            "has_elevator": True,
            "condition": "buen_estado",
        },
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["surface_m2"] == 80
    assert data["bedrooms"] == 2
    assert data["bathrooms"] == 1
    assert data["floor"] == 3
    assert data["has_elevator"] is True
    assert data["condition"] == "buen_estado"


def test_api_f29_03_patch_physical_attributes_validation_errors(client: TestClient):
    """TEST-F29-11: Validaciones en PATCH /api/properties/{id}/physical-attributes."""
    create_res = client.post(
        "/api/properties",
        json={
            "name": "Piso Tetuán",
            "address": {
                "street": "Calle Bravo Murillo 100",
                "city": "Madrid",
                "postal_code": "28020",
                "country": "ES",
            },
            "property_type": "apartment",
        },
    )
    prop_id = create_res.json()["id"]

    # Superficie no puede ser <= 0
    res1 = client.patch(
        f"/api/properties/{prop_id}/physical-attributes",
        json={"surface_m2": 0},
    )
    assert res1.status_code == 422

    # Habitaciones no pueden ser negativas
    res2 = client.patch(
        f"/api/properties/{prop_id}/physical-attributes",
        json={"bedrooms": -1},
    )
    assert res2.status_code == 422


def test_api_f29_04_get_latest_valuation_returns_none_when_empty(client: TestClient):
    """TEST-F29-12: GET /api/properties/{id}/valuation/latest sin valoraciones."""
    create_res = client.post(
        "/api/properties",
        json={
            "name": "Piso Sin Tasación",
            "address": {
                "street": "Calle Alcalá 200",
                "city": "Madrid",
                "postal_code": "28028",
                "country": "ES",
            },
            "property_type": "apartment",
        },
    )
    prop_id = create_res.json()["id"]

    val_res = client.get(f"/api/properties/{prop_id}/valuation/latest")
    assert val_res.status_code == 200
    assert val_res.json() is None


from backend.api.dependencies import get_db

def test_api_f29_05_get_latest_and_history_valuation(client: TestClient):
    """TEST-F29-13: GET /api/properties/{id}/valuation/latest y /history con datos."""
    create_res = client.post(
        "/api/properties",
        json={
            "name": "Piso Tasado",
            "address": {
                "street": "Calle Goya 80",
                "city": "Madrid",
                "postal_code": "28001",
                "country": "ES",
            },
            "property_type": "apartment",
        },
    )
    prop_id = create_res.json()["id"]

    # Guardar dos valoraciones en BD del cliente de test
    db = client.app.dependency_overrides[get_db]()
    val_repo = SQLitePropertyValuationRepository(db)

    val1 = PropertyValuation(
        property_id=prop_id,
        valuation_date=date(2026, 3, 1),
        sale_range=ValuationRange(Money(Decimal("300000")), Money(Decimal("320000")), Money(Decimal("340000"))),
        rent_range=ValuationRange(Money(Decimal("1200")), Money(Decimal("1300")), Money(Decimal("1400"))),
        confidence=ValuationConfidence.MEDIUM,
    )
    val2 = PropertyValuation(
        property_id=prop_id,
        valuation_date=date(2026, 9, 1),
        sale_range=ValuationRange(Money(Decimal("310000")), Money(Decimal("330000")), Money(Decimal("350000"))),
        rent_range=ValuationRange(Money(Decimal("1250")), Money(Decimal("1350")), Money(Decimal("1450"))),
        confidence=ValuationConfidence.HIGH,
        reasoning_factors=[ReasoningFactor("Ascensor", Decimal("0.05"), "Dispone de ascensor")],
        sources=[ValuationSource("Anuncio Test", "https://idealista.com/test", Decimal("1350"), 75)],
    )
    val_repo.save(val1)
    val_repo.save(val2)

    # Latest (debe ser val2)
    latest_res = client.get(f"/api/properties/{prop_id}/valuation/latest")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["id"] == val2.id
    assert latest_data["confidence"] == "high"
    assert latest_data["rent_range"]["median"] == 1350.0
    assert len(latest_data["reasoning_factors"]) == 1
    assert latest_data["reasoning_factors"][0]["factor_name"] == "Ascensor"

    # History (debe tener val2 primero y val1 segundo)
    history_res = client.get(f"/api/properties/{prop_id}/valuation/history")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data) == 2
    assert history_data[0]["id"] == val2.id
    assert history_data[1]["id"] == val1.id
