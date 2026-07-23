"""
Schemas Pydantic (DTOs) para la API REST.

Los Schemas son la frontera de traducción entre el mundo HTTP (JSON) y el dominio.
Nunca exponemos entidades de dominio directamente en la API.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


# ──────────────────────────────────────────────
# Property Schemas
# ──────────────────────────────────────────────

class AddressSchema(BaseModel):
    """Representación JSON de una dirección."""

    street: str
    city: str
    postal_code: str
    country: str = "ES"


class PropertyCreate(BaseModel):
    """Request body para crear una propiedad."""

    name: str
    address: AddressSchema
    property_type: str  # Valor del enum: "apartment", "house", etc.


class PropertyResponse(BaseModel):
    """Response body con los datos de una propiedad."""

    id: str
    name: str
    address: AddressSchema
    property_type: str
    status: str
    image_url: str | None = None


# ──────────────────────────────────────────────
# Income Schemas
# ──────────────────────────────────────────────

class IncomeCreate(BaseModel):
    """Request body para registrar un ingreso."""

    property_id: str
    amount: Decimal
    date: date
    category: str  # Valor del enum: "rent", "deposit", "other"
    description: str = ""


class IncomeResponse(BaseModel):
    """Response body con los datos de un ingreso."""

    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str


# ──────────────────────────────────────────────
# Expense Schemas
# ──────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    """Request body para registrar un gasto."""

    property_id: str
    amount: Decimal
    date: date
    category: str  # Valor del enum: "repair", "tax", etc.
    description: str = ""


class ExpenseResponse(BaseModel):
    """Response body con los datos de un gasto."""

    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str


# ──────────────────────────────────────────────
# Profit Report Schema
# ──────────────────────────────────────────────

class ProfitReportResponse(BaseModel):
    """Response body con el beneficio neto de una propiedad."""

    property_id: str
    net_profit: Decimal
    currency: str
