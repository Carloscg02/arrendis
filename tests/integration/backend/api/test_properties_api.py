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
    
    response = client.post(
        f"/api/properties/{prop_id}/image",
        files={"file": ("test.jpg", test_jpeg, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "image_url" in data
    assert data["image_url"] == f"/api/images/{prop_id}.jpg"


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

