"""
Schemas Pydantic (DTOs) para la API REST.

Los Schemas son la frontera de traducción entre el mundo HTTP (JSON) y el dominio.
Nunca exponemos entidades de dominio directamente en la API.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator


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
    has_fiscal_data: bool = False
    cups_electricity: str | None = None
    cups_gas: str | None = None
    cups_water: str | None = None


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
    fiscal_category: str | None = None


class IncomeResponse(BaseModel):
    """Response body con los datos de un ingreso."""

    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str
    fiscal_category: str | None = None


# ──────────────────────────────────────────────
# Expense Schemas
# ──────────────────────────────────────────────

class UtilityInvoiceDataSchema(BaseModel):
    cups: str
    amount: Decimal
    issue_date: date
    provider_name: str
    utility_type: str
    invoice_number: str | None = None
    extraction_confidence: str

class ExpenseCreate(BaseModel):
    """Request body para registrar un gasto."""

    property_id: str
    amount: Decimal
    date: date
    category: str  # Valor del enum: "repair", "tax", etc.
    description: str = ""
    fiscal_category: str | None = None


class ExpenseResponse(BaseModel):
    """Response body con los datos de un gasto."""

    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str
    fiscal_category: str | None = None
    is_verified: bool = True
    source: str = "manual"
    receipt_path: str | None = None
    utility_data: UtilityInvoiceDataSchema | None = None


# ──────────────────────────────────────────────
# Profit Report Schema
# ──────────────────────────────────────────────

class ProfitReportResponse(BaseModel):
    """Response body con el beneficio neto de una propiedad."""

    property_id: str
    net_profit: Decimal
    currency: str


# ──────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CadastralBreakdownSchema(BaseModel):
    """Desglose del valor catastral."""
    land_value: Decimal
    construction_value: Decimal

class AcquisitionCostSchema(BaseModel):
    """Datos de adquisición del inmueble."""
    purchase_price: Decimal
    construction_portion: Decimal
    land_portion: Decimal
    transfer_tax: Decimal = Decimal("0")
    notary_fees: Decimal = Decimal("0")
    registry_fees: Decimal = Decimal("0")

class FiscalDataUpdate(BaseModel):
    """Request body para actualizar datos fiscales de una propiedad."""
    cadastral_ref: str | None = None
    cadastral_breakdown: CadastralBreakdownSchema | None = None
    acquisition_cost: AcquisitionCostSchema | None = None
    acquisition_date: date | None = None

    @field_validator("cadastral_ref")
    @classmethod
    def validate_cadastral_ref(cls, v: str | None) -> str | None:
        if v is not None:
            v_clean = v.strip()
            if not v_clean:
                return None
            if len(v_clean) != 20:
                raise ValueError(
                    f"La referencia catastral debe tener 20 caracteres, tiene {len(v_clean)}."
                )
            return v_clean
        return None

class FiscalDataResponse(BaseModel):
    """Response body con los datos fiscales de una propiedad."""
    property_id: str
    cadastral_ref: str | None = None
    cadastral_breakdown: CadastralBreakdownSchema | None = None
    acquisition_cost: AcquisitionCostSchema | None = None
    acquisition_date: date | None = None
    has_fiscal_data: bool

class PropertyCupsUpdate(BaseModel):
    cups_electricity: str | None = None
    cups_gas: str | None = None
    cups_water: str | None = None


# ──────────────────────────────────────────────
# Lease Contract Schemas
# ──────────────────────────────────────────────

class LeaseContractCreate(BaseModel):
    tenant_name: str
    tenant_nif: str
    start_date: date
    end_date: date | None = None
    monthly_rent: float
    lease_type: str

class LeaseContractUpdate(BaseModel):
    tenant_name: str | None = None
    tenant_nif: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    monthly_rent: float | None = None
    lease_type: str | None = None

class LeaseContractResponse(BaseModel):
    id: str
    property_id: str
    tenant_name: str
    tenant_nif: str
    start_date: date
    end_date: date | None
    monthly_rent: str
    currency: str
    lease_type: str
    is_active: bool


# ──────────────────────────────────────────────
# Fiscal Classification Schemas
# ──────────────────────────────────────────────

class FiscalCategoryUpdate(BaseModel):
    fiscal_category: str

class FiscalSuggestionItem(BaseModel):
    id: str
    amount: Decimal
    category: str
    description: str
    date: date
    suggested_fiscal_category: str | None

class FiscalSuggestionsResponse(BaseModel):
    unclassified_incomes: list[FiscalSuggestionItem]
    unclassified_expenses: list[FiscalSuggestionItem]
    total_unclassified: int

class FiscalReportResponse(BaseModel):
    fiscal_year: int
    property_id: str

    # Rendimientos
    gross_rental_income: Decimal
    other_income: Decimal
    total_income: Decimal

    # Ocupación
    rented_days: int
    total_days_in_year: int
    occupation_ratio: Decimal

    # Gastos por categoría
    expenses_intereses: Decimal
    expenses_reparacion: Decimal
    expenses_tributos: Decimal
    expenses_seguros: Decimal
    expenses_comunidad: Decimal
    expenses_suministros: Decimal
    expenses_formalizacion: Decimal
    expenses_dudoso_cobro: Decimal
    expenses_muebles: Decimal
    expenses_otros: Decimal

    # Tope
    repair_interest_raw: Decimal
    repair_interest_cap: Decimal
    repair_interest_applied: Decimal
    repair_interest_excess: Decimal

    prior_excess_available: Decimal
    prior_excess_applied: Decimal

    # Amortización
    amortization_base: Decimal
    amortization_rate: Decimal
    amortization_full_year: Decimal
    amortization_prorated: Decimal

    # Rendimiento neto
    total_deductible_expenses: Decimal
    net_income_before_reduction: Decimal

    # Reducción VH
    vivienda_habitual_days: int
    vivienda_habitual_ratio: Decimal
    reduction_base: Decimal
    reduction_percentage: Decimal
    reduction_amount: Decimal

    # Final
    net_income_final: Decimal

    # Metadatos
    unclassified_income_count: int
    unclassified_expense_count: int
    has_warnings: bool
