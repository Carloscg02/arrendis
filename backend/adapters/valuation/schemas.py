from decimal import Decimal
from pydantic import BaseModel, Field


class _RangePayload(BaseModel):
    min: Decimal
    median: Decimal
    max: Decimal


class _FactorPayload(BaseModel):
    factor_name: str
    impact_percent: float
    description: str


class _SourcePayload(BaseModel):
    title: str
    url: str
    price: Decimal | None = None
    surface_m2: int | None = None


class _GeminiValuationPayload(BaseModel):
    sale_range: _RangePayload
    rent_range: _RangePayload
    confidence: str
    reasoning_factors: list[_FactorPayload] = Field(default_factory=list)
    sources: list[_SourcePayload] = Field(default_factory=list)
    raw_notes: str | None = None
