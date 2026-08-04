from fastapi.testclient import TestClient

VALID_PROPERTY_PAYLOAD = {
    "name": "Test Property",
    "address": {
        "street": "Calle Test 1",
        "city": "Madrid",
        "postal_code": "28001",
        "country": "ES"
    },
    "property_type": "apartment"
}

def test_create_property(client: TestClient):
    """AP-01: POST /api/properties with valid data."""
    response = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Property"
    assert data["address"]["city"] == "Madrid"
    assert data["property_type"] == "apartment"
    assert data["status"] == "available"

def test_create_property_invalid_type(client):
    payload = {
        "name": "Invalid Prop",
        "address": {
            "street": "Test", "city": "Madrid", 
            "postal_code": "28001", "country": "ES"
        },
        "property_type": "invalid_type"
    }
    response = client.post("/api/properties", json=payload)
    assert response.status_code == 400  # Capturado como ValueError en el router

def test_create_property_duplicate_name(client):
    payload = {
        "name": "Unique Name",
        "address": {
            "street": "Test", "city": "Madrid", 
            "postal_code": "28001", "country": "ES"
        },
        "property_type": "apartment"
    }
    # Primera vez: 201 Created
    res1 = client.post("/api/properties", json=payload)
    assert res1.status_code == 201
    
    # Segunda vez: 400 Bad Request
    res2 = client.post("/api/properties", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_create_property_empty_name(client: TestClient):
    """AP-03: POST with empty name."""
    payload = VALID_PROPERTY_PAYLOAD.copy()
    payload["name"] = "   "
    response = client.post("/api/properties", json=payload)
    assert response.status_code == 400

def test_list_properties_empty(client: TestClient):
    """AP-04: GET /api/properties when empty."""
    response = client.get("/api/properties")
    assert response.status_code == 200
    assert response.json() == []

def test_list_properties_after_create(client: TestClient):
    """AP-05: POST then GET."""
    client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    
    response = client.get("/api/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Property"

def test_get_property_by_id(client: TestClient):
    """AP-06: POST then GET /api/properties/{id}."""
    create_response = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = create_response.json()["id"]
    
    response = client.get(f"/api/properties/{prop_id}")
    assert response.status_code == 200
    assert response.json()["id"] == prop_id

def test_get_property_not_found(client: TestClient):
    """AP-07: GET /api/properties/fake-uuid."""
    response = client.get("/api/properties/fake-uuid")
    assert response.status_code == 404


def test_upload_property_image_valid(client: TestClient):
    """T-04: POST /api/properties/{id}/image con JPG válido."""
    create_response = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = create_response.json()["id"]
    
    # Minimal valid JPEG
    test_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9])
    
    try:
        response = client.post(
            f"/api/properties/{prop_id}/image",
            files={"file": ("test.jpg", test_jpeg, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
        assert data["image_url"] == f"/api/images/{prop_id}.jpg"
    finally:
        client.delete(f"/api/properties/{prop_id}")


def test_upload_property_image_not_found(client: TestClient):
    """T-05: POST /api/properties/{id}/image con propiedad inexistente."""
    test_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9])
    
    response = client.post(
        "/api/properties/fake-uuid/image",
        files={"file": ("test.jpg", test_jpeg, "image/jpeg")}
    )
    assert response.status_code == 404


def test_upload_property_image_invalid_type(client: TestClient):
    """T-06: POST /api/properties/{id}/image con archivo no imagen."""
    create_response = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = create_response.json()["id"]
    
    response = client.post(
        f"/api/properties/{prop_id}/image",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400


def test_get_properties_includes_image_url(client: TestClient):
    """T-07: GET /api/properties response incluye campo image_url."""
    # Vaciar primero para este test no es necesario si la base de datos es fresca
    client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    
    response = client.get("/api/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "image_url" in data[0]
    
    
def test_delete_property_deletes_image_file(client: TestClient):
    """T-08: DELETE /api/properties/{id} elimina también el archivo de imagen."""
    import os
    
    create_response = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = create_response.json()["id"]
    
    test_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9])
    client.post(
        f"/api/properties/{prop_id}/image",
        files={"file": ("test.jpg", test_jpeg, "image/jpeg")}
    )
    
    image_path = f"data/images/{prop_id}.jpg"
    assert os.path.exists(image_path)
    
    client.delete(f"/api/properties/{prop_id}")
    assert not os.path.exists(image_path)

def test_list_properties_isolated(client: TestClient, auth_user):
    """AP-09: Properties isolation between users."""
    from backend.api.main import app
    from backend.api.dependencies import get_current_user
    from backend.domain.entities import User
    from backend.domain.value_objects import Email, PasswordHash
    
    # User A (user-1) creates property
    client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    
    # User B creates property
    user_b = User(
        email=Email("userb@test.com"),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="user_b",
        id="user-2",
    )
    
    # Temporarily override user
    app.dependency_overrides[get_current_user] = lambda: user_b
    payload_b = VALID_PROPERTY_PAYLOAD.copy()
    payload_b["name"] = "Property B"
    client.post("/api/properties", json=payload_b)
    
    # Check user B sees 1
    res_b = client.get("/api/properties")
    assert len(res_b.json()) == 1
    assert res_b.json()[0]["name"] == "Property B"
    
    # Restore User A and check sees 1
    app.dependency_overrides[get_current_user] = lambda: auth_user
    res_a = client.get("/api/properties")
    assert len(res_a.json()) == 1
    assert res_a.json()[0]["name"] == "Test Property"

def test_create_property_unauthenticated(client: TestClient):
    """AP-10: POST without token is 401."""
    from backend.api.main import app
    from backend.api.dependencies import get_current_user
    
    # Remove mock completely
    del app.dependency_overrides[get_current_user]
    
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    assert res.status_code == 401
    
    # No need to restore, fixture takes care of it, but just in case, this is last in execution

def test_record_expense_for_others_property(client: TestClient, auth_user):
    """AP-11: 404/403 for other user's property."""
    from backend.api.main import app
    from backend.api.dependencies import get_current_user
    from backend.domain.entities import User
    from backend.domain.value_objects import Email, PasswordHash
    
    # User A creates property
    res_a = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = res_a.json()["id"]
    
    # Switch to User B
    user_b = User(
        email=Email("userb@test.com"),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="user_b",
        id="user-2",
    )
    app.dependency_overrides[get_current_user] = lambda: user_b
    
    expense_payload = {
        "property_id": prop_id,
        "amount": 100,
        "date": "2026-08-01",
        "category": "repair",
        "description": "Test"
    }
    res = client.post("/api/expenses", json=expense_payload)
    assert res.status_code == 404
    assert "No existe" in res.json()["detail"]


def test_get_fiscal_data_empty(client: TestClient, auth_user):
    """T-I-09-06: GET /api/properties/{id}/fiscal-data retorna datos vacíos inicialmente"""
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = res.json()["id"]
    
    fiscal_res = client.get(f"/api/properties/{prop_id}/fiscal-data")
    assert fiscal_res.status_code == 200
    data = fiscal_res.json()
    assert data["cadastral_ref"] is None
    assert data["has_fiscal_data"] is False


def test_put_fiscal_data(client: TestClient, auth_user):
    """T-I-09-07: PUT /api/properties/{id}/fiscal-data persiste y retorna datos fiscales"""
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = res.json()["id"]
    
    payload = {
        "cadastral_ref": "1234567AB1234C0001XY",
        "cadastral_breakdown": {"land_value": "40000", "construction_value": "80000"},
        "acquisition_cost": {
            "purchase_price": "200000",
            "construction_portion": "120000",
            "land_portion": "80000"
        },
        "acquisition_date": "2020-01-01"
    }
    
    fiscal_res = client.put(f"/api/properties/{prop_id}/fiscal-data", json=payload)
    assert fiscal_res.status_code == 200
    data = fiscal_res.json()
    assert data["has_fiscal_data"] is True
    assert data["cadastral_ref"] == "1234567AB1234C0001XY"


def test_put_fiscal_data_invalid(client: TestClient, auth_user):
    """T-I-09-08: PUT /api/properties/{id}/fiscal-data con datos inválidos no corrompe la BD y retorna 422 o 400"""
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = res.json()["id"]
    
    payload = {
        "cadastral_ref": "123",  # invalid length
    }
    fiscal_res = client.put(f"/api/properties/{prop_id}/fiscal-data", json=payload)
    assert fiscal_res.status_code in (400, 422)

    # Verificar que las consultas posteriores de propiedades sigan funcionando (no hay corrupción en DB)
    list_res = client.get("/api/properties")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_get_fiscal_data_other_user(client: TestClient, auth_user):
    """T-I-09-09: GET /api/properties/{id}/fiscal-data de propiedad ajena retorna 404"""
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = res.json()["id"]
    
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
    
    fiscal_res = client.get(f"/api/properties/{prop_id}/fiscal-data")
    assert fiscal_res.status_code == 404
    
    app.dependency_overrides[get_current_user] = lambda: auth_user


def test_property_response_includes_has_fiscal_data(client: TestClient, auth_user):
    """T-I-09-10: PropertyResponse incluye has_fiscal_data"""
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    assert "has_fiscal_data" in res.json()
    assert res.json()["has_fiscal_data"] is False


def test_get_fiscal_suggestions(client: TestClient, auth_user):
    """T-I-11-10: GET /api/properties/{id}/fiscal-suggestions"""
    res = client.post("/api/properties", json=VALID_PROPERTY_PAYLOAD)
    prop_id = res.json()["id"]
    
    client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 750.00,
        "date": "2026-07-01",
        "category": "rent"
    })
    
    client.post("/api/expenses", json={
        "property_id": prop_id,
        "amount": 200.00,
        "date": "2026-07-05",
        "category": "repair"
    })
    
    res_sugg = client.get(f"/api/properties/{prop_id}/fiscal-suggestions")
    assert res_sugg.status_code == 200
    data = res_sugg.json()
    
    assert data["total_unclassified"] == 2
    assert len(data["unclassified_incomes"]) == 1
    assert data["unclassified_incomes"][0]["suggested_fiscal_category"] == "rendimiento_integro"
    
    assert len(data["unclassified_expenses"]) == 1
    assert data["unclassified_expenses"][0]["suggested_fiscal_category"] == "reparacion_conservacion"
