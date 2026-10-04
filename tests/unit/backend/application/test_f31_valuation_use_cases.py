from datetime import date, timedelta
from unittest.mock import MagicMock
import pytest

from backend.application.valuation_use_cases import RequestPropertyValuationUseCase
from backend.domain.entities import (
    Property,
    PropertyType,
    PropertyCondition,
    MissingPhysicalAttributesError,
)
from backend.domain.value_objects import Address
from backend.adapters.valuation import MockMarketValuationAdapter




def _create_sample_property(
    property_repo,
    user_id="user-123",
    property_id="prop-abc",
    surface_m2=85,
    bedrooms=2,
    bathrooms=1,
) -> Property:
    prop = Property(
        name="Piso Chamberí",
        address=Address(street="Calle Santa Engracia 10", city="Madrid", postal_code="28010"),
        property_type=PropertyType.APARTMENT,
        user_id=user_id,
        id=property_id,
        surface_m2=surface_m2,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        floor=2,
        has_elevator=True,
        condition=PropertyCondition.BUEN_ESTADO,
    )
    property_repo.save(prop)
    return prop


def test_valuation_use_case_property_not_found(property_repo, valuation_repo):
    port = MockMarketValuationAdapter()
    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, port)

    with pytest.raises(ValueError, match="no encontrada"):
        use_case.execute(property_id="non-existent", user_id="user-123")


def test_valuation_use_case_property_foreign_user(property_repo, valuation_repo):
    _create_sample_property(property_repo, user_id="user-123", property_id="prop-abc")
    port = MockMarketValuationAdapter()
    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, port)

    with pytest.raises(ValueError, match="no encontrada"):
        use_case.execute(property_id="prop-abc", user_id="foreign-user")


def test_valuation_use_case_missing_surface_m2(property_repo, valuation_repo):
    prop = Property(
        name="Piso Sin Metros",
        address=Address(street="Calle Mayor 1", city="Madrid", postal_code="28013"),
        property_type=PropertyType.APARTMENT,
        user_id="user-123",
        id="prop-no-m2",
        surface_m2=None,
    )
    property_repo.save(prop)

    port = MockMarketValuationAdapter()
    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, port)

    with pytest.raises(MissingPhysicalAttributesError, match="requiere especificar la superficie"):
        use_case.execute(property_id="prop-no-m2", user_id="user-123")


def test_valuation_use_case_fresh_request_success(property_repo, valuation_repo):
    _create_sample_property(property_repo, user_id="user-123", property_id="prop-1")
    port = MockMarketValuationAdapter()
    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, port, cooldown_days=30)

    result = use_case.execute(
        property_id="prop-1",
        user_id="user-123",
        force=False,
        current_date=date(2026, 9, 26),
    )

    assert result.is_cached is False
    assert result.cooldown_days_remaining == 30
    assert result.valuation.property_id == "prop-1"
    assert result.valuation.valuation_date == date(2026, 9, 26)
    assert valuation_repo.find_by_id(result.valuation.id) is not None


def test_valuation_use_case_cooldown_returns_cached_without_calling_port(property_repo, valuation_repo):
    _create_sample_property(property_repo, user_id="user-123", property_id="prop-1")
    mock_port = MagicMock()
    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, mock_port, cooldown_days=30)

    # First execution on Day 0
    day0 = date(2026, 9, 1)
    real_adapter = MockMarketValuationAdapter()
    mock_port.estimate_valuation.return_value = real_adapter.estimate_valuation(
        address=Address("Calle", "Madrid", "28010"), surface_m2=85
    )

    res1 = use_case.execute(property_id="prop-1", user_id="user-123", current_date=day0)
    assert res1.is_cached is False
    assert mock_port.estimate_valuation.call_count == 1

    # Second execution on Day 10 (cooldown active: 30 - 10 = 20 days remaining)
    day10 = date(2026, 9, 11)
    res2 = use_case.execute(property_id="prop-1", user_id="user-123", force=False, current_date=day10)

    assert res2.is_cached is True
    assert res2.cooldown_days_remaining == 20
    assert res2.valuation.id == res1.valuation.id
    # Ensure port was NOT called a second time
    assert mock_port.estimate_valuation.call_count == 1


def test_valuation_use_case_cooldown_force_recalculates(property_repo, valuation_repo):
    _create_sample_property(property_repo, user_id="user-123", property_id="prop-1")
    mock_port = MagicMock()
    real_adapter = MockMarketValuationAdapter()
    mock_port.estimate_valuation.return_value = real_adapter.estimate_valuation(
        address=Address("Calle", "Madrid", "28010"), surface_m2=85
    )

    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, mock_port, cooldown_days=30)

    day0 = date(2026, 9, 1)
    res1 = use_case.execute(property_id="prop-1", user_id="user-123", current_date=day0)

    # Forced execution on Day 10 with force=True
    day10 = date(2026, 9, 11)
    res2 = use_case.execute(property_id="prop-1", user_id="user-123", force=True, current_date=day10)

    assert res2.is_cached is False
    assert res2.cooldown_days_remaining == 30
    assert res2.valuation.id != res1.valuation.id
    assert res2.valuation.valuation_date == day10
    assert mock_port.estimate_valuation.call_count == 2


def test_valuation_use_case_cooldown_expired_recalculates(property_repo, valuation_repo):
    _create_sample_property(property_repo, user_id="user-123", property_id="prop-1")
    mock_port = MagicMock()
    real_adapter = MockMarketValuationAdapter()
    mock_port.estimate_valuation.return_value = real_adapter.estimate_valuation(
        address=Address("Calle", "Madrid", "28010"), surface_m2=85
    )

    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, mock_port, cooldown_days=30)

    day0 = date(2026, 8, 1)
    res1 = use_case.execute(property_id="prop-1", user_id="user-123", current_date=day0)

    # 35 days later (expired cooldown)
    day35 = date(2026, 9, 5)
    res2 = use_case.execute(property_id="prop-1", user_id="user-123", force=False, current_date=day35)

    assert res2.is_cached is False
    assert res2.cooldown_days_remaining == 30
    assert res2.valuation.id != res1.valuation.id
    assert mock_port.estimate_valuation.call_count == 2


def test_valuation_use_case_get_latest(property_repo, valuation_repo):
    _create_sample_property(property_repo, user_id="user-123", property_id="prop-1")
    port = MockMarketValuationAdapter()
    use_case = RequestPropertyValuationUseCase(property_repo, valuation_repo, port, cooldown_days=30)

    # Initially None
    assert use_case.get_latest("prop-1", "user-123") is None

    # After valuation
    use_case.execute("prop-1", "user-123", current_date=date(2026, 9, 20))

    # Retrieve on 2026-09-26 (6 days later -> 24 days cooldown remaining)
    latest = use_case.get_latest("prop-1", "user-123", current_date=date(2026, 9, 26))
    assert latest is not None
    assert latest.is_cached is True
    assert latest.cooldown_days_remaining == 24
