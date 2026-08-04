import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

def test_create_contract_api(client: TestClient, auth_user):
    """T-I-10-05"""
    # Create property
    prop_res = client.post("/api/properties", json={
        "name": "Prop", "address": {"street":"S","city":"C","postal_code":"P"}, "property_type": "apartment"
    })
    prop_id = prop_res.json()["id"]

    res = client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "John",
        "tenant_nif": "123",
        "start_date": "2025-01-01",
        "monthly_rent": 1000.50,
        "lease_type": "vivienda_habitual"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["tenant_name"] == "John"
    assert data["monthly_rent"] == "1000.5"
    assert data["is_active"] is True

def test_list_contracts_api(client: TestClient, auth_user):
    """T-I-10-06"""
    prop_res = client.post("/api/properties", json={
        "name": "Prop2", "address": {"street":"S","city":"C","postal_code":"P"}, "property_type": "apartment"
    })
    prop_id = prop_res.json()["id"]
    client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "John", "tenant_nif": "123", "start_date": "2025-01-01", "monthly_rent": 1000, "lease_type": "vivienda_habitual"
    })

    res = client.get(f"/api/properties/{prop_id}/contracts")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["tenant_name"] == "John"

def test_update_contract_api(client: TestClient, auth_user):
    """T-I-10-07"""
    prop_res = client.post("/api/properties", json={
        "name": "Prop3", "address": {"street":"S","city":"C","postal_code":"P"}, "property_type": "apartment"
    })
    prop_id = prop_res.json()["id"]
    c_res = client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "John", "tenant_nif": "123", "start_date": "2025-01-01", "monthly_rent": 1000, "lease_type": "vivienda_habitual"
    })
    c_id = c_res.json()["id"]
    
    res = client.put(f"/api/contracts/{c_id}", json={
        "tenant_name": "Jane", "monthly_rent": 1500
    })
    assert res.status_code == 200
    assert res.json()["tenant_name"] == "Jane"
    assert Decimal(res.json()["monthly_rent"]) == Decimal("1500")

def test_delete_contract_api(client: TestClient, auth_user):
    """T-I-10-08"""
    prop_res = client.post("/api/properties", json={
        "name": "Prop4", "address": {"street":"S","city":"C","postal_code":"P"}, "property_type": "apartment"
    })
    prop_id = prop_res.json()["id"]
    c_res = client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "John", "tenant_nif": "123", "start_date": "2025-01-01", "monthly_rent": 1000, "lease_type": "vivienda_habitual"
    })
    c_id = c_res.json()["id"]

    res = client.delete(f"/api/contracts/{c_id}")
    assert res.status_code == 204

def test_create_contract_wrong_user(client: TestClient, auth_user):
    """T-I-10-09"""
    prop_res = client.post("/api/properties", json={
        "name": "Prop5", "address": {"street":"S","city":"C","postal_code":"P"}, "property_type": "apartment"
    })
    prop_id = prop_res.json()["id"]

    from backend.api.main import app
    from backend.api.dependencies import get_current_user
    from backend.domain.entities import User
    from backend.domain.value_objects import Email, PasswordHash
    user_b = User(
        email=Email("userb@test.com"),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="user_b",
        id="user-2",
    )
    app.dependency_overrides[get_current_user] = lambda: user_b

    res = client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "John", "tenant_nif": "123", "start_date": "2025-01-01", "monthly_rent": 1000, "lease_type": "vivienda_habitual"
    })
    assert res.status_code == 404
    app.dependency_overrides[get_current_user] = lambda: auth_user

def test_contract_response_is_active_calculated(client: TestClient, auth_user):
    """T-I-10-10"""
    prop_res = client.post("/api/properties", json={
        "name": "Prop6", "address": {"street":"S","city":"C","postal_code":"P"}, "property_type": "apartment"
    })
    prop_id = prop_res.json()["id"]
    
    # Active contract
    c1 = client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "A", "tenant_nif": "1", "start_date": "2025-01-01", "monthly_rent": 100, "lease_type": "vivienda_habitual"
    }).json()
    assert c1["is_active"] is True
    
    # Inactive contract
    c2 = client.post(f"/api/properties/{prop_id}/contracts", json={
        "tenant_name": "B", "tenant_nif": "2", "start_date": "2023-01-01", "end_date": "2024-01-01", "monthly_rent": 100, "lease_type": "vivienda_habitual"
    }).json()
    assert c2["is_active"] is False
