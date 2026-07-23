"""
Funciones de inyección de dependencias para FastAPI.

Proveen los repositorios concretos (SQLite) a los endpoints via Depends().
"""

from __future__ import annotations

from fastapi import Depends, Request

from backend.adapters.sqlite_adapter import (
    SQLiteConnection,
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
)


def get_db(request: Request) -> SQLiteConnection:
    """Retorna la conexión a BD almacenada en app.state durante el lifespan."""
    return request.app.state.db


def get_property_repo(db: SQLiteConnection = Depends(get_db)) -> SQLitePropertyRepository:
    """Retorna el repositorio de propiedades con la conexión activa."""
    return SQLitePropertyRepository(db)


def get_income_repo(db: SQLiteConnection = Depends(get_db)) -> SQLiteIncomeRepository:
    """Retorna el repositorio de ingresos con la conexión activa."""
    return SQLiteIncomeRepository(db)


def get_expense_repo(db: SQLiteConnection = Depends(get_db)) -> SQLiteExpenseRepository:
    """Retorna el repositorio de gastos con la conexión activa."""
    return SQLiteExpenseRepository(db)
