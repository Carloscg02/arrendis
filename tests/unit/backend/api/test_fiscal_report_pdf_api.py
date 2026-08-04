import pytest
from fastapi.testclient import TestClient

from backend.domain.entities import User
from backend.domain.value_objects import Email, PasswordHash


def _setup_property_with_fiscal_data(client: TestClient) -> str:
    # Crear propiedad
    res = client.post(
        "/api/properties",
        json={
            "name": "Piso Fiscal PDF",
            "address": {"street": "Calle Mayor 10", "city": "Madrid", "postal_code": "28001", "country": "ES"},
            "property_type": "apartment",
        },
    )
    prop_id = res.json()["id"]

    # Añadir datos fiscales
    client.put(
        f"/api/properties/{prop_id}/fiscal-data",
        json={
            "cadastral_breakdown": {"land_value": "40000", "construction_value": "60000"},
            "acquisition_cost": {
                "purchase_price": "150000",
                "construction_portion": "90000",
                "land_portion": "60000",
                "transfer_tax": "15000",
                "notary_fees": "1000",
                "registry_fees": "500",
            },
            "acquisition_date": "2020-01-01",
        },
    )
    return prop_id


def test_ti_13_01_download_pdf_success(client: TestClient):
    """T-I-13-01: GET /api/properties/{id}/fiscal-report/pdf?year=2026 retorna 200 y content-type application/pdf."""
    prop_id = _setup_property_with_fiscal_data(client)

    res = client.get(f"/api/properties/{prop_id}/fiscal-report/pdf?year=2026")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_ti_13_02_pdf_magic_bytes(client: TestClient):
    """T-I-13-02: El body del response empieza con %PDF-."""
    prop_id = _setup_property_with_fiscal_data(client)

    res = client.get(f"/api/properties/{prop_id}/fiscal-report/pdf?year=2026")
    assert res.status_code == 200
    assert res.content[:5] == b"%PDF-"


def test_ti_13_03_content_disposition_header(client: TestClient):
    """T-I-13-03: Header Content-Disposition contiene attachment y filename con nombre y año."""
    prop_id = _setup_property_with_fiscal_data(client)

    res = client.get(f"/api/properties/{prop_id}/fiscal-report/pdf?year=2026")
    assert res.status_code == 200
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "borrador_fiscal_Piso_Fiscal_PDF_2026.pdf" in cd


def test_ti_13_04_no_fiscal_data_returns_400(client: TestClient):
    """T-I-13-04: Propiedad sin datos fiscales retorna 400."""
    res = client.post(
        "/api/properties",
        json={
            "name": "Piso Sin Fiscalidad",
            "address": {"street": "Calle B", "city": "Madrid", "postal_code": "28002", "country": "ES"},
            "property_type": "apartment",
        },
    )
    prop_id = res.json()["id"]

    res = client.get(f"/api/properties/{prop_id}/fiscal-report/pdf?year=2026")
    assert res.status_code == 400
    assert "datos fiscales" in res.json()["detail"].lower()


def test_ti_13_05_wrong_user_returns_404(client: TestClient):
    """T-I-13-05: Propiedad de otro usuario retorna 404."""
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

    try:
        res = client.get(f"/api/properties/{prop_id}/fiscal-report/pdf?year=2026")
        assert res.status_code == 404
    finally:
        auth_user = User(
            email=Email("test@example.com"),
            password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
            username="testuser",
            id="user-1",
        )
        app.dependency_overrides[get_current_user] = lambda: auth_user


def test_ti_13_06_no_auth_returns_401(client: TestClient):
    """T-I-13-06: Sin token de autenticación retorna 401."""
    from backend.api.main import app
    from backend.api.dependencies import get_current_user

    original_override = app.dependency_overrides.pop(get_current_user, None)
    try:
        res = client.get("/api/properties/some-prop-id/fiscal-report/pdf?year=2026")
        assert res.status_code == 401
    finally:
        if original_override:
            app.dependency_overrides[get_current_user] = original_override
