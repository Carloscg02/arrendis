"""
Tests para F-20: API de Subida de Facturas de Suministros, Deduplicación y Borrado.

Verifica:
- API-F20-01: POST /api/expenses/upload-invoice (201 Created, is_verified=True)
- API-F20-02: POST /api/expenses/upload-invoice duplicada (409 Conflict)
- API-F20-03: POST /api/expenses/upload-invoice CUPS no registrado (422 Unprocessable Entity)
- API-F20-04: POST /api/expenses/upload-invoices por lote (200 OK con desglose)
- API-F20-05: DELETE /api/expenses/{id} (204 No Content y 404)
- API-F20-06: Computación directa de facturas subidas en profit report
"""

from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

SAMPLE_PDF_PATH = Path("specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf")
REPSOL_CUPS = "ES0031103721971011PR0F"


def _create_property_with_cups(client: TestClient, cups: str = REPSOL_CUPS) -> str:
    """Helper para crear una propiedad con el CUPS indicado."""
    response = client.post("/api/properties", json={
        "name": "Piso Frank Capra",
        "address": {
            "street": "Calle Frank Capra 4",
            "city": "Málaga",
            "postal_code": "29010",
            "country": "ES",
        },
        "property_type": "apartment",
    })
    prop_id = response.json()["id"]

    # Asignar CUPS
    cups_res = client.put(f"/api/properties/{prop_id}/cups", json={
        "cups_electricity": cups,
    })
    assert cups_res.status_code == 200
    return prop_id


def test_api_f20_01_upload_single_invoice_success(client: TestClient):
    """API-F20-01: POST /api/expenses/upload-invoice procesa PDF válido y crea gasto verificado."""
    prop_id = _create_property_with_cups(client)
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()

    response = client.post(
        "/api/expenses/upload-invoice",
        files={"file": ("factura_repsol.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == prop_id
    assert Decimal(str(data["amount"])) == Decimal("75.46")
    assert data["currency"] == "EUR"
    assert data["is_verified"] is True
    assert data["source"] == "auto_import"
    assert data["category"] == "utility"
    assert data["fiscal_category"] == "servicios_suministros"
    assert data["utility_data"] is not None
    assert data["utility_data"]["cups"] == REPSOL_CUPS
    assert data["utility_data"]["invoice_number"] == "61088387754"
    assert data["utility_data"]["extraction_confidence"] == "high"


def test_api_f20_02_upload_single_invoice_duplicate_returns_409(client: TestClient):
    """API-F20-02: Subir dos veces la misma factura devuelve 409 Conflict."""
    _create_property_with_cups(client)
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()

    # 1. Primera subida (éxito)
    res1 = client.post(
        "/api/expenses/upload-invoice",
        files={"file": ("factura_repsol.pdf", pdf_bytes, "application/pdf")},
    )
    assert res1.status_code == 201

    # 2. Segunda subida (duplicado)
    res2 = client.post(
        "/api/expenses/upload-invoice",
        files={"file": ("factura_repsol_copia.pdf", pdf_bytes, "application/pdf")},
    )
    assert res2.status_code == 409
    assert "ya fue importada previamente" in res2.json()["detail"]


def test_api_f20_03_upload_single_invoice_unmatched_cups_returns_422(client: TestClient):
    """API-F20-03: Factura con CUPS no asignado a propiedades del usuario devuelve 422."""
    # Creamos propiedad con un CUPS distinto
    _create_property_with_cups(client, cups="ES0000000000000000PR0F")
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()

    response = client.post(
        "/api/expenses/upload-invoice",
        files={"file": ("factura_repsol.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422
    assert "No se encontró ningún inmueble" in response.json()["detail"]


def test_api_f20_04_upload_batch_invoices(client: TestClient):
    """API-F20-04: POST /api/expenses/upload-invoices procesa múltiples archivos devolviendo resumen."""
    _create_property_with_cups(client)
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()

    # Enviamos 3 archivos:
    # 1. Factura real (éxito)
    # 2. Misma factura (duplicado)
    # 3. Archivo corrupto (error)
    files = [
        ("files", ("factura_1.pdf", pdf_bytes, "application/pdf")),
        ("files", ("factura_1_dup.pdf", pdf_bytes, "application/pdf")),
        ("files", ("corrupt.pdf", b"corrupted data", "application/pdf")),
    ]

    response = client.post("/api/expenses/upload-invoices", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["total_processed"] == 3
    assert data["successful_count"] == 1
    assert data["duplicate_count"] == 1
    assert data["error_count"] == 1
    assert Decimal(str(data["total_amount_imported"])) == Decimal("75.46")

    # Item 1: success
    assert data["items"][0]["filename"] == "factura_1.pdf"
    assert data["items"][0]["status"] == "success"
    assert data["items"][0]["expense"]["is_verified"] is True
    assert data["items"][0]["property_name"] == "Piso Frank Capra"

    # Item 2: duplicate
    assert data["items"][1]["filename"] == "factura_1_dup.pdf"
    assert data["items"][1]["status"] == "duplicate"
    assert "ya fue importada" in data["items"][1]["message"]

    # Item 3: error
    assert data["items"][2]["filename"] == "corrupt.pdf"
    assert data["items"][2]["status"] == "error"


def test_api_f20_05_delete_expense(client: TestClient):
    """API-F20-05: DELETE /api/expenses/{id} elimina el gasto y devuelve 204."""
    prop_id = _create_property_with_cups(client)
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()

    # Subir gasto
    res_upload = client.post(
        "/api/expenses/upload-invoice",
        files={"file": ("factura.pdf", pdf_bytes, "application/pdf")},
    )
    expense_id = res_upload.json()["id"]

    # Verificar que existe
    res_list = client.get(f"/api/properties/{prop_id}/expenses")
    assert len(res_list.json()) == 1

    # Eliminar
    res_del = client.delete(f"/api/expenses/{expense_id}")
    assert res_del.status_code == 204

    # Verificar que ya no está
    res_list_after = client.get(f"/api/properties/{prop_id}/expenses")
    assert len(res_list_after.json()) == 0

    # Eliminar de nuevo devuelve 404
    res_del_again = client.delete(f"/api/expenses/{expense_id}")
    assert res_del_again.status_code == 404


def test_api_f20_06_direct_accounting_computes_in_profit_report(client: TestClient):
    """API-F20-06: Factura auto-importada (is_verified=True) se refleja inmediatamente en el beneficio neto."""
    prop_id = _create_property_with_cups(client)

    # 1. Registrar un ingreso de 1000 €
    client.post("/api/incomes", json={
        "property_id": prop_id,
        "amount": 1000.00,
        "date": "2026-08-01",
        "category": "rent",
    })

    # Beneficio inicial = 1000 €
    profit_res = client.get(f"/api/properties/{prop_id}/profit")
    assert profit_res.status_code == 200
    assert Decimal(str(profit_res.json()["net_profit"])) == Decimal("1000")

    # 2. Subir factura de 75.46 €
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()
    upload_res = client.post(
        "/api/expenses/upload-invoice",
        files={"file": ("factura_repsol.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201

    # 3. Beneficio neto actualizado inmediatamente: 1000 - 75.46 = 924.54 €
    profit_res_after = client.get(f"/api/properties/{prop_id}/profit")
    assert profit_res_after.status_code == 200
    assert Decimal(str(profit_res_after.json()["net_profit"])) == Decimal("924.54")
