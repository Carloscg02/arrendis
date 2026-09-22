"""
Pruebas unitarias para FiscalQuickEstimate y FiscalSimulatorService (F-28).
"""

from decimal import Decimal
import pytest
from backend.domain.value_objects import FiscalQuickEstimate
from backend.domain.entities import User
from backend.domain.services import FiscalSimulatorService


def test_ut_f28_01_quick_estimate_standard_calculation():
    """UT-F28-01: FiscalQuickEstimate calcula el 70% de construcción y 3% de amortización."""
    # Inmueble comprado por 210.000 € en 2021
    estimate = FiscalQuickEstimate(
        purchase_price=Decimal("210000.00"),
        acquisition_year=2021,
    )
    # Construcción estimada: 70% de 210.000 = 147.000,00 €
    assert estimate.estimated_construction_value == Decimal("147000.00")
    # Suelo estimado: 30% de 210.000 = 63.000,00 €
    assert estimate.estimated_land_value == Decimal("63000.00")
    # Amortización 3% s/ 147.000 = 4.410,00 €
    assert estimate.annual_amortization == Decimal("4410.00")
    # Ahorro fiscal medio orientativo (~30% de 4.410): 1.323,00 €
    assert estimate.estimated_tax_savings_typical == Decimal("1323.00")


def test_ut_f28_02_quick_estimate_rejects_non_positive_price():
    """UT-F28-02: Rechaza precios negativos o cero con ValueError."""
    with pytest.raises(ValueError, match="El precio de adquisición debe ser un importe positivo"):
        FiscalQuickEstimate(purchase_price=Decimal("0.00"), acquisition_year=2020)

    with pytest.raises(ValueError, match="El precio de adquisición debe ser un importe positivo"):
        FiscalQuickEstimate(purchase_price=Decimal("-50000"), acquisition_year=2020)


def test_ut_f28_03_quick_estimate_rejects_invalid_year():
    """UT-F28-03: Rechaza años de adquisición fuera de rango."""
    with pytest.raises(ValueError, match="Año de adquisición fuera de rango válido"):
        FiscalQuickEstimate(purchase_price=Decimal("150000"), acquisition_year=1850)

    with pytest.raises(ValueError, match="Año de adquisición fuera de rango válido"):
        FiscalQuickEstimate(purchase_price=Decimal("150000"), acquisition_year=2150)


def test_ut_f28_04_quick_estimate_custom_ratio():
    """UT-F28-04: Ratio de construcción configurable (ej. 80%) recalcula adecuadamente."""
    estimate = FiscalQuickEstimate(
        purchase_price=Decimal("100000.00"),
        acquisition_year=2022,
        construction_ratio=Decimal("0.80"),
    )
    assert estimate.estimated_construction_value == Decimal("80000.00")
    assert estimate.estimated_land_value == Decimal("20000.00")
    assert estimate.annual_amortization == Decimal("2400.00")  # 3% de 80.000
    assert estimate.estimated_tax_savings_typical == Decimal("720.00")  # 30% de 2.400


def test_ut_f28_05_user_entity_default_onboarding_completed():
    """UT-F28-05: Entidad User inicializa onboarding_completed = False por defecto."""
    from backend.domain.value_objects import Email, PasswordHash
    user = User(
        email=Email("test@example.com"),
        password_hash=PasswordHash("$2b$12$e8Y7z7rXgG9vV8wW8xX8ye8Y7z7rXgG9vV8wW8xX8ye8Y7z7rXgG9"),
        username="testuser",
    )
    assert user.onboarding_completed is False


def test_ut_f28_06_fiscal_simulator_service():
    """UT-F28-06: FiscalSimulatorService.simulate_quick_estimate produce el VO esperado."""
    estimate = FiscalSimulatorService.simulate_quick_estimate(
        purchase_price=Decimal("300000"),
        acquisition_year=2019,
    )
    assert isinstance(estimate, FiscalQuickEstimate)
    assert estimate.annual_amortization == Decimal("6300.00")  # 300.000 * 0.70 * 0.03
