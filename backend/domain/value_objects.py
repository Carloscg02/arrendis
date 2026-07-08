"""
Value Objects del dominio.

Los Value Objects son inmutables y se comparan por el valor de todos sus campos.
No tienen identidad propia — dos Money(100, "EUR") son intercambiables.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """Representa una cantidad monetaria con precisión decimal.

    Inmutable: una vez creado, no se puede modificar.
    Igualdad por valor: Money(100, "EUR") == Money(100, "EUR") → True.
    """

    amount: Decimal
    currency: str = "EUR"

    def __post_init__(self) -> None:
        # Validar que la moneda sea EUR (MVP)
        if self.currency != "EUR":
            raise ValueError(
                f"Moneda no soportada: '{self.currency}'. Solo se acepta 'EUR' en el MVP."
            )
        # Validar que el amount no sea negativo (salvo creación interna)
        if self.amount < 0:
            raise ValueError(
                f"El importe no puede ser negativo: {self.amount}"
            )

    @classmethod
    def _create_allowing_negative(cls, amount: Decimal, currency: str = "EUR") -> Money:
        """Crea un Money permitiendo valores negativos (uso interno para cálculos de beneficio neto)."""
        # Saltamos la validación de __post_init__ usando object.__setattr__
        instance = object.__new__(cls)
        object.__setattr__(instance, "amount", amount)
        object.__setattr__(instance, "currency", currency)
        # Validar solo la moneda
        if currency != "EUR":
            raise ValueError(
                f"Moneda no soportada: '{currency}'. Solo se acepta 'EUR' en el MVP."
            )
        return instance

    def __add__(self, other: Money) -> Money:
        """Suma dos Money de la misma moneda."""
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden sumar monedas diferentes: {self.currency} y {other.currency}"
            )
        result = self.amount + other.amount
        # El resultado de una suma puede ser negativo si alguno de los operandos lo es
        if result < 0:
            return Money._create_allowing_negative(result, self.currency)
        return Money(result, self.currency)

    def __sub__(self, other: Money) -> Money:
        """Resta dos Money de la misma moneda. El resultado puede ser negativo."""
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden restar monedas diferentes: {self.currency} y {other.currency}"
            )
        result = self.amount - other.amount
        # La resta puede dar resultado negativo (beneficio neto negativo)
        if result < 0:
            return Money._create_allowing_negative(result, self.currency)
        return Money(result, self.currency)

    def __repr__(self) -> str:
        return f"Money({self.amount:.2f} {self.currency})"


@dataclass(frozen=True)
class Address:
    """Dirección postal completa de una propiedad.

    Inmutable: una vez creada, no se puede modificar.
    Igualdad por valor: dos direcciones con los mismos campos son iguales.
    """

    street: str
    city: str
    postal_code: str
    country: str = "ES"

    def __post_init__(self) -> None:
        # Validar que ningún campo esté vacío o solo contenga espacios
        if not self.street or not self.street.strip():
            raise ValueError("La calle (street) no puede estar vacía.")
        if not self.city or not self.city.strip():
            raise ValueError("La ciudad (city) no puede estar vacía.")
        if not self.postal_code or not self.postal_code.strip():
            raise ValueError("El código postal (postal_code) no puede estar vacío.")
        if not self.country or not self.country.strip():
            raise ValueError("El país (country) no puede estar vacío.")

    def __repr__(self) -> str:
        return f"Address({self.street}, {self.city}, {self.postal_code}, {self.country})"
