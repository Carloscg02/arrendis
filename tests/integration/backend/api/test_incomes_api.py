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

def test_record_income(client: TestClient):
    """AI-01: POST /api/incomes with valid data."""
    prop_id = create_property(client)
    
    response = client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent",
        "description": "Test rent"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["property_id"] == prop_id
    assert data["amount"] == "750.0"
    assert data["currency"] == "EUR"
    assert data["category"] == "rent"

def test_record_income_invalid_property(client: TestClient):
    """AI-02: POST with fake property_id."""
    response = client.post("/api/incomes", json={
        "property_id": "fake-uuid",
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent",
        "description": "Test rent"
    })
    assert response.status_code == 404

def test_list_incomes_by_property(client: TestClient):
    """AI-03: POST income + GET /{id}/incomes."""
    prop_id = create_property(client)
    
    client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent",
        "description": "Test rent"
    })
    
    response = client.get(f"/api/properties/{prop_id}/incomes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == "750.0"

def test_get_profit_report(client: TestClient):
    """AI-04: GET /{id}/profit after income and expense."""
    prop_id = create_property(client)
    
    # Record income
    client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent"
    })
    
    # Record expense
    client.post("/api/expenses", json={
        "property_id": prop_id,
        "amount": 200.00,
        "date": "2026-07-05",
        "category": "repair"
    })
    
    response = client.get(f"/api/properties/{prop_id}/profit")
    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == prop_id
    assert data["net_profit"] == "550.00"
    assert data["currency"] == "EUR"
