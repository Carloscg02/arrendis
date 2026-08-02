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


@dataclass(frozen=True)
class Email:
    """Dirección de correo electrónico validada e inmutable."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or "@" not in self.value or "." not in self.value.split("@")[-1]:
            raise ValueError(f"Email no válido: '{self.value}'")
        object.__setattr__(self, "value", self.value.strip().lower())


@dataclass(frozen=True)
class PasswordHash:
    """Hash bcrypt de una contraseña. Nunca almacena texto plano."""
    hash_value: str

    def __post_init__(self) -> None:
        if not self.hash_value or not self.hash_value.startswith("$2b$"):
            raise ValueError("PasswordHash debe ser un hash bcrypt válido.")


@dataclass(frozen=True)
class CadastralBreakdown:
    """Desglose del valor catastral de un inmueble (del recibo del IBI)."""
    land_value: Decimal
    construction_value: Decimal

    def __post_init__(self) -> None:
        if self.land_value < 0:
            raise ValueError(f"El valor catastral del suelo no puede ser negativo: {self.land_value}")
        if self.construction_value < 0:
            raise ValueError(f"El valor catastral de la construcción no puede ser negativo: {self.construction_value}")
        if self.land_value == 0 and self.construction_value == 0:
            raise ValueError("El desglose catastral no puede ser todo ceros.")

    @property
    def total_value(self) -> Decimal:
        return self.land_value + self.construction_value


@dataclass(frozen=True)
class AcquisitionCost:
    """Coste total de adquisición de un inmueble."""
    purchase_price: Decimal
    construction_portion: Decimal
    land_portion: Decimal
    transfer_tax: Decimal
    notary_fees: Decimal
    registry_fees: Decimal

    def __post_init__(self) -> None:
        for field_name in ["purchase_price", "construction_portion", "land_portion",
                           "transfer_tax", "notary_fees", "registry_fees"]:
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} no puede ser negativo: {getattr(self, field_name)}")
        if self.purchase_price <= 0:
            raise ValueError("El precio de compraventa debe ser positivo.")
        total_portions = self.construction_portion + self.land_portion
        if total_portions != self.purchase_price:
            raise ValueError(
                f"construction_portion ({self.construction_portion}) + "
                f"land_portion ({self.land_portion}) = {total_portions}, "
                f"pero purchase_price es {self.purchase_price}. Deben coincidir."
            )

    @property
    def total_acquisition_expenses(self) -> Decimal:
        return self.transfer_tax + self.notary_fees + self.registry_fees

    @property
    def total_cost(self) -> Decimal:
        return self.purchase_price + self.total_acquisition_expenses


@dataclass(frozen=True)
class FiscalReport:
    """Resultado completo del cálculo fiscal para una propiedad en un año fiscal."""
    fiscal_year: int
    property_id: str

    # Rendimientos Íntegros
    gross_rental_income: Decimal
    other_income: Decimal
    total_income: Decimal

    # Ocupación
    rented_days: int
    total_days_in_year: int
    occupation_ratio: Decimal

    # Gastos Deducibles por Categoría (tras prorrateo)
    expenses_intereses: Decimal
    expenses_reparacion: Decimal
    expenses_tributos: Decimal
    expenses_seguros: Decimal
    expenses_suministros: Decimal
    expenses_formalizacion: Decimal
    expenses_dudoso_cobro: Decimal
    expenses_otros: Decimal

    # Tope Reparación + Intereses
    repair_interest_raw: Decimal
    repair_interest_cap: Decimal
    repair_interest_applied: Decimal
    repair_interest_excess: Decimal

    # Amortización
    amortization_base: Decimal
    amortization_rate: Decimal
    amortization_full_year: Decimal
    amortization_prorated: Decimal

    # Rendimiento Neto
    total_deductible_expenses: Decimal
    net_income_before_reduction: Decimal

    # Reducción por Vivienda Habitual
    vivienda_habitual_days: int
    vivienda_habitual_ratio: Decimal
    reduction_base: Decimal
    reduction_percentage: Decimal
    reduction_amount: Decimal

    # Resultado Final
    net_income_final: Decimal

    # Metadatos
    unclassified_income_count: int
    unclassified_expense_count: int
    has_warnings: bool
