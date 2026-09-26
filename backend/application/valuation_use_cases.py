from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.domain.entities import (
    PropertyValuation,
    MissingPhysicalAttributesError,
)
from backend.domain.ports import (
    PropertyRepository,
    PropertyValuationRepository,
    MarketValuationPort,
)


@dataclass(frozen=True)
class ValuationExecutionResult:
    """Resultado de la ejecución o consulta de valoración con metadatos de cooldown."""
    valuation: PropertyValuation
    is_cached: bool
    cooldown_days_remaining: int


class RequestPropertyValuationUseCase:
    """Orquesta la solicitud y consulta de estimaciones de mercado con política de cooldown."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        valuation_repo: PropertyValuationRepository,
        valuation_port: MarketValuationPort,
        cooldown_days: int = 30,
    ) -> None:
        self.property_repo = property_repo
        self.valuation_repo = valuation_repo
        self.valuation_port = valuation_port
        self.cooldown_days = cooldown_days

    def execute(
        self,
        property_id: str,
        user_id: str,
        force: bool = False,
        current_date: date | None = None,
    ) -> ValuationExecutionResult:
        today = current_date or date.today()

        # 1. Validar existencia y titularidad del inmueble
        prop = self.property_repo.find_by_id(property_id)
        if not prop or prop.user_id != user_id:
            raise ValueError(f"Propiedad '{property_id}' no encontrada para este usuario.")

        # 2. Validar atributos físicos mínimos
        if prop.surface_m2 is None or prop.surface_m2 <= 0:
            raise MissingPhysicalAttributesError(
                f"La propiedad '{prop.name}' requiere especificar la superficie en m2 para estimar su valor.",
                provider="validation",
            )

        # 3. Comprobar Cooldown con la última valoración
        latest = self.valuation_repo.find_latest_by_property_id(property_id)
        if latest is not None:
            days_elapsed = (today - latest.valuation_date).days
            cooldown_remaining = max(0, self.cooldown_days - days_elapsed)

            # Si aún está en periodo de enfriamiento y no se fuerza, devolver datos cacheados
            if cooldown_remaining > 0 and not force:
                return ValuationExecutionResult(
                    valuation=latest,
                    is_cached=True,
                    cooldown_days_remaining=cooldown_remaining,
                )

        # 4. Invocar el puerto de estimación de mercado
        result = self.valuation_port.estimate_valuation(
            address=prop.address,
            surface_m2=prop.surface_m2,
            property_type=prop.property_type,
            bedrooms=prop.bedrooms,
            bathrooms=prop.bathrooms,
            floor=prop.floor,
            has_elevator=prop.has_elevator,
            condition=prop.condition,
        )

        # 5. Construir y persistir la nueva entidad PropertyValuation
        new_valuation = PropertyValuation(
            property_id=property_id,
            valuation_date=today,
            sale_range=result.sale_range,
            rent_range=result.rent_range,
            confidence=result.confidence,
            reasoning_factors=result.reasoning_factors,
            sources=result.sources,
            raw_notes=result.raw_notes,
        )
        self.valuation_repo.save(new_valuation)

        return ValuationExecutionResult(
            valuation=new_valuation,
            is_cached=False,
            cooldown_days_remaining=self.cooldown_days,
        )

    def get_latest(
        self,
        property_id: str,
        user_id: str,
        current_date: date | None = None,
    ) -> ValuationExecutionResult | None:
        """Recupera la última valoración calculando el cooldown restante en la capa de aplicación."""
        today = current_date or date.today()
        prop = self.property_repo.find_by_id(property_id)
        if not prop or prop.user_id != user_id:
            raise ValueError(f"Propiedad '{property_id}' no encontrada para este usuario.")

        latest = self.valuation_repo.find_latest_by_property_id(property_id)
        if latest is None:
            return None

        days_elapsed = (today - latest.valuation_date).days
        cooldown_remaining = max(0, self.cooldown_days - days_elapsed)

        return ValuationExecutionResult(
            valuation=latest,
            is_cached=True,
            cooldown_days_remaining=cooldown_remaining,
        )
