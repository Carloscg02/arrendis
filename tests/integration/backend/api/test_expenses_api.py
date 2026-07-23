from fastapi.testclient import TestClient

def create_property(client: TestClient) -> str:
    """Helper to create a property and return its ID."""
    response = client.post("/api/properties", json={
        "name": "Test Property",
        "address": {
            "street": "Calle Test 1",
            "city": "Madrid",
            "postal_code": "28001",
            "country": "ES"
        },
        "property_type": "apartment"
    })
    return response.json()["id"]

def test_record_expense(client: TestClient):
    """AE-01: POST /api/expenses with valid data."""
    prop_id = create_property(client)
    
    response = client.post("/api/expenses", json={
        "property_id": prop_id,
        "amount": 200.00,
        "date": "2026-07-05",
        "category": "repair",
        "description": "Test repair"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["property_id"] == prop_id
    assert data["amount"] == "200.0"
    assert data["currency"] == "EUR"
    assert data["category"] == "repair"

def test_record_expense_invalid_property(client: TestClient):
    """AE-02: POST with fake property_id."""
    response = client.post("/api/expenses", json={
        "property_id": "fake-uuid",
        "amount": 200.00,
        "date": "2026-07-05",
        "category": "repair",
        "description": "Test repair"
    })
    assert response.status_code == 404

def test_list_expenses_by_property(client: TestClient):
    """AE-03: POST expense + GET /{id}/expenses."""
    prop_id = create_property(client)
    
    client.post("/api/expenses", json={
        "property_id": prop_id,
        "amount": 200.00,
        "date": "2026-07-05",
        "category": "repair",
        "description": "Test repair"
    })
    
    response = client.get(f"/api/properties/{prop_id}/expenses")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == "200.0"
