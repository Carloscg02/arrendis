from decimal import Decimal
from backend.domain.ports import MarketValuationPort
from backend.domain.entities import (
    PropertyType,
    PropertyCondition,
    ValuationConfidence,
)
from backend.domain.value_objects import (
    Address,
    Money,
    ValuationRange,
    ReasoningFactor,
    ValuationSource,
    MarketValuationResult,
)


class MockMarketValuationAdapter(MarketValuationPort):
    """Adaptador de pruebas con fórmulas heurísticas deterministas sin dependencias externas."""

    def estimate_valuation(
        self,
        address: Address,
        surface_m2: int,
        property_type: PropertyType = PropertyType.APARTMENT,
        bedrooms: int | None = None,
        bathrooms: int | None = None,
        floor: int | None = None,
        has_elevator: bool | None = None,
        condition: PropertyCondition | None = None,
    ) -> MarketValuationResult:
        if surface_m2 <= 0:
            raise ValueError(f"La superficie construida debe ser positiva: {surface_m2}")

        # Multiplicadores por estado de conservación
        condition_factors = {
            PropertyCondition.A_REFORMAR: Decimal("0.80"),
            PropertyCondition.BUEN_ESTADO: Decimal("1.00"),
            PropertyCondition.REFORMADO: Decimal("1.15"),
            PropertyCondition.A_ESTRENAR: Decimal("1.30"),
        }
        factor_cond = condition_factors.get(condition, Decimal("1.00"))

        # Factor ascensor
        elevator_factor = Decimal("0.00")
        if has_elevator is True:
            elevator_factor = Decimal("0.05")
        elif has_elevator is False and floor is not None and floor >= 2:
            elevator_factor = Decimal("-0.07")

        combined_mult = factor_cond * (Decimal("1.00") + elevator_factor)

        # Precio de venta base: 2200 €/m2
        sale_base_m2 = Decimal("2200")
        sale_median_raw = Decimal(surface_m2) * sale_base_m2 * combined_mult
        sale_median = (sale_median_raw / Decimal("100")).quantize(Decimal("1")) * Decimal("100")
        sale_min = (sale_median * Decimal("0.90")).quantize(Decimal("1.00"))
        sale_max = (sale_median * Decimal("1.10")).quantize(Decimal("1.00"))

        # Precio de alquiler base: 11 €/m2
        rent_base_m2 = Decimal("11")
        rent_median_raw = Decimal(surface_m2) * rent_base_m2 * combined_mult
        rent_median = (rent_median_raw / Decimal("10")).quantize(Decimal("1")) * Decimal("10")
        rent_min = (rent_median * Decimal("0.90")).quantize(Decimal("1.00"))
        rent_max = (rent_median * Decimal("1.10")).quantize(Decimal("1.00"))

        factors: list[ReasoningFactor] = []
        if condition:
            factors.append(
                ReasoningFactor(
                    factor_name=f"Estado {condition.value}",
                    impact_percent=Decimal(str((factor_cond - Decimal("1.00")).quantize(Decimal("0.01")))),
                    description=f"Ajuste por estado de conservación {condition.value}.",
                )
            )
        if elevator_factor != Decimal("0.00"):
            factors.append(
                ReasoningFactor(
                    factor_name="Ascensor",
                    impact_percent=elevator_factor,
                    description="Impacto de la presencia o ausencia de ascensor en la planta.",
                )
            )

        city_slug = address.city.lower().strip().replace(" ", "-") if address.city else "malaga"
        sources = [
            ValuationSource(
                title=f"Búsqueda de mercado residencial en {address.city} (Idealista)",
                url=f"https://www.idealista.com/venta-viviendas/{city_slug}/",
                price=sale_median,
                surface_m2=surface_m2,
            ),
            ValuationSource(
                title=f"Búsqueda de alquileres en {address.city} (Fotocasa)",
                url=f"https://www.fotocasa.es/es/alquiler/viviendas/{city_slug}/l",
                price=rent_median,
                surface_m2=surface_m2,
            ),
        ]

        return MarketValuationResult(
            sale_range=ValuationRange(
                min_price=Money(sale_min),
                median_price=Money(sale_median),
                max_price=Money(sale_max),
            ),
            rent_range=ValuationRange(
                min_price=Money(rent_min),
                median_price=Money(rent_median),
                max_price=Money(rent_max),
            ),
            confidence=ValuationConfidence.HIGH,
            reasoning_factors=factors,
            sources=sources,
            raw_notes=(
                f"[MODO SIMULADO / MOCK] Estimación heurística calculada para {surface_m2} m² en {address.city}. "
                "Para obtener tasaciones reales con inteligencia artificial y análisis contextual, verifique su GEMINI_API_KEY."
            ),
        )
