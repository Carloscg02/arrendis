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

from backend.domain.value_objects import Address, Money


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
    status: PropertyStatus = PropertyStatus.AVAILABLE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # Validar que el nombre no esté vacío
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la propiedad (name) no puede estar vacío.")

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
