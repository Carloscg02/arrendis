import pytest
from decimal import Decimal
from datetime import date
from backend.domain.entities import Property, Address, PropertyType, Expense, ExpenseCategory, ExpenseSource, UtilityType, ExtractionConfidence
from backend.domain.value_objects import Money, UtilityInvoiceData
from backend.adapters.sqlite_adapter import SQLitePropertyRepository, SQLiteExpenseRepository

def test_it_f16_01_save_property_cups(sqlite_connection):
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="P1",
        address=Address("C/ 1", "City", "28000"),
        property_type=PropertyType.APARTMENT,
        user_id="u1",
        cups_electricity="ES00210000000000000000",
        cups_gas="ES00310000000000000000"
    )
    repo.save(prop)
    
    saved = repo.find_by_id(prop.id)
    assert saved.cups_electricity == "ES00210000000000000000"
    assert saved.cups_gas == "ES00310000000000000000"
    assert saved.cups_water is None

def test_it_f16_02_find_by_cups(sqlite_connection):
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="P1",
        address=Address("C/ 1", "City", "28000"),
        property_type=PropertyType.APARTMENT,
        user_id="u1",
        cups_electricity="ES00210000000000000000"
    )
    repo.save(prop)
    
    found = repo.find_by_cups("ES00210000000000000000", "u1")
    assert found is not None
    assert found.id == prop.id
    
    not_found = repo.find_by_cups("ES00210000000000000000", "u2")
    assert not_found is None
    
    wrong_cups = repo.find_by_cups("ES999", "u1")
    assert wrong_cups is None

def test_it_f16_03_update_cups(sqlite_connection):
    repo = SQLitePropertyRepository(sqlite_connection)
    prop = Property(
        name="P1",
        address=Address("C/ 1", "City", "28000"),
        property_type=PropertyType.APARTMENT,
        user_id="u1"
    )
    repo.save(prop)
    
    repo.update_cups(prop.id, "ES00210000000000000000", None, "ES00410000000000000000")
    updated = repo.find_by_id(prop.id)
    assert updated.cups_electricity == "ES00210000000000000000"
    assert updated.cups_gas is None
    assert updated.cups_water == "ES00410000000000000000"

def test_it_f16_04_save_manual_expense(sqlite_connection):
    property_repo = SQLitePropertyRepository(sqlite_connection)
    expense_repo = SQLiteExpenseRepository(sqlite_connection)
    prop = Property(name="P1", address=Address("C/1", "C", "28000"), property_type=PropertyType.APARTMENT, user_id="u1")
    property_repo.save(prop)
    
    expense = Expense(
        property_id=prop.id,
        amount=Money(Decimal("50.0")),
        date=date.today(),
        category=ExpenseCategory.REPAIR
    )
    expense_repo.save(expense)
    
    expenses = expense_repo.find_by_property_id(prop.id)
    assert len(expenses) == 1
    assert expenses[0].source == ExpenseSource.MANUAL
    assert expenses[0].is_verified is True
    assert expenses[0].utility_data is None

def test_it_f16_05_save_auto_utility_expense(sqlite_connection):
    property_repo = SQLitePropertyRepository(sqlite_connection)
    expense_repo = SQLiteExpenseRepository(sqlite_connection)
    prop = Property(name="P1", address=Address("C/1", "C", "28000"), property_type=PropertyType.APARTMENT, user_id="u1")
    property_repo.save(prop)
    
    utility_data = UtilityInvoiceData(
        cups="ES00210000000000000000",
        amount=Decimal("45.5"),
        issue_date=date.today(),
        provider_name="Iberdrola",
        utility_type=UtilityType.ELECTRICITY
    )
    
    expense = Expense(
        property_id=prop.id,
        amount=Money(Decimal("45.5")),
        date=date.today(),
        category=ExpenseCategory.UTILITY,
        source=ExpenseSource.AUTO_IMPORT,
        is_verified=False,
        utility_data=utility_data,
        receipt_path="path/to/invoice.pdf"
    )
    expense_repo.save(expense)
    
    expenses = expense_repo.find_by_property_id(prop.id)
    assert len(expenses) == 1
    saved_exp = expenses[0]
    assert saved_exp.source == ExpenseSource.AUTO_IMPORT
    assert saved_exp.is_verified is False
    assert saved_exp.receipt_path == "path/to/invoice.pdf"
    assert saved_exp.utility_data is not None
    assert saved_exp.utility_data.cups == "ES00210000000000000000"
    assert saved_exp.utility_data.utility_type == UtilityType.ELECTRICITY
