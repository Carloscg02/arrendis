# 📐 F-09: Datos Fiscales de Propiedad (Catastral + Adquisición) — Design

> **Épica:** E-01 — Sistema de Fiscalidad y Declaración de Impuestos  
> **Estado:** Borrador — Pendiente de aprobación  
> **Dependencia:** F-08 (Multi-tenancy) ✅ completada  
> **Fecha:** 2026-08-01

---

## 1. Lenguaje Ubicuo (Términos nuevos)

| Término | Definición | Ejemplo en el proyecto |
|---|---|---|
| **CadastralBreakdown** | Value Object inmutable que desglosa el valor catastral total de un inmueble en `land_value` (suelo) y `construction_value` (construcción). Se obtiene del recibo del IBI. | `CadastralBreakdown(land_value=Decimal("40000"), construction_value=Decimal("80000"))` |
| **AcquisitionCost** | Value Object inmutable que captura el coste total de adquisición: precio de compra desglosado en suelo y construcción, más impuestos y gastos de compra. | `AcquisitionCost(purchase_price=Decimal("200000"), construction_portion=Decimal("120000"), land_portion=Decimal("80000"), transfer_tax=Decimal("16000"), notary_fees=Decimal("800"), registry_fees=Decimal("400"))` |
| **FiscalData** | Concepto compuesto que agrupa los datos fiscales opcionales de una propiedad: su `CadastralBreakdown` y su `AcquisitionCost`. No es una entidad separada, sino campos opcionales en la propiedad. |  |
| **Referencia Catastral** | Identificador único de 20 caracteres asignado por el Catastro a cada inmueble. Formato: 7 dígitos finca + 7 dígitos parcela + 4 caracteres control + 2 caracteres piso/puerta. | `"1234567AB1234C0001XY"` |

---

## 2. Value Objects del Dominio

### 2.1 `CadastralBreakdown`

```python
# backend/domain/value_objects.py (NUEVO)

@dataclass(frozen=True)
class CadastralBreakdown:
    """Desglose del valor catastral de un inmueble.

    Se obtiene del recibo del IBI. El valor catastral total = land_value + construction_value.
    El suelo NO se amortiza; solo la construcción.

    Inmutable: una vez creado, no se puede modificar.
    """
    land_value: Decimal          # Valor catastral del suelo (€)
    construction_value: Decimal  # Valor catastral de la construcción (€)

    def __post_init__(self) -> None:
        if self.land_value < 0:
            raise ValueError(
                f"El valor catastral del suelo no puede ser negativo: {self.land_value}"
            )
        if self.construction_value < 0:
            raise ValueError(
                f"El valor catastral de la construcción no puede ser negativo: {self.construction_value}"
            )
        if self.land_value == 0 and self.construction_value == 0:
            raise ValueError(
                "El desglose catastral no puede ser todo ceros."
            )

    @property
    def total_value(self) -> Decimal:
        """Valor catastral total = suelo + construcción."""
        return self.land_value + self.construction_value
```

### 2.2 `AcquisitionCost`

```python
# backend/domain/value_objects.py (NUEVO)

@dataclass(frozen=True)
class AcquisitionCost:
    """Coste total de adquisición de un inmueble.

    Captura el precio de compra desglosado (construcción vs suelo) más los gastos
    asociados a la compra: ITP, notaría y registro.

    Inmutable: una vez creado, no se puede modificar.
    """
    purchase_price: Decimal        # Precio total de compraventa (€)
    construction_portion: Decimal  # Porción del precio atribuible a la construcción (€)
    land_portion: Decimal          # Porción del precio atribuible al suelo (€)
    transfer_tax: Decimal          # Impuesto de Transmisiones Patrimoniales (ITP) (€)
    notary_fees: Decimal           # Gastos de notaría (€)
    registry_fees: Decimal         # Gastos de registro de la propiedad (€)

    def __post_init__(self) -> None:
        for field_name in [
            "purchase_price", "construction_portion", "land_portion",
            "transfer_tax", "notary_fees", "registry_fees"
        ]:
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} no puede ser negativo: {value}")

        if self.purchase_price <= 0:
            raise ValueError("El precio de compraventa debe ser positivo.")

        # construction_portion + land_portion deben sumar purchase_price
        total_portions = self.construction_portion + self.land_portion
        if total_portions != self.purchase_price:
            raise ValueError(
                f"construction_portion ({self.construction_portion}) + "
                f"land_portion ({self.land_portion}) = {total_portions}, "
                f"pero purchase_price es {self.purchase_price}. Deben coincidir."
            )

    @property
    def total_acquisition_expenses(self) -> Decimal:
        """Total de gastos asociados a la compra (ITP + notaría + registro)."""
        return self.transfer_tax + self.notary_fees + self.registry_fees

    @property
    def total_cost(self) -> Decimal:
        """Coste total = precio de compra + todos los gastos."""
        return self.purchase_price + self.total_acquisition_expenses
```

---

## 3. Extensión de la Entidad `Property`

La entidad `Property` existente se extiende con **campos opcionales** para mantener la compatibilidad con F-01 a F-08. Las propiedades creadas antes de F-09 seguirán funcionando con `cadastral_ref = None`, `cadastral_breakdown = None` y `acquisition_cost = None`.

```python
# backend/domain/entities.py — Cambios en Property

@dataclass
class Property:
    name: str
    address: Address
    property_type: PropertyType
    user_id: str
    status: PropertyStatus = PropertyStatus.AVAILABLE
    image_filename: str | None = None
    # ── Campos fiscales (F-09) ──────────────────────
    cadastral_ref: str | None = None                        # Referencia catastral (20 chars)
    cadastral_breakdown: CadastralBreakdown | None = None   # Desglose valor catastral
    acquisition_cost: AcquisitionCost | None = None         # Datos de adquisición
    acquisition_date: date | None = None                    # Fecha de compra del inmueble
    # ────────────────────────────────────────────────
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la propiedad (name) no puede estar vacío.")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("El user_id del propietario no puede estar vacío.")
        # Validar referencia catastral si se proporciona
        if self.cadastral_ref is not None:
            ref = self.cadastral_ref.strip()
            if len(ref) != 20:
                raise ValueError(
                    f"La referencia catastral debe tener 20 caracteres, tiene {len(ref)}."
                )

    @property
    def has_fiscal_data(self) -> bool:
        """Indica si la propiedad tiene datos fiscales completos."""
        return (
            self.cadastral_breakdown is not None
            and self.acquisition_cost is not None
            and self.acquisition_date is not None
        )
```

**Estrategia de compatibilidad:** Todos los campos fiscales tienen valor por defecto `None`. El `__post_init__` existente no se altera, solo se extiende con la validación del `cadastral_ref`.

---

## 4. Puerto (Interfaz) — Extensión del `PropertyRepository`

Se añade un nuevo método al puerto existente `PropertyRepository`:

```python
# backend/domain/ports.py — Nuevo método en PropertyRepository

class PropertyRepository(ABC):
    # ... métodos existentes ...

    @abstractmethod
    def update_fiscal_data(
        self,
        property_id: str,
        cadastral_ref: str | None,
        cadastral_breakdown: CadastralBreakdown | None,
        acquisition_cost: AcquisitionCost | None,
        acquisition_date: date | None,
    ) -> None:
        """Actualiza los datos fiscales de una propiedad."""
        ...
```

> **Decisión de diseño:** Se crea un método dedicado `update_fiscal_data` en lugar de usar `save` para evitar sobreescritura accidental de otros campos y para expresar claramente la intención de la operación.

---

## 5. Caso de Uso

### 5.1 `UpdatePropertyFiscalDataUseCase`

```python
# backend/application/use_cases.py (NUEVO)

class UpdatePropertyFiscalDataUseCase:
    """Caso de uso: actualizar los datos fiscales de una propiedad."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(
        self,
        user_id: str,
        property_id: str,
        cadastral_ref: str | None,
        land_value: Decimal | None,
        construction_value: Decimal | None,
        purchase_price: Decimal | None,
        construction_portion: Decimal | None,
        land_portion: Decimal | None,
        transfer_tax: Decimal | None,
        notary_fees: Decimal | None,
        registry_fees: Decimal | None,
        acquisition_date: date | None,
    ) -> Property:
        """Actualiza los datos fiscales de una propiedad existente.

        Recibe datos primitivos, construye los Value Objects y persiste.
        Si todos los campos catastrales son None, cadastral_breakdown será None.
        Si todos los campos de adquisición son None, acquisition_cost será None.
        """
        # 1. Validar que la propiedad existe y pertenece al usuario
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")

        # 2. Construir CadastralBreakdown si hay datos
        cadastral_breakdown: CadastralBreakdown | None = None
        if land_value is not None and construction_value is not None:
            cadastral_breakdown = CadastralBreakdown(
                land_value=land_value,
                construction_value=construction_value,
            )

        # 3. Construir AcquisitionCost si hay datos
        acquisition_cost: AcquisitionCost | None = None
        if purchase_price is not None:
            acquisition_cost = AcquisitionCost(
                purchase_price=purchase_price,
                construction_portion=construction_portion or Decimal("0"),
                land_portion=land_portion or Decimal("0"),
                transfer_tax=transfer_tax or Decimal("0"),
                notary_fees=notary_fees or Decimal("0"),
                registry_fees=registry_fees or Decimal("0"),
            )

        # 4. Persistir
        self._property_repo.update_fiscal_data(
            property_id=property_id,
            cadastral_ref=cadastral_ref,
            cadastral_breakdown=cadastral_breakdown,
            acquisition_cost=acquisition_cost,
            acquisition_date=acquisition_date,
        )

        # 5. Retornar la propiedad actualizada
        updated = self._property_repo.find_by_id(property_id)
        assert updated is not None
        return updated
```

### 5.2 `GetPropertyFiscalDataUseCase`

```python
# backend/application/use_cases.py (NUEVO)

class GetPropertyFiscalDataUseCase:
    """Caso de uso: obtener los datos fiscales de una propiedad."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(self, user_id: str, property_id: str) -> Property:
        """Retorna la propiedad con sus datos fiscales."""
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        return prop
```

---

## 6. Adaptador SQLite

### 6.1 Migración de Esquema

Nuevas columnas en la tabla `properties` (migración `ALTER TABLE`):

```sql
-- Referencia catastral
ALTER TABLE properties ADD COLUMN cadastral_ref TEXT DEFAULT NULL;

-- Desglose catastral (almacenados como TEXT para precisión Decimal)
ALTER TABLE properties ADD COLUMN cadastral_land_value TEXT DEFAULT NULL;
ALTER TABLE properties ADD COLUMN cadastral_construction_value TEXT DEFAULT NULL;

-- Datos de adquisición
ALTER TABLE properties ADD COLUMN acquisition_purchase_price TEXT DEFAULT NULL;
ALTER TABLE properties ADD COLUMN acquisition_construction_portion TEXT DEFAULT NULL;
ALTER TABLE properties ADD COLUMN acquisition_land_portion TEXT DEFAULT NULL;
ALTER TABLE properties ADD COLUMN acquisition_transfer_tax TEXT DEFAULT NULL;
ALTER TABLE properties ADD COLUMN acquisition_notary_fees TEXT DEFAULT NULL;
ALTER TABLE properties ADD COLUMN acquisition_registry_fees TEXT DEFAULT NULL;

-- Fecha de adquisición
ALTER TABLE properties ADD COLUMN acquisition_date TEXT DEFAULT NULL;
```

> **Patrón de migración:** Se sigue el patrón existente de `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL` con `try/except sqlite3.OperationalError: pass` para idempotencia.

### 6.2 Implementación `update_fiscal_data`

```python
# backend/adapters/sqlite_adapter.py — Nuevo método en SQLitePropertyRepository

def update_fiscal_data(
    self,
    property_id: str,
    cadastral_ref: str | None,
    cadastral_breakdown: CadastralBreakdown | None,
    acquisition_cost: AcquisitionCost | None,
    acquisition_date: date | None,
) -> None:
    """Actualiza los datos fiscales de una propiedad en la base de datos."""
    self._conn.execute(
        """
        UPDATE properties SET
            cadastral_ref = ?,
            cadastral_land_value = ?,
            cadastral_construction_value = ?,
            acquisition_purchase_price = ?,
            acquisition_construction_portion = ?,
            acquisition_land_portion = ?,
            acquisition_transfer_tax = ?,
            acquisition_notary_fees = ?,
            acquisition_registry_fees = ?,
            acquisition_date = ?
        WHERE id = ?
        """,
        (
            cadastral_ref,
            str(cadastral_breakdown.land_value) if cadastral_breakdown else None,
            str(cadastral_breakdown.construction_value) if cadastral_breakdown else None,
            str(acquisition_cost.purchase_price) if acquisition_cost else None,
            str(acquisition_cost.construction_portion) if acquisition_cost else None,
            str(acquisition_cost.land_portion) if acquisition_cost else None,
            str(acquisition_cost.transfer_tax) if acquisition_cost else None,
            str(acquisition_cost.notary_fees) if acquisition_cost else None,
            str(acquisition_cost.registry_fees) if acquisition_cost else None,
            acquisition_date.isoformat() if acquisition_date else None,
            property_id,
        ),
    )
    self._conn.commit()
```

### 6.3 Actualización de `_row_to_entity`

```python
@staticmethod
def _row_to_entity(row: sqlite3.Row) -> Property:
    """Convierte una fila de SQLite a una entidad Property."""
    # Reconstruir CadastralBreakdown si hay datos
    cadastral_breakdown = None
    if row["cadastral_land_value"] is not None and row["cadastral_construction_value"] is not None:
        cadastral_breakdown = CadastralBreakdown(
            land_value=Decimal(row["cadastral_land_value"]),
            construction_value=Decimal(row["cadastral_construction_value"]),
        )

    # Reconstruir AcquisitionCost si hay datos
    acquisition_cost = None
    if row["acquisition_purchase_price"] is not None:
        acquisition_cost = AcquisitionCost(
            purchase_price=Decimal(row["acquisition_purchase_price"]),
            construction_portion=Decimal(row["acquisition_construction_portion"]),
            land_portion=Decimal(row["acquisition_land_portion"]),
            transfer_tax=Decimal(row["acquisition_transfer_tax"]),
            notary_fees=Decimal(row["acquisition_notary_fees"]),
            registry_fees=Decimal(row["acquisition_registry_fees"]),
        )

    # Reconstruir acquisition_date
    acquisition_date = None
    if row["acquisition_date"] is not None:
        acquisition_date = date.fromisoformat(row["acquisition_date"])

    return Property(
        id=row["id"],
        name=row["name"],
        address=Address(
            street=row["street"],
            city=row["city"],
            postal_code=row["postal_code"],
            country=row["country"],
        ),
        property_type=PropertyType(row["property_type"]),
        user_id=row["user_id"],
        status=PropertyStatus(row["status"]),
        image_filename=row["image_filename"],
        cadastral_ref=row["cadastral_ref"],
        cadastral_breakdown=cadastral_breakdown,
        acquisition_cost=acquisition_cost,
        acquisition_date=acquisition_date,
    )
```

---

## 7. API REST — Endpoints

### 7.1 Schemas Pydantic

```python
# backend/api/schemas.py (NUEVO)

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

class FiscalDataResponse(BaseModel):
    """Response body con los datos fiscales de una propiedad."""
    property_id: str
    cadastral_ref: str | None = None
    cadastral_breakdown: CadastralBreakdownSchema | None = None
    acquisition_cost: AcquisitionCostSchema | None = None
    acquisition_date: date | None = None
    has_fiscal_data: bool
```

### 7.2 Endpoints

| Método | Path | Descripción | Request | Response |
|---|---|---|---|---|
| `GET` | `/api/properties/{id}/fiscal-data` | Obtener datos fiscales | — | `FiscalDataResponse` |
| `PUT` | `/api/properties/{id}/fiscal-data` | Crear/Actualizar datos fiscales | `FiscalDataUpdate` | `FiscalDataResponse` |

```python
# backend/api/routes/properties.py (NUEVOS endpoints)

@router.get("/{property_id}/fiscal-data", response_model=FiscalDataResponse)
def get_fiscal_data(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> FiscalDataResponse:
    """Obtiene los datos fiscales de una propiedad."""
    use_case = GetPropertyFiscalDataUseCase(property_repo)
    try:
        prop = use_case.execute(current_user.id, property_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada.")

    return _property_to_fiscal_response(prop)


@router.put("/{property_id}/fiscal-data", response_model=FiscalDataResponse)
def update_fiscal_data(
    property_id: str,
    body: FiscalDataUpdate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
    current_user: User = Depends(get_current_user),
) -> FiscalDataResponse:
    """Actualiza los datos fiscales de una propiedad."""
    use_case = UpdatePropertyFiscalDataUseCase(property_repo)
    try:
        prop = use_case.execute(
            user_id=current_user.id,
            property_id=property_id,
            cadastral_ref=body.cadastral_ref,
            land_value=body.cadastral_breakdown.land_value if body.cadastral_breakdown else None,
            construction_value=body.cadastral_breakdown.construction_value if body.cadastral_breakdown else None,
            purchase_price=body.acquisition_cost.purchase_price if body.acquisition_cost else None,
            construction_portion=body.acquisition_cost.construction_portion if body.acquisition_cost else None,
            land_portion=body.acquisition_cost.land_portion if body.acquisition_cost else None,
            transfer_tax=body.acquisition_cost.transfer_tax if body.acquisition_cost else None,
            notary_fees=body.acquisition_cost.notary_fees if body.acquisition_cost else None,
            registry_fees=body.acquisition_cost.registry_fees if body.acquisition_cost else None,
            acquisition_date=body.acquisition_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _property_to_fiscal_response(prop)


def _property_to_fiscal_response(prop: Property) -> FiscalDataResponse:
    """Helper para convertir Property a FiscalDataResponse."""
    cadastral = None
    if prop.cadastral_breakdown:
        cadastral = CadastralBreakdownSchema(
            land_value=prop.cadastral_breakdown.land_value,
            construction_value=prop.cadastral_breakdown.construction_value,
        )

    acquisition = None
    if prop.acquisition_cost:
        acquisition = AcquisitionCostSchema(
            purchase_price=prop.acquisition_cost.purchase_price,
            construction_portion=prop.acquisition_cost.construction_portion,
            land_portion=prop.acquisition_cost.land_portion,
            transfer_tax=prop.acquisition_cost.transfer_tax,
            notary_fees=prop.acquisition_cost.notary_fees,
            registry_fees=prop.acquisition_cost.registry_fees,
        )

    return FiscalDataResponse(
        property_id=prop.id,
        cadastral_ref=prop.cadastral_ref,
        cadastral_breakdown=cadastral,
        acquisition_cost=acquisition,
        acquisition_date=prop.acquisition_date,
        has_fiscal_data=prop.has_fiscal_data,
    )
```

### 7.3 Extensión de `PropertyResponse`

El `PropertyResponse` existente se extiende con un campo que indica si la propiedad tiene datos fiscales completos:

```python
class PropertyResponse(BaseModel):
    id: str
    name: str
    address: AddressSchema
    property_type: str
    status: str
    image_url: str | None = None
    has_fiscal_data: bool = False  # ← NUEVO
```

---

## 8. Frontend — Pestaña "Datos Fiscales"

### 8.1 Nuevos tipos TypeScript

```typescript
// frontend/src/types/index.ts (NUEVO)

export interface CadastralBreakdown {
  land_value: string;          // Decimal como string
  construction_value: string;
}

export interface AcquisitionCost {
  purchase_price: string;
  construction_portion: string;
  land_portion: string;
  transfer_tax: string;
  notary_fees: string;
  registry_fees: string;
}

export interface FiscalData {
  property_id: string;
  cadastral_ref: string | null;
  cadastral_breakdown: CadastralBreakdown | null;
  acquisition_cost: AcquisitionCost | null;
  acquisition_date: string | null;  // ISO date string
  has_fiscal_data: boolean;
}

export interface FiscalDataInput {
  cadastral_ref?: string | null;
  cadastral_breakdown?: {
    land_value: number;
    construction_value: number;
  } | null;
  acquisition_cost?: {
    purchase_price: number;
    construction_portion: number;
    land_portion: number;
    transfer_tax?: number;
    notary_fees?: number;
    registry_fees?: number;
  } | null;
  acquisition_date?: string | null;
}
```

### 8.2 Nuevos métodos API

```typescript
// frontend/src/services/api.ts (NUEVO)

export async function getFiscalData(propertyId: string): Promise<FiscalData> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/fiscal-data`);
  return handleResponse<FiscalData>(res);
}

export async function updateFiscalData(
  propertyId: string,
  data: FiscalDataInput
): Promise<FiscalData> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/fiscal-data`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<FiscalData>(res);
}
```

### 8.3 Componente `FiscalDataForm`

Nuevo componente `frontend/src/components/FiscalDataForm.tsx` que renderiza un formulario con dos secciones colapsables:

1. **Datos Catastrales**: Referencia catastral, valor suelo, valor construcción.
2. **Datos de Adquisición**: Precio de compra (con desglose automático), ITP, notaría, registro, fecha de compra.

Patrón de interacción:
- Al abrir la pestaña, se carga `GET /api/properties/{id}/fiscal-data`.
- El formulario se rellena con los datos existentes (o vacío si no hay).
- Al enviar el formulario, se hace `PUT /api/properties/{id}/fiscal-data`.
- Feedback visual con Toast de éxito/error.

### 8.4 Integración en `PropertyDetail`

Se añade una nueva pestaña o sección "📊 Datos Fiscales" en la vista de detalle de la propiedad (`PropertyDetail.tsx`), junto a las secciones de Ingresos y Gastos existentes.

La pestaña muestra un badge/indicador:
- 🟢 si `has_fiscal_data === true`
- 🟡 si hay datos parciales
- ⚪ si no hay datos fiscales

---

## 9. Especificación de Tests

### Tests Unitarios (`tests/unit/`)

| ID | Archivo | Qué verifica |
|---|---|---|
| **T-U-09-01** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `CadastralBreakdown` se crea correctamente con valores positivos |
| **T-U-09-02** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `CadastralBreakdown` rechaza valores negativos con `ValueError` |
| **T-U-09-03** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `CadastralBreakdown` rechaza todo ceros con `ValueError` |
| **T-U-09-04** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `CadastralBreakdown.total_value` suma correctamente |
| **T-U-09-05** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `CadastralBreakdown` es inmutable (`frozen=True`) |
| **T-U-09-06** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `AcquisitionCost` se crea correctamente con valores válidos |
| **T-U-09-07** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `AcquisitionCost` rechaza si `construction_portion + land_portion ≠ purchase_price` |
| **T-U-09-08** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `AcquisitionCost` rechaza valores negativos |
| **T-U-09-09** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `AcquisitionCost.total_acquisition_expenses` calcula correctamente |
| **T-U-09-10** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `AcquisitionCost.total_cost` calcula correctamente |
| **T-U-09-11** | `tests/unit/backend/domain/test_fiscal_value_objects.py` | `AcquisitionCost` es inmutable (`frozen=True`) |
| **T-U-09-12** | `tests/unit/backend/domain/test_entities.py` | `Property` se crea sin datos fiscales (compatibilidad F-01–F-08) |
| **T-U-09-13** | `tests/unit/backend/domain/test_entities.py` | `Property` se crea con datos fiscales completos |
| **T-U-09-14** | `tests/unit/backend/domain/test_entities.py` | `Property.has_fiscal_data` retorna `True` solo con datos completos |
| **T-U-09-15** | `tests/unit/backend/domain/test_entities.py` | `Property` valida `cadastral_ref` de 20 caracteres |
| **T-U-09-16** | `tests/unit/backend/application/test_fiscal_use_cases.py` | `UpdatePropertyFiscalDataUseCase` persiste datos correctamente |
| **T-U-09-17** | `tests/unit/backend/application/test_fiscal_use_cases.py` | `UpdatePropertyFiscalDataUseCase` rechaza propiedad inexistente |
| **T-U-09-18** | `tests/unit/backend/application/test_fiscal_use_cases.py` | `UpdatePropertyFiscalDataUseCase` rechaza propiedad de otro usuario |

### Tests de Integración (`tests/integration/`)

| ID | Archivo | Qué verifica |
|---|---|---|
| **T-I-09-01** | `tests/integration/backend/adapters/test_sqlite_adapter.py` | Migración: columnas fiscales se crean sin error |
| **T-I-09-02** | `tests/integration/backend/adapters/test_sqlite_adapter.py` | `update_fiscal_data` persiste y recupera `CadastralBreakdown` |
| **T-I-09-03** | `tests/integration/backend/adapters/test_sqlite_adapter.py` | `update_fiscal_data` persiste y recupera `AcquisitionCost` |
| **T-I-09-04** | `tests/integration/backend/adapters/test_sqlite_adapter.py` | Propiedad sin datos fiscales retorna `None` en campos fiscales |
| **T-I-09-05** | `tests/integration/backend/adapters/test_sqlite_adapter.py` | `save` y `find_by_id` mantienen datos fiscales intactos |
| **T-I-09-06** | `tests/integration/backend/api/test_properties_api.py` | `GET /api/properties/{id}/fiscal-data` retorna datos vacíos inicialmente |
| **T-I-09-07** | `tests/integration/backend/api/test_properties_api.py` | `PUT /api/properties/{id}/fiscal-data` persiste y retorna datos fiscales |
| **T-I-09-08** | `tests/integration/backend/api/test_properties_api.py` | `PUT /api/properties/{id}/fiscal-data` con datos inválidos retorna 400 |
| **T-I-09-09** | `tests/integration/backend/api/test_properties_api.py` | `GET /api/properties/{id}/fiscal-data` de propiedad ajena retorna 404 |
| **T-I-09-10** | `tests/integration/backend/api/test_properties_api.py` | `PropertyResponse` incluye `has_fiscal_data` |

---

## 10. Impacto en Features Anteriores

| Componente | Impacto | Acción |
|---|---|---|
| `Property` (entity) | Se añaden 4 campos opcionales con `None` por defecto | **No rompe** nada existente |
| `PropertyRepository` (port) | Se añade 1 método abstracto | `SQLitePropertyRepository` lo implementa |
| `SQLiteConnection._create_tables` | Se añaden 9 `ALTER TABLE` con `try/except` | Migración idempotente |
| `_row_to_entity` | Se reconstruyen VOs fiscales desde la fila | Columnas nuevas tienen `DEFAULT NULL` |
| `PropertyResponse` (schema) | Se añade `has_fiscal_data: bool = False` | Valor por defecto mantiene compatibilidad |
| Tests existentes | **No se modifican** | Los nuevos campos con defaults no afectan |

---

## 📚 El Rincón del Estudiante

### ¿Qué son los Value Objects y por qué los usamos aquí?

Imagina que tienes un billete de 20€. No te importa **cuál** billete sea (no le pones nombre ni DNI al billete), solo te importa que valga 20€. Si alguien te cambia tu billete de 20€ por otro billete de 20€, te da igual. **Eso** es un Value Object: un objeto que se define por sus valores, no por su identidad.

En cambio, tu DNI sí tiene identidad única. Aunque dos personas se llamen igual, son personas distintas. **Eso** es una Entidad.

En esta feature:

| Concepto | ¿Es Value Object o Entidad? | ¿Por qué? |
|---|---|---|
| `CadastralBreakdown(40000, 80000)` | **Value Object** | Dos desgloses con los mismos valores son idénticos. No tiene "identidad propia" |
| `AcquisitionCost(200000, ...)` | **Value Object** | Si los datos de compra son iguales, el objeto es intercambiable |
| `Property("Piso Malasaña", ...)` | **Entidad** | Cada propiedad tiene un `id` único. Dos propiedades con el mismo nombre en distinta dirección son distintas |

### ¿Por qué son inmutables (`frozen=True`)?

```python
# ❌ SIN frozen — Peligro de mutación accidental
catastral = CadastralBreakdown(land_value=40000, construction_value=80000)
catastral.land_value = 99999  # 😱 ¡Alguien cambió el valor catastral sin querer!

# ✅ CON frozen — Python lanza error si intentas modificar
catastral = CadastralBreakdown(land_value=40000, construction_value=80000)
catastral.land_value = 99999  # ❌ FrozenInstanceError!
```

Es como un recibo de compraventa firmado ante notario: **no se puede tachar y reescribir**. Si los datos cambian, creas un nuevo recibo (un nuevo Value Object).

### ¿Por qué los campos fiscales son opcionales (`None`)?

Piensa en un formulario de papel con muchas páginas. Puedes rellenar la primera página (nombre, dirección del piso) y dejar las páginas de "datos catastrales" para después. El formulario sigue siendo válido, simplemente tiene páginas en blanco.

```python
# Propiedad creada en F-01 (antes de que existiera la fiscalidad)
piso = Property(name="Piso Malasaña", address=..., property_type=...)
# → piso.cadastral_breakdown = None  ← "Página en blanco"
# → piso.acquisition_cost = None     ← "Página en blanco"
# → piso.has_fiscal_data = False     ← "Le faltan datos fiscales"

# El usuario rellena los datos fiscales más tarde (F-09)
piso.cadastral_breakdown = CadastralBreakdown(40000, 80000)
piso.acquisition_cost = AcquisitionCost(200000, 120000, 80000, 16000, 800, 400)
piso.acquisition_date = date(2020, 3, 15)
# → piso.has_fiscal_data = True      ← "Datos fiscales completos"
```

### ¿Por qué un endpoint separado (`/fiscal-data`) en vez de meter todo en la creación de propiedad?

Principio de **responsabilidad única** aplicado a la API:

| Enfoque | Ventaja | Desventaja |
|---|---|---|
| Todo en `POST /properties` | Un solo endpoint | El body se vuelve enorme. El usuario tiene que saber todos los datos fiscales al crear la propiedad. Si falla la validación catastral, no se crea ni la propiedad. |
| **Endpoints separados** ✅ | Cada endpoint hace una cosa. Se puede crear la propiedad primero y rellenar los datos fiscales después, cuando el usuario tenga la documentación a mano. | Dos llamadas HTTP en vez de una. |

Es como en un banco: primero abres la cuenta (datos básicos) y después, otro día, configuras la domiciliación de recibos (datos fiscales). No te obligan a traer toda la documentación el primer día.

### ¿Qué es la `Referencia Catastral`?

Es el "DNI" de un inmueble en España. La asigna el Catastro (organismo público) y tiene exactamente 20 caracteres alfanuméricos. Se puede consultar en la [Sede Electrónica del Catastro](https://www.sedecatastro.gob.es/).

```
  1234567 AB 1234 C 0001 XY
  ├──────┤├──┤├───┤├┤├───┤├─┤
  Finca   Hoja Parcela  Piso  Control
```

En nuestro código la validamos como `len(ref) == 20`, sin entrar en la estructura interna (que puede cambiar entre provincias).
