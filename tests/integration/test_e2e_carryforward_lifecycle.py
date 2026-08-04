"""
Test de Integración E2E — Ciclo Multianual de Remanentes de Gastos (Casilla [0103]).

Este test simula la generación de un exceso de gastos de reparación en el Año N
y su posterior aplicación y deducción automática en la liquidación del Año N+1.
"""

from decimal import Decimal

def test_e2e_carryforward_multiyear_cycle(e2e_client):
    client = e2e_client

    # 1. Registro e inicio de sesión
    reg_res = client.post("/api/auth/register", json={
        "email": "propietario.excesos@example.com",
        "username": "propietario_excesos",
        "password": "PasswordSegura123!"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Alta de Propiedad
    prop_res = client.post("/api/properties", headers=headers, json={
        "name": "Piso Rambla Barcelona",
        "address": {"street": "La Rambla 50", "city": "Barcelona", "postal_code": "08002", "country": "ES"},
        "property_type": "apartment",
        "status": "available"
    })
    prop_id = prop_res.json()["id"]

    # Datos fiscales mínimos
    client.put(f"/api/properties/{prop_id}/fiscal-data", headers=headers, json={
        "cadastral_ref": "0800201VK4720A0001AZ",
        "cadastral_breakdown": {
            "land_value": 40000.0,
            "construction_value": 60000.0
        },
        "acquisition_cost": {
            "purchase_price": 150000.0,
            "construction_portion": 90000.0,
            "land_portion": 60000.0,
            "transfer_tax": 15000.0,
            "notary_fees": 1000.0,
            "registry_fees": 500.0
        },
        "acquisition_date": "2020-01-15"
    })

    # Contrato activo en 2024 y 2025
    client.post(f"/api/properties/{prop_id}/contracts", headers=headers, json={
        "tenant_name": "Marc Vila",
        "tenant_nif": "47123456K",
        "start_date": "2023-01-01",
        "end_date": "2026-12-31",
        "monthly_rent": 1000.0,
        "lease_type": "vivienda_habitual"
    })

    # 3. AÑO 2024: Ingresos reducidos (3.000 €) y gran reparación (10.000 €)
    client.post("/api/incomes", headers=headers, json={
        "property_id": prop_id, "amount": 3000.0, "date": "2024-03-01", "category": "rent", "fiscal_category": "rendimiento_integro"
    })

    # Gasto de reparación elevado (10.000 €)
    client.post("/api/expenses", headers=headers, json={
        "property_id": prop_id, "amount": 10000.0, "date": "2024-04-15", "category": "repair", "description": "Reforma cocina", "fiscal_category": "reparacion_conservacion"
    })

    # Reporte 2024
    report_2024_res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2024", headers=headers)
    assert report_2024_res.status_code == 200
    report_2024 = report_2024_res.json()

    assert Decimal(str(report_2024["expenses_reparacion"])) == Decimal("10000")
    # Total Deducible en 2024 limita las reparaciones a 3.000 € (tope de ingresos) + amortización edificación (2.997 €) = 5.997 €
    assert Decimal(str(report_2024["total_deductible_expenses"])) == Decimal("5997")

    # Guardar el exceso generado en 2024 en la tabla de carryforwards
    from backend.api.main import app
    from backend.api.dependencies import get_db
    from backend.adapters.sqlite_adapter import SQLiteFiscalCarryforwardRepository
    from backend.domain.entities import FiscalCarryforward
    from backend.domain.value_objects import Money

    test_db = app.dependency_overrides[get_db]()
    cf_repo = SQLiteFiscalCarryforwardRepository(test_db)
    cf_repo.save(FiscalCarryforward(
        property_id=prop_id,
        year_generated=2024,
        original_amount=Decimal("7000"),
        amount_applied=Decimal("0")
    ))

    # 4. AÑO 2025: Ingresos normales (12.000 €) sin nuevas reparaciones
    for m in range(1, 13):
        client.post("/api/incomes", headers=headers, json={
            "property_id": prop_id, "amount": 1000.0, "date": f"2025-{m:02d}-05", "category": "rent", "fiscal_category": "rendimiento_integro"
        })

    # Reporte 2025: El sistema debe recuperar el exceso de 2024 (7.000 €) en Casilla [0103] y aplicarlo en 2025
    report_2025_res = client.get(f"/api/properties/{prop_id}/fiscal-report?year=2025", headers=headers)
    assert report_2025_res.status_code == 200
    report_2025 = report_2025_res.json()

    assert Decimal(str(report_2025["total_income"])) == Decimal("12000")
    assert Decimal(str(report_2025["prior_excess_available"])) == Decimal("7000")
    assert Decimal(str(report_2025["prior_excess_applied"])) == Decimal("7000")
