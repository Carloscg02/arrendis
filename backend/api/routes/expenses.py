"""
Router de Expenses — endpoints para registrar y listar gastos.

Traduce peticiones HTTP a llamadas del caso de uso RecordExpenseUseCase
y formatea las respuestas como ExpenseResponse.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
)
from backend.api.dependencies import get_expense_repo, get_income_repo, get_property_repo, get_current_user
from backend.api.schemas import ExpenseCreate, ExpenseResponse
from backend.application.use_cases import RecordExpenseUseCase, GetPropertyUseCase, UpdateFiscalCategoryUseCase
from backend.domain.entities import Expense, User

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
        fiscal_category=expense.fiscal_category.value if expense.fiscal_category else None,
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def record_expense(
    body: ExpenseCreate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Registra un nuevo gasto vinculado a una propiedad."""
    try:
        use_case = RecordExpenseUseCase(property_repo, expense_repo)
        expense = use_case.execute(
            user_id=current_user.id,
            property_id=body.property_id,
            amount=body.amount,
            expense_date=body.date,
            category=body.category,
            description=body.description,
            fiscal_category=body.fiscal_category,
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
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseResponse]:
    """Lista todos los gastos de una propiedad."""
    try:
        GetPropertyUseCase(property_repo).execute(property_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"No existe la propiedad con id '{property_id}'.")
        
    expenses = expense_repo.find_by_property_id(property_id)
    return [_entity_to_response(e) for e in expenses]


@router.patch("/expenses/{expense_id}/fiscal-category", response_model=ExpenseResponse)
def update_fiscal_category(
    expense_id: str,
    body: __import__('backend.api.schemas', fromlist=['FiscalCategoryUpdate']).FiscalCategoryUpdate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    try:
        use_case = UpdateFiscalCategoryUseCase(property_repo, income_repo, expense_repo)
        expense = use_case.execute(
            user_id=current_user.id,
            record_id=expense_id,
            record_type="expense",
            fiscal_category=body.fiscal_category,
        )
        return _entity_to_response(expense)
    except ValueError as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
