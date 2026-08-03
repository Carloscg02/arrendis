"""
Router de Properties — endpoints CRUD para propiedades.

Traduce peticiones HTTP a llamadas de Casos de Uso (CreateProperty, ListProperties)
y formatea las respuestas como PropertyResponse.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response

from backend.adapters.sqlite_adapter import SQLiteConnection, SQLitePropertyRepository, SQLiteIncomeRepository, SQLiteExpenseRepository, SQLiteLeaseContractRepository
from backend.adapters.aeat_pdf_renderer_adapter import AEATPdfRendererAdapter
from backend.api.schemas import AddressSchema, PropertyCreate, PropertyResponse, FiscalDataUpdate, FiscalDataResponse, CadastralBreakdownSchema, AcquisitionCostSchema, FiscalSuggestionsResponse, FiscalReportResponse
from backend.application.use_cases import CreatePropertyUseCase, ListPropertiesUseCase, GetPropertyUseCase, UpdatePropertyFiscalDataUseCase, GetPropertyFiscalDataUseCase, SuggestFiscalCategoriesUseCase, GenerateFiscalReportUseCase, DownloadFiscalReportPdfUseCase
from backend.domain.entities import Property, User
from backend.api.dependencies import get_db, get_property_repo, get_income_repo, get_expense_repo, get_current_user, get_contract_repo, get_fiscal_report_renderer

router = APIRouter(prefix="/api/properties", tags=["properties"])


def _entity_to_response(prop: Property) -> PropertyResponse:
    """Convierte una entidad Property del dominio a un schema de respuesta."""
    image_url = f"/api/images/{prop.image_filename}" if prop.image_filename else None
    return PropertyResponse(
        id=prop.id,
        name=prop.name,
        address=AddressSchema(
            street=prop.address.street,
            city=prop.address.city,
            postal_code=prop.address.postal_code,
            country=prop.address.country,
        ),
        property_type=prop.property_type.value,
        status=prop.status.value,
        image_url=image_url,
        has_fiscal_data=prop.has_fiscal_data,
    )


@router.post("", response_model=PropertyResponse, status_code=201)
def create_property(
    body: PropertyCreate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Crea una nueva propiedad."""
    try:
        use_case = CreatePropertyUseCase(property_repo)
        prop = use_case.execute(
            user_id=current_user.id,
            name=body.name,
            street=body.address.street,
            city=body.address.city,
            postal_code=body.address.postal_code,
            country=body.address.country,
            property_type=body.property_type,
        )
        return _entity_to_response(prop)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PropertyResponse])
def list_properties(
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> list[PropertyResponse]:
    """Lista todas las propiedades registradas."""
    use_case = ListPropertiesUseCase(property_repo)
    properties = use_case.execute(current_user.id)
    return [_entity_to_response(p) for p in properties]


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Obtiene una propiedad por su ID."""
    try:
        prop = GetPropertyUseCase(property_repo).execute(property_id, current_user.id)
        return _entity_to_response(prop)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Property '{property_id}' not found",
        )
    return _entity_to_response(prop)


@router.delete("/{property_id}")
def delete_property(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Elimina una propiedad por su ID."""
    try:
        GetPropertyUseCase(property_repo).execute(property_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found")
        
    property_repo.delete(property_id)
    return {"detail": f"Property '{property_id}' deleted"}


@router.post("/{property_id}/image", response_model=PropertyResponse)
async def upload_property_image(
    property_id: str,
    file: UploadFile = File(...),
    db: SQLiteConnection = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Sube o actualiza la foto de una propiedad."""
    prop_repo = SQLitePropertyRepository(db)
    try:
        prop = GetPropertyUseCase(prop_repo).execute(property_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found")
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos JPG o PNG")
    
    # Validate file size (5MB max)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no puede superar 5 MB")
    
    # Determine extension
    ext = "jpg" if file.content_type == "image/jpeg" else "png"
    filename = f"{property_id}.{ext}"
    
    # Delete old image if exists
    if prop.image_filename:
        old_path = Path("data/images") / prop.image_filename
        if old_path.exists():
            old_path.unlink()
            
    # Save file
    images_dir = Path("data/images")
    images_dir.mkdir(parents=True, exist_ok=True)
    (images_dir / filename).write_bytes(contents)
    
    # Update database
    prop_repo.update_image(property_id, filename)
    
    # Return updated property
    updated = prop_repo.find_by_id(property_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found after update")
    return _entity_to_response(updated)


@router.get("/{property_id}/fiscal-data", response_model=FiscalDataResponse)
def get_fiscal_data(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> FiscalDataResponse:
    """Obtiene los datos fiscales de una propiedad."""
    use_case = GetPropertyFiscalDataUseCase(property_repo)
    try:
        prop = use_case.execute(current_user.id, property_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada.")

    return _property_to_fiscal_response(prop)


@router.put("/{property_id}/fiscal-data", response_model=FiscalDataResponse)
def update_fiscal_data(
    property_id: str,
    body: FiscalDataUpdate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> FiscalDataResponse:
    """Actualiza los datos fiscales de una propiedad."""
    use_case = UpdatePropertyFiscalDataUseCase(property_repo)
    try:
        prop = use_case.execute(
            user_id=current_user.id,
            property_id=property_id,
            cadastral_ref=body.cadastral_ref,
            land_value=body.cadastral_breakdown.land_value if body.cadastral_breakdown else None,
            construction_value=body.cadastral_breakdown.construction_value if body.cadastral_breakdown else None,
            purchase_price=body.acquisition_cost.purchase_price if body.acquisition_cost else None,
            construction_portion=body.acquisition_cost.construction_portion if body.acquisition_cost else None,
            land_portion=body.acquisition_cost.land_portion if body.acquisition_cost else None,
            transfer_tax=body.acquisition_cost.transfer_tax if body.acquisition_cost else None,
            notary_fees=body.acquisition_cost.notary_fees if body.acquisition_cost else None,
            registry_fees=body.acquisition_cost.registry_fees if body.acquisition_cost else None,
            acquisition_date=body.acquisition_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _property_to_fiscal_response(prop)


def _property_to_fiscal_response(prop: Property) -> FiscalDataResponse:
    """Helper para convertir Property a FiscalDataResponse."""
    cadastral = None
    if prop.cadastral_breakdown:
        cadastral = CadastralBreakdownSchema(
            land_value=prop.cadastral_breakdown.land_value,
            construction_value=prop.cadastral_breakdown.construction_value,
        )

    acquisition = None
    if prop.acquisition_cost:
        acquisition = AcquisitionCostSchema(
            purchase_price=prop.acquisition_cost.purchase_price,
            construction_portion=prop.acquisition_cost.construction_portion,
            land_portion=prop.acquisition_cost.land_portion,
            transfer_tax=prop.acquisition_cost.transfer_tax,
            notary_fees=prop.acquisition_cost.notary_fees,
            registry_fees=prop.acquisition_cost.registry_fees,
        )

    return FiscalDataResponse(
        property_id=prop.id,
        cadastral_ref=prop.cadastral_ref,
        cadastral_breakdown=cadastral,
        acquisition_cost=acquisition,
        acquisition_date=prop.acquisition_date,
        has_fiscal_data=prop.has_fiscal_data,
    )


@router.get("/{property_id}/fiscal-suggestions", response_model=FiscalSuggestionsResponse)
def get_fiscal_suggestions(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        use_case = SuggestFiscalCategoriesUseCase(property_repo, income_repo, expense_repo)
        return use_case.execute(current_user.id, property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{property_id}/fiscal-report", response_model=FiscalReportResponse)
async def get_fiscal_report(
    property_id: str,
    year: int,
    user: User = Depends(get_current_user),
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
):
    """Calcula y devuelve el informe fiscal para una propiedad y un año."""
    uc = GenerateFiscalReportUseCase(property_repo, income_repo, expense_repo, contract_repo)
    try:
        report = uc.execute(user.id, property_id, year)
    except ValueError as e:
        if "datos fiscales" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    return FiscalReportResponse(
        fiscal_year=report.fiscal_year,
        property_id=report.property_id,
        gross_rental_income=report.gross_rental_income,
        other_income=report.other_income,
        total_income=report.total_income,
        rented_days=report.rented_days,
        total_days_in_year=report.total_days_in_year,
        occupation_ratio=report.occupation_ratio,
        expenses_intereses=report.expenses_intereses,
        expenses_reparacion=report.expenses_reparacion,
        expenses_tributos=report.expenses_tributos,
        expenses_seguros=report.expenses_seguros,
        expenses_suministros=report.expenses_suministros,
        expenses_formalizacion=report.expenses_formalizacion,
        expenses_dudoso_cobro=report.expenses_dudoso_cobro,
        expenses_otros=report.expenses_otros,
        repair_interest_raw=report.repair_interest_raw,
        repair_interest_cap=report.repair_interest_cap,
        repair_interest_applied=report.repair_interest_applied,
        repair_interest_excess=report.repair_interest_excess,
        amortization_base=report.amortization_base,
        amortization_rate=report.amortization_rate,
        amortization_full_year=report.amortization_full_year,
        amortization_prorated=report.amortization_prorated,
        total_deductible_expenses=report.total_deductible_expenses,
        net_income_before_reduction=report.net_income_before_reduction,
        vivienda_habitual_days=report.vivienda_habitual_days,
        vivienda_habitual_ratio=report.vivienda_habitual_ratio,
        reduction_base=report.reduction_base,
        reduction_percentage=report.reduction_percentage,
        reduction_amount=report.reduction_amount,
        net_income_final=report.net_income_final,
        unclassified_income_count=report.unclassified_income_count,
        unclassified_expense_count=report.unclassified_expense_count,
        has_warnings=report.has_warnings,
    )


@router.get("/{property_id}/fiscal-report/pdf")
async def download_fiscal_report_pdf(
    property_id: str,
    year: int,
    user: User = Depends(get_current_user),
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    income_repo: SQLiteIncomeRepository = Depends(get_income_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
    renderer: AEATPdfRendererAdapter = Depends(get_fiscal_report_renderer),
):
    """Genera y descarga el borrador fiscal en PDF."""
    uc = DownloadFiscalReportPdfUseCase(
        property_repo, income_repo, expense_repo, contract_repo, renderer
    )
    try:
        pdf_bytes, content_type, filename = uc.execute(user.id, property_id, year)
    except ValueError as e:
        if "datos fiscales" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


