"""
Router de Expenses — endpoints para registrar y listar gastos.

Traduce peticiones HTTP a llamadas del caso de uso RecordExpenseUseCase
y formatea las respuestas como ExpenseResponse.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLitePropertyRepository,
)
from backend.api.dependencies import get_expense_repo, get_property_repo
from backend.api.schemas import ExpenseCreate, ExpenseResponse
from backend.application.use_cases import RecordExpenseUseCase
from backend.domain.entities import Expense

router = APIRouter(prefix="/api", tags=["expenses"])


def _entity_to_response(expense: Expense) -> ExpenseResponse:
    """Convierte una entidad Expense del dominio a un schema de respuesta."""
    return ExpenseResponse(
        id=expense.id,
        property_id=expense.property_id,
        amount=expense.amount.amount,
        currency=expense.amount.currency,
        date=expense.date,
        category=expense.category.value,
        description=expense.description,
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def record_expense(
    body: ExpenseCreate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
) -> ExpenseResponse:
    """Registra un nuevo gasto vinculado a una propiedad."""
    try:
        use_case = RecordExpenseUseCase(property_repo, expense_repo)
        expense = use_case.execute(
            property_id=body.property_id,
            amount=body.amount,
            expense_date=body.date,
            category=body.category,
            description=body.description,
        )
        return _entity_to_response(expense)
    except ValueError as e:
        # Distinguir entre propiedad no encontrada y otros errores de validación
        if "No existe la propiedad" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/properties/{property_id}/expenses",
    response_model=list[ExpenseResponse],
)
def list_expenses(
    property_id: str,
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
) -> list[ExpenseResponse]:
    """Lista todos los gastos de una propiedad."""
    expenses = expense_repo.find_by_property_id(property_id)
    return [_entity_to_response(e) for e in expenses]
