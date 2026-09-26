from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.api.dependencies import get_market_valuation_port
from backend.domain.entities import (
    ValuationRateLimitError,
    MarketValuationError,
)


def _create_test_property(client: TestClient, surface_m2: int | None = 90) -> str:
    payload = {
        "name": "Piso Malasaña",
        "address": {
            "street": "Calle Pez 15",
            "city": "Madrid",
            "postal_code": "28004",
            "country": "ES",
        },
        "property_type": "apartment",
    }
    if surface_m2 is not None:
        payload.update({
            "surface_m2": surface_m2,
            "bedrooms": 2,
            "bathrooms": 1,
            "floor": 2,
            "has_elevator": True,
            "condition": "buen_estado",
        })
    res = client.post("/api/properties", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_api_f31_01_request_valuation_fresh_success(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=90)

    res = client.post(f"/api/properties/{prop_id}/valuation")
    assert res.status_code == 200
    data = res.json()

    assert data["property_id"] == prop_id
    assert data["is_cached"] is False
    assert data["cooldown_days_remaining"] == 30
    assert data["sale_range"]["median"] > 0
    assert data["rent_range"]["median"] > 0
    assert len(data["sources"]) >= 1
    assert data["confidence"] == "high"


def test_api_f31_02_request_valuation_cooldown_cached(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=80)

    # First request
    res1 = client.post(f"/api/properties/{prop_id}/valuation")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_cached"] is False

    # Second request immediately afterwards (cached due to cooldown)
    res2 = client.post(f"/api/properties/{prop_id}/valuation")
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["is_cached"] is True
    assert data2["id"] == data1["id"]
    assert data2["cooldown_days_remaining"] == 30


def test_api_f31_03_request_valuation_force_refresh(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=80)

    # First request
    res1 = client.post(f"/api/properties/{prop_id}/valuation")
    assert res1.status_code == 200
    data1 = res1.json()

    # Forced request with ?force=true
    res2 = client.post(f"/api/properties/{prop_id}/valuation?force=true")
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["is_cached"] is False
    assert data2["id"] != data1["id"]
    assert data2["cooldown_days_remaining"] == 30


def test_api_f31_04_request_valuation_missing_surface_returns_422(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=None)

    res = client.post(f"/api/properties/{prop_id}/valuation")
    assert res.status_code == 422
    assert "superficie" in res.json()["detail"].lower()


def test_api_f31_05_request_valuation_property_not_found_returns_404(client: TestClient):
    res = client.post("/api/properties/non-existent-uuid/valuation")
    assert res.status_code == 404


def test_api_f31_06_request_valuation_rate_limit_error_returns_429(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=75)

    mock_port = MagicMock()
    mock_port.estimate_valuation.side_effect = ValuationRateLimitError(
        provider="gemini",
        retry_after_seconds=60,
    )

    client.app.dependency_overrides[get_market_valuation_port] = lambda: mock_port
    try:
        res = client.post(f"/api/properties/{prop_id}/valuation")
        assert res.status_code == 429
        assert res.headers.get("Retry-After") == "60"
    finally:
        client.app.dependency_overrides.pop(get_market_valuation_port, None)


def test_api_f31_07_request_valuation_provider_error_returns_502(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=75)

    mock_port = MagicMock()
    mock_port.estimate_valuation.side_effect = MarketValuationError(
        "Fallo de conexión",
        provider="gemini",
    )

    client.app.dependency_overrides[get_market_valuation_port] = lambda: mock_port
    try:
        res = client.post(f"/api/properties/{prop_id}/valuation")
        assert res.status_code == 502
        assert "proveedor de valoración" in res.json()["detail"].lower()
    finally:
        client.app.dependency_overrides.pop(get_market_valuation_port, None)


def test_api_f31_08_get_latest_valuation_includes_cooldown(client: TestClient):
    prop_id = _create_test_property(client, surface_m2=100)

    # Initial get latest should be null/empty
    res0 = client.get(f"/api/properties/{prop_id}/valuation/latest")
    assert res0.status_code == 200
    assert res0.json() is None

    # Request valuation
    post_res = client.post(f"/api/properties/{prop_id}/valuation")
    assert post_res.status_code == 200

    # Get latest should return cached with cooldown
    res_latest = client.get(f"/api/properties/{prop_id}/valuation/latest")
    assert res_latest.status_code == 200
    latest_data = res_latest.json()
    assert latest_data["is_cached"] is True
    assert latest_data["cooldown_days_remaining"] == 30
    assert latest_data["property_id"] == prop_id
