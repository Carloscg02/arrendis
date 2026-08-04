"""
Test de Integración E2E — Ciclo de Vida Fiscal Completo del Propietario.

Este test simula la jornada completa de un usuario real desde el registro hasta
la descarga del borrador fiscal oficial en PDF, haciendo llamadas acumulativas a la API.
"""

from decimal import Decimal
import io

def test_e2e_fiscal_lifecycle_complete(e2e_client):
    client = e2e_client

    # 1. Registro de usuario
    reg_res = client.post("/api/auth/register", json={
        "email": "propietario.castellana@example.com",
        "username": "propietario_castellana",
        "password": "PasswordSegura123!"
    })
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Alta de Propiedad
    prop_res = client.post("/api/properties", headers=headers, json={
        "name": "Piso Castellana 100",
        "address": {
            "street": "Paseo de la Castellana 100",
            "city": "Madrid",
            "postal_code": "28046",
            "country": "ES"
        },
        "property_type": "apartment",
        "status": "available"
    })
    assert prop_res.status_code == 201
    prop_id = prop_res.json()["id"]

    # 3. Subida de Imagen de Propiedad
    jpeg_bytes = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9])
    img_res = client.post(
        f"/api/properties/{prop_id}/image",
        headers=headers,
        files={"file": ("castellana.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert img_res.status_code == 200
    assert img_res.json()["image_url"] == f"/api/images/{prop_id}.jpg"

    # 4. Configuración de Datos Catastrales y Adquisición Fiscal
    fiscal_data_res = client.put(
        f"/api/properties/{prop_id}/fiscal-data",
        headers=headers,
        json={
            "cadastral_ref": "2804601VK4720A0001AZ",
            "cadastral_breakdown": {
                "land_value": 60000.0,
                "construction_value": 90000.0
            },
            "acquisition_cost": {
                "purchase_price": 200000.0,
                "construction_portion": 120000.0,
                "land_portion": 80000.0,
                "transfer_tax": 16000.0,
                "notary_fees": 1200.0,
                "registry_fees": 800.0
            },
            "acquisition_date": "2022-05-10"
        }
    )
    assert fiscal_data_res.status_code == 200

    # 5. Alta de Contrato de Arrendamiento (Firmado en 2024 -> Ley de Vivienda 50%)
    contract_res = client.post(
        f"/api/properties/{prop_id}/contracts",
        headers=headers,
        json={
            "tenant_name": "Laura Martínez",
            "tenant_nif": "52345678B",
            "start_date": "2024-03-01",
            "end_date": "2026-02-28",
            "monthly_rent": 1500.0,
            "lease_type": "vivienda_habitual"
        }
    )
    assert contract_res.status_code == 201

    # 6. Registro de Ingresos (12 mensualidades de 1.500 € = 18.000 € en 2025)
    for m in range(1, 13):
        inc_res = client.post("/api/incomes", headers=headers, json={
            "property_id": prop_id,
            "amount": 1500.0,
            "date": f"2025-{m:02d}-05",
            "category": "rent",
            "description": f"Alquiler mes {m}/2025",
            "fiscal_category": "rendimiento_integro"
        })
        assert inc_res.status_code == 201

    # 7. Registro de Gastos Multicategoría (2025)
    expenses_payloads = [
        {"amount": 900.0, "date": "2025-05-15", "category": "tax", "description": "IBI 2025", "fiscal_category": "tributos"},
        {"amount": 500.0, "date": "2025-01-20", "category": "insurance", "description": "Seguro hogar", "fiscal_category": "primas_seguros"},
        {"amount": 1200.0, "date": "2025-06-30", "category": "community_fee", "description": "Comunidad 2025", "fiscal_category": "servicios_suministros"},
        {"amount": 960.0, "date": "2025-11-10", "category": "utility", "description": "Suministros", "fiscal_category": "servicios_suministros"},
        {"amount": 2100.0, "date": "2025-12-01", "category": "mortgage", "description": "Intereses hipotecarios", "fiscal_category": "intereses_capital"},
        {"amount": 1400.0, "date": "2025-04-10", "category": "repair", "description": "Reparación fontanería", "fiscal_category": "reparacion_conservacion"},
        {"amount": 400.0, "date": "2025-02-05", "category": "other", "description": "Gestoría", "fiscal_category": "formalizacion"},
        {"amount": 3000.0, "date": "2024-06-15", "category": "other", "description": "Sofá y Lavavajillas", "fiscal_category": "amortizacion_muebles"},  # 10% = 300€/año
    ]

    for exp_data in expenses_payloads:
        exp_data["property_id"] = prop_id
        exp_res = client.post("/api/expenses", headers=headers, json=exp_data)
        assert exp_res.status_code == 201

    # 8. Generación del Reporte Fiscal Consolidado (Año 2025)
    report_res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025", headers=headers)
    assert report_res.status_code == 200
    report = report_res.json()

    # Verificaciones numéricas de negocio
    assert report["rented_days"] == 365
    assert Decimal(str(report["total_income"])) == Decimal("18000")
    assert Decimal(str(report["expenses_tributos"])) == Decimal("900")
    assert Decimal(str(report["expenses_seguros"])) == Decimal("500")
    assert Decimal(str(report["expenses_muebles"])) == Decimal("300")  # 10% de 3.000€
    
    # Base amortización construcción = max(120.000 + 10.800, 90.000) = 130.800 € -> 3% = 3.924 €
    assert Decimal(str(report["amortization_base"])) == Decimal("130800")
    assert Decimal(str(report["amortization_prorated"])) == Decimal("3924")
    
    # Total gastos = 900 + 500 + 1200 + 960 + 2100 + 1400 + 400 + 300 + 3924 = 11684 €
    assert Decimal(str(report["total_deductible_expenses"])) == Decimal("11684")
    
    # Rendimiento Neto previo = 18.000 - 11.684 = 6.316 €
    assert Decimal(str(report["net_income_before_reduction"])) == Decimal("6316")
    
    # Reducción Ley de Vivienda (Contrato post-2024 -> 50%) = 6.316 * 0.50 = 3.158 €
    assert Decimal(str(report["reduction_percentage"])) == Decimal("0.50")
    assert Decimal(str(report["reduction_amount"])) == Decimal("3158")
    assert Decimal(str(report["net_income_final"])) == Decimal("3158")

    # 9. Descarga y Verificación del PDF Borrador Oficial
    pdf_res = client.get(f"/api/properties/{prop_id}/fiscal-report/pdf?year=2025", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers["content-disposition"]
    assert "borrador_fiscal" in pdf_res.headers["content-disposition"]

    pdf_bytes = pdf_res.content
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
