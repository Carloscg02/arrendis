"""
Casos de Uso (Application Layer).

Los casos de uso orquestan las operaciones de negocio. Reciben datos primitivos,
crean entidades y value objects internamente, y llaman a los repositorios (puertos).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.domain.entities import (
    Expense,
    ExpenseCategory,
    Income,
    IncomeCategory,
    Property,
    PropertyStatus,
    PropertyType,
)
from backend.domain.ports import ExpenseRepository, IncomeRepository, PropertyRepository
from backend.domain.services import ProfitCalculator
from backend.domain.value_objects import Address, Money


class CreatePropertyUseCase:
    """Caso de uso: crear y persistir una nueva propiedad."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(
        self,
        name: str,
        street: str,
        city: str,
        postal_code: str,
        country: str,
        property_type: str,
    ) -> Property:
        """Crea una Property con los datos proporcionados y la persiste.

        Args:
            name: Nombre descriptivo de la propiedad.
            street: Calle de la dirección.
            city: Ciudad.
            postal_code: Código postal.
            country: País (por defecto "ES").
            property_type: Tipo de propiedad (valor del enum PropertyType).

        Returns:
            La Property creada.
        """
        # Crear value objects
        address = Address(
            street=street,
            city=city,
            postal_code=postal_code,
            country=country,
        )

        # Crear la entidad
        prop = Property(
            name=name,
            address=address,
            property_type=PropertyType(property_type),
            status=PropertyStatus.AVAILABLE,
        )

        # Persistir
        self._property_repo.save(prop)

        return prop


class ListPropertiesUseCase:
    """Caso de uso: devolver todas las propiedades."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(self) -> list[Property]:
        """Retorna todas las propiedades registradas."""
        return self._property_repo.find_all()


class RecordIncomeUseCase:
    """Caso de uso: registrar un ingreso vinculado a una propiedad."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo

    def execute(
        self,
        property_id: str,
        amount: Decimal,
        income_date: date,
        category: str,
        description: str = "",
    ) -> Income:
        """Registra un ingreso para una propiedad existente.

        Args:
            property_id: ID de la propiedad asociada.
            amount: Importe del ingreso (Decimal).
            income_date: Fecha del ingreso.
            category: Categoría del ingreso (valor del enum IncomeCategory).
            description: Descripción opcional.

        Returns:
            El Income creado.

        Raises:
            ValueError: Si la propiedad no existe.
        """
        # Validar que la propiedad exista
        prop = self._property_repo.find_by_id(property_id)
        if prop is None:
            raise ValueError(
                f"No existe la propiedad con id '{property_id}'."
            )

        # Crear la entidad
        income = Income(
            property_id=property_id,
            amount=Money(amount, "EUR"),
            date=income_date,
            category=IncomeCategory(category),
            description=description,
        )

        # Persistir
        self._income_repo.save(income)

        return income


class RecordExpenseUseCase:
    """Caso de uso: registrar un gasto vinculado a una propiedad."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        expense_repo: ExpenseRepository,
    ) -> None:
        self._property_repo = property_repo
        self._expense_repo = expense_repo

    def execute(
        self,
        property_id: str,
        amount: Decimal,
        expense_date: date,
        category: str,
        description: str = "",
    ) -> Expense:
        """Registra un gasto para una propiedad existente.

        Args:
            property_id: ID de la propiedad asociada.
            amount: Importe del gasto (Decimal).
            expense_date: Fecha del gasto.
            category: Categoría del gasto (valor del enum ExpenseCategory).
            description: Descripción opcional.

        Returns:
            El Expense creado.

        Raises:
            ValueError: Si la propiedad no existe.
        """
        # Validar que la propiedad exista
        prop = self._property_repo.find_by_id(property_id)
        if prop is None:
            raise ValueError(
                f"No existe la propiedad con id '{property_id}'."
            )

        # Crear la entidad
        expense = Expense(
            property_id=property_id,
            amount=Money(amount, "EUR"),
            date=expense_date,
            category=ExpenseCategory(category),
            description=description,
        )

        # Persistir
        self._expense_repo.save(expense)

        return expense


class GetPropertyProfitReportUseCase:
    """Caso de uso: calcular el beneficio neto de una propiedad."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
        expense_repo: ExpenseRepository,
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo

    def execute(self, property_id: str) -> Money:
        """Calcula el Net Profit de una propiedad.

        Args:
            property_id: ID de la propiedad.

        Returns:
            Money con el beneficio neto (puede ser negativo).

        Raises:
            ValueError: Si la propiedad no existe.
        """
        # Validar que la propiedad exista
        prop = self._property_repo.find_by_id(property_id)
        if prop is None:
            raise ValueError(
                f"No existe la propiedad con id '{property_id}'."
            )

        # Obtener ingresos y gastos
        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)

        # Delegar el cálculo al servicio de dominio
        return ProfitCalculator.calculate_net_profit(incomes, expenses)
