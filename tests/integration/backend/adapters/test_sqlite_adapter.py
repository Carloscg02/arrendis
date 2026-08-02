"""
Tests de integración para adaptadores SQLite.

DB-01 a DB-06: persistencia real con SQLite :memory:.
"""

from datetime import date
from decimal import Decimal

from backend.adapters.sqlite_adapter import (
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
    SQLiteLeaseContractRepository,
)
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
    LeaseContract,
    LeaseType,
)
from backend.domain.value_objects import Address, Money


def test_save_and_find_property(sqlite_connection):
    """DB-01: Guardar una propiedad y recuperarla por id."""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Centro",
        address=Address("Calle Mayor 15", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id="user-db",
        id="prop-db-001",
    )
    repo.save(prop)
    found = repo.find_by_id("prop-db-001")
    assert found is not None
    assert found.name == "Piso Centro"
    assert found.address.street == "Calle Mayor 15"
    assert found.property_type == PropertyType.APARTMENT
    assert found.status == PropertyStatus.AVAILABLE


def test_find_all_properties(sqlite_connection):
    """DB-02: Guardar 3 propiedades y recuperar todas."""
    repo = SQLitePropertyRepository(sqlite_connection)
    for i in range(3):
        prop = Property(
            name=f"Propiedad {i}",
            address=Address(f"Calle {i}", "Madrid", "28001", "ES"),
            property_type=PropertyType.APARTMENT,
            user_id="user-db",
            id=f"prop-db-{i}",
        )
        repo.save(prop)
    all_props = repo.list_properties("user-db")
    assert len(all_props) == 3


def test_delete_property(sqlite_connection):
    """DB-03: Guardar y eliminar una propiedad."""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Para borrar",
        address=Address("Calle Z", "Barcelona", "08001", "ES"),
        property_type=PropertyType.HOUSE,
        user_id="user-db",
        id="prop-delete-001",
    )
    repo.save(prop)
    assert repo.find_by_id("prop-delete-001") is not None
    repo.delete("prop-delete-001")
    assert repo.find_by_id("prop-delete-001") is None


def test_save_and_find_income(sqlite_connection):
    """DB-04: Guardar un ingreso y recuperarlo por property_id."""
    # Primero crear la propiedad (FK)
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Ingresos",
        address=Address("Calle A", "Madrid", "28001", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id="user-db",
        id="prop-income-001",
    )
    prop_repo.save(prop)

    # Guardar ingreso
    income_repo = SQLiteIncomeRepository(sqlite_connection)
    income = Income(
        property_id="prop-income-001",
        amount=Money(Decimal("750.00"), "EUR"),
        date=date(2026, 7, 1),
        category=IncomeCategory.RENT,
        description="Alquiler julio",
        id="income-001",
    )
    income_repo.save(income)

    # Recuperar
    found = income_repo.find_by_property_id("prop-income-001")
    assert len(found) == 1
    assert found[0].amount.amount == Decimal("750.00")
    assert found[0].category == IncomeCategory.RENT
    assert found[0].date == date(2026, 7, 1)


def test_save_and_find_expense(sqlite_connection):
    """DB-05: Guardar un gasto y recuperarlo por property_id."""
    # Primero crear la propiedad (FK)
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Gastos",
        address=Address("Calle B", "Sevilla", "41001", "ES"),
        property_type=PropertyType.HOUSE,
        user_id="user-db",
        id="prop-expense-001",
    )
    prop_repo.save(prop)

    # Guardar gasto
    expense_repo = SQLiteExpenseRepository(sqlite_connection)
    expense = Expense(
        property_id="prop-expense-001",
        amount=Money(Decimal("200.00"), "EUR"),
        date=date(2026, 7, 5),
        category=ExpenseCategory.REPAIR,
        description="Fontanero",
        id="expense-001",
    )
    expense_repo.save(expense)

    # Recuperar
    found = expense_repo.find_by_property_id("prop-expense-001")
    assert len(found) == 1
    assert found[0].amount.amount == Decimal("200.00")
    assert found[0].category == ExpenseCategory.REPAIR


def test_delete_income(sqlite_connection):
    """DB-06: Guardar y eliminar un ingreso."""
    # Crear propiedad (FK)
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Delete Income",
        address=Address("Calle C", "Valencia", "46001", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id="user-db",
        id="prop-del-income",
    )
    prop_repo.save(prop)

    # Guardar ingreso
    income_repo = SQLiteIncomeRepository(sqlite_connection)
    income = Income(
        property_id="prop-del-income",
        amount=Money(Decimal("500.00"), "EUR"),
        date=date(2026, 8, 1),
        category=IncomeCategory.DEPOSIT,
        id="income-del-001",
    )
    income_repo.save(income)

    # Verificar que existe
    found = income_repo.find_by_property_id("prop-del-income")
    assert len(found) == 1

    income_repo.delete("income-del-001")
    found_after = income_repo.find_by_property_id("prop-del-income")
    assert len(found_after) == 0


from backend.domain.value_objects import CadastralBreakdown, AcquisitionCost

def test_sqlite_migration_fiscal_columns(sqlite_connection):
    """T-I-09-01: Migración: columnas fiscales se crean sin error"""
    cursor = sqlite_connection.connection.cursor()
    cursor.execute("PRAGMA table_info(properties)")
    columns = [row["name"] for row in cursor.fetchall()]
    assert "cadastral_ref" in columns
    assert "cadastral_land_value" in columns
    assert "acquisition_purchase_price" in columns


def test_sqlite_update_fiscal_data_cadastral(sqlite_connection):
    """T-I-09-02: update_fiscal_data persiste y recupera CadastralBreakdown"""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Fiscal", address=Address("Calle A", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT, user_id="u1", id="prop-fiscal-001"
    )
    repo.save(prop)
    
    repo.update_fiscal_data(
        property_id="prop-fiscal-001",
        cadastral_ref="1234567AB1234C0001XY",
        cadastral_breakdown=CadastralBreakdown(Decimal("40000"), Decimal("80000")),
        acquisition_cost=None,
        acquisition_date=None,
    )
    
    found = repo.find_by_id("prop-fiscal-001")
    assert found.cadastral_ref == "1234567AB1234C0001XY"
    assert found.cadastral_breakdown is not None
    assert found.cadastral_breakdown.land_value == Decimal("40000")


def test_sqlite_update_fiscal_data_acquisition(sqlite_connection):
    """T-I-09-03: update_fiscal_data persiste y recupera AcquisitionCost"""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Fiscal", address=Address("Calle A", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT, user_id="u1", id="prop-fiscal-002"
    )
    repo.save(prop)
    
    repo.update_fiscal_data(
        property_id="prop-fiscal-002",
        cadastral_ref=None,
        cadastral_breakdown=None,
        acquisition_cost=AcquisitionCost(Decimal("200000"), Decimal("120000"), Decimal("80000"), Decimal("16000"), Decimal("800"), Decimal("400")),
        acquisition_date=date(2020, 1, 1),
    )
    
    found = repo.find_by_id("prop-fiscal-002")
    assert found.acquisition_cost is not None
    assert found.acquisition_cost.purchase_price == Decimal("200000")
    assert found.acquisition_date == date(2020, 1, 1)


def test_sqlite_find_property_without_fiscal_data(sqlite_connection):
    """T-I-09-04: Propiedad sin datos fiscales retorna None en campos fiscales"""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Fiscal", address=Address("Calle A", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT, user_id="u1", id="prop-fiscal-003"
    )
    repo.save(prop)
    
    found = repo.find_by_id("prop-fiscal-003")
    assert found.cadastral_ref is None
    assert found.cadastral_breakdown is None
    assert found.acquisition_cost is None
    assert found.acquisition_date is None


def test_sqlite_save_keeps_fiscal_data(sqlite_connection):
    """T-I-09-05: save y find_by_id mantienen datos fiscales intactos"""
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="Piso Fiscal", address=Address("Calle A", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT, user_id="u1", id="prop-fiscal-004",
        cadastral_ref="1234567AB1234C0001XY",
        cadastral_breakdown=CadastralBreakdown(Decimal("40000"), Decimal("80000")),
        acquisition_cost=AcquisitionCost(Decimal("200000"), Decimal("120000"), Decimal("80000"), Decimal("16000"), Decimal("800"), Decimal("400")),
        acquisition_date=date(2020, 1, 1),
    )
    repo.save(prop)
    
    found = repo.find_by_id("prop-fiscal-004")
    assert found.cadastral_ref == "1234567AB1234C0001XY"
    assert found.cadastral_breakdown is not None
    assert found.acquisition_cost is not None
    assert found.acquisition_date is not None


def test_sqlite_lease_contract_save_and_find(sqlite_connection):
    """T-I-10-01"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p1")
    prop_repo.save(prop)

    repo = SQLiteLeaseContractRepository(sqlite_connection)
    contract = LeaseContract(
        property_id="p1", tenant_name="John", tenant_nif="123",
        start_date=date(2025, 1, 1), monthly_rent=Money(Decimal("100"), "EUR"),
        lease_type=LeaseType.VIVIENDA_HABITUAL, id="c1"
    )
    repo.save(contract)
    
    found = repo.find_by_id("c1")
    assert found is not None
    assert found.tenant_name == "John"
    assert found.start_date == date(2025, 1, 1)
    
def test_sqlite_lease_contract_find_by_property_id(sqlite_connection):
    """T-I-10-02"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop2", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p2")
    prop_repo.save(prop)

    repo = SQLiteLeaseContractRepository(sqlite_connection)
    c1 = LeaseContract("p2", "John", "123", date(2025, 1, 1), Money(Decimal("100"), "EUR"), LeaseType.VIVIENDA_HABITUAL)
    c2 = LeaseContract("p2", "Jane", "456", date(2025, 2, 1), Money(Decimal("200"), "EUR"), LeaseType.TEMPORAL)
    repo.save(c1)
    repo.save(c2)
    
    found = repo.find_by_property_id("p2")
    assert len(found) == 2
    assert found[0].id == c2.id # DESC order
    
def test_sqlite_lease_contract_delete(sqlite_connection):
    """T-I-10-03"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop3", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p3")
    prop_repo.save(prop)

    repo = SQLiteLeaseContractRepository(sqlite_connection)
    c1 = LeaseContract("p3", "John", "123", date(2025, 1, 1), Money(Decimal("100"), "EUR"), LeaseType.VIVIENDA_HABITUAL)
    repo.save(c1)
    
    repo.delete(c1.id)
    assert repo.find_by_id(c1.id) is None

def test_sqlite_lease_contract_cascade_delete(sqlite_connection):
    """T-I-10-04"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop4", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p4")
    prop_repo.save(prop)

    repo = SQLiteLeaseContractRepository(sqlite_connection)
    c1 = LeaseContract("p4", "John", "123", date(2025, 1, 1), Money(Decimal("100"), "EUR"), LeaseType.VIVIENDA_HABITUAL)
    repo.save(c1)
    
    prop_repo.delete("p4")
    assert repo.find_by_id(c1.id) is None


def test_sqlite_income_save_and_find_fiscal_category(sqlite_connection):
    """T-I-11-01: save/find Income con fiscal_category"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p-inc-fisc")
    prop_repo.save(prop)

    income_repo = SQLiteIncomeRepository(sqlite_connection)
    inc = Income(
        property_id="p-inc-fisc",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=IncomeCategory.RENT,
        fiscal_category=FiscalIncomeCategory.RENDIMIENTO_INTEGRO,
        id="inc-fisc-1"
    )
    income_repo.save(inc)
    
    found = income_repo.find_by_property_id("p-inc-fisc")[0]
    assert found.fiscal_category == FiscalIncomeCategory.RENDIMIENTO_INTEGRO


def test_sqlite_expense_save_and_find_fiscal_category(sqlite_connection):
    """T-I-11-02: save/find Expense con fiscal_category"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p-exp-fisc")
    prop_repo.save(prop)

    expense_repo = SQLiteExpenseRepository(sqlite_connection)
    exp = Expense(
        property_id="p-exp-fisc",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=ExpenseCategory.REPAIR,
        fiscal_category=FiscalExpenseCategory.REPARACION_CONSERVACION,
        id="exp-fisc-1"
    )
    expense_repo.save(exp)
    
    found = expense_repo.find_by_property_id("p-exp-fisc")[0]
    assert found.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION


def test_sqlite_income_update_fiscal_category(sqlite_connection):
    """T-I-11-03: update_fiscal_category en Income"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p-inc-upd")
    prop_repo.save(prop)

    income_repo = SQLiteIncomeRepository(sqlite_connection)
    inc = Income(
        property_id="p-inc-upd",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=IncomeCategory.RENT,
        id="inc-upd-1"
    )
    income_repo.save(inc)
    
    income_repo.update_fiscal_category("inc-upd-1", "rendimiento_integro")
    
    found = income_repo.find_by_property_id("p-inc-upd")[0]
    assert found.fiscal_category == FiscalIncomeCategory.RENDIMIENTO_INTEGRO


def test_sqlite_expense_update_fiscal_category(sqlite_connection):
    """T-I-11-04: update_fiscal_category en Expense"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p-exp-upd")
    prop_repo.save(prop)

    expense_repo = SQLiteExpenseRepository(sqlite_connection)
    exp = Expense(
        property_id="p-exp-upd",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=ExpenseCategory.REPAIR,
        id="exp-upd-1"
    )
    expense_repo.save(exp)
    
    expense_repo.update_fiscal_category("exp-upd-1", "reparacion_conservacion")
    
    found = expense_repo.find_by_property_id("p-exp-upd")[0]
    assert found.fiscal_category == FiscalExpenseCategory.REPARACION_CONSERVACION


def test_sqlite_income_retrocompat(sqlite_connection):
    """T-I-11-05: Income sin fiscal_category sigue funcionando"""
    prop_repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(name="Prop", address=Address("S", "C", "P", "ES"), property_type=PropertyType.APARTMENT, user_id="u1", id="p-inc-retro")
    prop_repo.save(prop)

    income_repo = SQLiteIncomeRepository(sqlite_connection)
    inc = Income(
        property_id="p-inc-retro",
        amount=Money(Decimal("100"), "EUR"),
        date=date.today(),
        category=IncomeCategory.RENT,
        id="inc-retro-1"
    )
    income_repo.save(inc)
    
    found = income_repo.find_by_property_id("p-inc-retro")[0]
    assert found.fiscal_category is None

