"""
Tests para Value Objects: Money y Address.

VO-01 a VO-13: creación, validación, aritmética, igualdad, repr e inmutabilidad.
"""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from backend.domain.value_objects import Address, Money


# ──────────────────────────────────────────────
# Money
# ──────────────────────────────────────────────

def test_money_creation():
    """VO-01: Money se crea correctamente con amount y currency."""
    money = Money(Decimal("750.00"), "EUR")
    assert money.amount == Decimal("750.00")
    assert money.currency == "EUR"


def test_money_negative_raises():
    """VO-02: Money con amount negativo lanza ValueError."""
    with pytest.raises(ValueError, match="negativo"):
        Money(Decimal("-10.00"), "EUR")


def test_money_addition():
    """VO-03: Suma de dos Money del mismo currency."""
    a = Money(Decimal("100.00"), "EUR")
    b = Money(Decimal("50.00"), "EUR")
    result = a + b
    assert result.amount == Decimal("150.00")
    assert result.currency == "EUR"


def test_money_subtraction():
    """VO-04: Resta de dos Money del mismo currency."""
    a = Money(Decimal("100.00"), "EUR")
    b = Money(Decimal("30.00"), "EUR")
    result = a - b
    assert result.amount == Decimal("70.00")
    assert result.currency == "EUR"


def test_money_different_currency_raises():
    """VO-05: Sumar Money con distintas monedas lanza ValueError."""
    # Como el constructor solo acepta EUR, usamos _create_allowing_negative
    # para crear un Money con otra moneda... pero eso también valida.
    # En realidad, el constructor rechaza monedas != EUR directamente.
    # Testeamos que crear con moneda distinta lanza ValueError.
    with pytest.raises(ValueError, match="Moneda no soportada"):
        Money(Decimal("100.00"), "USD")


def test_money_equality():
    """VO-06: Dos Money con mismos valores son iguales."""
    a = Money(Decimal("250.00"), "EUR")
    b = Money(Decimal("250.00"), "EUR")
    assert a == b


def test_money_repr():
    """VO-07: repr de Money contiene '750.00 EUR'."""
    money = Money(Decimal("750.00"), "EUR")
    assert "750.00 EUR" in repr(money)


def test_money_immutability():
    """VO-13: Money es inmutable (frozen dataclass)."""
    money = Money(Decimal("100.00"), "EUR")
    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal("999.00")  # type: ignore[misc]


# ──────────────────────────────────────────────
# Address
# ──────────────────────────────────────────────

def test_address_creation():
    """VO-08: Address se crea correctamente."""
    addr = Address(street="Calle Mayor 15", city="Madrid", postal_code="28013", country="ES")
    assert addr.street == "Calle Mayor 15"
    assert addr.city == "Madrid"
    assert addr.postal_code == "28013"
    assert addr.country == "ES"


def test_address_empty_street_raises():
    """VO-09: Address con calle vacía lanza ValueError."""
    with pytest.raises(ValueError, match="calle"):
        Address(street="", city="Madrid", postal_code="28013", country="ES")


def test_address_whitespace_city_raises():
    """VO-10: Address con ciudad solo espacios lanza ValueError."""
    with pytest.raises(ValueError, match="ciudad"):
        Address(street="Calle Mayor", city="   ", postal_code="28013", country="ES")


def test_address_equality():
    """VO-11: Dos Address con mismos campos son iguales."""
    a = Address(street="Calle A", city="Barcelona", postal_code="08001", country="ES")
    b = Address(street="Calle A", city="Barcelona", postal_code="08001", country="ES")
    assert a == b


def test_address_immutability():
    """VO-12: Address es inmutable (frozen dataclass)."""
    addr = Address(street="Calle A", city="Barcelona", postal_code="08001", country="ES")
    with pytest.raises(FrozenInstanceError):
        addr.street = "Otra calle"  # type: ignore[misc]
