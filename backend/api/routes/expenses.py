"""
Router de Expenses — endpoints para registrar, listar, eliminar y subir facturas de gastos.

Traduce peticiones HTTP a llamadas de casos de uso y formatea las respuestas.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
)
from backend.api.dependencies import (
    get_expense_repo,
    get_income_repo,
    get_property_repo,
    get_current_user,
    get_process_utility_invoice_use_case,
    get_process_batch_utility_invoices_use_case,
)
from backend.api.schemas import (
    BatchInvoiceUploadResponse,
    ExpenseCreate,
    ExpenseResponse,
    FiscalCategoryUpdate,
    InvoiceUploadItemResultSchema,
    UtilityInvoiceDataSchema,
)
from backend.application.use_cases import (
    GetPropertyUseCase,
    ProcessBatchUtilityInvoicesUseCase,
    ProcessUtilityInvoiceUseCase,
    RecordExpenseUseCase,
    UpdateFiscalCategoryUseCase,
)
from backend.domain.entities import (
    DuplicateInvoiceError,
    EmptyPDFTextError,
    Expense,
    ExtractionFailedError,
    PDFExtractionError,
    PropertyNotFoundForCUPSError,
    User,
)

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
        is_verified=expense.is_verified,
        source=expense.source.value,
        receipt_path=expense.receipt_path,
        utility_data=UtilityInvoiceDataSchema(
            cups=expense.utility_data.cups,
            amount=expense.utility_data.amount,
            issue_date=expense.utility_data.issue_date,
            provider_name=expense.utility_data.provider_name,
            utility_type=expense.utility_data.utility_type.value,
            invoice_number=expense.utility_data.invoice_number,
            extraction_confidence=expense.utility_data.extraction_confidence.value,
        ) if expense.utility_data else None,
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


@router.post("/expenses/upload-invoice", response_model=ExpenseResponse, status_code=201)
async def upload_single_invoice(
    file: UploadFile = File(...),
    use_case: ProcessUtilityInvoiceUseCase = Depends(get_process_utility_invoice_use_case),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Procesa una única factura PDF de suministro y registra el gasto verificado."""
    try:
        pdf_bytes = await file.read()
        result = use_case.execute(pdf_bytes, current_user.id)
        return _entity_to_response(result.expense)
    except DuplicateInvoiceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PropertyNotFoundForCUPSError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except (EmptyPDFTextError, PDFExtractionError, ExtractionFailedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/expenses/upload-invoices", response_model=BatchInvoiceUploadResponse, status_code=200)
async def upload_batch_invoices(
    files: list[UploadFile] = File(...),
    batch_use_case: ProcessBatchUtilityInvoicesUseCase = Depends(get_process_batch_utility_invoices_use_case),
    current_user: User = Depends(get_current_user),
) -> BatchInvoiceUploadResponse:
    """Procesa un lote de múltiples facturas PDF de suministros."""
    files_data: list[tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        files_data.append((f.filename or "factura.pdf", content))

    batch_result = batch_use_case.execute(files_data, current_user.id)

    response_items: list[InvoiceUploadItemResultSchema] = []
    for item in batch_result.items:
        response_items.append(
            InvoiceUploadItemResultSchema(
                filename=item.filename,
                status=item.status,
                expense=_entity_to_response(item.expense) if item.expense else None,
                property_name=item.property_name,
                message=item.message,
                cups=item.cups,
                amount=item.amount,
            )
        )

    return BatchInvoiceUploadResponse(
        total_processed=batch_result.total_processed,
        successful_count=batch_result.successful_count,
        duplicate_count=batch_result.duplicate_count,
        error_count=batch_result.error_count,
        total_amount_imported=batch_result.total_amount_imported,
        items=response_items,
    )


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Elimina un gasto perteneciente a una propiedad del usuario actual."""
    expense = expense_repo.find_by_id(expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail=f"No existe el gasto con id '{expense_id}'.")

    # Verificar que la propiedad pertenece al usuario actual
    prop = property_repo.find_by_id(expense.property_id)
    if prop is None or prop.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No existe el gasto con id '{expense_id}'.")

    expense_repo.delete(expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/expenses/{expense_id}/fiscal-category", response_model=ExpenseResponse)
def update_fiscal_category(
    expense_id: str,
    body: FiscalCategoryUpdate,
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

