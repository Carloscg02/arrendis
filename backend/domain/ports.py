"""
Puertos (Interfaces) del dominio.

Los puertos son contratos abstractos que definen QUÉ necesita el dominio,
sin especificar CÓMO se implementa. Los adaptadores los implementan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.domain.entities import Expense, Income, Property


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
    def find_all(self) -> list[Property]:
        """Retorna todas las propiedades."""
        ...

    @abstractmethod
    def delete(self, property_id: str) -> None:
        """Elimina una propiedad por su id."""
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
