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

def test_record_income_with_fiscal_category(client: TestClient):
    """T-I-11-06: POST /api/incomes con fiscal_category"""
    prop_id = create_property(client)
    
    response = client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent",
        "fiscal_category": "rendimiento_integro"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["fiscal_category"] == "rendimiento_integro"

def test_update_income_fiscal_category(client: TestClient):
    """T-I-11-08: PATCH /api/incomes/{id}/fiscal-category"""
    prop_id = create_property(client)
    
    create_response = client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent"
    })
    inc_id = create_response.json()["id"]
    
    response = client.patch(f"/api/incomes/{inc_id}/fiscal-category", json={
        "fiscal_category": "rendimiento_integro"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["fiscal_category"] == "rendimiento_integro"


def test_delete_income_success(client: TestClient):
    """DELETE /api/incomes/{id} elimina el ingreso y devuelve 204."""
    prop_id = create_property(client)
    create_res = client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 500.00,
        "date": "2026-07-01",
        "category": "rent"
    })
    inc_id = create_res.json()["id"]

    # Verificar que existe
    list_res = client.get(f"/api/properties/{prop_id}/incomes")
    assert len(list_res.json()) == 1

    # Eliminar
    del_res = client.delete(f"/api/incomes/{inc_id}")
    assert del_res.status_code == 204

    # Verificar que ya no existe
    list_res_after = client.get(f"/api/properties/{prop_id}/incomes")
    assert len(list_res_after.json()) == 0


def test_delete_income_not_found(client: TestClient):
    """DELETE /api/incomes/{id} con id inexistente devuelve 404."""
    response = client.delete("/api/incomes/non-existent-id")
    assert response.status_code == 404

