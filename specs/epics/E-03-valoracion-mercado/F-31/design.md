# F-31: Caso de Uso de Estimación con Política de Cooldown y Persistencia de Fuentes

## 1. Visión y Objetivos

La Feature **F-31** implementa la lógica de orquestación en la capa de aplicación para la solicitud de valoraciones inmobiliarias bajo demanda, incorporando una **política de cooldown configurable** (`VALUATION_COOLDOWN_DAYS`, por defecto 30 días) para prevenir el abuso de peticiones y optimizar las cuotas de búsqueda web, garantizando al mismo tiempo la **persistencia íntegra de los informes y sus fuentes de contraste**.

---

## 2. Dominio y Casos de Uso (Application Layer)

### 2.1 Excepciones de Dominio
En `backend/domain/entities.py`:
```python
class MissingPhysicalAttributesError(MarketValuationError):
    """La propiedad carece de los atributos físicos mínimos (superficie construida m2 > 0) para ser valorada."""
    pass
```
*Hereda de `MarketValuationError` (no de `ValueError`) para evitar que se enmascare en los bloques `except ValueError` de los routers de FastAPI que gestionan el 404.*

### 2.2 DTO de Resultado del Caso de Uso
En `backend/application/valuation_use_cases.py`:
```python
@dataclass(frozen=True)
class ValuationExecutionResult:
    valuation: PropertyValuation
    is_cached: bool
    cooldown_days_remaining: int
```

### 2.3 Caso de Uso: `RequestPropertyValuationUseCase`
Ubicación: `backend/application/valuation_use_cases.py`.

```python
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
```

---

## 3. Capa de API y Contratos de Entrada/Salida

### 3.1 DTO y Schemas
En `backend/api/schemas.py`:
```python
class PropertyValuationResponse(BaseModel):
    id: str
    property_id: str
    valuation_date: str
    sale_range: ValuationRangeDTO
    rent_range: ValuationRangeDTO
    confidence: ValuationConfidenceEnum
    reasoning_factors: list[ReasoningFactorDTO] = []
    sources: list[ValuationSourceDTO] = []
    raw_notes: str | None = None
    cooldown_days_remaining: int = 0
    is_cached: bool = False
```

### 3.2 Helper de Mapeo
En `backend/api/routes/properties.py`:
```python
def _valuation_entity_to_response(
    val: PropertyValuation,
    cooldown_days_remaining: int = 0,
    is_cached: bool = False,
) -> PropertyValuationResponse:
    return PropertyValuationResponse(
        id=val.id,
        property_id=val.property_id,
        valuation_date=val.valuation_date.isoformat(),
        sale_range=ValuationRangeDTO(
            min=float(val.sale_range.min_price.amount),
            median=float(val.sale_range.median_price.amount),
            max=float(val.sale_range.max_price.amount),
            currency=val.sale_range.min_price.currency,
        ),
        rent_range=ValuationRangeDTO(
            min=float(val.rent_range.min_price.amount),
            median=float(val.rent_range.median_price.amount),
            max=float(val.rent_range.max_price.amount),
            currency=val.rent_range.min_price.currency,
        ),
        confidence=ValuationConfidenceEnum(val.confidence.value),
        reasoning_factors=[
            ReasoningFactorDTO(
                factor_name=f.factor_name,
                impact_percent=float(f.impact_percent),
                description=f.description,
            )
            for f in val.reasoning_factors
        ],
        sources=[
            ValuationSourceDTO(
                title=s.title,
                url=s.url,
                price=float(s.price) if s.price else None,
                surface_m2=s.surface_m2,
                date_found=s.date_found.isoformat() if s.date_found else None,
            )
            for s in val.sources
        ],
        raw_notes=val.raw_notes,
        cooldown_days_remaining=cooldown_days_remaining,
        is_cached=is_cached,
    )
```

### 3.3 Endpoint: `POST /api/properties/{id}/valuation`
- **Contrato:**
  `force: bool = Query(default=False, description="Forzar nuevo cálculo omitiendo el periodo de cooldown restante.")`
- **Mapeo explícito de excepciones y códigos de estado:**
  ```python
  @router.post("/{property_id}/valuation", response_model=PropertyValuationResponse)
  async def request_property_valuation(
      property_id: str,
      force: bool = Query(default=False, description="Forzar recálculo omitiendo el cooldown"),
      current_user: User = Depends(get_current_user),
      use_case: RequestPropertyValuationUseCase = Depends(get_request_property_valuation_use_case),
  ) -> PropertyValuationResponse:
      try:
          result = use_case.execute(property_id=property_id, user_id=current_user.id, force=force)
          return _valuation_entity_to_response(
              result.valuation,
              cooldown_days_remaining=result.cooldown_days_remaining,
              is_cached=result.is_cached,
          )
      except MissingPhysicalAttributesError as e:
          raise HTTPException(status_code=422, detail=str(e))
      except ValueError as e:
          raise HTTPException(status_code=404, detail=str(e))
      except ValuationRateLimitError as e:
          headers = {}
          if e.retry_after_seconds:
              headers["Retry-After"] = str(e.retry_after_seconds)
          raise HTTPException(status_code=429, detail=str(e), headers=headers)
      except MarketValuationError as e:
          raise HTTPException(status_code=502, detail=f"Error en proveedor de valoración: {e}")
      except Exception as e:
          raise HTTPException(status_code=500, detail=f"Error interno inesperado: {e}")
  ```

### 3.4 Endpoint: `GET /api/properties/{id}/valuation/latest`
Se actualiza para invocar `use_case.get_latest(property_id, current_user.id)`:
```python
@router.get("/{property_id}/valuation/latest", response_model=PropertyValuationResponse | None)
async def get_latest_valuation(
    property_id: str,
    current_user: User = Depends(get_current_user),
    use_case: RequestPropertyValuationUseCase = Depends(get_request_property_valuation_use_case),
) -> PropertyValuationResponse | None:
    try:
        result = use_case.get_latest(property_id=property_id, user_id=current_user.id)
        if result is None:
            return None
        return _valuation_entity_to_response(
            result.valuation,
            cooldown_days_remaining=result.cooldown_days_remaining,
            is_cached=result.is_cached,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 4. Inyección de Dependencias
En `backend/api/dependencies.py`:
```python
def get_request_property_valuation_use_case(
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    valuation_repo: SQLitePropertyValuationRepository = Depends(get_valuation_repo),
    valuation_port: MarketValuationPort = Depends(get_market_valuation_port),
) -> RequestPropertyValuationUseCase:
    cooldown_days = int(os.getenv("VALUATION_COOLDOWN_DAYS", "30"))
    return RequestPropertyValuationUseCase(
        property_repo=property_repo,
        valuation_repo=valuation_repo,
        valuation_port=valuation_port,
        cooldown_days=cooldown_days,
    )
```

---

## 5. Estrategia de Testing

1. **`tests/unit/backend/application/test_f31_valuation_use_cases.py`:**
   - Propiedad inexistente o ajena levanta `ValueError` (mapea a 404).
   - Inmueble con `surface_m2=None` o `<= 0` levanta `MissingPhysicalAttributesError` (mapea a 422).
   - Propiedad sin valoración previa calcula e invoca el puerto, guardando nueva valoración (`is_cached=False`, `cooldown_days_remaining=30`).
   - Propiedad con valoración reciente (`days_elapsed < 30`) retorna datos cacheados sin invocar puerto si `force=False` (`is_cached=True`, `cooldown_days_remaining > 0`).
   - Propiedad con valoración reciente invocada con `force=True` recalcula, invoca puerto y persiste nuevo registro en BD.
   - `get_latest` calcula correctamente `cooldown_days_remaining` y devuelve `None` si no hay valoraciones.
2. **`tests/integration/backend/test_f31_valuation_api.py`:**
   - `POST /api/properties/{id}/valuation` exitoso retorna 200 con `PropertyValuationResponse`.
   - Segundo `POST` inmediato retorna 200 con `is_cached=True` y `cooldown_days_remaining > 0`.
   - `POST ...?force=true` recalcula y retorna `is_cached=False`.
   - Propiedad sin `surface_m2` retorna 422 con detalle descriptivo.
   - Fallo por `ValuationRateLimitError` retorna 429 con cabecera `Retry-After`.
   - Fallo por `MarketValuationError` retorna 502 Bad Gateway.
   - Intento de valoración de inmueble inexistente o de otro usuario retorna 404.

---

## 6. Criterios de Aceptación
1. `MissingPhysicalAttributesError` implementado en dominio heredando de `MarketValuationError`.
2. `RequestPropertyValuationUseCase` orquesta validación, cooldown, llamada al puerto y persistencia en SQLite.
3. Router HTTP mapea explícitamente 200, 404, 422, 429 y 502 sin fugas de lógica de negocio.
4. Cobertura del 100% en tests unitarios y de integración de la feature.
