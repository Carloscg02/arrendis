import pytest
from decimal import Decimal
from backend.adapters.aeat_pdf_renderer_adapter import AEATPdfRendererAdapter
from backend.domain.value_objects import FiscalReport


@pytest.fixture
def sample_fiscal_report() -> FiscalReport:
    return FiscalReport(
        fiscal_year=2026,
        property_id="p-100",
        gross_rental_income=Decimal("12000"),
        other_income=Decimal("0"),
        total_income=Decimal("12000"),
        rented_days=365,
        total_days_in_year=365,
        occupation_ratio=Decimal("1.0"),
        expenses_intereses=Decimal("1200"),
        expenses_reparacion=Decimal("800"),
        expenses_tributos=Decimal("450"),
        expenses_seguros=Decimal("300"),
        expenses_comunidad=Decimal("0"),
        expenses_suministros=Decimal("150"),
        expenses_formalizacion=Decimal("0"),
        expenses_dudoso_cobro=Decimal("0"),
        expenses_muebles=Decimal("0"),
        expenses_otros=Decimal("200"),
        repair_interest_raw=Decimal("2000"),
        repair_interest_cap=Decimal("12000"),
        repair_interest_applied=Decimal("2000"),
        repair_interest_excess=Decimal("0"),
        prior_excess_available=Decimal("0"),
        prior_excess_applied=Decimal("0"),
        amortization_base=Decimal("127200"),
        amortization_rate=Decimal("0.03"),
        amortization_full_year=Decimal("3816"),
        amortization_prorated=Decimal("3816"),
        total_deductible_expenses=Decimal("6916"),
        net_income_before_reduction=Decimal("5084"),
        vivienda_habitual_days=365,
        vivienda_habitual_ratio=Decimal("1.0"),
        reduction_base=Decimal("5084"),
        reduction_percentage=Decimal("0.60"),
        reduction_amount=Decimal("3050.40"),
        net_income_final=Decimal("2033.60"),
        unclassified_income_count=0,
        unclassified_expense_count=0,
        has_warnings=False,
    )


def test_tu_13_01_render_returns_nonempty_bytes(sample_fiscal_report):
    """T-U-13-01: render() retorna bytes no vacíos."""
    adapter = AEATPdfRendererAdapter()
    result = adapter.render(sample_fiscal_report, "Piso Centro", "Calle Mayor 10")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_tu_13_02_content_type_is_pdf():
    """T-U-13-02: content_type() retorna 'application/pdf'."""
    adapter = AEATPdfRendererAdapter()
    assert adapter.content_type() == "application/pdf"


def test_tu_13_03_file_extension_is_pdf():
    """T-U-13-03: file_extension() retorna 'pdf'."""
    adapter = AEATPdfRendererAdapter()
    assert adapter.file_extension() == "pdf"


def test_tu_13_04_pdf_magic_bytes(sample_fiscal_report):
    """T-U-13-04: Los bytes generados empiezan por %PDF-."""
    adapter = AEATPdfRendererAdapter()
    result = adapter.render(sample_fiscal_report, "Piso Centro", "Calle Mayor 10")
    assert result[:5] == b"%PDF-"


def test_tu_13_05_pdf_is_valid_document(sample_fiscal_report):
    """T-U-13-05: El PDF generado tiene estructura de documento válida y finaliza con %%EOF."""
    adapter = AEATPdfRendererAdapter()
    result = adapter.render(sample_fiscal_report, "Piso Centro", "Calle Mayor 10")
    assert b"%%EOF" in result


def test_tu_13_06_pdf_contains_property_name(sample_fiscal_report):
    """T-U-13-06: Los elementos del documento contienen el nombre de la propiedad."""
    adapter = AEATPdfRendererAdapter()
    elements = adapter._build_elements(sample_fiscal_report, "Piso Centro", "Calle Mayor 10")
    texts = [e.text for e in elements if hasattr(e, "text")]
    assert any("Piso Centro" in text for text in texts)


def test_tu_13_07_pdf_contains_fiscal_year(sample_fiscal_report):
    """T-U-13-07: Los elementos del documento contienen el ejercicio fiscal."""
    adapter = AEATPdfRendererAdapter()
    elements = adapter._build_elements(sample_fiscal_report, "Piso Centro", "Calle Mayor 10")
    texts = [e.text for e in elements if hasattr(e, "text")]
    assert any("2026" in text for text in texts)


def test_tu_13_08_custom_casilla_map(sample_fiscal_report):
    """T-U-13-08: Se puede inyectar un mapa de casillas personalizado."""
    custom_map = {
        "rendimiento_integro": "9999",
        "rendimiento_neto_reducido": "8888",
    }
    adapter = AEATPdfRendererAdapter(casilla_map=custom_map)
    result = adapter.render(sample_fiscal_report, "Piso Personalizado", "Calle Test 5")
    assert isinstance(result, bytes)
    assert len(result) > 0
