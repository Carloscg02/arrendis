from __future__ import annotations

from abc import ABC, abstractmethod
from backend.domain.value_objects import UtilityInvoiceData


class ExtractionStrategy(ABC):
    """Contrato base para cualquier estrategia de extracción de facturas de suministros."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre canónico del proveedor o estrategia (ej. 'Repsol', 'AI_Fallback')."""
        ...

    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """Determina si esta estrategia reconoce el formato del texto de la factura."""
        ...

    @abstractmethod
    def extract(self, text: str) -> UtilityInvoiceData | None:
        """Extrae los datos estructurados del texto.

        Returns:
            UtilityInvoiceData si todos los campos requeridos se extrajeron correctamente.
            None si la extracción no fue concluyente o falló la validación.
        """
        ...


class UtilityExtractorRegistry:
    """Registro extensible de estrategias de extracción de facturas (Open/Closed Principle).

    Permite incorporar soporte para nuevas comercializadoras en tiempo de ejecución
    o configuración sin modificar el código de los casos de uso.
    """

    def __init__(self, strategies: list[ExtractionStrategy] | None = None) -> None:
        self._strategies: list[ExtractionStrategy] = list(strategies or [])

    def register(self, strategy: ExtractionStrategy) -> None:
        """Añade una nueva estrategia al registro."""
        self._strategies.append(strategy)

    def find_strategy(self, text: str) -> ExtractionStrategy | None:
        """Retorna la primera estrategia cuyo can_handle() devuelva True."""
        for strategy in self._strategies:
            if strategy.can_handle(text):
                return strategy
        return None

    @property
    def registered_providers(self) -> list[str]:
        return [s.provider_name for s in self._strategies]
