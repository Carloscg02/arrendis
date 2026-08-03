import pytest
from backend.domain.ports import FiscalReportRendererPort


def test_tu_13_13_cannot_instantiate_port():
    """T-U-13-13: FiscalReportRendererPort es abstracta y no se puede instanciar directamente."""
    with pytest.raises(TypeError):
        FiscalReportRendererPort()
