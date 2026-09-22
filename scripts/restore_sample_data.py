#!/usr/bin/env python3
"""
Script de restauración de datos locales para Arrendis.
Restaura 'Piso Gran Vía' con su histórico completo de ingresos, gastos, contrato y datos fiscales.
"""

import sqlite3
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "rental.db"

PROP_ID = "796adc13-d7e5-414e-bd8d-6944b47ecbd9"
USER_ID = "053eb0c7-f8dd-4ba7-988b-6377649fc48d"  # CarlosCanoAdmin


def restore_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Insert or Replace Piso Gran Vía
    cur.execute(
        """
        INSERT OR REPLACE INTO properties (
            id, name, street, city, postal_code, country,
            property_type, status, image_filename, user_id,
            cadastral_ref, cadastral_land_value, cadastral_construction_value,
            acquisition_purchase_price, acquisition_construction_portion, acquisition_land_portion,
            acquisition_transfer_tax, acquisition_notary_fees, acquisition_registry_fees,
            acquisition_date, cups_electricity, cups_gas, cups_water
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            PROP_ID,
            "Piso Gran Vía",
            "Calle Gran Vía 42",
            "Madrid",
            "28013",
            "ES",
            "apartment",
            "available",
            f"{PROP_ID}.jpg",
            USER_ID,
            "2801301VK4720A0001AZ",
            "50000.00",
            "75000.00",
            "250000.00",
            "100000.00",
            "150000.00",
            "15000.00",
            "1200.00",
            "800.00",
            "2021-03-15",
            "ES0031103721971011PR0F",
            None,
            None,
        ),
    )

    # 2. Contrato de arrendamiento
    cur.execute("DELETE FROM lease_contracts WHERE property_id = ?", (PROP_ID,))
    cur.execute(
        """
        INSERT INTO lease_contracts (
            id, property_id, tenant_name, tenant_nif,
            start_date, end_date, monthly_rent_amount, monthly_rent_currency, lease_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "92ea7ac4-b6b8-40d6-837d-bb8a080d06e0",
            PROP_ID,
            "Elena Gómez Ruiz",
            "48123456K",
            "2024-02-01",
            "2026-12-31",
            "1250.00",
            "EUR",
            "vivienda_habitual",
        ),
    )

    # 3. Ingresos (2025 y 2026: 24 mensualidades de 1.250 €)
    cur.execute("DELETE FROM incomes WHERE property_id = ?", (PROP_ID,))
    for y in [2025, 2026]:
        for m in range(1, 13):
            cur.execute(
                """
                INSERT INTO incomes (id, property_id, amount, currency, date, category, description, fiscal_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(uuid.uuid4()),
                    PROP_ID,
                    "1250.00",
                    "EUR",
                    f"{y}-{m:02d}-05",
                    "rent",
                    f"Alquiler mensual {m}/{y}",
                    "rendimiento_integro",
                ),
            )

    # 4. Gastos (2024, 2025 y 2026: 15 gastos)
    cur.execute("DELETE FROM expenses WHERE property_id = ?", (PROP_ID,))
    expenses = [
        # 2024 Muebles
        ("2500.00", "2024-06-15", "other", "Sofá chaiselongue y frigorífico combi Bosch (Bienes Muebles)", "amortizacion_muebles", 1, "manual", None, None, None, None, None, None, None),
        # 2025 Gastos
        ("800.00", "2025-05-15", "tax", "IBI anual 2025 y Tasa de basuras", "tributos", 1, "manual", None, None, None, None, None, None, None),
        ("450.00", "2025-01-20", "insurance", "Seguro multirriesgo hogar e impago", "primas_seguros", 1, "manual", None, None, None, None, None, None, None),
        ("1020.00", "2025-06-30", "community_fee", "Cuotas de comunidad 2025 (12x85€)", "servicios_suministros", 1, "manual", None, None, None, None, None, None, None),
        ("840.00", "2025-11-10", "utility", "Suministros de agua, luz y gas anuales", "servicios_suministros", 1, "manual", None, None, None, None, None, None, None),
        ("1800.00", "2025-12-01", "mortgage", "Intereses hipotecarios Banco Santander 2025", "intereses_capital", 1, "manual", None, None, None, None, None, None, None),
        ("1200.00", "2025-04-10", "repair", "Pintura completa y reparación de tuberías", "reparacion_conservacion", 1, "manual", None, None, None, None, None, None, None),
        ("350.00", "2025-02-05", "other", "Gestoría y redactado contrato arrendamiento", "formalizacion", 1, "manual", None, None, None, None, None, None, None),
        # 2026 Gastos
        ("820.00", "2026-05-15", "tax", "IBI anual 2026 y Tasa de basuras", "tributos", 1, "manual", None, None, None, None, None, None, None),
        ("470.00", "2026-01-20", "insurance", "Seguro multirriesgo hogar e impago 2026", "primas_seguros", 1, "manual", None, None, None, None, None, None, None),
        ("1020.00", "2026-06-30", "community_fee", "Cuotas de comunidad 2026 (12x85€)", "servicios_suministros", 1, "manual", None, None, None, None, None, None, None),
        ("860.00", "2026-11-10", "utility", "Suministros de agua, luz y gas 2026", "servicios_suministros", 1, "manual", None, None, None, None, None, None, None),
        ("1650.00", "2026-12-01", "mortgage", "Intereses hipotecarios Banco Santander 2026", "intereses_capital", 1, "manual", None, None, None, None, None, None, None),
        ("900.00", "2026-04-10", "repair", "Mantenimiento de caldera y fontanería", "reparacion_conservacion", 1, "manual", None, None, None, None, None, None, None),
        ("75.46", "2026-08-01", "utility", "Factura Repsol Comercializadora de Electricidad y Gas, S.L.U. - 61088387754", "servicios_suministros", 1, "auto_import", "ES0031103721971011PR0F", "75.46", "2026-08-01", "Repsol Comercializadora de Electricidad y Gas, S.L.U.", "electricity", "61088387754", "high"),
    ]

    for amt, dt, cat, desc, fcat, ver, src, cups, u_amt, u_date, u_prov, u_type, u_inv, u_conf in expenses:
        cur.execute(
            """
            INSERT INTO expenses (
                id, property_id, amount, currency, date, category, description, fiscal_category,
                is_verified, source, utility_cups, utility_amount, utility_issue_date,
                utility_provider_name, utility_type, utility_invoice_number, utility_extraction_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                PROP_ID,
                amt,
                "EUR",
                dt,
                cat,
                desc,
                fcat,
                ver,
                src,
                cups,
                u_amt,
                u_date,
                u_prov,
                u_type,
                u_inv,
                u_conf,
            ),
        )

    # 5. Fiscal Carryforwards (2024)
    cur.execute("DELETE FROM fiscal_carryforwards WHERE property_id = ?", (PROP_ID,))
    cur.execute(
        """
        INSERT INTO fiscal_carryforwards (id, property_id, year_generated, original_amount, amount_applied)
        VALUES (?, ?, ?, ?, ?)
    """,
        (str(uuid.uuid4()), PROP_ID, 2024, "400.00", "0.00"),
    )

    # 6. Reinsertar también las otras 3 propiedades si no existen
    other_props = [
        ("ce1d97c4-dd65-4bae-9001-a1a292619492", "piso 2", "22", "22", "22", "ES", "apartment", "available"),
        ("92f4a2e5-e1e8-48ab-ac08-0cd8aacf4716", "Piso de antonio", "Calle Mayor 1", "Madrid", "28001", "ES", "apartment", "available"),
        ("d5fd1d38-0a41-41b5-a639-8d31367e7f41", "fsaaf", "Calle Test 5", "Madrid", "28002", "ES", "apartment", "available"),
    ]
    for pid, pname, st, ct, pc, cntry, pt, stts in other_props:
        cur.execute(
            """
            INSERT OR IGNORE INTO properties (id, name, street, city, postal_code, country, property_type, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (pid, pname, st, ct, pc, cntry, pt, stts, USER_ID),
        )

    conn.commit()
    conn.close()
    print("✅ Restauración completada con éxito.")
    print("  • Piso Gran Vía restaurado (24 ingresos, 15 gastos, contrato y datos fiscales)")
    print("  • piso 2, Piso de antonio y fsaaf restaurados")


if __name__ == "__main__":
    restore_data()
