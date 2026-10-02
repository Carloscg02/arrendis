# F-30: Puerto de Valoración y Adaptador Gemini con Search Grounding

## 1. Visión y Objetivos

El objetivo de esta feature es dotar a la arquitectura de Arrendis de un puerto de dominio agnóstico (`MarketValuationPort`) y su implementación de infraestructura (`GeminiMarketValuationAdapter`) utilizando el SDK oficial `google-genai` con soporte de **Google Search Grounding**.

Esto permite:
1. Consultar el mercado inmobiliario real español en vivo sin cuotas prohibitivas de portales de anuncios.
2. Anclar la estimación a testigos reales con URLs activas gracias al grounding de Google Search.
3. Devolver rangos de venta, rangos de alquiler, nivel de confianza, desglose de factores de corrección y enlaces de referencia estructurados.
4. Mantener la capa de dominio 100% aislada de Google Gemini y dependencias de infraestructura.

---

## 2. Contratos y Dominio

### 2.1 Excepciones de Dominio
En `backend/domain/entities.py`:

```python
class MarketValuationError(Exception):
    """Error base de dominio para fallos en la estimación de mercado."""
    def __init__(self, message: str, provider: str = "unknown") -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")

class ValuationRateLimitError(MarketValuationError):
    """Exceso de cuota o rate limit alcanzado en el servicio de valoración."""
    def __init__(self, provider: str = "unknown", retry_after_seconds: int | None = None) -> None:
        self.retry_after_seconds = retry_after_seconds
        msg = "Límite de tasa excedido en el servicio de valoración"
        if retry_after_seconds:
            msg += f" (reintentar tras {retry_after_seconds}s)"
        super().__init__(msg, provider=provider)
```

### 2.2 Value Object: `MarketValuationResult`
En `backend/domain/value_objects.py`:

```python
@dataclass(frozen=True)
class MarketValuationResult:
    """Resultado bruto devuelto por el puerto de estimación de mercado."""
    sale_range: ValuationRange
    rent_range: ValuationRange
    confidence: ValuationConfidence
    reasoning_factors: list[ReasoningFactor] = field(default_factory=list)
    sources: list[ValuationSource] = field(default_factory=list)
    raw_notes: str | None = None

    def __post_init__(self) -> None:
        if self.sale_range.min_price.currency != self.rent_range.min_price.currency:
            raise ValueError("Las divisas de los rangos de venta y alquiler deben coincidir.")
        if self.confidence in (ValuationConfidence.LOW, ValuationConfidence.MEDIUM):
            if not self.reasoning_factors and not (self.raw_notes and self.raw_notes.strip()):
                raise ValueError("Se requiere al menos un factor o nota explicativa para confianza LOW o MEDIUM.")
```

### 2.3 Puerto: `MarketValuationPort`
En `backend/domain/ports.py`:

```python
class MarketValuationPort(ABC):
    """Puerto de salida agnóstico para la estimación de valor de venta y alquiler de inmuebles."""

    @abstractmethod
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
        """Estima el valor de mercado de compraventa y alquiler mensual.

        Args:
            address: Dirección física completa (calle, número, código postal, ciudad).
            surface_m2: Superficie construida en metros cuadrados (> 0).
            property_type: Tipología del inmueble (piso, unifamiliar, local, garaje).
            bedrooms: Número de dormitorios (None o >= 0, ej: 0 para estudios).
            bathrooms: Número de cuartos de baño (None o >= 0).
            floor: Planta (opcional, None si unifamiliar o desconocido).
            has_elevator: Presencia de ascensor (opcional).
            condition: Estado de conservación (opcional).

        Returns:
            MarketValuationResult con los rangos calculados, testigos y factores explicativos.

        Raises:
            ValuationRateLimitError: Si se agotan los reintentos por límite de cuota (429).
            MarketValuationError: Si ocurre un error en la llamada o en la validación estructurada.
            ValueError: Si los parámetros físicos de entrada son inválidos (ej. surface_m2 <= 0).
        """
        ...
```

---

## 3. Adaptador de Infraestructura: `GeminiMarketValuationAdapter`

### 3.1 Ubicación
`backend/adapters/gemini_valuation_adapter.py`.

### 3.2 Incompatibilidad Crítica del SDK `google-genai` (Grounding vs Schema)
> **ADVERTENCIA TÉCNICA:**  
> En la API de Google Gemini (`google-genai` SDK), el uso concurrente de herramientas `tools=[types.Tool(google_search=types.GoogleSearch())]` junto con `response_mime_type="application/json"` o `response_schema` está **terminantemente prohibido por la API** y devuelve error HTTP 400: `Tool use with a response mime type: 'application/json' is unsupported`.  
> Por tanto, `GenerateContentConfig` se instancia **sin** `response_mime_type` ni `response_schema`. El formato JSON estructurado se impone estrictamente vía system instruction y se decodifica limpiando delimitadores markdown (````json ... ````).

### 3.3 Configuración de Generación y Timeouts
- Modelo: `os.getenv("GEMINI_MODEL", "gemini-2.5-flash")`
- `temperature = 0.2`
- `tools = [types.Tool(google_search=types.GoogleSearch())]`
- Configuración de cliente con timeout holgado para soportar la síntesis multi-fuente en vivo (45 segundos):
  ```python
  self.client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha", "timeout": 45.0})
  ```

### 3.4 Validación Interna con Pydantic (`_GeminiValuationPayload`)
Para evitar `KeyError` o tipos inesperados, la salida del LLM se valida con Pydantic antes de instanciar entidades de dominio:

```python
class _RangePayload(BaseModel):
    min: Decimal
    median: Decimal
    max: Decimal

class _FactorPayload(BaseModel):
    factor_name: str
    impact_percent: float  # Ej: 7.5 para +7.5%
    description: str

class _SourcePayload(BaseModel):
    title: str
    url: str
    price: Decimal | None = None
    surface_m2: int | None = None

class _GeminiValuationPayload(BaseModel):
    sale_range: _RangePayload
    rent_range: _RangePayload
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    reasoning_factors: list[_FactorPayload] = Field(default_factory=list)
    sources: list[_SourcePayload] = Field(default_factory=list)
    raw_notes: str | None = None
```

### 3.5 Reglas de Normalización de Factores y Confianza
1. **Escala de `impact_percent`:**
   En F-29, el dominio usa notación fraccional (`Decimal("0.05")` para $+5\%$). Si el payload del LLM reporta valores porcentuales enteros/decimales habituales (ej. `7.5` o `-10.0`), el adaptador normaliza automáticamente:
   `normalized_impact = Decimal(str(f.impact_percent)) / Decimal("100")` si `abs(f.impact_percent) > 1.0`, garantizando compatibilidad absoluta con F-29.
2. **Normalización de `confidence`:**
   Se normaliza con `.lower()`: `ValuationConfidence(payload.confidence.lower())`. Si el valor es desconocido, fallback seguro a `ValuationConfidence.LOW`.

### 3.6 Extracción Defensiva de Fuentes de Grounding
Si la respuesta de Gemini contiene metadatos de búsqueda (`response.candidates[0].grounding_metadata.grounding_chunks`):
1. Se itera sobre cada chunk.
2. Se valida defensivamente:
   - Que `chunk.web` no sea `None`.
   - Que `chunk.web.uri` exista, sea string y comience por `http://` o `https://`.
   - Que `title` no esté vacío; si está vacío o es `None`, se utiliza fallback a `chunk.web.title or chunk.web.uri or "Referencia web encontrada"`.
3. Deduplicación: Si la URL ya existe en la lista de `sources` del payload, no se duplica.

### 3.7 Manejo de Errores y Reintentos
- Reintentos con exponential backoff (1s a 30s) ante `APIError(429)` o errores 5xx / timeouts de red.
- Mapeo de excepciones:
  - Error 429 agotado $\rightarrow$ `ValuationRateLimitError(provider="gemini")`.
  - Fallo de parseo JSON o error de API $\rightarrow$ `MarketValuationError(provider="gemini")`.
  - Candidato vacío o bloqueado por filtros $\rightarrow$ `MarketValuationError("Respuesta bloqueada por filtros de seguridad", provider="gemini")`.

---

## 4. `MockMarketValuationAdapter` Determinista

Para tests unitarios, CI/CD y desarrollo local sin credenciales externas, se define `MockMarketValuationAdapter(MarketValuationPort)` con coeficientes deterministas:
- Multiplicador por estado (`condition`):
  - `A_REFORMAR`: `0.80`
  - `BUEN_ESTADO`: `1.00`
  - `REFORMADO`: `1.15`
  - `A_ESTRENAR`: `1.30`
  - `None`: `1.00`
- Factor ascensor (`has_elevator` y `floor`):
  - Si `has_elevator is True`: `+5%`
  - Si `has_elevator is False` y `floor is not None and floor >= 2`: `-7%`
  - En otro caso: `0%`
- Venta mediana: `surface_m2 * 2200 * factor_estado * (1 + factor_ascensor)`
- Renta mediana: `surface_m2 * 11 * factor_estado * (1 + factor_ascensor)`
- Horquillas:
  - `min_price = median * 0.90`
  - `max_price = median * 1.10`
- Confianza: `ValuationConfidence.HIGH`
- Fuentes: 2 testigos mock realistas con URLs simuladas.

---

## 5. Inyección de Dependencias (FastAPI)

En `backend/api/dependencies.py`:
```python
def get_market_valuation_port() -> MarketValuationPort:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and os.getenv("USE_MOCK_VALUATION", "false").lower() != "true":
        return GeminiMarketValuationAdapter(api_key=api_key)
    return MockMarketValuationAdapter()
```

---

## 6. Estrategia de Testing

1. **`tests/unit/backend/domain/test_f30_valuation_domain.py`:**
   - Invariantes de `MarketValuationResult`: divisas dispares fallan, LOW/MEDIUM sin justificación falla, validación de rangos.
2. **`tests/unit/backend/adapters/test_gemini_valuation_adapter.py`:**
   - Test de inicialización y llamada a Gemini sin `response_schema` ni `response_mime_type`.
   - Test de decodificación JSON con markdown stripping (````json ... ````).
   - Test de normalización de factores porcentuales (`7.5` -> `Decimal("0.075")`).
   - Test de extracción defensiva de `grounding_chunks` (URLs malformadas, títulos ausentes, deduplicación).
   - Test de manejo de excepciones y reintentos (429 -> `ValuationRateLimitError`, 500 -> `MarketValuationError`).
   - Test de `MockMarketValuationAdapter` verificando fórmulas deterministas.

---

## 7. Criterios de Aceptación
1. Excepciones `MarketValuationError` y `ValuationRateLimitError` en dominio.
2. `MarketValuationPort` y `MarketValuationResult` implementados y cubiertos por tests.
3. `GeminiMarketValuationAdapter` integrado de forma robusta con Google Search Grounding y sin provocar errores HTTP 400.
4. `MockMarketValuationAdapter` funcional y reproducible.
5. Inyección de dependencias en `backend/api/dependencies.py`.
6. 100% de tests de la suite pasando limpiamente.
