"""
Adaptador SQLite — implementación concreta de los puertos de persistencia.

Este módulo contiene las implementaciones de PropertyRepository, IncomeRepository
y ExpenseRepository usando SQLite como base de datos.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

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
from backend.domain.value_objects import Address, Money


class SQLiteConnection:
    """Gestiona la conexión a SQLite y la creación automática de tablas.

    Almacena Decimal como TEXT para mantener la precisión.
    Usa consultas parametrizadas (?) para prevenir inyección SQL.
    """

    def __init__(self, db_path: str = "data/rental.db") -> None:
        """Inicializa la conexión a la base de datos.

        Args:
            db_path: Ruta al archivo de base de datos SQLite.
                     Usar ":memory:" para bases de datos en memoria (tests).
        """
        self._db_path = db_path

        # Crear el directorio padre si no existe (excepto para :memory:)
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        # Activar claves foráneas
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        """Crea las tablas si no existen."""
        cursor = self._connection.cursor()

        # Tabla de propiedades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                street TEXT NOT NULL,
                city TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                country TEXT NOT NULL,
                property_type TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        # Migración: añadir columna image_filename si no existe
        try:
            cursor.execute("ALTER TABLE properties ADD COLUMN image_filename TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            pass  # La columna ya existe

        # Tabla de ingresos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incomes (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                currency TEXT NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        """)

        # Tabla de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                currency TEXT NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        """)

        self._connection.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        """Retorna la conexión activa."""
        return self._connection

    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        self._connection.close()


class SQLitePropertyRepository(PropertyRepository):
    """Implementación de PropertyRepository usando SQLite."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._conn = connection.connection

    def save(self, property: Property) -> None:
        """Guarda o actualiza una propiedad en la base de datos."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO properties
                (id, name, street, city, postal_code, country, property_type, status, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                property.id,
                property.name,
                property.address.street,
                property.address.city,
                property.address.postal_code,
                property.address.country,
                property.property_type.value,
                property.status.value,
                property.image_filename,
            ),
        )
        self._conn.commit()

    def find_by_id(self, property_id: str) -> Property | None:
        """Busca una propiedad por su id. Retorna None si no existe."""
        cursor = self._conn.execute(
            "SELECT * FROM properties WHERE id = ?",
            (property_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def find_by_name(self, name: str) -> Property | None:
        """Busca una propiedad por su nombre exacto. Retorna None si no existe."""
        cursor = self._conn.execute(
            "SELECT * FROM properties WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def find_all(self) -> list[Property]:
        """Retorna todas las propiedades."""
        cursor = self._conn.execute("SELECT * FROM properties")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def delete(self, property_id: str) -> None:
        """Elimina una propiedad por su id."""
        # Check if property has an image file and delete it
        cursor = self._conn.execute("SELECT image_filename FROM properties WHERE id = ?", (property_id,))
        row = cursor.fetchone()
        if row and row["image_filename"]:
            image_path = Path("data/images") / row["image_filename"]
            if image_path.exists():
                image_path.unlink()
        
        # Eliminar registros dependientes primero para evitar fallos de Foreign Key
        self._conn.execute("DELETE FROM incomes WHERE property_id = ?", (property_id,))
        self._conn.execute("DELETE FROM expenses WHERE property_id = ?", (property_id,))
        # Eliminar la propiedad
        self._conn.execute(
            "DELETE FROM properties WHERE id = ?",
            (property_id,),
        )
        self._conn.commit()

    def update_image(self, property_id: str, image_filename: str | None) -> None:
        """Actualiza el nombre de archivo de imagen de una propiedad."""
        self._conn.execute(
            "UPDATE properties SET image_filename = ? WHERE id = ?",
            (image_filename, property_id),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Property:
        """Convierte una fila de SQLite a una entidad Property."""
        return Property(
            id=row["id"],
            name=row["name"],
            address=Address(
                street=row["street"],
                city=row["city"],
                postal_code=row["postal_code"],
                country=row["country"],
            ),
            property_type=PropertyType(row["property_type"]),
            status=PropertyStatus(row["status"]),
            image_filename=row["image_filename"],
        )


class SQLiteIncomeRepository(IncomeRepository):
    """Implementación de IncomeRepository usando SQLite."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._conn = connection.connection

    def save(self, income: Income) -> None:
        """Guarda un ingreso en la base de datos."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO incomes
                (id, property_id, amount, currency, date, category, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                income.id,
                income.property_id,
                str(income.amount.amount),  # Decimal → TEXT para precisión
                income.amount.currency,
                income.date.isoformat(),
                income.category.value,
                income.description,
            ),
        )
        self._conn.commit()

    def find_by_property_id(self, property_id: str) -> list[Income]:
        """Retorna todos los ingresos de una propiedad."""
        cursor = self._conn.execute(
            "SELECT * FROM incomes WHERE property_id = ?",
            (property_id,),
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def delete(self, income_id: str) -> None:
        """Elimina un ingreso por su id."""
        self._conn.execute(
            "DELETE FROM incomes WHERE id = ?",
            (income_id,),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Income:
        """Convierte una fila de SQLite a una entidad Income."""
        return Income(
            id=row["id"],
            property_id=row["property_id"],
            amount=Money(Decimal(row["amount"]), row["currency"]),
            date=date.fromisoformat(row["date"]),
            category=IncomeCategory(row["category"]),
            description=row["description"],
        )


class SQLiteExpenseRepository(ExpenseRepository):
    """Implementación de ExpenseRepository usando SQLite."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._conn = connection.connection

    def save(self, expense: Expense) -> None:
        """Guarda un gasto en la base de datos."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO expenses
                (id, property_id, amount, currency, date, category, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense.id,
                expense.property_id,
                str(expense.amount.amount),  # Decimal → TEXT para precisión
                expense.amount.currency,
                expense.date.isoformat(),
                expense.category.value,
                expense.description,
            ),
        )
        self._conn.commit()

    def find_by_property_id(self, property_id: str) -> list[Expense]:
        """Retorna todos los gastos de una propiedad."""
        cursor = self._conn.execute(
            "SELECT * FROM expenses WHERE property_id = ?",
            (property_id,),
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def delete(self, expense_id: str) -> None:
        """Elimina un gasto por su id."""
        self._conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Expense:
        """Convierte una fila de SQLite a una entidad Expense."""
        return Expense(
            id=row["id"],
            property_id=row["property_id"],
            amount=Money(Decimal(row["amount"]), row["currency"]),
            date=date.fromisoformat(row["date"]),
            category=ExpenseCategory(row["category"]),
            description=row["description"],
        )
