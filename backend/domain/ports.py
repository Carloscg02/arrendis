"""
Puertos (Interfaces) del dominio.

Los puertos son contratos abstractos que definen QUÉ necesita el dominio,
sin especificar CÓMO se implementa. Los adaptadores los implementan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from datetime import date
from backend.domain.entities import Expense, Income, Property, User, LeaseContract
from backend.domain.value_objects import CadastralBreakdown, AcquisitionCost, FiscalReport


class PropertyRepository(ABC):
    """Puerto de salida para persistir y recuperar Properties."""

    @abstractmethod
    def save(self, property: Property) -> None:
        """Guarda o actualiza una propiedad."""
        ...

    @abstractmethod
    def find_by_id(self, property_id: str) -> Property | None:
        """Busca una propiedad por su id. Retorna None si no existe."""
        ...

    @abstractmethod
    def find_by_name(self, name: str) -> Property | None:
        """Busca una propiedad por su nombre exacto. Retorna None si no existe."""
        ...

    @abstractmethod
    def list_properties(self, user_id: str) -> list[Property]:
        """Retorna todas las propiedades de un usuario."""
        ...

    @abstractmethod
    def delete(self, property_id: str) -> None:
        """Elimina una propiedad por su id."""
        ...

    @abstractmethod
    def update_image(self, property_id: str, image_filename: str | None) -> None:
        """Actualiza el nombre de archivo de imagen de una propiedad."""
        ...

    @abstractmethod
    def update_fiscal_data(
        self,
        property_id: str,
        cadastral_ref: str | None,
        cadastral_breakdown: CadastralBreakdown | None,
        acquisition_cost: AcquisitionCost | None,
        acquisition_date: date | None,
    ) -> None:
        """Actualiza los datos fiscales de una propiedad."""
        ...


class IncomeRepository(ABC):
    """Puerto de salida para persistir y recuperar Incomes."""

    @abstractmethod
    def save(self, income: Income) -> None:
        """Guarda un ingreso."""
        ...

    @abstractmethod
    def find_by_property_id(self, property_id: str) -> list[Income]:
        """Retorna todos los ingresos de una propiedad."""
        ...

    @abstractmethod
    def delete(self, income_id: str) -> None:
        """Elimina un ingreso por su id."""
        ...

    @abstractmethod
    def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
        """Actualiza la categoría fiscal de un registro."""
        ...


class ExpenseRepository(ABC):
    """Puerto de salida para persistir y recuperar Expenses."""

    @abstractmethod
    def save(self, expense: Expense) -> None:
        """Guarda un gasto."""
        ...

    @abstractmethod
    def find_by_property_id(self, property_id: str) -> list[Expense]:
        """Retorna todos los gastos de una propiedad."""
        ...

    @abstractmethod
    def delete(self, expense_id: str) -> None:
        """Elimina un gasto por su id."""
        ...

    @abstractmethod
    def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
        """Actualiza la categoría fiscal de un registro."""
        ...


class UserRepository(ABC):
    """Puerto de salida para persistir y recuperar Users."""
    @abstractmethod
    def save(self, user: User) -> None: ...
    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None: ...
    @abstractmethod
    def find_by_email(self, email: str) -> User | None: ...

class PasswordHasherPort(ABC):
    """Puerto de salida para hashear y verificar contraseñas."""
    @abstractmethod
    def hash(self, plain_password: str) -> str: ...
    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...

class TokenServicePort(ABC):
    """Puerto de salida para generar y verificar tokens JWT."""
    @abstractmethod
    def create_access_token(self, user_id: str) -> str: ...
    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str: ...
    @abstractmethod
    def verify_token(self, token: str) -> str | None: ...


class LeaseContractRepository(ABC):
    """Puerto de salida para persistir y recuperar LeaseContracts."""

    @abstractmethod
    def save(self, contract: LeaseContract) -> None:
        """Guarda o actualiza un contrato."""
        ...

    @abstractmethod
    def find_by_id(self, contract_id: str) -> LeaseContract | None:
        """Busca un contrato por su id. Retorna None si no existe."""
        ...

    @abstractmethod
    def find_by_property_id(self, property_id: str) -> list[LeaseContract]:
        """Retorna todos los contratos de una propiedad (ordenados por start_date desc)."""
        ...

    @abstractmethod
    def delete(self, contract_id: str) -> None:
        """Elimina un contrato por su id."""
        ...


class FiscalReportRendererPort(ABC):
    """Puerto de salida para renderizar un FiscalReport a un formato descargable.

    El dominio define QUÉ se renderiza (FiscalReport), pero no CÓMO.
    Cada adaptador concreto decide el formato (PDF, Excel, HTML, etc.).
    """

    @abstractmethod
    def render(self, report: FiscalReport, property_name: str, property_address: str) -> bytes:
        """Renderiza un FiscalReport a bytes."""
        ...

    @abstractmethod
    def content_type(self) -> str:
        """Retorna el MIME type del formato de salida (e.g., 'application/pdf')."""
        ...

    @abstractmethod
    def file_extension(self) -> str:
        """Retorna la extensión del archivo (e.g., 'pdf')."""
        ...

