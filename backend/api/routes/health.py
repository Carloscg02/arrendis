"""
Router para sonda de salud y monitorización (F-39).

Expone GET /api/health para verificar el estado del servidor y la conectividad activa
con la base de datos SQLite sin requerir autenticación JWT.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.dependencies import get_db
from backend.api.schemas import HealthDegradedResponse, HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    responses={
        200: {"model": HealthResponse},
        503: {"model": HealthDegradedResponse},
    },
)
def get_health(db: SQLiteConnection = Depends(get_db)):
    """Verifica el estado de salud del servicio y la base de datos."""
    is_healthy = db.check_health()
    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthDegradedResponse(
                status="degraded",
                database="disconnected",
                error="Database connectivity check failed",
            ).model_dump(),
        )
    return HealthResponse(status="healthy", database="connected", version="0.1.0")
