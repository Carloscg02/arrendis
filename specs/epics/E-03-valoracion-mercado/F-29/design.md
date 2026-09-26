# 📐 F-29: Atributos Físicos de Propiedad y Entidades de Dominio de Valoración — Design

> **Épica:** E-03 — Estimación de Mercado y Orientación de Renta por IA  
> **Estado:** Borrador — Pendiente de aprobación  
> **Dependencias:** F-08 (Multi-tenancy) ✅, F-09 (Datos Fiscales) ✅, F-10 (Contratos) ✅  
> **Fecha:** 2026-09-26  

---

## 1. Lenguaje Ubicuo (Términos nuevos)

| Término | Definición | Ejemplo en el proyecto |
|---|---|---|
| **PropertyCondition** | Enum que clasifica el estado de conservación física de la vivienda: a reformar, buen estado, reformado o a estrenar. | `PropertyCondition.REFORMADO` |
| **PhysicalAttributes** | Conjunto de características físicas intrínsecas del inmueble: superficie útil/construida ($m^2$), número de habitaciones, baños, planta y ascensor. | `surface_m2=85, bedrooms=2, floor=3, has_elevator=True` |
| **ValuationConfidence** | Nivel de confianza del análisis de mercado según la dispersión y cantidad de ofertas comparables halladas: ALTA, MEDIA o BAJA. | `ValuationConfidence.HIGH` |
| **ValuationRange** | Value Object inmutable que representa una horquilla monetaria: precio mínimo, precio mediano recomendado y precio máximo. | `ValuationRange(min_price=Money(1100), median_price=Money(1200), max_price=Money(1350))` |
| **ReasoningFactor** | Value Object inmutable que cuantifica el impacto porcentual y la justificación de una característica en el precio. | `ReasoningFactor(factor_name="Presencia de ascensor", impact_percent=Decimal("0.05"), description="Planta intermedia con ascensor")` |
| **ValuationSource** | Value Object inmutable que documenta una oferta testigo real encontrada en el mercado: título, URL del anuncio, precio y $m^2$. | `ValuationSource(title="Piso en Calle Almagro", url="https://...", price=Decimal("1250"), surface_m2=80)` |
| **PropertyValuation** | Entidad de dominio con identidad propia (UUID) que registra el informe de estimación de mercado para venta y alquiler de una propiedad en una fecha dada. | `PropertyValuation(id="...", property_id="...", sale_range=..., rent_range=...)` |
| **PropertyValuationRepository** | Puerto de salida que define los contratos de persistencia y consulta para los informes de valoración. | `PropertyValuationRepository` |

---

## 2. Enumeraciones Nuevas

```python
# backend/domain/entities.py

class PropertyCondition(Enum):
    """Estado de conservación de un inmueble."""
    A_REFORMAR = "a_reformar"
    BUEN_ESTADO = "buen_estado"
    REFORMADO = "reformado"
    A_ESTRENAR = "a_estrenar"


class ValuationConfidence(Enum):
    """Nivel de confianza de la estimación de mercado."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

---

## 3. Modificaciones a Entidades Existentes: `Property`

Se añaden a la entidad `Property` los campos físicos necesarios para la valoración inmobiliaria (todos opcionales con `default=None` para preservar retrocompatibilidad con las propiedades ya existentes):

```python
# backend/domain/entities.py

@dataclass
class Property:
    name: str
    address: Address
    property_type: PropertyType
    user_id: str
    status: PropertyStatus = PropertyStatus.AVAILABLE
    image_filename: str | None = None
    cadastral_ref: str | None = None
    cadastral_breakdown: CadastralBreakdown | None = None
    acquisition_cost: AcquisitionCost | None = None
    acquisition_date: date | None = None
    cups_electricity: str | None = None
    cups_gas: str | None = None
    cups_water: str | None = None
    # ── F-29: Atributos Físicos de Mercado ──
    surface_m2: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    floor: int | None = None
    has_elevator: bool | None = None
    condition: PropertyCondition | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # (Validaciones previas de nombre, user_id, cadastral_ref, CUPS...)
        # ── Validaciones F-29 ──
        if self.surface_m2 is not None and self.surface_m2 <= 0:
            raise ValueError("La superficie en m² debe ser estrictamente positiva (> 0).")
        if self.bedrooms is not None and self.bedrooms < 0:
            raise ValueError("El número de habitaciones no puede ser negativo.")
        if self.bathrooms is not None and self.bathrooms < 0:
            raise ValueError("El número de baños no puede ser negativo.")
```

---

## 4. Value Objects Nuevos

```python
# backend/domain/value_objects.py

@dataclass(frozen=True)
class ValuationRange:
    """Horquilla de precios estimada (mínimo, mediano, máximo)."""
    min_price: Money
    median_price: Money
    max_price: Money

    def __post_init__(self) -> None:
        if self.min_price.currency != self.median_price.currency or self.median_price.currency != self.max_price.currency:
            raise ValueError("Todas las cantidades del rango deben tener la misma moneda.")
        if self.min_price.amount > self.median_price.amount:
            raise ValueError(f"El precio mínimo ({self.min_price}) no puede superar al mediano ({self.median_price}).")
        if self.median_price.amount > self.max_price.amount:
            raise ValueError(f"El precio mediano ({self.median_price}) no puede superar al máximo ({self.max_price}).")


@dataclass(frozen=True)
class ReasoningFactor:
    """Factor explicativo de ajuste que impacta en la valoración."""
    factor_name: str
    impact_percent: Decimal  # Ejemplo: Decimal("0.05") para +5%, Decimal("-0.10") para -10%
    description: str

    def __post_init__(self) -> None:
        if not self.factor_name or not self.factor_name.strip():
            raise ValueError("El nombre del factor no puede estar vacío.")
        if not self.description or not self.description.strip():
            raise ValueError("La descripción del factor no puede estar vacía.")


@dataclass(frozen=True)
class ValuationSource:
    """Testigo o anuncio de referencia encontrado en la búsqueda web."""
    title: str
    url: str
    price: Decimal | None = None
    surface_m2: int | None = None
    date_found: date | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("El título de la fuente no puede estar vacío.")
        if not self.url or not self.url.strip() or not (self.url.startswith("http://") or self.url.startswith("https://")):
            raise ValueError("La URL de la fuente debe ser válida (http:// o https://).")
```

---

## 5. Nueva Entidad de Dominio: `PropertyValuation`

```python
# backend/domain/entities.py

@dataclass
class PropertyValuation:
    """Informe de valoración de mercado para venta y alquiler de una propiedad."""
    property_id: str
    valuation_date: date
    sale_range: ValuationRange
    rent_range: ValuationRange
    confidence: ValuationConfidence
    reasoning_factors: list[ReasoningFactor] = field(default_factory=list)
    sources: list[ValuationSource] = field(default_factory=list)
    raw_notes: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.property_id or not self.property_id.strip():
            raise ValueError("El property_id no puede estar vacío.")
        if self.sale_range.min_price.currency != self.rent_range.min_price.currency:
            raise ValueError("Las divisas de venta y alquiler deben coincidir.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PropertyValuation):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

---

## 6. Puertos Nuevos (`backend/domain/ports.py`)

### 6.1 `PropertyValuationRepository`

```python
class PropertyValuationRepository(ABC):
    """Puerto de salida para persistir y consultar informes de valoración."""

    @abstractmethod
    def save(self, valuation: PropertyValuation) -> None:
        """Guarda o actualiza una valoración."""
        ...

    @abstractmethod
    def find_by_id(self, valuation_id: str) -> PropertyValuation | None:
        """Recupera una valoración por su ID."""
        ...

    @abstractmethod
    def find_latest_by_property_id(self, property_id: str) -> PropertyValuation | None:
        """Recupera la valoración más reciente de una propiedad."""
        ...

    @abstractmethod
    def list_by_property_id(self, property_id: str) -> list[PropertyValuation]:
        """Recupera el histórico completo de valoraciones de una propiedad ordenadas por fecha descendente."""
        ...
```

### 6.2 Actualización de `PropertyRepository`

El método `save()` de `PropertyRepository` almacenará los nuevos campos. Además se añade un método específico de actualización rápida de atributos físicos:

```python
    @abstractmethod
    def update_physical_attributes(
        self,
        property_id: str,
        surface_m2: int | None,
        bedrooms: int | None,
        bathrooms: int | None,
        floor: int | None,
        has_elevator: bool | None,
        condition: PropertyCondition | None,
    ) -> None:
        """Actualiza exclusivamente los atributos físicos de una propiedad."""
        ...
```

---

## 7. Persistencia SQLite (`backend/adapters/sqlite_adapter.py`)

### 7.1 Migración de la tabla `properties`

```sql
ALTER TABLE properties ADD COLUMN surface_m2 INTEGER DEFAULT NULL;
ALTER TABLE properties ADD COLUMN bedrooms INTEGER DEFAULT NULL;
ALTER TABLE properties ADD COLUMN bathrooms INTEGER DEFAULT NULL;
ALTER TABLE properties ADD COLUMN floor INTEGER DEFAULT NULL;
ALTER TABLE properties ADD COLUMN has_elevator INTEGER DEFAULT NULL;
ALTER TABLE properties ADD COLUMN condition TEXT DEFAULT NULL;
```

### 7.2 Nueva tabla `property_valuations`

```sql
CREATE TABLE IF NOT EXISTS property_valuations (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    valuation_date TEXT NOT NULL,
    sale_price_min TEXT NOT NULL,
    sale_price_median TEXT NOT NULL,
    sale_price_max TEXT NOT NULL,
    rent_price_min TEXT NOT NULL,
    rent_price_median TEXT NOT NULL,
    rent_price_max TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    confidence TEXT NOT NULL,
    reasoning_factors TEXT NOT NULL, -- JSON serializado
    sources TEXT NOT NULL,           -- JSON serializado
    raw_notes TEXT DEFAULT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_property_valuations_prop_date 
ON property_valuations(property_id, valuation_date DESC);
```

---

## 8. Esquemas DTO / API (`backend/api/schemas.py`)

```python
class PropertyConditionEnum(str, Enum):
    A_REFORMAR = "a_reformar"
    BUEN_ESTADO = "buen_estado"
    REFORMADO = "reformado"
    A_ESTRENAR = "a_estrenar"


class ValuationConfidenceEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PhysicalAttributesUpdate(BaseModel):
    surface_m2: int | None = Field(default=None, gt=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    floor: int | None = None
    has_elevator: bool | None = None
    condition: PropertyConditionEnum | None = None


class ValuationRangeDTO(BaseModel):
    min: float
    median: float
    max: float
    currency: str = "EUR"


class ReasoningFactorDTO(BaseModel):
    factor_name: str
    impact_percent: float
    description: str


class ValuationSourceDTO(BaseModel):
    title: str
    url: str
    price: float | None = None
    surface_m2: int | None = None
    date_found: str | None = None


class PropertyValuationResponse(BaseModel):
    id: str
    property_id: str
    valuation_date: str
    sale_range: ValuationRangeDTO
    rent_range: ValuationRangeDTO
    confidence: ValuationConfidenceEnum
    reasoning_factors: list[ReasoningFactorDTO]
    sources: list[ValuationSourceDTO]
    raw_notes: str | None = None
```

---

## 9. Endpoints de la API

* `PATCH /api/properties/{property_id}/physical-attributes`: Actualiza los atributos físicos del inmueble.
* `GET /api/properties/{property_id}/valuation/latest`: Devuelve el último informe de valoración guardado (o `null` si aún no se ha tasado).
* `GET /api/properties/{property_id}/valuation/history`: Devuelve el histórico de valoraciones del inmueble.

---

## 10. Wireframe UI (Atelier Editorial — `DESIGN.md`)

Formulario de edición de inmueble y tarjeta de características físicas:

```
┌────────────────────────────────────────────────────────────────────────┐
│  DETALLES FÍSICOS Y DE MERCADO                                         │
│                                                                        │
│  Superficie (m²)       Habitaciones            Baños                  │
│  ┌──────────────────┐  ┌────────────────────┐  ┌─────────────────────┐ │
│  │ 85               │  │ 2                  │  │ 1                   │ │
│  └──────────────────┘  └────────────────────┘  └─────────────────────┘ │
│                                                                        │
│  Planta                Ascensor                Estado Conservación    │
│  ┌──────────────────┐  ┌────────────────────┐  ┌─────────────────────┐ │
│  │ 3ª               │  │ [x] Con ascensor   │  │ Reformado        ▼  │ │
│  └──────────────────┘  └────────────────────┘  └─────────────────────┘ │
│                                                                        │
│  [ Guardar Cambios Físicos ]                                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Especificación de Tests

| ID | Tipo | Qué verifica |
|---|---|---|
| `TEST-F29-01` | Unit (Domain) | Instanciación válida de `Property` con atributos físicos (`surface_m2`, `condition`, etc.). |
| `TEST-F29-02` | Unit (Domain) | Validación de `surface_m2 <= 0` o `bedrooms < 0` lanza `ValueError`. |
| `TEST-F29-03` | Unit (Domain) | `ValuationRange` valida que `min <= median <= max` y homogeneidad de divisa. |
| `TEST-F29-04` | Unit (Domain) | `ReasoningFactor` y `ValuationSource` validan campos requeridos y formato de URL. |
| `TEST-F29-05` | Unit (Domain) | Entidad `PropertyValuation` igualdad por `id` y validación de `property_id`. |
| `TEST-F29-06` | Integration (SQLite) | Migración y persistencia de columnas físicas en `properties` (save, update, find_by_id). |
| `TEST-F29-07` | Integration (SQLite) | CRUD completo en `PropertyValuationRepository`: `save`, `find_latest_by_property_id`, `list_by_property_id`. |
| `TEST-F29-08` | Integration (API) | `PATCH /api/properties/{id}/physical-attributes` actualiza campos y devuelve DTO actualizado. |
| `TEST-F29-09` | Integration (API) | `GET /api/properties/{id}/valuation/latest` devuelve 200 con la valoración más reciente o 404/204 si no hay. |

---

## 12. 📚 El Rincón del Estudiante

### 🎓 Concepto 1: Entidad vs. Value Object en Valoraciones Inmobiliarias

En Domain-Driven Design (DDD), distinguir entre **Entidad** y **Value Object (VO)** es crucial para no llenar la base de datos de complejidad innecesaria:

* **¿Por qué `PropertyValuation` es una Entidad?**  
  Porque representa un **hecho en el tiempo con ciclo de vida e identidad**. Si valoramos el piso hoy y volvemos a valorarlo dentro de 6 meses, queremos guardar ambos informes en el historial. Dos valoraciones que casualmente estimen el mismo precio son dos informes distintos con IDs distintos y fechas distintas.
* **¿Por qué `ValuationRange`, `ReasoningFactor` y `ValuationSource` son Value Objects?**  
  Porque **no tienen identidad propia**. Si una fuente es `https://idealista.com/inmueble/123` con precio `1.200 €`, solo nos importa su contenido. No necesitamos una tabla SQL con un ID para cada factor de razonamiento ni para cada URL; se serializan limpiamente en JSON dentro de la fila de la valoración.

```
       ┌───────────────────────────┐
       │     PropertyValuation     │  ◀── ENTIDAD (UUID único, fecha, histórico)
       │  id: "val-987"            │
       └─────────────┬─────────────┘
                     │ Contiene
       ┌─────────────▼─────────────┐
       │      ValuationRange       │  ◀── VALUE OBJECT (Inmutable, sin ID)
       │  min: 1.100€              │
       │  median: 1.200€           │
       │  max: 1.350€              │
       └───────────────────────────┘
```

### 🎓 Concepto 2: Evolución No Destructiva del Esquema en SQLite (`ALTER TABLE ADD COLUMN`)

Cuando una aplicación ya está en funcionamiento (como Arrendis, que tiene propiedades guardadas), **nunca debemos borrar la base de datos ni recrear las tablas** para añadir nuevos campos.

En SQLite, la instrucción:
```sql
ALTER TABLE properties ADD COLUMN surface_m2 INTEGER DEFAULT NULL;
```
agrega la columna de manera instantánea y segura. Las filas que ya existían tendrán `NULL` en ese campo, sin romper ninguna consulta previa. Al envolver cada `ALTER TABLE` en un bloque `try...except sqlite3.OperationalError: pass` dentro de `_create_tables()`, garantizamos que la aplicación pueda arrancar en cualquier entorno (desarrollo, tests o producción en Docker) ejecutando la migración automáticamente sin fallar si la columna ya existía.
