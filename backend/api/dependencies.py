"""
Funciones de inyección de dependencias para FastAPI.

Proveen los repositorios concretos (SQLite) a los endpoints via Depends().
"""

from __future__ import annotations

from fastapi import Depends, Request, Header, HTTPException
from backend.domain.entities import User

from backend.adapters.aeat_pdf_renderer_adapter import AEATPdfRendererAdapter
from backend.adapters.auth_adapter import BcryptPasswordHasherAdapter, JWTTokenServiceAdapter
from backend.adapters.sqlite_adapter import (
    SQLiteConnection,
    SQLiteExpenseRepository,
    SQLiteIncomeRepository,
    SQLitePropertyRepository,
    SQLiteUserRepository,
    SQLiteLeaseContractRepository,
    SQLiteFiscalCarryforwardRepository,
)
from backend.domain.ports import PasswordHasherPort, TokenServicePort, UserRepository, LLMProviderPort
from backend.adapters.gemini_adapter import GeminiFlashAdapter


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


def get_carryforward_repo(db: SQLiteConnection = Depends(get_db)) -> SQLiteFiscalCarryforwardRepository:
    """Retorna el repositorio de excesos pendientes con la conexión activa."""
    return SQLiteFiscalCarryforwardRepository(db)


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


def get_fiscal_report_renderer() -> AEATPdfRendererAdapter:
    """Retorna el renderizador de informes fiscales (PDF AEAT por defecto)."""
    return AEATPdfRendererAdapter()

def get_llm_provider(request: Request) -> LLMProviderPort | None:
    """Retorna el proveedor de LLM configurado (almacenado en app.state), o None si no hay key."""
    return getattr(request.app.state, "llm_provider", None)


def get_utility_registry() -> UtilityExtractorRegistry:
    from backend.domain.extraction import UtilityExtractorRegistry, RepsolExtractionStrategy
    return UtilityExtractorRegistry([
        RepsolExtractionStrategy(),
    ])


def get_process_utility_invoice_use_case(
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    expense_repo: SQLiteExpenseRepository = Depends(get_expense_repo),
    registry: UtilityExtractorRegistry = Depends(get_utility_registry),
    llm_provider: LLMProviderPort | None = Depends(get_llm_provider),
) -> ProcessUtilityInvoiceUseCase:
    from backend.adapters.pdf_extractor_adapter import PyMuPDFTextExtractorAdapter
    from backend.domain.extraction import AIExtractionStrategy
    from backend.application.use_cases import ProcessUtilityInvoiceUseCase

    pdf_extractor = PyMuPDFTextExtractorAdapter()
    fallback_strategy = AIExtractionStrategy(llm_provider) if llm_provider is not None else None
    return ProcessUtilityInvoiceUseCase(
        pdf_extractor=pdf_extractor,
        registry=registry,
        property_repo=property_repo,
        expense_repo=expense_repo,
        fallback_strategy=fallback_strategy,
    )


def get_process_batch_utility_invoices_use_case(
    single_use_case: ProcessUtilityInvoiceUseCase = Depends(get_process_utility_invoice_use_case),
) -> ProcessBatchUtilityInvoicesUseCase:
    from backend.application.use_cases import ProcessBatchUtilityInvoicesUseCase
    return ProcessBatchUtilityInvoicesUseCase(single_use_case)


def get_process_inbound_email_use_case(
    user_repo: SQLiteUserRepository = Depends(get_user_repo),
    single_use_case: ProcessUtilityInvoiceUseCase = Depends(get_process_utility_invoice_use_case),
) -> ProcessInboundEmailUseCase:
    from backend.application.use_cases import ProcessInboundEmailUseCase
    return ProcessInboundEmailUseCase(
        user_repo=user_repo,
        single_invoice_use_case=single_use_case,
    )

