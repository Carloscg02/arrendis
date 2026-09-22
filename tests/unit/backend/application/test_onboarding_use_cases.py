"""
Tests unitarios para los Casos de Uso de Onboarding (F-28).
"""

from decimal import Decimal
from unittest.mock import MagicMock
from backend.application.use_cases import (
    QuickFiscalEstimateUseCase,
    BootstrapOnboardingUseCase,
    SkipOnboardingUseCase,
)
from backend.domain.entities import Property, PropertyStatus


def test_quick_fiscal_estimate_use_case():
    use_case = QuickFiscalEstimateUseCase()
    result = use_case.execute(
        purchase_price=Decimal("200000"),
        acquisition_year=2020,
    )
    assert result.purchase_price == Decimal("200000")
    assert result.estimated_construction_value == Decimal("140000.00")
    assert result.annual_amortization == Decimal("4200.00")


def test_it_f28_03_bootstrap_onboarding_use_case_complete():
    """Valida creación atómica de inmueble, fiscalidad, contrato y estado de onboarding."""
    prop_repo = MagicMock()
    user_repo = MagicMock()
    contract_repo = MagicMock()

    use_case = BootstrapOnboardingUseCase(
        property_repo=prop_repo,
        user_repo=user_repo,
        contract_repo=contract_repo,
    )

    prop = use_case.execute(
        user_id="user-123",
        property_name="Piso en Fuencarral",
        property_type="apartment",
        street="Calle Fuencarral 12",
        city="Madrid",
        postal_code="28004",
        country="España",
        purchase_price=Decimal("250000"),
        acquisition_year=2021,
        monthly_rent=Decimal("1200"),
        cups_electricity="ES0031103721971011PR0F",
    )

    # 1. Propiedad guardada
    prop_repo.save.assert_called_once()
    saved_prop = prop_repo.save.call_args[0][0]
    assert saved_prop.name == "Piso en Fuencarral"
    assert saved_prop.status == PropertyStatus.RENTED
    assert saved_prop.cups_electricity == "ES0031103721971011PR0F"

    # 2. Fiscalidad guardada
    prop_repo.update_fiscal_data.assert_called_once()
    args = prop_repo.update_fiscal_data.call_args[0]
    prop_id, cad_ref, cad_breakdown, acq_cost, acq_date = args
    assert prop_id == saved_prop.id
    assert acq_cost is not None
    assert acq_cost.purchase_price == Decimal("250000")
    assert acq_cost.construction_portion == Decimal("175000.00")  # 70%

    # 3. Contrato guardado
    contract_repo.save.assert_called_once()
    saved_contract = contract_repo.save.call_args[0][0]
    assert saved_contract.monthly_rent.amount == Decimal("1200")
    assert saved_contract.property_id == saved_prop.id

    # 4. Usuario marcado como completado
    user_repo.update_onboarding_status.assert_called_once_with(user_id="user-123", completed=True)


def test_it_f28_04_skip_onboarding_use_case():
    """Valida omisión de onboarding."""
    user_repo = MagicMock()
    use_case = SkipOnboardingUseCase(user_repo=user_repo)

    use_case.execute(user_id="user-999")
    user_repo.update_onboarding_status.assert_called_once_with(user_id="user-999", completed=True)
