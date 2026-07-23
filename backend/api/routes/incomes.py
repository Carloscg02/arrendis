"""
Router de Incomes — endpoints para registrar y listar ingresos.

Incluye también el endpoint de Profit Report (GET /properties/{id}/profit),
ya que es una vista de lectura vinculada a una propiedad específica.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
)
from backend.api.dependencies import (
    get_expense_repo,
    get_income_repo,
    get_property_repo,
)
from backend.api.schemas import IncomeCreate, IncomeResponse, ProfitReportResponse
from backend.application.use_cases import (
    GetPropertyProfitReportUseCase,
    RecordIncomeUseCase,
)
from backend.domain.entities import Income

router = APIRouter(prefix="/api", tags=["incomes"])


def _entity_to_response(income: Income) -> IncomeResponse:
    """Convierte una entidad Income del dominio a un schema de respuesta."""
    return IncomeResponse(
        id=income.id,
        property_id=income.property_id,
        amount=income.amount.amount,
        currency=income.amount.currency,
        date=income.date,
        category=income.category.value,
        description=income.description,
    )


@router.post("/incomes", response_model=IncomeResponse, status_code=201)
def record_income(
    body: IncomeCreate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
) -> IncomeResponse:
    """Registra un nuevo ingreso vinculado a una propiedad."""
    try:
        use_case = RecordIncomeUseCase(property_repo, income_repo)
        income = use_case.execute(
            property_id=body.property_id,
            amount=body.amount,
            income_date=body.date,
            category=body.category,
            description=body.description,
        )
        return _entity_to_response(income)
    except ValueError as e:
        # Distinguir entre propiedad no encontrada y otros errores de validación
        if "No existe la propiedad" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/properties/{property_id}/incomes",
    response_model=list[IncomeResponse],
)
def list_incomes(
    property_id: str,
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
) -> list[IncomeResponse]:
    """Lista todos los ingresos de una propiedad."""
    incomes = income_repo.find_by_property_id(property_id)
    return [_entity_to_response(i) for i in incomes]


@router.get(
    "/properties/{property_id}/profit",
    response_model=ProfitReportResponse,
)
def get_profit_report(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
) -> ProfitReportResponse:
    """Calcula el beneficio neto de una propiedad."""
    try:
        use_case = GetPropertyProfitReportUseCase(
            property_repo, income_repo, expense_repo,
        )
        net_profit = use_case.execute(property_id)
        return ProfitReportResponse(
            property_id=property_id,
            net_profit=net_profit.amount,
            currency=net_profit.currency,
        )
    except ValueError as e:
        if "No existe la propiedad" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
