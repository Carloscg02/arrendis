"""
Test de integración: Pipeline completo de procesamiento de facturas con base de datos SQLite (IT-F18-02).

Prueba el flujo extremo a extremo:
1. Inmueble persistido en SQLite con CUPS asignado.
2. Ingesta del PDF real de Repsol mediante ProcessUtilityInvoiceUseCase.
3. Extracción vía PyMuPDF + RepsolExtractionStrategy.
4. Matching unívoco con la propiedad por CUPS.
5. Persistencia del Expense en SQLite con is_verified = False y utility_data serializado.
6. Recuperación desde el repositorio y verificación de la integridad del gasto.
7. Aislamiento multi-tenancy.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from backend.adapters.pdf_extractor_adapter import PyMuPDFTextExtractorAdapter
from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLitePropertyRepository,
)
from backend.application.use_cases import ProcessUtilityInvoiceUseCase
from backend.domain.entities import (
    Address,
    ExpenseCategory,
    ExpenseSource,
    ExtractionConfidence,
    FiscalExpenseCategory,
    Property,
    PropertyNotFoundForCUPSError,
    PropertyStatus,
    PropertyType,
    UtilityType,
)
from backend.domain.extraction import (
    RepsolExtractionStrategy,
    UtilityExtractorRegistry,
)


def test_process_utility_invoice_full_lifecycle_sqlite(sqlite_connection):
    """IT-F18-02: Pipeline completo de procesamiento y persistencia con SQLite."""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    expense_repo = SQLiteExpenseRepository(sqlite_connection)

    # 1. Crear e insertar propiedad para el usuario "user_propietario"
    # con el CUPS que contiene la factura real de Repsol
    prop = Property(
        name="Piso Frank Capra",
        address=Address("CL Frank Capra 4", "Málaga", "29010", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id="user_propietario",
        status=PropertyStatus.AVAILABLE,
        cups_electricity="ES0031103721971011PR0F",
    )
    prop_repo.save(prop)

    # 2. Configurar el caso de uso
    pdf_extractor = PyMuPDFTextExtractorAdapter()
    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    use_case = ProcessUtilityInvoiceUseCase(
        pdf_extractor=pdf_extractor,
        registry=registry,
        property_repo=prop_repo,
        expense_repo=expense_repo,
        fallback_strategy=None,
    )

    # 3. Cargar el PDF de muestra real
    pdf_path = Path("specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf")
    assert pdf_path.exists()
    pdf_bytes = pdf_path.read_bytes()

    # 4. Ejecutar el caso de uso para el usuario propietario
    result = use_case.execute(pdf_bytes=pdf_bytes, user_id="user_propietario")

    assert result.strategy_used == "Repsol"
    assert result.property.id == prop.id
    assert result.expense.is_verified is True
    assert result.expense.source == ExpenseSource.AUTO_IMPORT
    assert result.expense.amount.amount == Decimal("75.46")

    # 5. Consultar SQLite directamente mediante el repositorio de gastos
    saved_expenses = expense_repo.find_by_property_id(prop.id)
    assert len(saved_expenses) == 1

    db_expense = saved_expenses[0]
    assert db_expense.id == result.expense.id
    assert db_expense.property_id == prop.id
    assert db_expense.amount.amount == Decimal("75.46")
    assert db_expense.date == date(2026, 8, 1)
    assert db_expense.category == ExpenseCategory.UTILITY
    assert db_expense.fiscal_category == FiscalExpenseCategory.SERVICIOS_SUMINISTROS
    assert db_expense.is_verified is True
    assert db_expense.source == ExpenseSource.AUTO_IMPORT

    # Verificar que el Value Object UtilityInvoiceData se deserializó íntegro
    assert db_expense.utility_data is not None
    assert db_expense.utility_data.cups == "ES0031103721971011PR0F"
    assert db_expense.utility_data.amount == Decimal("75.46")
    assert db_expense.utility_data.issue_date == date(2026, 8, 1)
    assert db_expense.utility_data.invoice_number == "61088387754"
    assert db_expense.utility_data.utility_type == UtilityType.ELECTRICITY
    assert db_expense.utility_data.extraction_confidence == ExtractionConfidence.HIGH

    # 6. Verificar aislamiento multi-tenant: otro usuario no puede vincular esta factura
    with pytest.raises(PropertyNotFoundForCUPSError) as exc_info:
        use_case.execute(pdf_bytes=pdf_bytes, user_id="otro_usuario_distinto")

    assert exc_info.value.cups == "ES0031103721971011PR0F"
