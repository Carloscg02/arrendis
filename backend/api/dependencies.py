"""
Funciones de inyección de dependencias para FastAPI.

Proveen los repositorios concretos (SQLite) a los endpoints via Depends().
"""

from __future__ import annotations

from fastapi import Depends, Request, Header, HTTPException
from backend.domain.entities import User

from backend.adapters.auth_adapter import BcryptPasswordHasherAdapter, JWTTokenServiceAdapter
from backend.adapters.sqlite_adapter import (
    SQLiteConnection,
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
    SQLiteUserRepository,
    SQLiteLeaseContractRepository,
)
from backend.domain.ports import PasswordHasherPort, TokenServicePort, UserRepository


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


def get_user_repo(db: SQLiteConnection = Depends(get_db)) -> SQLiteUserRepository:
    return SQLiteUserRepository(db)


def get_contract_repo(db: SQLiteConnection = Depends(get_db)) -> SQLiteLeaseContractRepository:
    """Retorna el repositorio de contratos con la conexión activa."""
    return SQLiteLeaseContractRepository(db)


def get_hasher() -> BcryptPasswordHasherAdapter:
    return BcryptPasswordHasherAdapter()


def get_token_service() -> JWTTokenServiceAdapter:
    return JWTTokenServiceAdapter()


async def get_current_user(
    authorization: str | None = Header(None),
    db: SQLiteConnection = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    token = authorization.split(" ", 1)[1]
    token_service = get_token_service()
    user_id = token_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user_repo = SQLiteUserRepository(db)
    user = user_repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
