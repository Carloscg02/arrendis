"""
Entidades y Enumeraciones del dominio.

Las Entidades tienen identidad propia (UUID4). Dos entidades con el mismo id
son la misma entidad, aunque sus demás campos difieran.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from backend.domain.value_objects import Address, Email, Money, PasswordHash, CadastralBreakdown, AcquisitionCost


# ──────────────────────────────────────────────
# Enumeraciones
# ──────────────────────────────────────────────

class PropertyType(Enum):
    """Clasificación del tipo de propiedad."""
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    GARAGE = "garage"
    LAND = "land"


class PropertyStatus(Enum):
    """Estado actual de una propiedad."""
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"


class IncomeCategory(Enum):
    """Categoría de un ingreso."""
    RENT = "rent"
    DEPOSIT = "deposit"
    OTHER = "other"


class ExpenseCategory(Enum):
    """Categoría de un gasto."""
    REPAIR = "repair"
    TAX = "tax"
    INSURANCE = "insurance"
    COMMUNITY_FEE = "community_fee"
    MORTGAGE = "mortgage"
    UTILITY = "utility"
    OTHER = "other"


class LeaseType(Enum):
    """Clasificación fiscal del tipo de arrendamiento."""
    VIVIENDA_HABITUAL = "vivienda_habitual"
    TEMPORAL = "temporal"
    TURISTICO = "turistico"
    COMERCIAL = "comercial"


class FiscalExpenseCategory(Enum):
    """Clasificación fiscal del gasto según partidas AEAT (Capital Inmobiliario)."""
    INTERESES_CAPITAL = "intereses_capital"
    REPARACION_CONSERVACION = "reparacion_conservacion"
    TRIBUTOS = "tributos"
    PRIMAS_SEGUROS = "primas_seguros"
    SERVICIOS_SUMINISTROS = "servicios_suministros"
    FORMALIZACION = "formalizacion"
    DUDOSO_COBRO = "dudoso_cobro"
    OTROS_DEDUCIBLES = "otros_deducibles"
    NO_DEDUCIBLE = "no_deducible"


class FiscalIncomeCategory(Enum):
    """Clasificación fiscal del ingreso según AEAT."""
    RENDIMIENTO_INTEGRO = "rendimiento_integro"
    OTROS_INGRESOS = "otros_ingresos"


# ──────────────────────────────────────────────
# Entidades
# ──────────────────────────────────────────────

@dataclass
class Property:
    """Representa un inmueble que se alquila para obtener ingresos.

    Identidad basada en el campo `id` (UUID4).
    """

    name: str
    address: Address
    property_type: PropertyType
    user_id: str
    status: PropertyStatus = PropertyStatus.AVAILABLE
    image_filename: str | None = None
    cadastral_ref: str | None = None
    cadastral_breakdown: CadastralBreakdown | None = None
    acquisition_cost: AcquisitionCost | None = None
    acquisition_date: date | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # Validar que el nombre no esté vacío
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la propiedad (name) no puede estar vacío.")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("El user_id del propietario no puede estar vacío.")
        if self.cadastral_ref is not None:
            ref = self.cadastral_ref.strip()
            if len(ref) != 20:
                raise ValueError(
                    f"La referencia catastral debe tener 20 caracteres, tiene {len(ref)}."
                )

    @property
    def has_fiscal_data(self) -> bool:
        return (
            self.cadastral_breakdown is not None
            and self.acquisition_cost is not None
            and self.acquisition_date is not None
        )

    def __eq__(self, other: object) -> bool:
        """Igualdad basada en identidad (id)."""
        if not isinstance(other, Property):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Tenant:
    """Representa un inquilino que alquila una propiedad.

    Identidad basada en el campo `id` (UUID4).
    """

    first_name: str
    last_name: str
    email: str
    phone: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # Validar nombre y apellido
        if not self.first_name or not self.first_name.strip():
            raise ValueError("El nombre (first_name) no puede estar vacío.")
        if not self.last_name or not self.last_name.strip():
            raise ValueError("El apellido (last_name) no puede estar vacío.")
        # Validación básica del email: debe contener @
        if "@" not in self.email:
            raise ValueError(
                f"El email no es válido (debe contener '@'): '{self.email}'"
            )

    def __eq__(self, other: object) -> bool:
        """Igualdad basada en identidad (id)."""
        if not isinstance(other, Tenant):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Income:
    """Representa un ingreso vinculado a una propiedad.

    Identidad basada en el campo `id` (UUID4).
    """

    property_id: str
    amount: Money
    date: date
    category: IncomeCategory
    description: str = ""
    fiscal_category: FiscalIncomeCategory | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # Validar que property_id no esté vacío
        if not self.property_id or not self.property_id.strip():
            raise ValueError(
                "El identificador de propiedad (property_id) no puede estar vacío."
            )

    def __eq__(self, other: object) -> bool:
        """Igualdad basada en identidad (id)."""
        if not isinstance(other, Income):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Expense:
    """Representa un gasto vinculado a una propiedad.

    Identidad basada en el campo `id` (UUID4).
    """

    property_id: str
    amount: Money
    date: date
    category: ExpenseCategory
    description: str = ""
    fiscal_category: FiscalExpenseCategory | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # Validar que property_id no esté vacío
        if not self.property_id or not self.property_id.strip():
            raise ValueError(
                "El identificador de propiedad (property_id) no puede estar vacío."
            )

    def __eq__(self, other: object) -> bool:
        """Igualdad basada en identidad (id)."""
        if not isinstance(other, Expense):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class User:
    """Representa un usuario registrado en la plataforma."""
    email: Email
    password_hash: PasswordHash
    username: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.username or not self.username.strip():
            raise ValueError("El nombre de usuario (username) no puede estar vacío.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class LeaseContract:
    """Contrato de arrendamiento de un inmueble.

    Identidad basada en el campo `id` (UUID4).
    Un contrato vincula una propiedad con un inquilino durante un periodo.
    """
    property_id: str
    tenant_name: str
    tenant_nif: str
    start_date: date
    monthly_rent: Money
    lease_type: LeaseType
    end_date: date | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.property_id or not self.property_id.strip():
            raise ValueError("El property_id no puede estar vacío.")
        if not self.tenant_name or not self.tenant_name.strip():
            raise ValueError("El nombre del inquilino no puede estar vacío.")
        if not self.tenant_nif or not self.tenant_nif.strip():
            raise ValueError("El NIF del inquilino no puede estar vacío.")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError(
                f"La fecha de fin ({self.end_date}) no puede ser anterior "
                f"a la fecha de inicio ({self.start_date})."
            )

    @property
    def is_active(self) -> bool:
        if self.end_date is None:
            return True
        return self.end_date >= date.today()

    def rented_days_in_year(self, fiscal_year: int) -> int:
        year_start = date(fiscal_year, 1, 1)
        year_end = date(fiscal_year, 12, 31)
        effective_start = max(self.start_date, year_start)
        effective_end = min(self.end_date or year_end, year_end)
        if effective_start > effective_end:
            return 0
        return (effective_end - effective_start).days + 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LeaseContract):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
