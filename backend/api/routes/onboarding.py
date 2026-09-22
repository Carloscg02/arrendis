"""
Endpoints de Onboarding y Estimación Fiscal Rápida (F-28).

Diseñado para ser agnóstico de plataforma: consumible tanto por la SPA Web
como por la futura aplicación móvil nativa.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status

from backend.adapters.sqlite_adapter import (
    SQLitePropertyRepository,
    SQLiteUserRepository,
    SQLiteLeaseContractRepository,
)
from backend.api.dependencies import (
    get_current_user,
    get_property_repo,
    get_user_repo,
    get_contract_repo,
)
from backend.api.schemas import (
    QuickEstimateRequest,
    QuickEstimateResponse,
    OnboardingBootstrapRequest,
    PropertyResponse,
    AddressSchema,
)
from backend.application.use_cases import (
    QuickFiscalEstimateUseCase,
    BootstrapOnboardingUseCase,
    SkipOnboardingUseCase,
)
from backend.domain.entities import User, Property

router = APIRouter(prefix="/api", tags=["onboarding"])


@router.post("/fiscal/quick-estimate", response_model=QuickEstimateResponse)
def quick_fiscal_estimate(body: QuickEstimateRequest) -> QuickEstimateResponse:
    """Calcula en tiempo real una estimación de amortización deducible (3% AEAT).
    
    Accesible para el simulador interactivo de onboarding (web o móvil)
    sin requerir autenticación obligatoria previa ni crear datos en BD.
    """
    use_case = QuickFiscalEstimateUseCase()
    try:
        estimate = use_case.execute(
            purchase_price=body.purchase_price,
            acquisition_year=body.acquisition_year,
            construction_ratio=body.construction_ratio,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return QuickEstimateResponse(
        purchase_price=f"{estimate.purchase_price:.2f}",
        estimated_construction_value=f"{estimate.estimated_construction_value:.2f}",
        estimated_land_value=f"{estimate.estimated_land_value:.2f}",
        annual_amortization=f"{estimate.annual_amortization:.2f}",
        estimated_tax_savings_typical=f"{estimate.estimated_tax_savings_typical:.2f}",
        legal_reference="Art. 23.1.b Ley 35/2006 del IRPF (3% anual sobre coste de construcción)",
        disclaimer="Cálculo preliminar orientativo basado en ratio estándar (70% construcción). Para el cálculo vinculante se aplicará el valor catastral del IBI.",
    )


@router.post("/onboarding/bootstrap", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_onboarding(
    body: OnboardingBootstrapRequest,
    current_user: User = Depends(get_current_user),
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    user_repo: SQLiteUserRepository = Depends(get_user_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
) -> PropertyResponse:
    """Crea atómicamente el inmueble inicial, fiscalidad y contrato, finalizando el onboarding.
    
    Una sola llamada HTTP previene estados inconsistentes o 'zombis' en conexiones móviles.
    """
    use_case = BootstrapOnboardingUseCase(
        property_repo=property_repo,
        user_repo=user_repo,
        contract_repo=contract_repo,
    )
    try:
        prop = use_case.execute(
            user_id=current_user.id,
            property_name=body.property_name,
            property_type=body.property_type,
            street=body.street,
            city=body.city,
            postal_code=body.postal_code,
            country=body.country,
            purchase_price=body.purchase_price,
            acquisition_year=body.acquisition_year,
            construction_ratio=body.construction_ratio,
            monthly_rent=body.monthly_rent,
            cups_electricity=body.cups_electricity,
            cups_gas=body.cups_gas,
            cups_water=body.cups_water,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

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
        cups_electricity=prop.cups_electricity,
        cups_gas=prop.cups_gas,
        cups_water=prop.cups_water,
    )


@router.post("/users/me/onboarding/skip", status_code=status.HTTP_200_OK)
def skip_onboarding(
    current_user: User = Depends(get_current_user),
    user_repo: SQLiteUserRepository = Depends(get_user_repo),
) -> dict:
    """Marca el onboarding como completado / omitido para el usuario autenticado."""
    use_case = SkipOnboardingUseCase(user_repo=user_repo)
    use_case.execute(user_id=current_user.id)
    return {"status": "ok", "onboarding_completed": True}
