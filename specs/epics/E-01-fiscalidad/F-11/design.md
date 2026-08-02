# F-11 — Clasificación Fiscal de Gastos e Ingresos

> **Épica:** E-01 Fiscalidad  
> **Dependencias:** F-09, F-10  
> **Estado:** Pendiente de aprobación

---

## 1. Objetivo

Las categorías actuales de gastos (`REPAIR`, `TAX`, `INSURANCE`, etc.) e ingresos (`RENT`, `DEPOSIT`, `OTHER`)
son útiles para la contabilidad general del usuario, pero **no se corresponden con las casillas exactas
de la Agencia Tributaria (modelo D-100, Rendimientos del Capital Inmobiliario)**.

F-11 introduce una **clasificación fiscal paralela** que permite etiquetar cada gasto e ingreso
según las categorías exactas de Hacienda. Esta clasificación es la entrada directa que el motor
de cálculo fiscal (F-12) necesita para:

- Agrupar gastos por concepto fiscal (intereses, reparación, tributos, seguros, etc.).
- Aplicar el **tope conjunto** a gastos de reparación/conservación + intereses de capital.
- Separar gastos **deducibles** de los **no deducibles** (ej. amortización de capital de hipoteca).
- Prorratear correctamente los gastos según días de ocupación.

### Estrategia: Clasificación Paralela, No Sustitución

No reemplazamos las categorías actuales. Añadimos un campo **opcional** `fiscal_category` que
convive con `category`. El usuario mantiene su contabilidad general intacta y puede añadir
la capa fiscal cuando prepare su declaración.

---

## 2. Lenguaje Ubicuo (Nuevos Términos)

| Término | Definición |
|---|---|
| **FiscalExpenseCategory** | Clasificación de un gasto según las partidas deducibles del modelo D-100 de la AEAT para rendimientos del capital inmobiliario. |
| **FiscalIncomeCategory** | Clasificación de un ingreso según el tipo de rendimiento íntegro en la declaración fiscal. |
| **Sugerencia Fiscal** | Mapeo automático que propone una categoría fiscal por defecto basándose en la categoría general del gasto/ingreso. El usuario puede aceptarla o cambiarla. |
| **Gasto No Deducible** | Gasto que, aunque se registra en la contabilidad, no es deducible fiscalmente (ej. amortización de capital de la hipoteca, mejoras no reparaciones). |

---

## 3. Modelo de Dominio

### 3.1 Nuevos Enums

Se añaden en `backend/domain/entities.py`:

```python
class FiscalExpenseCategory(Enum):
    """Clasificación fiscal del gasto según partidas AEAT (Capital Inmobiliario)."""
    INTERESES_CAPITAL = "intereses_capital"               # Intereses de préstamos (hipoteca)
    REPARACION_CONSERVACION = "reparacion_conservacion"    # Reparación y conservación
    TRIBUTOS = "tributos"                                  # IBI, basura, tasas municipales
    PRIMAS_SEGUROS = "primas_seguros"                      # Seguros del inmueble
    SERVICIOS_SUMINISTROS = "servicios_suministros"        # Comunidad, suministros
    FORMALIZACION = "formalizacion"                        # Gastos jurídicos del arrendamiento
    DUDOSO_COBRO = "dudoso_cobro"                          # Saldos de dudoso cobro
    OTROS_DEDUCIBLES = "otros_deducibles"                  # Otros gastos fiscalmente deducibles
    NO_DEDUCIBLE = "no_deducible"                          # No deducible (capital hipoteca, mejoras...)


class FiscalIncomeCategory(Enum):
    """Clasificación fiscal del ingreso según AEAT."""
    RENDIMIENTO_INTEGRO = "rendimiento_integro"   # Renta de alquiler (rendimiento íntegro)
    OTROS_INGRESOS = "otros_ingresos"             # Fianza retenida, indemnización, etc.
```

### 3.2 Extensión de Entidades Existentes

#### `Expense` — nuevo campo opcional:

```diff
 @dataclass
 class Expense:
     property_id: str
     amount: Money
     date: date
     category: ExpenseCategory
     description: str = ""
+    fiscal_category: FiscalExpenseCategory | None = None
     id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

#### `Income` — nuevo campo opcional:

```diff
 @dataclass
 class Income:
     property_id: str
     amount: Money
     date: date
     category: IncomeCategory
     description: str = ""
+    fiscal_category: FiscalIncomeCategory | None = None
     id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

> **¿Por qué opcional?** Para mantener retrocompatibilidad. Los gastos/ingresos existentes
> seguirán funcionando sin clasificación fiscal. El usuario clasificará cuando lo necesite
> (antes de generar el informe fiscal en F-13).

### 3.3 Nuevo Servicio de Dominio — `FiscalCategoryMapper`

Se añade en `backend/domain/services.py`:

```python
class FiscalCategoryMapper:
    """Servicio de dominio que sugiere categorías fiscales a partir de categorías generales.

    Es lógica pura de negocio: dado un tipo contable, devuelve la categoría fiscal
    más probable según las reglas de la AEAT. El usuario puede aceptar o modificar.
    """

    EXPENSE_SUGGESTIONS: dict[ExpenseCategory, FiscalExpenseCategory] = {
        ExpenseCategory.REPAIR: FiscalExpenseCategory.REPARACION_CONSERVACION,
        ExpenseCategory.TAX: FiscalExpenseCategory.TRIBUTOS,
        ExpenseCategory.INSURANCE: FiscalExpenseCategory.PRIMAS_SEGUROS,
        ExpenseCategory.COMMUNITY_FEE: FiscalExpenseCategory.SERVICIOS_SUMINISTROS,
        ExpenseCategory.MORTGAGE: FiscalExpenseCategory.INTERESES_CAPITAL,
        ExpenseCategory.UTILITY: FiscalExpenseCategory.SERVICIOS_SUMINISTROS,
        ExpenseCategory.OTHER: FiscalExpenseCategory.OTROS_DEDUCIBLES,
    }

    INCOME_SUGGESTIONS: dict[IncomeCategory, FiscalIncomeCategory] = {
        IncomeCategory.RENT: FiscalIncomeCategory.RENDIMIENTO_INTEGRO,
        IncomeCategory.DEPOSIT: FiscalIncomeCategory.OTROS_INGRESOS,
        IncomeCategory.OTHER: FiscalIncomeCategory.OTROS_INGRESOS,
    }

    @classmethod
    def suggest_expense_fiscal_category(cls, category: ExpenseCategory) -> FiscalExpenseCategory:
        return cls.EXPENSE_SUGGESTIONS[category]

    @classmethod
    def suggest_income_fiscal_category(cls, category: IncomeCategory) -> FiscalIncomeCategory:
        return cls.INCOME_SUGGESTIONS[category]
```

> **Nota sobre MORTGAGE:** La sugerencia es `INTERESES_CAPITAL` pero con advertencia en la UI:
> solo los intereses de la hipoteca son deducibles, no la amortización de capital.
> Si el usuario registra la cuota completa, debería clasificar solo la parte de intereses
> como `INTERESES_CAPITAL` y la parte de capital como `NO_DEDUCIBLE` (o registrarlos como
> dos gastos separados). Esto se documentará en la UI.

---

## 4. Puertos

No se necesitan nuevos puertos. Los repositorios existentes (`IncomeRepository`, `ExpenseRepository`)
ya tienen `save()` que persiste la entidad completa. Solo hay que actualizar las implementaciones
SQLite para incluir la nueva columna.

---

## 5. Casos de Uso

### 5.1 Modificar `RecordIncomeUseCase` y `RecordExpenseUseCase`

Añadir el parámetro opcional `fiscal_category: str | None = None` al método `execute()`.
Si se proporciona, se convierte al enum correspondiente. Si no, queda `None`.

```diff
 def execute(
     self,
     user_id: str,
     property_id: str,
     amount: Decimal,
     income_date: date,
     category: str,
     description: str = "",
+    fiscal_category: str | None = None,
 ) -> Income:
```

### 5.2 Nuevo Use Case — `UpdateFiscalCategoryUseCase`

Permite actualizar la clasificación fiscal de un gasto o ingreso existente sin recrearlo.

```
Entrada: user_id, record_id, record_type ("income" | "expense"), fiscal_category (str)
Proceso:
  1. Buscar el registro (income o expense) por id.
  2. Verificar que la propiedad asociada pertenece al user_id.
  3. Validar que fiscal_category es un valor válido del enum correspondiente.
  4. Actualizar el campo fiscal_category y persistir.
Salida:  Income | Expense actualizado.
Error:   ValueError si el registro no existe, la propiedad no pertenece al usuario,
         o la categoría fiscal es inválida.
```

### 5.3 Nuevo Use Case — `SuggestFiscalCategoriesUseCase`

Genera sugerencias de clasificación fiscal para todos los registros de una propiedad
que aún no tengan `fiscal_category` asignada.

```
Entrada: user_id, property_id
Proceso:
  1. Verificar que la propiedad existe y pertenece al user_id.
  2. Obtener todos los ingresos y gastos de la propiedad.
  3. Para cada uno sin fiscal_category, usar FiscalCategoryMapper para sugerir.
Salida:  dict con:
         - unclassified_expenses: list[{id, category, suggested_fiscal_category, description, amount}]
         - unclassified_incomes: list[{id, category, suggested_fiscal_category, description, amount}]
         - total_unclassified: int
```

---

## 6. Adaptador SQLite

### 6.1 Migración — Nuevas columnas

```python
# Migración F-11: clasificación fiscal
try:
    cursor.execute("ALTER TABLE incomes ADD COLUMN fiscal_category TEXT DEFAULT NULL")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE expenses ADD COLUMN fiscal_category TEXT DEFAULT NULL")
except sqlite3.OperationalError:
    pass
```

### 6.2 Actualizar `SQLiteIncomeRepository`

- **`save()`**: Incluir `fiscal_category` en INSERT (como `.value` si no es None, else None).
- **`_row_to_entity()`**: Reconstruir `FiscalIncomeCategory(row["fiscal_category"])` si no es None.
- **Nuevo `update_fiscal_category(income_id, fiscal_category)`**: UPDATE puntual.

### 6.3 Actualizar `SQLiteExpenseRepository`

- Análogo al de Income.
- **Nuevo `update_fiscal_category(expense_id, fiscal_category)`**: UPDATE puntual.

### 6.4 Actualizar Puertos

Añadir `update_fiscal_category` a `IncomeRepository` y `ExpenseRepository`:

```python
@abstractmethod
def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
    """Actualiza la categoría fiscal de un registro."""
    ...
```

---

## 7. API REST

### 7.1 Actualizar Schemas Existentes

```diff
 class IncomeCreate(BaseModel):
     property_id: str
     amount: Decimal
     date: date
     category: str
     description: str = ""
+    fiscal_category: str | None = None

 class IncomeResponse(BaseModel):
     id: str
     property_id: str
     amount: Decimal
     currency: str
     date: date
     category: str
     description: str
+    fiscal_category: str | None = None
```

Lo mismo para `ExpenseCreate` y `ExpenseResponse`.

### 7.2 Nuevos Schemas

```python
class FiscalCategoryUpdate(BaseModel):
    """Request body para actualizar la categoría fiscal de un registro."""
    fiscal_category: str

class FiscalSuggestionItem(BaseModel):
    id: str
    category: str
    suggested_fiscal_category: str
    description: str
    amount: Decimal

class FiscalSuggestionsResponse(BaseModel):
    unclassified_expenses: list[FiscalSuggestionItem]
    unclassified_incomes: list[FiscalSuggestionItem]
    total_unclassified: int
```

### 7.3 Nuevos Endpoints

| Método | Ruta | Descripción | Response |
|---|---|---|---|
| `PATCH` | `/api/incomes/{income_id}/fiscal-category` | Actualizar categoría fiscal de un ingreso | `IncomeResponse` |
| `PATCH` | `/api/expenses/{expense_id}/fiscal-category` | Actualizar categoría fiscal de un gasto | `ExpenseResponse` |
| `GET` | `/api/properties/{property_id}/fiscal-suggestions` | Obtener sugerencias para registros sin clasificar | `FiscalSuggestionsResponse` |

> **¿Por qué PATCH y no PUT?** Porque solo se actualiza un campo (`fiscal_category`),
> no el recurso completo.

### 7.4 Modificar endpoints existentes

Los endpoints de creación de ingreso/gasto (`POST /api/incomes`, `POST /api/expenses`)
aceptan opcionalmente `fiscal_category` en el body. Los de listado (`GET`) lo incluyen
en la respuesta.

---

## 8. Frontend

### 8.1 Tipos TypeScript

```typescript
// Añadir a los tipos existentes
export type FiscalExpenseCategory =
  | "intereses_capital"
  | "reparacion_conservacion"
  | "tributos"
  | "primas_seguros"
  | "servicios_suministros"
  | "formalizacion"
  | "dudoso_cobro"
  | "otros_deducibles"
  | "no_deducible";

export type FiscalIncomeCategory =
  | "rendimiento_integro"
  | "otros_ingresos";

// Extender interfaces existentes
export interface Income {
  // ...campos existentes...
  fiscal_category: FiscalExpenseCategory | null;  // NOTA: FiscalIncomeCategory
}

export interface Expense {
  // ...campos existentes...
  fiscal_category: FiscalExpenseCategory | null;
}

export interface FiscalSuggestion {
  id: string;
  category: string;
  suggested_fiscal_category: string;
  description: string;
  amount: string;
}

export interface FiscalSuggestionsResponse {
  unclassified_expenses: FiscalSuggestion[];
  unclassified_incomes: FiscalSuggestion[];
  total_unclassified: number;
}
```

### 8.2 Servicio API

```typescript
export const updateIncomeFiscalCategory = (incomeId: string, fiscal_category: string): Promise<Income> => { ... }
export const updateExpenseFiscalCategory = (expenseId: string, fiscal_category: string): Promise<Expense> => { ... }
export const getFiscalSuggestions = (propertyId: string): Promise<FiscalSuggestionsResponse> => { ... }
```

### 8.3 Modificar Formularios Existentes

#### `IncomeForm.tsx` y `ExpenseForm.tsx`

Añadir un `<select>` opcional al final del formulario para la categoría fiscal.
Este select se pre-rellena con la sugerencia automática basada en la categoría general
seleccionada (llamando al mapper del frontend).

### 8.4 Nuevo Componente — `FiscalClassificationPanel`

Panel que se integra en la pestaña "Datos Fiscales" de `PropertyDetail`.
Muestra:
- Un resumen: "X gastos sin clasificar / Y ingresos sin clasificar".
- Botón "Clasificar automáticamente" que llama a `GET /fiscal-suggestions` y permite
  al usuario aceptar/modificar cada sugerencia en lote.
- Una lista de los registros ya clasificados con su etiqueta fiscal.

### 8.5 Integración en `PropertyDetail`

El panel `FiscalClassificationPanel` se renderiza dentro de la pestaña "Datos Fiscales"
debajo del formulario de datos catastrales/adquisición existente (`FiscalDataForm`).

---

## 9. Tests

### 9.1 Tests Unitarios

| ID | Archivo | Descripción |
|---|---|---|
| T-U-11-01 | `test_entities.py` | Expense acepta fiscal_category válida |
| T-U-11-02 | `test_entities.py` | Expense funciona sin fiscal_category (None por defecto) |
| T-U-11-03 | `test_entities.py` | Income acepta fiscal_category válida |
| T-U-11-04 | `test_entities.py` | Income funciona sin fiscal_category (None por defecto) |
| T-U-11-05 | `test_fiscal_services.py` | FiscalCategoryMapper sugiere REPARACION_CONSERVACION para REPAIR |
| T-U-11-06 | `test_fiscal_services.py` | FiscalCategoryMapper sugiere TRIBUTOS para TAX |
| T-U-11-07 | `test_fiscal_services.py` | FiscalCategoryMapper sugiere INTERESES_CAPITAL para MORTGAGE |
| T-U-11-08 | `test_fiscal_services.py` | FiscalCategoryMapper sugiere SERVICIOS_SUMINISTROS para COMMUNITY_FEE y UTILITY |
| T-U-11-09 | `test_fiscal_services.py` | FiscalCategoryMapper sugiere RENDIMIENTO_INTEGRO para RENT |
| T-U-11-10 | `test_fiscal_services.py` | FiscalCategoryMapper sugiere OTROS_INGRESOS para DEPOSIT |
| T-U-11-11 | `test_fiscal_services.py` | FiscalCategoryMapper cubre TODOS los valores de ExpenseCategory |
| T-U-11-12 | `test_fiscal_services.py` | FiscalCategoryMapper cubre TODOS los valores de IncomeCategory |
| T-U-11-13 | `test_fiscal_use_cases.py` | RecordExpenseUseCase acepta fiscal_category |
| T-U-11-14 | `test_fiscal_use_cases.py` | RecordIncomeUseCase acepta fiscal_category |
| T-U-11-15 | `test_fiscal_use_cases.py` | UpdateFiscalCategoryUseCase actualiza gasto |
| T-U-11-16 | `test_fiscal_use_cases.py` | UpdateFiscalCategoryUseCase rechaza propiedad ajena |
| T-U-11-17 | `test_fiscal_use_cases.py` | SuggestFiscalCategoriesUseCase retorna sugerencias |
| T-U-11-18 | `test_fiscal_use_cases.py` | SuggestFiscalCategoriesUseCase ignora ya clasificados |

### 9.2 Tests de Integración

| ID | Archivo | Descripción |
|---|---|---|
| T-I-11-01 | `test_sqlite_adapter.py` | save/find Income con fiscal_category |
| T-I-11-02 | `test_sqlite_adapter.py` | save/find Expense con fiscal_category |
| T-I-11-03 | `test_sqlite_adapter.py` | update_fiscal_category en Income |
| T-I-11-04 | `test_sqlite_adapter.py` | update_fiscal_category en Expense |
| T-I-11-05 | `test_sqlite_adapter.py` | Income sin fiscal_category sigue funcionando (retrocompat) |
| T-I-11-06 | `test_incomes_api.py` | POST ingreso con fiscal_category |
| T-I-11-07 | `test_incomes_api.py` | GET ingresos incluye fiscal_category en response |
| T-I-11-08 | `test_expenses_api.py` | POST gasto con fiscal_category |
| T-I-11-09 | `test_expenses_api.py` | PATCH actualiza fiscal_category de gasto |
| T-I-11-10 | `test_properties_api.py` | GET fiscal-suggestions retorna sugerencias correctas |

---

## 10. Archivos Afectados (Resumen)

| Acción | Archivo |
|---|---|
| ✏️ Modificar | `backend/domain/entities.py` — nuevos enums `FiscalExpenseCategory`, `FiscalIncomeCategory` + campo en Expense/Income |
| ✏️ Modificar | `backend/domain/services.py` — nuevo servicio `FiscalCategoryMapper` |
| ✏️ Modificar | `backend/domain/ports.py` — nuevo método `update_fiscal_category` en Income/ExpenseRepository |
| ✏️ Modificar | `backend/application/use_cases.py` — modificar RecordIncome/Expense + 2 nuevos UCs |
| ✏️ Modificar | `backend/adapters/sqlite_adapter.py` — migración columnas + actualizar save/_row_to_entity + update_fiscal_category |
| ✏️ Modificar | `backend/api/schemas.py` — fiscal_category en schemas + nuevos schemas |
| ✏️ Modificar | `backend/api/routes/incomes.py` — PATCH fiscal-category + pasar fiscal_category en POST |
| ✏️ Modificar | `backend/api/routes/expenses.py` — PATCH fiscal-category + pasar fiscal_category en POST |
| ✏️ Modificar | `backend/api/routes/properties.py` — GET fiscal-suggestions |
| ✏️ Modificar | `backend/api/main.py` — (si se necesita registrar algo nuevo) |
| ✏️ Modificar | `frontend/src/types/index.ts` — nuevos tipos fiscales |
| ✏️ Modificar | `frontend/src/services/api.ts` — 3 nuevos métodos |
| ✏️ Modificar | `frontend/src/components/IncomeForm.tsx` — select fiscal_category |
| ✏️ Modificar | `frontend/src/components/ExpenseForm.tsx` — select fiscal_category |
| 🆕 Crear | `frontend/src/components/FiscalClassificationPanel.tsx` — panel de clasificación |
| ✏️ Modificar | `frontend/src/pages/PropertyDetail.tsx` — integrar panel en pestaña fiscal |
| ✏️ Modificar | `frontend/src/index.css` — estilos panel clasificación |
| 🆕 Crear | `tests/unit/backend/domain/test_fiscal_services.py` — tests T-U-11-05 a T-U-11-12 |
| ✏️ Modificar | `tests/unit/backend/domain/test_entities.py` — tests T-U-11-01 a T-U-11-04 |
| ✏️ Modificar | `tests/unit/backend/application/test_fiscal_use_cases.py` — tests T-U-11-13 a T-U-11-18 |
| ✏️ Modificar | `tests/integration/backend/adapters/test_sqlite_adapter.py` — tests T-I-11-01 a T-I-11-05 |
| ✏️ Modificar | `tests/integration/backend/api/test_incomes_api.py` — tests T-I-11-06 a T-I-11-07 |
| ✏️ Modificar | `tests/integration/backend/api/test_expenses_api.py` — tests T-I-11-08 a T-I-11-09 |
| ✏️ Modificar | `tests/integration/backend/api/test_properties_api.py` — test T-I-11-10 |

---

## 11. 📚 Rincón del Estudiante

### ¿Por qué una clasificación paralela en vez de reemplazar las categorías existentes?

Las categorías actuales (`REPAIR`, `TAX`, etc.) cumplen una función contable: ayudan al usuario
a organizar sus gastos en el día a día. Las categorías fiscales (`REPARACION_CONSERVACION`,
`TRIBUTOS`, etc.) sirven para un propósito distinto: calcular la declaración de la renta.

Si reemplazáramos las categorías existentes:
- Romperíamos retrocompatibilidad (todos los gastos existentes perderían su categoría).
- Obligaríamos al usuario a pensar en términos fiscales al registrar un gasto cotidiano.
- Mezclaríamos dos responsabilidades en un solo campo.

Con la clasificación paralela:
- El usuario registra gastos con su categoría habitual (UX sin fricción).
- Cuando llega la campaña fiscal, clasifica fiscalmente (puede hacerlo de golpe con las sugerencias).
- El motor fiscal (F-12) lee `fiscal_category`, no `category`.

### ¿Por qué un Servicio de Dominio para el mapeo y no un dict en la API?

El mapeo entre categorías generales y fiscales es **conocimiento de negocio**: "un gasto
de tipo REPAIR generalmente corresponde a REPARACION_CONSERVACION según la AEAT". Este
conocimiento no pertenece a la capa de API (que solo traduce HTTP↔dominio), sino al dominio.

Además, el mapeo puede evolucionar (por ejemplo, si cambia la normativa fiscal) sin tocar
la capa HTTP.

### ¿Por qué PATCH y no PUT para actualizar la categoría fiscal?

- **PUT** implica reemplazar el recurso completo. Si usáramos PUT, el cliente tendría que
  enviar todos los campos del gasto (amount, date, category, description...) aunque solo
  quiera cambiar `fiscal_category`.
- **PATCH** indica una modificación parcial: "solo estoy actualizando un campo". Es
  semánticamente más correcto y reduce la posibilidad de errores (sobrescribir campos
  por accidente).

### ¿Qué pasa con la hipoteca? ¿Es deducible o no?

La cuota de hipoteca tiene dos partes:
- **Intereses** → Deducibles como `INTERESES_CAPITAL`.
- **Amortización de capital** → NO deducibles (es devolver el préstamo, no un gasto).

El sistema sugiere `INTERESES_CAPITAL` para gastos tipo `MORTGAGE`, pero la UI mostrará
una nota advirtiendo que solo la parte de intereses es deducible. Si el usuario registra
la cuota completa, debería separar ambas partes en dos registros distintos.
