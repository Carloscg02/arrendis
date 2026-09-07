"""
Tests para la API de Ingesta por Email y Webhooks (F-21).

Verifica:
- T-F21-API-01: POST /api/webhooks/inbound-email sin secret o con secret erróneo -> 401 Unauthorized.
- T-F21-API-02: POST /api/webhooks/inbound-email con remitente autorizado -> 200 OK y gasto creado.
- T-F21-API-03: POST /api/webhooks/inbound-email con remitente no registrado -> 200 OK (status: 'unauthorized_sender').
- T-F21-API-04: POST /api/webhooks/inbound-email con CUPS ajeno -> 200 OK (item status: 'cups_not_owned').
- T-F21-API-05: GET y PUT /api/auth/forwarding-email para consultar y actualizar email alternativo.
"""

from pathlib import Path
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.dependencies import get_current_user

SAMPLE_PDF_PATH = Path("specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf")
REPSOL_CUPS = "ES0031103721971011PR0F"
WEBHOOK_SECRET = "dev-inbound-secret"


@pytest.fixture(autouse=True)
def unmock_auth(client):
    app.dependency_overrides.pop(get_current_user, None)
    yield


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    return SAMPLE_PDF_PATH.read_bytes()


def _register_and_create_property(client: TestClient, email="carlos@example.com", cups=REPSOL_CUPS) -> tuple[str, str, str]:
    """Registra un usuario, crea una propiedad y le asigna el CUPS indicado."""
    # 1. Registrar
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "username": "carlos",
        "password": "Password123!",
    })
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Crear propiedad
    prop_res = client.post("/api/properties", json={
        "name": "Piso Gran Vía",
        "address": {
            "street": "Gran Vía 10",
            "city": "Madrid",
            "postal_code": "28013",
            "country": "ES",
        },
        "property_type": "apartment",
    }, headers=headers)
    prop_id = prop_res.json()["id"]

    # 3. Asignar CUPS
    client.put(f"/api/properties/{prop_id}/cups", json={
        "cups_electricity": cups,
    }, headers=headers)

    return token, user_id, prop_id


def test_t_f21_api_01_webhook_secret_validation(client: TestClient, sample_pdf_bytes):
    """T-F21-API-01: Rechazar llamadas sin secret o con secret erróneo con 401."""
    # Sin cabecera
    res_no_secret = client.post(
        "/api/webhooks/inbound-email",
        data={"from": "carlos@example.com"},
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert res_no_secret.status_code == 401

    # Con secret incorrecto
    res_bad_secret = client.post(
        "/api/webhooks/inbound-email",
        data={"from": "carlos@example.com"},
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": "clave-erronea"},
    )
    assert res_bad_secret.status_code == 401


def test_t_f21_api_02_webhook_authorized_sender(client: TestClient, sample_pdf_bytes):
    """T-F21-API-02: Remitente autorizado procesa factura vía Webhook."""
    token, user_id, prop_id = _register_and_create_property(client, email="carlos@example.com")

    response = client.post(
        "/api/webhooks/inbound-email",
        data={
            "from": "Carlos Cano <carlos@example.com>",
            "to": "facturas@rental-handler.com",
            "subject": "Factura luz Repsol",
        },
        files={"files": ("factura_repsol.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": WEBHOOK_SECRET},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sender"] == "carlos@example.com"
    assert data["processed_count"] == 1
    assert data["duplicate_count"] == 0
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["status"] == "success"
    assert item["cups"] == REPSOL_CUPS
    assert Decimal(str(item["amount"])) == Decimal("75.46")
    assert item["property_name"] == "Piso Gran Vía"


def test_t_f21_api_03_webhook_unauthorized_sender(client: TestClient, sample_pdf_bytes):
    """T-F21-API-03: Remitente desconocido devuelve 200 con status 'unauthorized_sender'."""
    response = client.post(
        "/api/webhooks/inbound-email",
        data={
            "from": "desconocido@ajeno.com",
            "to": "facturas@rental-handler.com",
            "subject": "Factura",
        },
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": WEBHOOK_SECRET},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unauthorized_sender"
    assert data["processed_count"] == 0
    assert len(data["items"]) == 0
    assert "no está registrado ni autorizado" in data["message"]


def test_t_f21_api_04_webhook_cups_not_owned(client: TestClient, sample_pdf_bytes):
    """T-F21-API-04: Remitente registrado envía factura cuyo CUPS no pertenece a sus propiedades."""
    token, user_id, prop_id = _register_and_create_property(
        client,
        email="otro@example.com",
        cups="ES1111111111111111XX0F",  # CUPS diferente al del PDF
    )

    response = client.post(
        "/api/webhooks/inbound-email",
        data={
            "from": "otro@example.com",
            "to": "facturas@rental-handler.com",
            "subject": "Factura ajena",
        },
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": WEBHOOK_SECRET},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["processed_count"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "cups_not_owned"
    assert data["items"][0]["cups"] == REPSOL_CUPS


def test_t_f21_api_05_get_and_update_forwarding_email(client: TestClient):
    """T-F21-API-05: Gestión de email de reenvío alternativo desde /api/auth/forwarding-email."""
    # 1. Registrar usuario
    reg_res = client.post("/api/auth/register", json={
        "email": "inversor@holding.com",
        "username": "inversor",
        "password": "Password123!",
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Consultar valor por defecto
    get_res = client.get("/api/auth/forwarding-email", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["forwarding_email"] is None
    assert "inbound_address" in get_res.json()

    # 3. Actualizar con email de facturas alternativo
    put_res = client.put(
        "/api/auth/forwarding-email",
        json={"forwarding_email": "facturas.personales@gmail.com"},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["forwarding_email"] == "facturas.personales@gmail.com"

    # 4. Verificar consulta posterior
    get_res2 = client.get("/api/auth/forwarding-email", headers=headers)
    assert get_res2.status_code == 200
    assert get_res2.json()["forwarding_email"] == "facturas.personales@gmail.com"

    # 5. Validación sintaxis incorrecta devuelve 400
    bad_res = client.put(
        "/api/auth/forwarding-email",
        json={"forwarding_email": "correo_no_valido"},
        headers=headers,
    )
    assert bad_res.status_code == 400


def test_t_f21_api_06_webhook_duplicate_detection(client: TestClient, sample_pdf_bytes):
    """T-F21-API-06: El Webhook detecta facturas ya importadas y retorna duplicate sin error de sistema (Idempotencia)."""
    token, user_id, prop_id = _register_and_create_property(client, email="carlos.cano@example.com")

    # Envío inicial: Éxito
    res1 = client.post(
        "/api/webhooks/inbound-email",
        data={"from": "carlos.cano@example.com", "to": "facturas@rental-handler.com", "subject": "Factura 1"},
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": WEBHOOK_SECRET},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"
    assert res1.json()["processed_count"] == 1

    # Reenvío de la misma factura: Duplicado detectado
    res2 = client.post(
        "/api/webhooks/inbound-email",
        data={"from": "carlos.cano@example.com", "to": "facturas@rental-handler.com", "subject": "Factura 1 reenviada"},
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": WEBHOOK_SECRET},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "success"
    assert data2["processed_count"] == 0
    assert data2["duplicate_count"] == 1
    assert data2["items"][0]["status"] == "duplicate"
    assert "ya fue importada previamente" in data2["items"][0]["message"]


def test_t_f21_api_07_webhook_authorized_by_forwarding_email(client: TestClient, sample_pdf_bytes):
    """T-F21-API-07: El Webhook acepta correos enviados desde el email alternativo configurado por el usuario."""
    token, user_id, prop_id = _register_and_create_property(client, email="login.account@empresa.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Configurar email alternativo de facturas
    client.put(
        "/api/auth/forwarding-email",
        json={"forwarding_email": "facturas.personales@gmail.com"},
        headers=headers,
    )

    # El correo al webhook llega desde el email alternativo
    response = client.post(
        "/api/webhooks/inbound-email",
        data={
            "from": "Carlos Personal <facturas.personales@gmail.com>",
            "to": "facturas@rental-handler.com",
            "subject": "Reenvío automático desde Gmail",
        },
        files={"files": ("factura.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"X-Webhook-Secret": WEBHOOK_SECRET},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sender"] == "facturas.personales@gmail.com"
    assert data["processed_count"] == 1
    assert data["items"][0]["status"] == "success"
    assert data["items"][0]["cups"] == REPSOL_CUPS
