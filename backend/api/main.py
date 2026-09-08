"""
Punto de entrada de la aplicación FastAPI — Gestión de Alquileres API.

Configura el lifespan (conexión a BD), CORS middleware e incluye los routers
de properties, incomes y expenses.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.routes.expenses import router as expenses_router
from backend.api.routes.incomes import router as incomes_router
from backend.api.routes.properties import router as properties_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.contracts import router as contracts_router
from backend.api.routes.llm import router as llm_router
from backend.api.routes.webhooks import router as webhooks_router
from backend.adapters.gemini_adapter import GeminiFlashAdapter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestiona el ciclo de vida de la app: setup y teardown de la BD."""
    import os, sys
    db_path = os.getenv("DATABASE_PATH", "data/rental.db")
    if os.getenv("TESTING") == "1" or "pytest" in sys.modules:
        db_path = ":memory:"
    db = SQLiteConnection(db_path)
    app.state.db = db
    Path("data/images").mkdir(parents=True, exist_ok=True)
    
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    app.state.llm_provider = GeminiFlashAdapter(api_key=gemini_api_key) if gemini_api_key else None
    
    yield
    db.close()


app = FastAPI(
    title="Gestión de Alquileres API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — permitir origenes tanto en local como en producción (Cloudflare Pages y dominio arrendis)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://arrendis.com",
        "https://app.arrendis.com",
        "https://staging.arrendis.com",
    ],
    allow_origin_regex=r"^https://.*\.arrendis\.(com|es)$|^https://.*\.pages\.dev$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(properties_router)
app.include_router(incomes_router)
app.include_router(expenses_router)
app.include_router(auth_router)
app.include_router(contracts_router)
app.include_router(llm_router)
app.include_router(webhooks_router)

# Mount static files para servir imágenes de propiedades
_images_dir = Path("data/images")
_images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=str(_images_dir)), name="images")
