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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestiona el ciclo de vida de la app: setup y teardown de la BD."""
    # SETUP: crear conexión y guardarla en app.state
    db = SQLiteConnection("data/rental.db")
    app.state.db = db
    Path("data/images").mkdir(parents=True, exist_ok=True)
    yield
    # TEARDOWN: cerrar conexión
    db.close()


app = FastAPI(
    title="Gestión de Alquileres API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — permitir todas las origenes (en producción, restringir al dominio del frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(properties_router)
app.include_router(incomes_router)
app.include_router(expenses_router)

# Mount static files para servir imágenes de propiedades
_images_dir = Path("data/images")
_images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=str(_images_dir)), name="images")
