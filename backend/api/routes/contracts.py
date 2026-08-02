from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.adapters.sqlite_adapter import SQLitePropertyRepository, SQLiteLeaseContractRepository
from backend.api.schemas import LeaseContractCreate, LeaseContractUpdate, LeaseContractResponse, UserResponse
from backend.application.use_cases import (
    CreateLeaseContractUseCase,
    ListLeaseContractsUseCase,
    UpdateLeaseContractUseCase,
    DeleteLeaseContractUseCase,
)
from backend.api.dependencies import get_current_user, get_property_repo, get_contract_repo
from backend.domain.entities import User

router = APIRouter(prefix="/api", tags=["contracts"])

@router.post("/properties/{property_id}/contracts", status_code=201, response_model=LeaseContractResponse)
def create_contract(
    property_id: str,
    data: LeaseContractCreate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
    user: User = Depends(get_current_user)
):
    use_case = CreateLeaseContractUseCase(property_repo, contract_repo)
    try:
        contract = use_case.execute(
            user_id=user.id,
            property_id=property_id,
            tenant_name=data.tenant_name,
            tenant_nif=data.tenant_nif,
            start_date=data.start_date,
            end_date=data.end_date,
            monthly_rent=Decimal(str(data.monthly_rent)),
            lease_type=data.lease_type
        )
        return LeaseContractResponse(
            id=contract.id,
            property_id=contract.property_id,
            tenant_name=contract.tenant_name,
            tenant_nif=contract.tenant_nif,
            start_date=contract.start_date,
            end_date=contract.end_date,
            monthly_rent=str(contract.monthly_rent.amount),
            currency=contract.monthly_rent.currency,
            lease_type=contract.lease_type.value,
            is_active=contract.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/properties/{property_id}/contracts", response_model=list[LeaseContractResponse])
def list_contracts(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
    user: User = Depends(get_current_user)
):
    use_case = ListLeaseContractsUseCase(property_repo, contract_repo)
    try:
        contracts = use_case.execute(user_id=user.id, property_id=property_id)
        return [
            LeaseContractResponse(
                id=c.id,
                property_id=c.property_id,
                tenant_name=c.tenant_name,
                tenant_nif=c.tenant_nif,
                start_date=c.start_date,
                end_date=c.end_date,
                monthly_rent=str(c.monthly_rent.amount),
                currency=c.monthly_rent.currency,
                lease_type=c.lease_type.value,
                is_active=c.is_active
            )
            for c in contracts
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/contracts/{contract_id}", response_model=LeaseContractResponse)
def update_contract(
    contract_id: str,
    data: LeaseContractUpdate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
    user: User = Depends(get_current_user)
):
    use_case = UpdateLeaseContractUseCase(property_repo, contract_repo)
    try:
        monthly_rent_decimal = Decimal(str(data.monthly_rent)) if data.monthly_rent is not None else None
        contract = use_case.execute(
            user_id=user.id,
            contract_id=contract_id,
            tenant_name=data.tenant_name,
            tenant_nif=data.tenant_nif,
            start_date=data.start_date,
            end_date=data.end_date,
            monthly_rent=monthly_rent_decimal,
            lease_type=data.lease_type
        )
        return LeaseContractResponse(
            id=contract.id,
            property_id=contract.property_id,
            tenant_name=contract.tenant_name,
            tenant_nif=contract.tenant_nif,
            start_date=contract.start_date,
            end_date=contract.end_date,
            monthly_rent=str(contract.monthly_rent.amount),
            currency=contract.monthly_rent.currency,
            lease_type=contract.lease_type.value,
            is_active=contract.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/contracts/{contract_id}", status_code=204)
def delete_contract(
    contract_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    contract_repo: SQLiteLeaseContractRepository = Depends(get_contract_repo),
    user: User = Depends(get_current_user)
):
    use_case = DeleteLeaseContractUseCase(property_repo, contract_repo)
    try:
        use_case.execute(user_id=user.id, contract_id=contract_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
