from backend.api.dependencies import get_current_user
from backend.domain.entities import User
from backend.domain.value_objects import Email, PasswordHash

def override_get_current_user():
    return User(
        id="test-user-id",
        email=Email("test@example.com"),
        username="testuser",
        password_hash=PasswordHash("$2b$12$somehash")
    )

def test_api_f16_01_update_cups(e2e_client):
    e2e_client.app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Crear propiedad
    resp = e2e_client.post("/api/properties", json={
        "name": "P1",
        "address": {"street": "C/ 1", "city": "Madrid", "postal_code": "28001"},
        "property_type": "apartment"
    })
    assert resp.status_code == 201
    prop_id = resp.json()["id"]
    
    # Update CUPS
    update_resp = e2e_client.put(f"/api/properties/{prop_id}/cups", json={
        "cups_electricity": "ES00210000000000000000",
        "cups_gas": "ES00310000000000000000",
        "cups_water": None
    })
    
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["cups_electricity"] == "ES00210000000000000000"
    assert data["cups_gas"] == "ES00310000000000000000"
    assert data["cups_water"] is None

def test_api_f16_02_update_cups_invalid(e2e_client):
    e2e_client.app.dependency_overrides[get_current_user] = override_get_current_user
    
    resp = e2e_client.post("/api/properties", json={
        "name": "P1",
        "address": {"street": "C/ 1", "city": "Madrid", "postal_code": "28001"},
        "property_type": "apartment"
    })
    prop_id = resp.json()["id"]
    
    update_resp = e2e_client.put(f"/api/properties/{prop_id}/cups", json={
        "cups_electricity": "INVALID_CUPS"
    })
    
    assert update_resp.status_code == 400

def test_api_f16_03_create_expense_response_fields(e2e_client):
    e2e_client.app.dependency_overrides[get_current_user] = override_get_current_user
    
    resp = e2e_client.post("/api/properties", json={
        "name": "P1",
        "address": {"street": "C/ 1", "city": "Madrid", "postal_code": "28001"},
        "property_type": "apartment"
    })
    prop_id = resp.json()["id"]
    
    exp_resp = e2e_client.post("/api/expenses", json={
        "property_id": prop_id,
        "amount": "50.0",
        "date": "2024-01-01",
        "category": "repair",
        "description": "test"
    })
    
    assert exp_resp.status_code == 201
    data = exp_resp.json()
    assert data["is_verified"] is True
    assert data["source"] == "manual"
    assert data["utility_data"] is None
