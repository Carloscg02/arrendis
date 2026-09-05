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
    FiscalExpenseCategory,
    Income,
    IncomeCategory,
    FiscalIncomeCategory,
    Property,
    PropertyStatus,
    PropertyType,
    User,
    LeaseContract,
    LeaseType,
    FiscalCarryforward,
)
from backend.domain.ports import ExpenseRepository, IncomeRepository, PropertyRepository, UserRepository, LeaseContractRepository, FiscalCarryforwardRepository
from backend.domain.value_objects import Address, Money, Email, PasswordHash, CadastralBreakdown, AcquisitionCost


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

        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

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
                user_id TEXT NOT NULL DEFAULT 'system',
                status TEXT NOT NULL
            )
        """)
        # Migración: añadir columna image_filename y user_id si no existen
        try:
            cursor.execute("ALTER TABLE properties ADD COLUMN image_filename TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            pass  # La columna ya existe
            
        try:
            cursor.execute("ALTER TABLE properties ADD COLUMN user_id TEXT NOT NULL DEFAULT 'system'")
        except sqlite3.OperationalError:
            pass  # La columna ya existe

        # Migración F-09: columnas fiscales
        for col in [
            "cadastral_ref TEXT DEFAULT NULL",
            "cadastral_land_value TEXT DEFAULT NULL",
            "cadastral_construction_value TEXT DEFAULT NULL",
            "acquisition_purchase_price TEXT DEFAULT NULL",
            "acquisition_construction_portion TEXT DEFAULT NULL",
            "acquisition_land_portion TEXT DEFAULT NULL",
            "acquisition_transfer_tax TEXT DEFAULT NULL",
            "acquisition_notary_fees TEXT DEFAULT NULL",
            "acquisition_registry_fees TEXT DEFAULT NULL",
            "acquisition_date TEXT DEFAULT NULL",
        ]:
            try:
                cursor.execute(f"ALTER TABLE properties ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass  # La columna ya existe

        # Migración F-16: Suministros (Propiedades)
        for col in [
            "cups_electricity TEXT DEFAULT NULL",
            "cups_gas TEXT DEFAULT NULL",
            "cups_water TEXT DEFAULT NULL",
        ]:
            try:
                cursor.execute(f"ALTER TABLE properties ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass

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

        # Migración F-16: Suministros (Gastos)
        for col in [
            "is_verified INTEGER NOT NULL DEFAULT 1",
            "source TEXT NOT NULL DEFAULT 'manual'",
            "receipt_path TEXT DEFAULT NULL",
            "utility_cups TEXT DEFAULT NULL",
            "utility_amount TEXT DEFAULT NULL",
            "utility_issue_date TEXT DEFAULT NULL",
            "utility_provider_name TEXT DEFAULT NULL",
            "utility_type TEXT DEFAULT NULL",
            "utility_invoice_number TEXT DEFAULT NULL",
            "utility_extraction_confidence TEXT DEFAULT NULL",
        ]:
            try:
                cursor.execute(f"ALTER TABLE expenses ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass

        # Tabla de contratos de arrendamiento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lease_contracts (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                tenant_name TEXT NOT NULL,
                tenant_nif TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT DEFAULT NULL,
                monthly_rent_amount TEXT NOT NULL,
                monthly_rent_currency TEXT NOT NULL DEFAULT 'EUR',
                lease_type TEXT NOT NULL,
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        """)

        # Cleanup query to self-heal any corrupted cadastral_ref with length != 20
        cursor.execute(
            """
            UPDATE properties
            SET cadastral_ref = NULL
            WHERE cadastral_ref IS NOT NULL
              AND length(trim(cadastral_ref)) != 20
            """
        )

        # Migración F-11: clasificación fiscal
        try:
            cursor.execute("ALTER TABLE incomes ADD COLUMN fiscal_category TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN fiscal_category TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            pass

        # Tabla de excesos pendientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fiscal_carryforwards (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                year_generated INTEGER NOT NULL,
                original_amount TEXT NOT NULL,
                amount_applied TEXT NOT NULL DEFAULT '0',
                FOREIGN KEY (property_id) REFERENCES properties(id),
                UNIQUE(property_id, year_generated)
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
                (id, name, street, city, postal_code, country, property_type, user_id, status, image_filename,
                 cadastral_ref, cadastral_land_value, cadastral_construction_value,
                 acquisition_purchase_price, acquisition_construction_portion, acquisition_land_portion,
                 acquisition_transfer_tax, acquisition_notary_fees, acquisition_registry_fees, acquisition_date,
                 cups_electricity, cups_gas, cups_water)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                property.id,
                property.name,
                property.address.street,
                property.address.city,
                property.address.postal_code,
                property.address.country,
                property.property_type.value,
                property.user_id,
                property.status.value,
                property.image_filename,
                property.cadastral_ref,
                str(property.cadastral_breakdown.land_value) if property.cadastral_breakdown else None,
                str(property.cadastral_breakdown.construction_value) if property.cadastral_breakdown else None,
                str(property.acquisition_cost.purchase_price) if property.acquisition_cost else None,
                str(property.acquisition_cost.construction_portion) if property.acquisition_cost else None,
                str(property.acquisition_cost.land_portion) if property.acquisition_cost else None,
                str(property.acquisition_cost.transfer_tax) if property.acquisition_cost else None,
                str(property.acquisition_cost.notary_fees) if property.acquisition_cost else None,
                str(property.acquisition_cost.registry_fees) if property.acquisition_cost else None,
                property.acquisition_date.isoformat() if property.acquisition_date else None,
                property.cups_electricity,
                property.cups_gas,
                property.cups_water,
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

    def list_properties(self, user_id: str) -> list[Property]:
        """Retorna todas las propiedades de un usuario."""
        cursor = self._conn.execute("SELECT * FROM properties WHERE user_id = ?", (user_id,))
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
        self._conn.execute("DELETE FROM lease_contracts WHERE property_id = ?", (property_id,))
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

    def update_cups(self, property_id: str, cups_electricity: str | None, cups_gas: str | None, cups_water: str | None) -> None:
        """Actualiza los CUPS de una propiedad."""
        self._conn.execute(
            "UPDATE properties SET cups_electricity = ?, cups_gas = ?, cups_water = ? WHERE id = ?",
            (cups_electricity, cups_gas, cups_water, property_id),
        )
        self._conn.commit()

    def find_by_cups(self, cups: str, user_id: str) -> Property | None:
        """Busca una propiedad de un usuario por cualquiera de sus CUPS."""
        cursor = self._conn.execute(
            """
            SELECT * FROM properties 
            WHERE user_id = ? AND 
                  (cups_electricity = ? OR cups_gas = ? OR cups_water = ?)
            """,
            (user_id, cups, cups, cups),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def update_fiscal_data(
        self,
        property_id: str,
        cadastral_ref: str | None,
        cadastral_breakdown: CadastralBreakdown | None,
        acquisition_cost: AcquisitionCost | None,
        acquisition_date: date | None,
    ) -> None:
        """Actualiza los datos fiscales de una propiedad en la base de datos."""
        self._conn.execute(
            """
            UPDATE properties SET
                cadastral_ref = ?,
                cadastral_land_value = ?,
                cadastral_construction_value = ?,
                acquisition_purchase_price = ?,
                acquisition_construction_portion = ?,
                acquisition_land_portion = ?,
                acquisition_transfer_tax = ?,
                acquisition_notary_fees = ?,
                acquisition_registry_fees = ?,
                acquisition_date = ?
            WHERE id = ?
            """,
            (
                cadastral_ref,
                str(cadastral_breakdown.land_value) if cadastral_breakdown else None,
                str(cadastral_breakdown.construction_value) if cadastral_breakdown else None,
                str(acquisition_cost.purchase_price) if acquisition_cost else None,
                str(acquisition_cost.construction_portion) if acquisition_cost else None,
                str(acquisition_cost.land_portion) if acquisition_cost else None,
                str(acquisition_cost.transfer_tax) if acquisition_cost else None,
                str(acquisition_cost.notary_fees) if acquisition_cost else None,
                str(acquisition_cost.registry_fees) if acquisition_cost else None,
                acquisition_date.isoformat() if acquisition_date else None,
                property_id,
            ),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Property:
        """Convierte una fila de SQLite a una entidad Property."""
        # Reconstruir CadastralBreakdown si hay datos
        cadastral_breakdown = None
        if row["cadastral_land_value"] is not None and row["cadastral_construction_value"] is not None:
            cadastral_breakdown = CadastralBreakdown(
                land_value=Decimal(row["cadastral_land_value"]),
                construction_value=Decimal(row["cadastral_construction_value"]),
            )

        # Reconstruir AcquisitionCost si hay datos
        acquisition_cost = None
        if row["acquisition_purchase_price"] is not None:
            acquisition_cost = AcquisitionCost(
                purchase_price=Decimal(row["acquisition_purchase_price"]),
                construction_portion=Decimal(row["acquisition_construction_portion"]),
                land_portion=Decimal(row["acquisition_land_portion"]),
                transfer_tax=Decimal(row["acquisition_transfer_tax"]),
                notary_fees=Decimal(row["acquisition_notary_fees"]),
                registry_fees=Decimal(row["acquisition_registry_fees"]),
            )

        # Reconstruir acquisition_date
        acquisition_date = None
        if row["acquisition_date"] is not None:
            acquisition_date = date.fromisoformat(row["acquisition_date"])

        cadastral_ref = row["cadastral_ref"]
        if cadastral_ref is not None:
            cadastral_ref = cadastral_ref.strip()
            if len(cadastral_ref) != 20:
                cadastral_ref = None

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
            user_id=row["user_id"],
            status=PropertyStatus(row["status"]),
            image_filename=row["image_filename"],
            cadastral_ref=cadastral_ref,
            cadastral_breakdown=cadastral_breakdown,
            acquisition_cost=acquisition_cost,
            acquisition_date=acquisition_date,
            cups_electricity=row["cups_electricity"],
            cups_gas=row["cups_gas"],
            cups_water=row["cups_water"],
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
                (id, property_id, amount, currency, date, category, description, fiscal_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                income.id,
                income.property_id,
                str(income.amount.amount),  # Decimal → TEXT para precisión
                income.amount.currency,
                income.date.isoformat(),
                income.category.value,
                income.description,
                income.fiscal_category.value if income.fiscal_category else None,
            ),
        )
        self._conn.commit()

    def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
        self._conn.execute(
            "UPDATE incomes SET fiscal_category = ? WHERE id = ?",
            (fiscal_category, record_id),
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
        fiscal_category = None
        try:
            if row["fiscal_category"]:
                fiscal_category = FiscalIncomeCategory(row["fiscal_category"])
        except IndexError:
            pass

        return Income(
            id=row["id"],
            property_id=row["property_id"],
            amount=Money(Decimal(row["amount"]), row["currency"]),
            date=date.fromisoformat(row["date"]),
            category=IncomeCategory(row["category"]),
            description=row["description"],
            fiscal_category=fiscal_category,
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
                (id, property_id, amount, currency, date, category, description, fiscal_category,
                 is_verified, source, receipt_path, utility_cups, utility_amount, utility_issue_date,
                 utility_provider_name, utility_type, utility_invoice_number, utility_extraction_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense.id,
                expense.property_id,
                str(expense.amount.amount),  # Decimal → TEXT para precisión
                expense.amount.currency,
                expense.date.isoformat(),
                expense.category.value,
                expense.description,
                expense.fiscal_category.value if expense.fiscal_category else None,
                1 if expense.is_verified else 0,
                expense.source.value,
                expense.receipt_path,
                expense.utility_data.cups if expense.utility_data else None,
                str(expense.utility_data.amount) if expense.utility_data else None,
                expense.utility_data.issue_date.isoformat() if expense.utility_data else None,
                expense.utility_data.provider_name if expense.utility_data else None,
                expense.utility_data.utility_type.value if expense.utility_data else None,
                expense.utility_data.invoice_number if expense.utility_data else None,
                expense.utility_data.extraction_confidence.value if expense.utility_data else None,
            ),
        )
        self._conn.commit()

    def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
        self._conn.execute(
            "UPDATE expenses SET fiscal_category = ? WHERE id = ?",
            (fiscal_category, record_id),
        )
        self._conn.commit()

    def find_by_property_id(self, property_id: str) -> list[Expense]:
        """Retorna todos los gastos de una propiedad."""
        cursor = self._conn.execute(
            "SELECT * FROM expenses WHERE property_id = ?",
            (property_id,),
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def find_by_id(self, expense_id: str) -> Expense | None:
        """Busca un gasto por su id."""
        cursor = self._conn.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

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
        fiscal_category = None
        try:
            if row["fiscal_category"]:
                fiscal_category = FiscalExpenseCategory(row["fiscal_category"])
        except IndexError:
            pass

        from backend.domain.entities import ExpenseSource
        from backend.domain.value_objects import UtilityInvoiceData
        from backend.domain.entities import UtilityType, ExtractionConfidence

        utility_data = None
        try:
            if row["utility_cups"] is not None:
                utility_data = UtilityInvoiceData(
                    cups=row["utility_cups"],
                    amount=Decimal(row["utility_amount"]),
                    issue_date=date.fromisoformat(row["utility_issue_date"]),
                    provider_name=row["utility_provider_name"],
                    utility_type=UtilityType(row["utility_type"]),
                    invoice_number=row["utility_invoice_number"],
                    extraction_confidence=ExtractionConfidence(row["utility_extraction_confidence"]),
                )
        except IndexError:
            pass
            
        try:
            is_verified = bool(row["is_verified"])
            source = ExpenseSource(row["source"])
            receipt_path = row["receipt_path"]
        except IndexError:
            is_verified = True
            source = ExpenseSource.MANUAL
            receipt_path = None

        return Expense(
            id=row["id"],
            property_id=row["property_id"],
            amount=Money(Decimal(row["amount"]), row["currency"]),
            date=date.fromisoformat(row["date"]),
            category=ExpenseCategory(row["category"]),
            description=row["description"],
            fiscal_category=fiscal_category,
            is_verified=is_verified,
            source=source,
            receipt_path=receipt_path,
            utility_data=utility_data,
        )


class SQLiteUserRepository(UserRepository):
    """Implementación de UserRepository usando SQLite."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._conn = connection.connection

    def save(self, user: User) -> None:
        """Guarda un usuario en la base de datos."""
        try:
            self._conn.execute(
                """
                INSERT INTO users (id, email, username, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email.value,
                    user.username,
                    user.password_hash.hash_value,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.email" in str(e):
                raise ValueError("Ya existe un usuario con ese email.")
            raise

    def find_by_id(self, user_id: str) -> User | None:
        """Busca un usuario por su id."""
        cursor = self._conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def find_by_email(self, email: str) -> User | None:
        """Busca un usuario por su email."""
        cursor = self._conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower(),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> User:
        """Convierte una fila de SQLite a una entidad User."""
        return User(
            id=row["id"],
            email=Email(row["email"]),
            username=row["username"],
            password_hash=PasswordHash(row["password_hash"]),
        )


class SQLiteLeaseContractRepository(LeaseContractRepository):
    """Implementación de LeaseContractRepository usando SQLite."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._conn = connection.connection

    def save(self, contract: LeaseContract) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO lease_contracts
                (id, property_id, tenant_name, tenant_nif, start_date, end_date,
                 monthly_rent_amount, monthly_rent_currency, lease_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract.id,
                contract.property_id,
                contract.tenant_name,
                contract.tenant_nif,
                contract.start_date.isoformat(),
                contract.end_date.isoformat() if contract.end_date else None,
                str(contract.monthly_rent.amount),
                contract.monthly_rent.currency,
                contract.lease_type.value,
            )
        )
        self._conn.commit()

    def find_by_id(self, contract_id: str) -> LeaseContract | None:
        cursor = self._conn.execute(
            "SELECT * FROM lease_contracts WHERE id = ?",
            (contract_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def find_by_property_id(self, property_id: str) -> list[LeaseContract]:
        cursor = self._conn.execute(
            "SELECT * FROM lease_contracts WHERE property_id = ? ORDER BY start_date DESC",
            (property_id,)
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def delete(self, contract_id: str) -> None:
        self._conn.execute("DELETE FROM lease_contracts WHERE id = ?", (contract_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> LeaseContract:
        end_date = None
        if row["end_date"]:
            end_date = date.fromisoformat(row["end_date"])
        return LeaseContract(
            id=row["id"],
            property_id=row["property_id"],
            tenant_name=row["tenant_name"],
            tenant_nif=row["tenant_nif"],
            start_date=date.fromisoformat(row["start_date"]),
            end_date=end_date,
            monthly_rent=Money(Decimal(row["monthly_rent_amount"]), row["monthly_rent_currency"]),
            lease_type=LeaseType(row["lease_type"]),
        )


class SQLiteFiscalCarryforwardRepository(FiscalCarryforwardRepository):
    """Implementación de FiscalCarryforwardRepository usando SQLite."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._conn = connection.connection

    def save(self, carryforward: FiscalCarryforward) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO fiscal_carryforwards
                (id, property_id, year_generated, original_amount, amount_applied)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                carryforward.id,
                carryforward.property_id,
                carryforward.year_generated,
                str(carryforward.original_amount),
                str(carryforward.amount_applied),
            )
        )
        self._conn.commit()

    def find_by_property_and_year(self, property_id: str, year_generated: int) -> FiscalCarryforward | None:
        cursor = self._conn.execute(
            "SELECT * FROM fiscal_carryforwards WHERE property_id = ? AND year_generated = ?",
            (property_id, year_generated)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def find_available_for_year(self, property_id: str, fiscal_year: int) -> list[FiscalCarryforward]:
        # Según la ley, los excesos caducan a los 4 años. 
        # Entonces year_generated >= fiscal_year - 4, y year_generated < fiscal_year
        cursor = self._conn.execute(
            """
            SELECT * FROM fiscal_carryforwards 
            WHERE property_id = ? 
              AND year_generated >= ? 
              AND year_generated < ?
            ORDER BY year_generated ASC
            """,
            (property_id, fiscal_year - 4, fiscal_year)
        )
        carryforwards = [self._row_to_entity(row) for row in cursor.fetchall()]
        # Filtrar solo los que tienen saldo
        return [cf for cf in carryforwards if cf.amount_remaining > 0]

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> FiscalCarryforward:
        return FiscalCarryforward(
            id=row["id"],
            property_id=row["property_id"],
            year_generated=row["year_generated"],
            original_amount=Decimal(row["original_amount"]),
            amount_applied=Decimal(row["amount_applied"]),
        )
