import pytest
from decimal import Decimal
from dataclasses import FrozenInstanceError

from backend.domain.value_objects import CadastralBreakdown, AcquisitionCost

def test_cadastral_breakdown_creation():
    """T-U-09-01: CadastralBreakdown se crea correctamente con valores positivos"""
    cb = CadastralBreakdown(Decimal("40000"), Decimal("80000"))
    assert cb.land_value == Decimal("40000")
    assert cb.construction_value == Decimal("80000")

def test_cadastral_breakdown_rejects_negative():
    """T-U-09-02: CadastralBreakdown rechaza valores negativos con ValueError"""
    with pytest.raises(ValueError, match="no puede ser negativo"):
        CadastralBreakdown(Decimal("-1"), Decimal("80000"))
    with pytest.raises(ValueError, match="no puede ser negativo"):
        CadastralBreakdown(Decimal("40000"), Decimal("-1"))

def test_cadastral_breakdown_rejects_all_zeros():
    """T-U-09-03: CadastralBreakdown rechaza todo ceros con ValueError"""
    with pytest.raises(ValueError, match="todo ceros"):
        CadastralBreakdown(Decimal("0"), Decimal("0"))

def test_cadastral_breakdown_total_value():
    """T-U-09-04: CadastralBreakdown.total_value suma correctamente"""
    cb = CadastralBreakdown(Decimal("40000"), Decimal("80000"))
    assert cb.total_value == Decimal("120000")

def test_cadastral_breakdown_is_immutable():
    """T-U-09-05: CadastralBreakdown es inmutable (frozen=True)"""
    cb = CadastralBreakdown(Decimal("40000"), Decimal("80000"))
    with pytest.raises(FrozenInstanceError):
        cb.land_value = Decimal("50000")

def test_acquisition_cost_creation():
    """T-U-09-06: AcquisitionCost se crea correctamente con valores válidos"""
    ac = AcquisitionCost(
        purchase_price=Decimal("200000"),
        construction_portion=Decimal("120000"),
        land_portion=Decimal("80000"),
        transfer_tax=Decimal("16000"),
        notary_fees=Decimal("800"),
        registry_fees=Decimal("400")
    )
    assert ac.purchase_price == Decimal("200000")

def test_acquisition_cost_rejects_invalid_portions():
    """T-U-09-07: AcquisitionCost rechaza si construction_portion + land_portion != purchase_price"""
    with pytest.raises(ValueError, match="Deben coincidir"):
        AcquisitionCost(
            purchase_price=Decimal("200000"),
            construction_portion=Decimal("100000"),
            land_portion=Decimal("80000"),
            transfer_tax=Decimal("16000"),
            notary_fees=Decimal("800"),
            registry_fees=Decimal("400")
        )

def test_acquisition_cost_rejects_negative_values():
    """T-U-09-08: AcquisitionCost rechaza valores negativos"""
    with pytest.raises(ValueError, match="no puede ser negativo"):
        AcquisitionCost(
            purchase_price=Decimal("200000"),
            construction_portion=Decimal("120000"),
            land_portion=Decimal("80000"),
            transfer_tax=Decimal("-16000"),
            notary_fees=Decimal("800"),
            registry_fees=Decimal("400")
        )

def test_acquisition_cost_total_acquisition_expenses():
    """T-U-09-09: AcquisitionCost.total_acquisition_expenses calcula correctamente"""
    ac = AcquisitionCost(
        purchase_price=Decimal("200000"),
        construction_portion=Decimal("120000"),
        land_portion=Decimal("80000"),
        transfer_tax=Decimal("16000"),
        notary_fees=Decimal("800"),
        registry_fees=Decimal("400")
    )
    assert ac.total_acquisition_expenses == Decimal("17200")

def test_acquisition_cost_total_cost():
    """T-U-09-10: AcquisitionCost.total_cost calcula correctamente"""
    ac = AcquisitionCost(
        purchase_price=Decimal("200000"),
        construction_portion=Decimal("120000"),
        land_portion=Decimal("80000"),
        transfer_tax=Decimal("16000"),
        notary_fees=Decimal("800"),
        registry_fees=Decimal("400")
    )
    assert ac.total_cost == Decimal("217200")

def test_acquisition_cost_is_immutable():
    """T-U-09-11: AcquisitionCost es inmutable (frozen=True)"""
    ac = AcquisitionCost(
        purchase_price=Decimal("200000"),
        construction_portion=Decimal("120000"),
        land_portion=Decimal("80000"),
        transfer_tax=Decimal("16000"),
        notary_fees=Decimal("800"),
        registry_fees=Decimal("400")
    )
    with pytest.raises(FrozenInstanceError):
        ac.purchase_price = Decimal("210000")

def _make_test_report() -> "FiscalReport":
    from backend.domain.value_objects import FiscalReport
    return FiscalReport(
        fiscal_year=2025,
        property_id="prop-123",
        gross_rental_income=Decimal("12000"),
        other_income=Decimal("0"),
        total_income=Decimal("12000"),
        rented_days=365,
        total_days_in_year=365,
        occupation_ratio=Decimal("1"),
        expenses_intereses=Decimal("100"),
        expenses_reparacion=Decimal("200"),
        expenses_tributos=Decimal("50"),
        expenses_seguros=Decimal("150"),
        expenses_comunidad=Decimal("0"),
        expenses_suministros=Decimal("0"),
        expenses_formalizacion=Decimal("0"),
        expenses_dudoso_cobro=Decimal("0"),
        expenses_muebles=Decimal("0"),
        expenses_otros=Decimal("0"),
        repair_interest_raw=Decimal("300"),
        repair_interest_cap=Decimal("12000"),
        repair_interest_applied=Decimal("300"),
        repair_interest_excess=Decimal("0"),
        prior_excess_available=Decimal("0"),
        prior_excess_applied=Decimal("0"),
        amortization_base=Decimal("100000"),
        amortization_rate=Decimal("0.03"),
        amortization_full_year=Decimal("3000"),
        amortization_prorated=Decimal("3000"),
        total_deductible_expenses=Decimal("3500"),
        net_income_before_reduction=Decimal("8500"),
        vivienda_habitual_days=365,
        vivienda_habitual_ratio=Decimal("1"),
        reduction_base=Decimal("8500"),
        reduction_percentage=Decimal("0.60"),
        reduction_amount=Decimal("5100"),
        net_income_final=Decimal("3400"),
        unclassified_income_count=0,
        unclassified_expense_count=0,
        has_warnings=False
    )

def test_fiscal_report_is_immutable():
    """T-U-12-21: FiscalReport es inmutable (frozen)"""
    report = _make_test_report()
    with pytest.raises(FrozenInstanceError):
        report.fiscal_year = 2026

def test_fiscal_report_value_equality():
    """T-U-12-22: FiscalReport se compara por valor"""
    report1 = _make_test_report()
    report2 = _make_test_report()
    assert report1 == report2
    assert report1 is not report2
