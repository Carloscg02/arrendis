# 📐 F-16: Modelo de Dominio de Suministros — Design

> **Épica:** E-02 — Automatización de Gastos de Suministros vía Email  
> **Estado:** Borrador — Pendiente de aprobación  
> **Dependencias:** F-08 (Multi-tenancy) ✅, F-11 (Clasificación Fiscal) ✅  
> **Fecha:** 2026-08-05

---

## 1. Lenguaje Ubicuo (Términos nuevos)

| Término | Definición | Ejemplo en el proyecto |
|---|---|---|
| **CUPS** | *Código Unificado de Punto de Suministro*. Identificador único de 20-22 caracteres alfanuméricos (formato `ESddddddddddddddddXXYY`) que identifica un punto de suministro de energía o agua en España. Clave para emparejar factura con inmueble. | `"ES0031103721971011PR0F"` |
| **UtilityType** | Enum que clasifica el tipo de suministro: electricidad, gas natural o agua. | `UtilityType.ELECTRICITY` |
| **ExpenseSource** | Enum que identifica el origen de un gasto: introducido manualmente por el usuario o importado automáticamente desde un PDF de factura. | `ExpenseSource.AUTO_IMPORT` |
| **UtilityInvoiceData** | Value Object inmutable que contiene los datos estructurados extraídos de una factura de suministros: CUPS, importe, fecha, proveedor, nº de factura y tipo de suministro. | `UtilityInvoiceData(cups="ES003...", amount=Decimal("75.46"), ...)` |
| **ExtractionConfidence** | Enum que indica el nivel de confianza de la extracción automática: ALTA (Regex exitoso), MEDIA (IA/LLM exitoso) o BAJA (datos parciales extraídos). | `ExtractionConfidence.HIGH` |
| **PendingReviewExpense** | Concepto de negocio: gasto creado automáticamente con `is_verified = False` que requiere confirmación explícita del propietario antes de computar en balances y borradores fiscales. | Un gasto con `source=AUTO_IMPORT, is_verified=False` |

---

## 2. Enumeraciones Nuevas

### 2.1 `UtilityType`

```python
# backend/domain/entities.py (NUEVO)

class UtilityType(Enum):
    """Clasificación del tipo de suministro."""
    ELECTRICITY = "electricity"
    GAS = "gas"
    WATER = "water"
```

### 2.2 `ExpenseSource`

```python
# backend/domain/entities.py (NUEVO)

class ExpenseSource(Enum):
    """Origen de un gasto: manual o auto-importado desde PDF."""
    MANUAL = "manual"
    AUTO_IMPORT = "auto_import"
```

### 2.3 `ExtractionConfidence`

```python
# backend/domain/entities.py (NUEVO)

class ExtractionConfidence(Enum):
    """Nivel de confianza de la extracción automática de datos."""
    HIGH = "high"       # Regex local exitoso — todos los campos extraídos
    MEDIUM = "medium"   # IA/LLM exitoso — campos extraídos por modelo generativo
    LOW = "low"         # Extracción parcial — algún campo falta o es ambiguo
```

---

## 3. Value Object Nuevo

### 3.1 `UtilityInvoiceData`

```python
# backend/domain/value_objects.py (NUEVO)

@dataclass(frozen=True)
class UtilityInvoiceData:
    """Datos estructurados extraídos de una factura de suministros.

    Inmutable. Se adjunta opcionalmente a un Expense cuando
    source == ExpenseSource.AUTO_IMPORT.

    Validaciones:
    - cups: debe cumplir el formato CUPS español (ES + 16-18 dígitos + 0-2 letras).
    - amount: debe ser positivo.
    - issue_date: no puede ser futura (no más de 60 días en el futuro como margen).
    - provider_name: no puede estar vacío.
    - utility_type: debe ser un UtilityType válido.
    """
    cups: str
    amount: Decimal
    issue_date: date
    provider_name: str
    utility_type: 'UtilityType'
    invoice_number: str | None = None
    extraction_confidence: 'ExtractionConfidence' = ExtractionConfidence.HIGH

    def __post_init__(self) -> None:
        import re
        from datetime import date as date_cls, timedelta

        # Validar formato CUPS: ES + 16-18 dígitos + 0-2 letras opcionales
        cups_pattern = r'^ES\d{16,18}[A-Z]{0,2}$'
        if not re.match(cups_pattern, self.cups):
            raise ValueError(
                f"CUPS no tiene formato válido (esperado ES + 16-18 dígitos + 0-2 letras): '{self.cups}'"
            )

        if self.amount <= 0:
            raise ValueError(f"El importe de la factura debe ser positivo: {self.amount}")

        # Margen de 60 días para facturas futuras (facturación anticipada)
        max_future = date_cls.today() + timedelta(days=60)
        if self.issue_date > max_future:
            raise ValueError(
                f"La fecha de emisión no puede ser tan futura: {self.issue_date}"
            )

        if not self.provider_name or not self.provider_name.strip():
            raise ValueError("El nombre del proveedor no puede estar vacío.")
```

---

## 4. Extensiones a Entidades Existentes

### 4.1 Cambios en `Property` — Campos CUPS

Se añaden 3 campos opcionales para registrar los códigos CUPS de cada tipo de suministro del inmueble:

```python
# backend/domain/entities.py — Property (MODIFICAR)

@dataclass
class Property:
    # ... campos existentes sin cambios ...
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
    # --- NUEVOS CAMPOS E-02 ---
    cups_electricity: str | None = None
    cups_gas: str | None = None
    cups_water: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

**Regla de validación en `__post_init__`**: Si algún campo `cups_*` se proporciona, debe cumplir el formato CUPS español (`ES` + 16-18 dígitos + 0-2 letras). Se validará con el mismo regex del VO `UtilityInvoiceData`.

```python
    # Añadir en __post_init__ de Property:
    import re
    _CUPS_PATTERN = re.compile(r'^ES\d{16,18}[A-Z]{0,2}$')

    for field_name in ("cups_electricity", "cups_gas", "cups_water"):
        value = getattr(self, field_name)
        if value is not None and not _CUPS_PATTERN.match(value):
            raise ValueError(
                f"{field_name} no tiene formato CUPS válido: '{value}'"
            )
```

### 4.2 Cambios en `Expense` — Estado de verificación y origen

Se añaden 4 campos con defaults **retrocompatibles** (los gastos existentes manuales siguen funcionando sin cambios):

```python
# backend/domain/entities.py — Expense (MODIFICAR)

@dataclass
class Expense:
    property_id: str
    amount: Money
    date: date
    category: ExpenseCategory
    description: str = ""
    fiscal_category: FiscalExpenseCategory | None = None
    # --- NUEVOS CAMPOS E-02 ---
    is_verified: bool = True                                   # True para manuales, False para auto-importados
    source: ExpenseSource = ExpenseSource.MANUAL                # Origen del gasto
    receipt_path: str | None = None                             # Ruta relativa al PDF (futuro F-19)
    utility_data: UtilityInvoiceData | None = None              # Datos extraídos (solo si AUTO_IMPORT)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

**Regla de negocio crítica**: Un gasto con `is_verified = False` **no debe computar** en el cálculo fiscal (`FiscalCalculatorService.calculate()`). Esto se logra añadiendo un filtro en el servicio existente:

```python
# backend/domain/services.py — FiscalCalculatorService.calculate() (MODIFICAR)
# PASO 1: Filtrar por año fiscal — AÑADIR filtro de verificación
expenses_year = [
    e for e in expenses
    if e.date.year == fiscal_year and e.is_verified  # ← NUEVO: solo gastos verificados
]
```

---

## 5. Nuevo Puerto (Port)

### 5.1 `PropertyRepository` — Nuevo método `find_by_cups`

Se necesita buscar propiedades por CUPS para el matching automático factura → inmueble (consumido por F-18):

```python
# backend/domain/ports.py — PropertyRepository (MODIFICAR, añadir método)

class PropertyRepository(ABC):
    # ... métodos existentes sin cambios ...

    @abstractmethod
    def find_by_cups(self, cups: str, user_id: str) -> Property | None:
        """Busca una propiedad por cualquiera de sus CUPS (electricity, gas, water).

        Filtra por user_id para respetar el aislamiento multi-tenant.
        Retorna None si no hay coincidencia.
        """
        ...
```

---

## 6. Cambios en el Adaptador SQLite

### 6.1 Migraciones de esquema

Siguiendo el patrón existente de `ALTER TABLE ... ADD COLUMN` con `try/except`:

```python
# backend/adapters/sqlite_adapter.py — SQLiteConnection._initialize_tables() (MODIFICAR)

# Migración F-16: CUPS en properties
for col in [
    "cups_electricity TEXT DEFAULT NULL",
    "cups_gas TEXT DEFAULT NULL",
    "cups_water TEXT DEFAULT NULL",
]:
    try:
        cursor.execute(f"ALTER TABLE properties ADD COLUMN {col}")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

# Migración F-16: campos de verificación y origen en expenses
for col in [
    "is_verified INTEGER NOT NULL DEFAULT 1",        # 1=True (retrocompatible)
    "source TEXT NOT NULL DEFAULT 'manual'",           # Retrocompatible
    "receipt_path TEXT DEFAULT NULL",
    "utility_cups TEXT DEFAULT NULL",
    "utility_amount TEXT DEFAULT NULL",
    "utility_issue_date TEXT DEFAULT NULL",
    "utility_provider_name TEXT DEFAULT NULL",
    "utility_type TEXT DEFAULT NULL",
    "utility_invoice_number TEXT DEFAULT NULL",
    "utility_extraction_confidence TEXT DEFAULT NULL",
]:
    try:
        cursor.execute(f"ALTER TABLE expenses ADD COLUMN {col}")
    except sqlite3.OperationalError:
        pass  # La columna ya existe
```

### 6.2 `SQLitePropertyRepository` — Implementación de `find_by_cups`

```python
# backend/adapters/sqlite_adapter.py — SQLitePropertyRepository (NUEVO método)

def find_by_cups(self, cups: str, user_id: str) -> Property | None:
    """Busca una propiedad cuyo cups_electricity, cups_gas o cups_water coincida."""
    cursor = self._conn.execute(
        """
        SELECT * FROM properties
        WHERE user_id = ?
          AND (cups_electricity = ? OR cups_gas = ? OR cups_water = ?)
        """,
        (user_id, cups, cups, cups),
    )
    row = cursor.fetchone()
    return self._row_to_property(row) if row else None
```

### 6.3 Serialización/Deserialización de `UtilityInvoiceData` en `SQLiteExpenseRepository`

El VO `UtilityInvoiceData` se almacena como columnas planas prefijadas con `utility_` (no como JSON BLOB), siguiendo el patrón de `CadastralBreakdown` en properties.

```python
# Serialización (save):
"utility_cups": expense.utility_data.cups if expense.utility_data else None,
"utility_amount": str(expense.utility_data.amount) if expense.utility_data else None,
# ... etc.

# Deserialización (find_by_property_id):
utility_data = None
if row["utility_cups"] is not None:
    utility_data = UtilityInvoiceData(
        cups=row["utility_cups"],
        amount=Decimal(row["utility_amount"]),
        issue_date=date.fromisoformat(row["utility_issue_date"]),
        provider_name=row["utility_provider_name"],
        utility_type=UtilityType(row["utility_type"]),
        invoice_number=row["utility_invoice_number"],
        extraction_confidence=ExtractionConfidence(row["utility_extraction_confidence"]),
    )
```

---

## 7. Cambios en Schemas de API (FastAPI)

### 7.1 `ExpenseResponse` — Campos nuevos

```python
# backend/api/schemas.py (MODIFICAR)

class ExpenseResponse(BaseModel):
    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str
    fiscal_category: str | None = None
    # --- NUEVOS CAMPOS F-16 ---
    is_verified: bool = True
    source: str = "manual"
    receipt_path: str | None = None
    utility_data: UtilityInvoiceDataSchema | None = None
```

### 7.2 `UtilityInvoiceDataSchema` — Nuevo schema de respuesta

```python
# backend/api/schemas.py (NUEVO)

class UtilityInvoiceDataSchema(BaseModel):
    """Representación API del VO UtilityInvoiceData."""
    cups: str
    amount: Decimal
    issue_date: date
    provider_name: str
    utility_type: str
    invoice_number: str | None = None
    extraction_confidence: str = "high"
```

### 7.3 `PropertyResponse` — Campos CUPS

```python
# backend/api/schemas.py — PropertyResponse (MODIFICAR, añadir campos)

class PropertyResponse(BaseModel):
    # ... campos existentes ...
    cups_electricity: str | None = None
    cups_gas: str | None = None
    cups_water: str | None = None
```

### 7.4 `PropertyCupsUpdate` — Nuevo schema para actualizar CUPS

```python
# backend/api/schemas.py (NUEVO)

class PropertyCupsUpdate(BaseModel):
    """Request body para actualizar los CUPS de una propiedad."""
    cups_electricity: str | None = None
    cups_gas: str | None = None
    cups_water: str | None = None
```

---

## 8. Nuevo Endpoint de API

### 8.1 `PUT /api/properties/{property_id}/cups`

```
PUT /api/properties/{property_id}/cups
Authorization: Bearer <token>
Content-Type: application/json

{
    "cups_electricity": "ES0031103721971011PR0F",
    "cups_gas": null,
    "cups_water": null
}

→ 200 OK: PropertyResponse (con los CUPS actualizados)
→ 400 Bad Request: Si un CUPS no cumple el formato
→ 404 Not Found: Propiedad no encontrada o no pertenece al usuario
```

### 8.2 Puerto en `PropertyRepository`

```python
# backend/domain/ports.py — PropertyRepository (NUEVO método)

@abstractmethod
def update_cups(
    self,
    property_id: str,
    cups_electricity: str | None,
    cups_gas: str | None,
    cups_water: str | None,
) -> None:
    """Actualiza los CUPS de una propiedad."""
    ...
```

---

## 9. Especificación de Tests

### 9.1 Tests Unitarios — Dominio

| ID | Archivo | Qué verifica |
|---|---|---|
| **UT-F16-01** | `test_entities.py` | `Property` con `cups_electricity` válido se crea correctamente. |
| **UT-F16-02** | `test_entities.py` | `Property` con `cups_electricity` inválido (formato incorrecto) lanza `ValueError`. |
| **UT-F16-03** | `test_entities.py` | `Property` con `cups_electricity=None` es válido (opcional). |
| **UT-F16-04** | `test_entities.py` | `Expense` con defaults de F-16 (`is_verified=True`, `source=MANUAL`) es retrocompatible. |
| **UT-F16-05** | `test_entities.py` | `Expense` con `is_verified=False` y `source=AUTO_IMPORT` se crea correctamente. |
| **UT-F16-06** | `test_entities.py` | `Expense` con `utility_data` adjunto (UtilityInvoiceData) se crea correctamente. |
| **UT-F16-07** | `test_value_objects.py` | `UtilityInvoiceData` con CUPS válido y datos completos se crea correctamente. |
| **UT-F16-08** | `test_value_objects.py` | `UtilityInvoiceData` con CUPS inválido lanza `ValueError`. |
| **UT-F16-09** | `test_value_objects.py` | `UtilityInvoiceData` con importe negativo lanza `ValueError`. |
| **UT-F16-10** | `test_value_objects.py` | `UtilityInvoiceData` con proveedor vacío lanza `ValueError`. |
| **UT-F16-11** | `test_value_objects.py` | `UtilityInvoiceData` es inmutable (`frozen=True`). |
| **UT-F16-12** | `test_fiscal_calculator.py` | `FiscalCalculatorService.calculate()` **ignora** gastos con `is_verified=False` (no computan en el rendimiento neto). |
| **UT-F16-13** | `test_fiscal_calculator.py` | `FiscalCalculatorService.calculate()` **incluye** gastos con `is_verified=True` (comportamiento existente intacto). |

### 9.2 Tests de Integración — Adaptadores

| ID | Archivo | Qué verifica |
|---|---|---|
| **IT-F16-01** | `test_sqlite_adapter.py` | `save()` y `find_by_id()` de Property con campos CUPS persisten y recuperan correctamente. |
| **IT-F16-02** | `test_sqlite_adapter.py` | `find_by_cups()` encuentra la propiedad correcta dado un CUPS de electricidad. |
| **IT-F16-03** | `test_sqlite_adapter.py` | `find_by_cups()` retorna `None` si el CUPS no coincide con ninguna propiedad del usuario. |
| **IT-F16-04** | `test_sqlite_adapter.py` | `find_by_cups()` respeta multi-tenancy: no retorna propiedades de otro usuario. |
| **IT-F16-05** | `test_sqlite_adapter.py` | `update_cups()` actualiza los CUPS y se reflejan en `find_by_id()`. |
| **IT-F16-06** | `test_sqlite_adapter.py` | `save()` y `find_by_property_id()` de Expense con `utility_data` persisten y deserializan el VO correctamente. |
| **IT-F16-07** | `test_sqlite_adapter.py` | `save()` de Expense sin `utility_data` (manual) es retrocompatible (columnas `utility_*` quedan NULL). |
| **IT-F16-08** | `test_sqlite_adapter.py` | Migración: BD existente sin columnas F-16 se migra correctamente al abrir conexión. |

### 9.3 Tests de API (Integration)

| ID | Archivo | Qué verifica |
|---|---|---|
| **API-F16-01** | `test_api_properties.py` | `PUT /api/properties/{id}/cups` actualiza CUPS y devuelve 200 con `PropertyResponse` incluyendo los CUPS. |
| **API-F16-02** | `test_api_properties.py` | `PUT /api/properties/{id}/cups` con CUPS inválido devuelve 400. |
| **API-F16-03** | `test_api_properties.py` | `GET /api/properties/{id}` incluye campos `cups_electricity`, `cups_gas`, `cups_water` en la respuesta. |
| **API-F16-04** | `test_api_expenses.py` | `GET /api/expenses/{property_id}` incluye campos `is_verified`, `source`, `utility_data` en la respuesta. |

---

## 10. Resumen de Archivos a Crear/Modificar

| Archivo | Acción | Qué cambia |
|---|---|---|
| `backend/domain/entities.py` | **Modificar** | Añadir enums `UtilityType`, `ExpenseSource`, `ExtractionConfidence`. Añadir campos CUPS a `Property`. Añadir campos `is_verified`, `source`, `receipt_path`, `utility_data` a `Expense`. |
| `backend/domain/value_objects.py` | **Modificar** | Añadir `UtilityInvoiceData` VO. |
| `backend/domain/ports.py` | **Modificar** | Añadir `find_by_cups()` y `update_cups()` a `PropertyRepository`. |
| `backend/domain/services.py` | **Modificar** | Filtrar gastos `is_verified=False` en `FiscalCalculatorService.calculate()`. |
| `backend/adapters/sqlite_adapter.py` | **Modificar** | Migraciones de esquema. Implementar `find_by_cups()` y `update_cups()`. Serializar/deserializar `UtilityInvoiceData`. |
| `backend/api/schemas.py` | **Modificar** | Añadir `UtilityInvoiceDataSchema`, `PropertyCupsUpdate`. Extender `ExpenseResponse` y `PropertyResponse`. |
| `backend/api/routes/` | **Modificar** | Añadir endpoint `PUT /api/properties/{id}/cups`. |
| `tests/unit/backend/domain/test_entities.py` | **Modificar** | Tests UT-F16-01 a UT-F16-06. |
| `tests/unit/backend/domain/test_value_objects.py` | **Modificar** | Tests UT-F16-07 a UT-F16-11. |
| `tests/unit/backend/domain/test_fiscal_calculator.py` | **Modificar** | Tests UT-F16-12, UT-F16-13. |
| `tests/integration/` | **Modificar** | Tests IT-F16-01 a IT-F16-08, API-F16-01 a API-F16-04. |

---

## 📚 El Rincón del Estudiante

### ¿Por qué campos opcionales con defaults retrocompatibles?

Un error frecuente al extender un modelo de datos es **romper lo que ya funciona**. En nuestro caso, miles de gastos ya existen en la BD creados manualmente. Si añadiéramos `is_verified` sin default, esos gastos perderían su estado.

**La regla de oro:**

| Sin defaults retrocompatibles ❌ | Con defaults retrocompatibles ✅ |
|---|---|
| Los gastos existentes necesitan una migración de datos | Los gastos existentes siguen funcionando sin tocarlos |
| Si olvidas migrar, la app se rompe | `is_verified=True` y `source="manual"` → comportamiento idéntico al anterior |
| Requiere coordinar migración + deploy | Se puede desplegar sin downtime |

```python
# ❌ Mal: rompe gastos existentes
is_verified: bool  # ¿Qué valor tienen los gastos antiguos?

# ✅ Bien: retrocompatible
is_verified: bool = True  # Los gastos antiguos son "verificados" por definición
```

En SQLite, esto se traduce en:
```sql
ALTER TABLE expenses ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 1;
-- 1 = True → todos los gastos existentes quedan como verificados automáticamente
```

### ¿Qué es el Patrón Strategy (y por qué aparece aquí)?

Aunque el Patrón Strategy se implementará completamente en F-18 (Motor de Extracción), la semilla se planta en F-16 con el enum `ExtractionConfidence`. Este enum permite al gasto "recordar" cómo fue extraído.

**Analogía del mundo real:** Imagina un hospital que acepta análisis de sangre de distintos laboratorios. Cada laboratorio usa una técnica diferente (manual, automatizada, IA). El hospital no necesita conocer la técnica — solo necesita el resultado y un **indicador de confianza** para decidir si repetir el análisis.

```python
# El gasto no sabe si fue Regex o IA — solo sabe cuánto confiar en los datos
expense.utility_data.extraction_confidence == ExtractionConfidence.HIGH   # Regex exitoso
expense.utility_data.extraction_confidence == ExtractionConfidence.MEDIUM # IA exitoso
expense.utility_data.extraction_confidence == ExtractionConfidence.LOW    # Datos parciales
```

### ¿Por qué 3 campos CUPS separados en Property?

Una propiedad puede tener **puntos de suministro diferentes** para luz, gas y agua, cada uno con su propio código CUPS (o equivalente). Agruparlos en un solo campo sería incorrecto:

```python
# ❌ Mal: un solo CUPS no cubre todos los suministros
cups: str | None  # ¿Es de luz? ¿de gas? ¿de agua?

# ✅ Bien: un CUPS por tipo de suministro
cups_electricity: str | None  # CUPS de la comercializadora eléctrica
cups_gas: str | None           # CUPS de gas natural
cups_water: str | None         # Código de contrato/abonado de agua
```

Cuando el sistema reciba una factura de Endesa, buscará en `cups_electricity`. Cuando reciba una de Naturgy Gas, buscará en `cups_gas`. Cada matching es independiente.
