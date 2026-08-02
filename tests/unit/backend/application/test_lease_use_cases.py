from datetime import date
from decimal import Decimal

import pytest

from backend.application.use_cases import (
    CreateLeaseContractUseCase,
    ListLeaseContractsUseCase,
    UpdateLeaseContractUseCase,
    DeleteLeaseContractUseCase,
)
from backend.domain.entities import LeaseType, Property, PropertyType
from backend.domain.value_objects import Address

def _setup_property(property_repo, user_id="u1", property_id="p1"):
    prop = Property(
        name="Test Prop",
        address=Address("Street 1", "City", "12345"),
        property_type=PropertyType.APARTMENT,
        user_id=user_id,
        id=property_id
    )
    property_repo.save(prop)
    return prop

def test_create_lease_contract_use_case(property_repo, lease_contract_repo):
    """T-U-10-13"""
    _setup_property(property_repo)
    use_case = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    contract = use_case.execute(
        user_id="u1", property_id="p1", tenant_name="John", tenant_nif="12345678Z",
        start_date=date(2025, 1, 1), monthly_rent=Decimal("1000.00"), lease_type="vivienda_habitual"
    )
    assert contract.property_id == "p1"
    assert contract.tenant_name == "John"
    assert contract.monthly_rent.amount == Decimal("1000.00")
    assert lease_contract_repo.find_by_id(contract.id) == contract

def test_create_lease_contract_missing_property(property_repo, lease_contract_repo):
    """T-U-10-14"""
    use_case = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    with pytest.raises(ValueError, match="No existe la propiedad"):
        use_case.execute(
            user_id="u1", property_id="p1", tenant_name="John", tenant_nif="12345678Z",
            start_date=date(2025, 1, 1), monthly_rent=Decimal("1000.00"), lease_type="vivienda_habitual"
        )

def test_create_lease_contract_wrong_user(property_repo, lease_contract_repo):
    """T-U-10-15"""
    _setup_property(property_repo, user_id="u2")
    use_case = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    with pytest.raises(ValueError, match="No existe la propiedad"):
        use_case.execute(
            user_id="u1", property_id="p1", tenant_name="John", tenant_nif="12345678Z",
            start_date=date(2025, 1, 1), monthly_rent=Decimal("1000.00"), lease_type="vivienda_habitual"
        )

def test_list_lease_contracts_use_case(property_repo, lease_contract_repo):
    """T-U-10-16"""
    _setup_property(property_repo)
    create_uc = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    create_uc.execute("u1", "p1", "John", "123", date(2025, 1, 1), Decimal("100"), "vivienda_habitual")
    create_uc.execute("u1", "p1", "Jane", "456", date(2025, 2, 1), Decimal("200"), "temporal")
    
    list_uc = ListLeaseContractsUseCase(property_repo, lease_contract_repo)
    contracts = list_uc.execute("u1", "p1")
    assert len(contracts) == 2
    # Should be sorted by start_date DESC
    assert contracts[0].tenant_name == "Jane"

def test_update_lease_contract_use_case(property_repo, lease_contract_repo):
    """T-U-10-17"""
    _setup_property(property_repo)
    create_uc = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    contract = create_uc.execute("u1", "p1", "John", "123", date(2025, 1, 1), Decimal("100"), "vivienda_habitual")
    
    update_uc = UpdateLeaseContractUseCase(property_repo, lease_contract_repo)
    updated = update_uc.execute(
        "u1", contract.id, tenant_name="John Doe", monthly_rent=Decimal("150.00")
    )
    assert updated.tenant_name == "John Doe"
    assert updated.monthly_rent.amount == Decimal("150.00")
    
def test_delete_lease_contract_use_case(property_repo, lease_contract_repo):
    """T-U-10-18"""
    _setup_property(property_repo)
    create_uc = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    contract = create_uc.execute("u1", "p1", "John", "123", date(2025, 1, 1), Decimal("100"), "vivienda_habitual")
    
    delete_uc = DeleteLeaseContractUseCase(property_repo, lease_contract_repo)
    delete_uc.execute("u1", contract.id)
    assert lease_contract_repo.find_by_id(contract.id) is None

def test_delete_lease_contract_wrong_user(property_repo, lease_contract_repo):
    """T-U-10-19"""
    _setup_property(property_repo, user_id="u1")
    create_uc = CreateLeaseContractUseCase(property_repo, lease_contract_repo)
    contract = create_uc.execute("u1", "p1", "John", "123", date(2025, 1, 1), Decimal("100"), "vivienda_habitual")
    
    delete_uc = DeleteLeaseContractUseCase(property_repo, lease_contract_repo)
    with pytest.raises(ValueError, match="La propiedad del contrato no pertenece al usuario."):
        delete_uc.execute("u2", contract.id)
