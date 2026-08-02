import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.domain.entities import User
from backend.domain.value_objects import Email, PasswordHash

def _setup_property_with_fiscal_data(client):
    # Crear propiedad
    res = client.post("/api/properties", json={
        "name": "Piso Fiscal",
        "address": {"street": "C", "city": "M", "postal_code": "28", "country": "ES"},
        "property_type": "apartment"
    })
    prop_id = res.json()["id"]

    # Añadir datos fiscales
    client.put(f"/api/properties/{prop_id}/fiscal-data", json={
        "cadastral_breakdown": {"land_value": "40000", "construction_value": "60000"},
        "acquisition_cost": {
            "purchase_price": "150000",
            "construction_portion": "90000",
            "land_portion": "60000",
            "transfer_tax": "15000",
            "notary_fees": "1000",
            "registry_fees": "500"
        },
        "acquisition_date": "2020-01-01"
    })
    return prop_id

def test_ti_12_01_get_fiscal_report_success(client: TestClient):
    """T-I-12-01: GET fiscal-report con datos completos retorna 200"""
    prop_id = _setup_property_with_fiscal_data(client)

    # Añadir contrato
    client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "Juan",
        "tenant_nif": "12345678A",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "monthly_rent": 1000,
        "lease_type": "vivienda_habitual"
    })

    res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025")
    assert res.status_code == 200
    data = res.json()
    assert data["fiscal_year"] == 2025
    assert data["property_id"] == prop_id
    assert data["rented_days"] == 365

def test_ti_12_02_get_fiscal_report_no_fiscal_data(client: TestClient):
    """T-I-12-02: GET fiscal-report sin datos fiscales retorna 400"""
    res = client.post("/api/properties", json={
        "name": "Piso Sin Datos",
        "address": {"street": "C", "city": "M", "postal_code": "28", "country": "ES"},
        "property_type": "apartment"
    })
    prop_id = res.json()["id"]

    res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025")
    assert res.status_code == 400
    assert "datos fiscales" in res.json()["detail"].lower()

def test_ti_12_03_get_fiscal_report_wrong_user(client: TestClient):
    """T-I-12-03: GET fiscal-report propiedad ajena retorna 404"""
    # Para simular propiedad de otro usuario, override get_current_user temporalmente
    from backend.api.main import app
    from backend.api.dependencies import get_current_user
    
    prop_id = _setup_property_with_fiscal_data(client)

    other_user = User(
        email=Email("other@example.com"),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="otheruser",
        id="user-2",
    )
    app.dependency_overrides[get_current_user] = lambda: other_user

    res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025")
    assert res.status_code == 404

    # Restaurar
    auth_user = User(
        email=Email("test@example.com"),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="testuser",
        id="user-1",
    )
    app.dependency_overrides[get_current_user] = lambda: auth_user

def test_ti_12_04_get_fiscal_report_no_contracts(client: TestClient):
    """T-I-12-04: GET fiscal-report sin contratos en año -> todo a 0"""
    prop_id = _setup_property_with_fiscal_data(client)
    res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025")
    assert res.status_code == 200
    data = res.json()
    assert data["rented_days"] == 0
    assert Decimal(str(data["total_deductible_expenses"])) == Decimal("0")
    assert Decimal(str(data["net_income_final"])) == Decimal("0")

def test_ti_12_05_get_fiscal_report_numeric_calculations(client: TestClient):
    """T-I-12-05: GET fiscal-report cálculos numéricos correctos end-to-end"""
    prop_id = _setup_property_with_fiscal_data(client)

    client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "Juan",
        "tenant_nif": "12345678A",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "monthly_rent": 1000,
        "lease_type": "vivienda_habitual"
    })

    client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 12000,
        "date": "2025-06-01",
        "category": "rent",
        "fiscal_category": "rendimiento_integro"
    })

    client.post("/api/expenses", json={
        "property_id": prop_id,
        "amount": 500,
        "date": "2025-06-01",
        "category": "tax",
        "fiscal_category": "tributos"
    })

    res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025")
    assert res.status_code == 200
    data = res.json()
    
    assert Decimal(str(data["total_income"])) == Decimal("12000")
    assert Decimal(str(data["amortization_base"])) == Decimal("99900")
    assert Decimal(str(data["total_deductible_expenses"])) == Decimal("3497")
    assert Decimal(str(data["net_income_before_reduction"])) == Decimal("8503")
    assert Decimal(str(data["reduction_amount"])) == Decimal("5101.8")
    assert Decimal(str(data["net_income_final"])) == Decimal("3401.2")
