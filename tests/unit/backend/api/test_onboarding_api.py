"""
Tests de API para Endpoints de Onboarding y Estimación Fiscal Rápida (F-28).
"""

import pytest
from fastapi.testclient import TestClient
from backend.adapters.sqlite_adapter import SQLiteUserRepository
from backend.api.dependencies import get_db


def test_api_f28_01_quick_estimate_success(client: TestClient):
    """API-F28-01: POST /api/fiscal/quick-estimate devuelve 200 y JSON con cálculos."""
    payload = {
        "purchase_price": 200000,
        "acquisition_year": 2021,
        "construction_ratio": 0.70,
    }
    response = client.post("/api/fiscal/quick-estimate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["purchase_price"] == "200000.00"
    assert data["estimated_construction_value"] == "140000.00"
    assert data["annual_amortization"] == "4200.00"
    assert data["estimated_tax_savings_typical"] == "1260.00"
    assert "Art. 23.1.b" in data["legal_reference"]
    assert "orientativo" in data["disclaimer"]


def test_api_f28_02_quick_estimate_invalid_price(client: TestClient):
    """API-F28-02: POST /api/fiscal/quick-estimate devuelve 422 si el precio es inválido."""
    payload = {
        "purchase_price": -500,
        "acquisition_year": 2021,
    }
    response = client.post("/api/fiscal/quick-estimate", json=payload)
    assert response.status_code == 422


def test_api_f28_03_onboarding_bootstrap_success(client: TestClient, auth_user):
    """API-F28-03: POST /api/onboarding/bootstrap crea recursos de forma atómica."""
    db = client.app.dependency_overrides[get_db]()
    user_repo = SQLiteUserRepository(db)
    user_repo.save(auth_user)

    payload = {
        "property_name": "Ático Malasaña",
        "property_type": "apartment",
        "street": "Calle Fuencarral 10",
        "city": "Madrid",
        "postal_code": "28004",
        "country": "ES",
        "purchase_price": 210000,
        "acquisition_year": 2022,
        "monthly_rent": 950,
        "cups_electricity": "ES0031103721971011PR0F",
    }
    response = client.post("/api/onboarding/bootstrap", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ático Malasaña"
    assert data["has_fiscal_data"] is True
    assert data["cups_electricity"] == "ES0031103721971011PR0F"

    # Verificar que el usuario quedó con onboarding_completed = True
    user = user_repo.find_by_id(auth_user.id)
    assert user.onboarding_completed is True


def test_api_f28_04_onboarding_skip_success(client: TestClient, auth_user):
    """API-F28-04: POST /api/users/me/onboarding/skip marca completado y devuelve 200."""
    db = client.app.dependency_overrides[get_db]()
    user_repo = SQLiteUserRepository(db)
    user_repo.save(auth_user)

    response = client.post("/api/users/me/onboarding/skip")
    assert response.status_code == 200
    assert response.json()["onboarding_completed"] is True

    user = user_repo.find_by_id(auth_user.id)
    assert user.onboarding_completed is True


def test_api_f28_05_auth_me_reflects_onboarding_completed(client: TestClient, auth_user):
    """API-F28-05: GET /api/auth/me incluye el campo onboarding_completed."""
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "onboarding_completed" in data
