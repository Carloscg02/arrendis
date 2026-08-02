# F-12 — Motor de Cálculo Fiscal (Amortización, Reducciones, Rendimiento Neto)

> **Épica:** E-01 Fiscalidad  
> **Dependencias:** F-09 (datos catastrales/adquisición), F-10 (contratos), F-11 (clasificación fiscal)  
> **Estado:** Pendiente de aprobación

---

## 1. Objetivo

F-12 es el **corazón del módulo fiscal**. Toma todas las entradas recopiladas en F-09, F-10 y F-11
y las procesa para generar el **Rendimiento Neto del Capital Inmobiliario** conforme a la normativa
fiscal española (IRPF, modelo D-100).

Este motor es **lógica de dominio pura** — no accede a bases de datos, no llama a APIs externas,
no depende de ningún framework. Recibe entidades y VOs como entrada y devuelve un Value Object
`FiscalReport` como salida.

### Lo que calcula:

1. **Rendimientos Íntegros** — Suma de ingresos fiscalmente clasificados del año fiscal.
2. **Prorrateo por Ocupación** — Calcula los días exactos que la vivienda estuvo alquilada
   y aplica esa proporción a los gastos fijos (IBI, seguro, comunidad, amortización).
3. **Tope de Reparación + Intereses** — Los gastos de reparación/conservación e intereses
   de capital no pueden superar los rendimientos íntegros (el exceso se traslada a 4 años).
4. **Amortización** — 3% del mayor entre el coste de adquisición de la construcción
   y el valor catastral de la construcción, prorrateado por ocupación.
5. **Reducción por Vivienda Habitual** — Si el arrendamiento es de larga duración
   (vivienda habitual), se aplica una reducción del 60% sobre el rendimiento neto positivo
   proporcional a los días bajo ese tipo de contrato.
6. **Rendimiento Neto Final** — La cifra exacta que el propietario debe declarar.

---

## 2. Lenguaje Ubicuo (Nuevos Términos)

| Término | Definición |
|---|---|
| **FiscalReport** | Value Object inmutable que contiene el resultado completo del cálculo fiscal para una propiedad en un año fiscal. |
| **Rendimiento Íntegro** | Suma de todos los ingresos clasificados como RENDIMIENTO_INTEGRO + OTROS_INGRESOS del año fiscal. |
| **Ratio de Ocupación** | `días_alquilados / días_del_año`. Se usa para prorratear gastos que aplican a todo el año. |
| **Base de Amortización** | `max(coste_construcción_adquisición, valor_catastral_construcción)`. Es el mayor de los dos valores, excluyendo siempre el suelo. |
| **Tope Art. 23.1.a LIRPF** | Los gastos de reparación/conservación e intereses de préstamos no pueden superar los rendimientos íntegros en el ejercicio. El exceso se deduce en los 4 años siguientes. |
| **Reducción VH** | Reducción del 60% aplicable cuando el arrendamiento es de vivienda habitual y el rendimiento neto es positivo. |

---

## 3. Modelo de Dominio

### 3.1 Nuevo Value Object — `FiscalReport`

Se añade en `backend/domain/value_objects.py`:

```python
@dataclass(frozen=True)
class FiscalReport:
    """Resultado completo del cálculo fiscal para una propiedad en un año fiscal.

    Es un Value Object: inmutable, sin identidad. Se compara por valor.
    Cada campo documenta una línea del cálculo paso a paso.
    """
    fiscal_year: int
    property_id: str

    # ── Rendimientos Íntegros ──
    gross_rental_income: Decimal      # Suma RENDIMIENTO_INTEGRO
    other_income: Decimal             # Suma OTROS_INGRESOS
    total_income: Decimal             # gross_rental_income + other_income

    # ── Ocupación ──
    rented_days: int                  # Días efectivos de alquiler en el año
    total_days_in_year: int           # 365 o 366
    occupation_ratio: Decimal         # rented_days / total_days_in_year

    # ── Gastos Deducibles por Categoría (tras prorrateo) ──
    expenses_intereses: Decimal
    expenses_reparacion: Decimal
    expenses_tributos: Decimal
    expenses_seguros: Decimal
    expenses_suministros: Decimal
    expenses_formalizacion: Decimal
    expenses_dudoso_cobro: Decimal
    expenses_otros: Decimal

    # ── Tope Reparación + Intereses ──
    repair_interest_raw: Decimal      # Suma sin tope
    repair_interest_cap: Decimal      # = total_income (el tope)
    repair_interest_applied: Decimal  # min(raw, cap)
    repair_interest_excess: Decimal   # max(0, raw - cap) → a deducir en 4 años

    # ── Amortización ──
    amortization_base: Decimal        # max(coste_construcción, catastral_construcción)
    amortization_rate: Decimal        # 0.03 (3%)
    amortization_full_year: Decimal   # base × rate
    amortization_prorated: Decimal    # full_year × occupation_ratio

    # ── Rendimiento Neto ──
    total_deductible_expenses: Decimal  # Suma de todo lo deducible (con tope + amortización)
    net_income_before_reduction: Decimal  # total_income - total_deductible

    # ── Reducción por Vivienda Habitual ──
    vivienda_habitual_days: int       # Días bajo contratos de VH
    vivienda_habitual_ratio: Decimal  # vh_days / rented_days (0 si no hay)
    reduction_base: Decimal           # Porción del RN atribuible a VH (si RN > 0)
    reduction_percentage: Decimal     # 0.60
    reduction_amount: Decimal         # reduction_base × reduction_percentage

    # ── Resultado Final ──
    net_income_final: Decimal         # net_income_before_reduction - reduction_amount

    # ── Metadatos ──
    unclassified_income_count: int    # Ingresos sin fiscal_category (excluidos del cálculo)
    unclassified_expense_count: int   # Gastos sin fiscal_category (excluidos del cálculo)
    has_warnings: bool                # True si hay registros sin clasificar
```

### 3.2 Nuevo Servicio de Dominio — `FiscalCalculator`

Se añade en `backend/domain/services.py`. Es el motor de cálculo puro:

```python
class FiscalCalculator:
    """Motor de cálculo fiscal para Rendimientos del Capital Inmobiliario.

    Servicio de Dominio: sin estado, sin identidad, sin dependencias externas.
    Recibe entidades y VOs, devuelve un FiscalReport.
    """

    AMORTIZATION_RATE = Decimal("0.03")  # 3% anual
    VIVIENDA_REDUCTION_RATE = Decimal("0.60")  # 60% reducción

    @classmethod
    def calculate(
        cls,
        fiscal_year: int,
        property: Property,
        incomes: list[Income],
        expenses: list[Expense],
        contracts: list[LeaseContract],
    ) -> FiscalReport:
        """Genera el informe fiscal completo para una propiedad y año fiscal."""
        ...
```

#### Algoritmo detallado:

```
ENTRADA: fiscal_year, property (con datos fiscales), incomes, expenses, contracts

PASO 1 — Filtrar por año fiscal:
  - incomes_year = [i for i in incomes if i.date.year == fiscal_year]
  - expenses_year = [e for e in expenses if e.date.year == fiscal_year]

PASO 2 — Separar clasificados de no clasificados:
  - classified_incomes = [i for i in incomes_year if i.fiscal_category is not None]
  - classified_expenses = [e for e in expenses_year if e.fiscal_category is not None
                           AND e.fiscal_category != NO_DEDUCIBLE]
  - unclassified_income_count = len(incomes_year) - len(classified_incomes)
  - unclassified_expense_count = len(expenses_year) - len([e sin fiscal_category])

PASO 3 — Rendimientos Íntegros:
  - gross_rental_income = Σ (i.amount para i en classified_incomes si RENDIMIENTO_INTEGRO)
  - other_income = Σ (i.amount para i en classified_incomes si OTROS_INGRESOS)
  - total_income = gross_rental_income + other_income

PASO 4 — Calcular ocupación:
  - rented_days = máx sin solapar de Σ contract.rented_days_in_year(fiscal_year)
    (NOTA: usamos la unión de intervalos para evitar contar días duplicados
     cuando hay contratos solapados)
  - total_days = 366 si bisiesto else 365
  - occupation_ratio = rented_days / total_days

PASO 5 — Gastos deducibles por categoría (prorrateados):
  Para cada FiscalExpenseCategory (excepto NO_DEDUCIBLE):
    raw = Σ (e.amount para e en classified_expenses si e.fiscal_category == cat)
    prorated = raw × occupation_ratio
  
  NOTA: Los gastos de REPARACION_CONSERVACION e INTERESES_CAPITAL
  NO se prorratean por ocupación (son deducibles al 100% si se producen
  durante el periodo de alquiler). Pero SÍ se sujetan al tope.
  Los demás gastos fijos (tributos, seguros, suministros, amortización) 
  SÍ se prorratean.

PASO 6 — Tope reparación + intereses (Art. 23.1.a LIRPF):
  repair_interest_raw = expenses_reparacion + expenses_intereses
  repair_interest_cap = total_income
  repair_interest_applied = min(raw, cap)
  repair_interest_excess = max(0, raw - cap)

PASO 7 — Amortización:
  construction_acquisition = property.acquisition_cost.construction_portion
    + (property.acquisition_cost.total_acquisition_expenses 
       × property.acquisition_cost.construction_portion 
       / property.acquisition_cost.purchase_price)
  construction_cadastral = property.cadastral_breakdown.construction_value
  
  amortization_base = max(construction_acquisition, construction_cadastral)
  amortization_full_year = amortization_base × 0.03
  amortization_prorated = amortization_full_year × occupation_ratio

PASO 8 — Total gastos deducibles:
  total_deductible = repair_interest_applied
    + expenses_tributos + expenses_seguros + expenses_suministros
    + expenses_formalizacion + expenses_dudoso_cobro + expenses_otros
    + amortization_prorated

PASO 9 — Rendimiento Neto previo:
  net_before = total_income - total_deductible

PASO 10 — Reducción por vivienda habitual:
  vh_days = Σ contract.rented_days_in_year(fiscal_year) para contratos VIVIENDA_HABITUAL
  (también con unión de intervalos para evitar solapamientos)
  vh_ratio = vh_days / rented_days (si rented_days > 0, else 0)
  
  Si net_before > 0 Y vh_days > 0:
    reduction_base = net_before × vh_ratio
    reduction_amount = reduction_base × 0.60
  Sino:
    reduction_amount = 0

PASO 11 — Rendimiento Neto Final:
  net_final = net_before - reduction_amount

SALIDA: FiscalReport con todos los campos calculados
```

### 3.3 Función auxiliar — Unión de intervalos de fechas

Para calcular `rented_days` sin contar días duplicados cuando hay contratos solapados,
se necesita una función auxiliar en el servicio:

```python
@staticmethod
def _merge_rented_intervals(
    contracts: list[LeaseContract],
    fiscal_year: int,
) -> int:
    """Calcula los días totales de alquiler sin solapamientos."""
    year_start = date(fiscal_year, 1, 1)
    year_end = date(fiscal_year, 12, 31)

    intervals = []
    for c in contracts:
        eff_start = max(c.start_date, year_start)
        eff_end = min(c.end_date or year_end, year_end)
        if eff_start <= eff_end:
            intervals.append((eff_start, eff_end))

    if not intervals:
        return 0

    # Ordenar y fusionar intervalos solapados
    intervals.sort()
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1] + timedelta(days=1):
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return sum((end - start).days + 1 for start, end in merged)
```

---

## 4. Puertos

No se necesitan nuevos puertos. El Use Case orquestará la recolección de datos
desde los repositorios existentes y los pasará al `FiscalCalculator`.

---

## 5. Caso de Uso — `GenerateFiscalReportUseCase`

```
Entrada: user_id, property_id, fiscal_year
Proceso:
  1. Obtener property del PropertyRepository. Validar pertenencia al usuario.
  2. Validar que property.has_fiscal_data es True. Si no, error.
  3. Obtener incomes del IncomeRepository (find_by_property_id).
  4. Obtener expenses del ExpenseRepository (find_by_property_id).
  5. Obtener contracts del LeaseContractRepository (find_by_property_id).
  6. Llamar a FiscalCalculator.calculate(fiscal_year, property, incomes, expenses, contracts).
  7. Retornar el FiscalReport.
Salida:  FiscalReport (Value Object)
Error:   ValueError si la propiedad no existe, no pertenece al usuario,
         o no tiene datos fiscales completos.
```

---

## 6. Adaptador SQLite

**No se necesitan cambios en el adaptador.** F-12 no crea ni persiste datos nuevos.
Solo lee de los repositorios existentes y calcula en memoria.

---

## 7. API REST

### 7.1 Nuevo Schema — `FiscalReportResponse`

```python
class FiscalReportResponse(BaseModel):
    fiscal_year: int
    property_id: str

    # Rendimientos
    gross_rental_income: Decimal
    other_income: Decimal
    total_income: Decimal

    # Ocupación
    rented_days: int
    total_days_in_year: int
    occupation_ratio: Decimal

    # Gastos por categoría
    expenses_intereses: Decimal
    expenses_reparacion: Decimal
    expenses_tributos: Decimal
    expenses_seguros: Decimal
    expenses_suministros: Decimal
    expenses_formalizacion: Decimal
    expenses_dudoso_cobro: Decimal
    expenses_otros: Decimal

    # Tope
    repair_interest_raw: Decimal
    repair_interest_cap: Decimal
    repair_interest_applied: Decimal
    repair_interest_excess: Decimal

    # Amortización
    amortization_base: Decimal
    amortization_rate: Decimal
    amortization_full_year: Decimal
    amortization_prorated: Decimal

    # Rendimiento neto
    total_deductible_expenses: Decimal
    net_income_before_reduction: Decimal

    # Reducción VH
    vivienda_habitual_days: int
    vivienda_habitual_ratio: Decimal
    reduction_base: Decimal
    reduction_percentage: Decimal
    reduction_amount: Decimal

    # Final
    net_income_final: Decimal

    # Metadatos
    unclassified_income_count: int
    unclassified_expense_count: int
    has_warnings: bool
```

### 7.2 Nuevo Endpoint

| Método | Ruta | Descripción | Response |
|---|---|---|---|
| `GET` | `/api/properties/{property_id}/fiscal-report?year={year}` | Calcula y devuelve el informe fiscal | `FiscalReportResponse` |

Se añade al router `properties.py`.

---

## 8. Frontend

### 8.1 Tipos TypeScript

```typescript
export interface FiscalReport {
  fiscal_year: number;
  property_id: string;
  gross_rental_income: string;
  other_income: string;
  total_income: string;
  rented_days: number;
  total_days_in_year: number;
  occupation_ratio: string;
  expenses_intereses: string;
  expenses_reparacion: string;
  expenses_tributos: string;
  expenses_seguros: string;
  expenses_suministros: string;
  expenses_formalizacion: string;
  expenses_dudoso_cobro: string;
  expenses_otros: string;
  repair_interest_raw: string;
  repair_interest_cap: string;
  repair_interest_applied: string;
  repair_interest_excess: string;
  amortization_base: string;
  amortization_rate: string;
  amortization_full_year: string;
  amortization_prorated: string;
  total_deductible_expenses: string;
  net_income_before_reduction: string;
  vivienda_habitual_days: number;
  vivienda_habitual_ratio: string;
  reduction_base: string;
  reduction_percentage: string;
  reduction_amount: string;
  net_income_final: string;
  unclassified_income_count: number;
  unclassified_expense_count: number;
  has_warnings: boolean;
}
```

### 8.2 Servicio API

```typescript
export const getFiscalReport = (propertyId: string, year: number): Promise<FiscalReport> =>
  api.get(`/api/properties/${propertyId}/fiscal-report?year=${year}`).then(r => r.data);
```

### 8.3 Nuevo Componente — `FiscalReportView`

Componente que muestra el informe fiscal completo en un formato claro y paso a paso:

- **Sección 1: Rendimientos Íntegros** — Tabla con gross_rental_income, other_income, total.
- **Sección 2: Ocupación** — Barra visual con rented_days / total_days y porcentaje.
- **Sección 3: Gastos Deducibles** — Tabla con cada categoría fiscal y su importe prorrateado.
- **Sección 4: Tope de Reparación e Intereses** — Indicador visual (verde si bajo tope, naranja si limitado).
- **Sección 5: Amortización** — Cálculo paso a paso (base × 3% × ratio).
- **Sección 6: Rendimiento Neto** — total_income − total_deductible.
- **Sección 7: Reducción por Vivienda Habitual** — Si aplica, con porcentaje y cálculo.
- **Sección 8: Resultado Final** — El número clave, destacado visualmente.
- **Warnings** — Si hay ingresos/gastos sin clasificar, aviso con link a clasificarlos.

### 8.4 Integración en `PropertyDetail`

El `FiscalReportView` se integra dentro de la pestaña "📊 Datos Fiscales", debajo del
`FiscalClassificationPanel`. Se muestra un selector de año fiscal y un botón "Generar Informe".

---

## 9. Tests

### 9.1 Tests Unitarios del Motor de Cálculo (lo más crítico)

| ID | Archivo | Descripción |
|---|---|---|
| T-U-12-01 | `test_fiscal_calculator.py` | Caso base: 1 contrato VH, todo el año, datos completos |
| T-U-12-02 | `test_fiscal_calculator.py` | Sin contratos en el año → rented_days=0, todo a 0 |
| T-U-12-03 | `test_fiscal_calculator.py` | Contrato parcial (6 meses) → prorrateo al 50% aprox |
| T-U-12-04 | `test_fiscal_calculator.py` | Tope reparación+intereses cuando exceden ingresos |
| T-U-12-05 | `test_fiscal_calculator.py` | Tope reparación+intereses cuando NO exceden ingresos |
| T-U-12-06 | `test_fiscal_calculator.py` | Amortización usa max(adquisición, catastral) |
| T-U-12-07 | `test_fiscal_calculator.py` | Amortización usa catastral cuando es mayor |
| T-U-12-08 | `test_fiscal_calculator.py` | Reducción 60% con contrato VH y RN positivo |
| T-U-12-09 | `test_fiscal_calculator.py` | Sin reducción si RN es negativo |
| T-U-12-10 | `test_fiscal_calculator.py` | Sin reducción si contrato no es VH |
| T-U-12-11 | `test_fiscal_calculator.py` | Mix de contratos VH + TEMPORAL → reducción proporcional |
| T-U-12-12 | `test_fiscal_calculator.py` | Gastos NO_DEDUCIBLE excluidos del cálculo |
| T-U-12-13 | `test_fiscal_calculator.py` | Ingresos/gastos sin fiscal_category excluidos + warnings |
| T-U-12-14 | `test_fiscal_calculator.py` | Contratos solapados: no doble-contar días |
| T-U-12-15 | `test_fiscal_calculator.py` | Año bisiesto: 366 días |
| T-U-12-16 | `test_fiscal_calculator.py` | Gastos de años distintos al fiscal_year excluidos |
| T-U-12-17 | `test_fiscal_calculator.py` | Cálculo proporcional de gastos adquisición en amortización |

### 9.2 Tests Unitarios del Use Case

| ID | Archivo | Descripción |
|---|---|---|
| T-U-12-18 | `test_fiscal_report_use_case.py` | Genera report con datos completos |
| T-U-12-19 | `test_fiscal_report_use_case.py` | Error si propiedad sin datos fiscales |
| T-U-12-20 | `test_fiscal_report_use_case.py` | Error si propiedad no pertenece al usuario |

### 9.3 Tests del Value Object

| ID | Archivo | Descripción |
|---|---|---|
| T-U-12-21 | `test_fiscal_value_objects.py` | FiscalReport es inmutable (frozen) |
| T-U-12-22 | `test_fiscal_value_objects.py` | FiscalReport se compara por valor |

### 9.4 Tests de Integración API

| ID | Archivo | Descripción |
|---|---|---|
| T-I-12-01 | `test_fiscal_report_api.py` | GET fiscal-report con datos completos retorna 200 |
| T-I-12-02 | `test_fiscal_report_api.py` | GET fiscal-report sin datos fiscales retorna 400 |
| T-I-12-03 | `test_fiscal_report_api.py` | GET fiscal-report propiedad ajena retorna 404 |
| T-I-12-04 | `test_fiscal_report_api.py` | GET fiscal-report sin contratos en año → todo a 0 |
| T-I-12-05 | `test_fiscal_report_api.py` | GET fiscal-report cálculos numéricos correctos end-to-end |

---

## 10. Archivos Afectados (Resumen)

| Acción | Archivo |
|---|---|
| ✏️ Modificar | `backend/domain/value_objects.py` — nuevo VO `FiscalReport` |
| ✏️ Modificar | `backend/domain/services.py` — nuevo servicio `FiscalCalculator` |
| ✏️ Modificar | `backend/application/use_cases.py` — nuevo `GenerateFiscalReportUseCase` |
| ✏️ Modificar | `backend/api/schemas.py` — nuevo `FiscalReportResponse` |
| ✏️ Modificar | `backend/api/routes/properties.py` — nuevo GET endpoint |
| ✏️ Modificar | `backend/api/dependencies.py` — (si se necesita inyectar repos para el UC) |
| ✏️ Modificar | `frontend/src/types/index.ts` — tipo `FiscalReport` |
| ✏️ Modificar | `frontend/src/services/api.ts` — método `getFiscalReport` |
| 🆕 Crear | `frontend/src/components/FiscalReportView.tsx` — visualización del informe |
| ✏️ Modificar | `frontend/src/pages/PropertyDetail.tsx` — integrar FiscalReportView |
| ✏️ Modificar | `frontend/src/index.css` — estilos del informe |
| 🆕 Crear | `tests/unit/backend/domain/test_fiscal_calculator.py` — 17 tests motor |
| 🆕 Crear | `tests/unit/backend/application/test_fiscal_report_use_case.py` — 3 tests UC |
| ✏️ Modificar | `tests/unit/backend/domain/test_fiscal_value_objects.py` — 2 tests VO |
| 🆕 Crear | `tests/integration/backend/api/test_fiscal_report_api.py` — 5 tests API |

---

## 11. 📚 Rincón del Estudiante

### ¿Por qué es un Servicio de Dominio y no un Caso de Uso?

La regla clave de la arquitectura hexagonal es:
- **Servicios de Dominio** = lógica de negocio pura (sin dependencias externas).
- **Casos de Uso** = orquestación (llaman a repos + servicios de dominio).

`FiscalCalculator.calculate()` no accede a ningún repositorio. Recibe entidades como
parámetros y devuelve un VO. Es matemática pura. Por eso vive en `services.py`.

`GenerateFiscalReportUseCase` sí accede a 4 repositorios para reunir los datos
y luego delega el cálculo al servicio. Es orquestación pura. Por eso vive en `use_cases.py`.

### ¿Cómo funciona la amortización exactamente?

La AEAT dice: *"El 3% sobre el mayor de: (a) coste de adquisición satisfecho, (b) valor
catastral, en ambos casos sin incluir el valor del suelo"*.

Pero "coste de adquisición" incluye los gastos asociados (notaría, registro, ITP),
prorrateados entre construcción y suelo:

```
gastos_adquisición = ITP + notaría + registro
proporción_construcción = precio_construcción / precio_compra
coste_construcción_total = precio_construcción + (gastos_adquisición × proporción_construcción)
```

Ejemplo: Piso comprado por 200.000€ (120.000€ construcción + 80.000€ suelo),
con 12.000€ de gastos de adquisición:
- proporción_construcción = 120.000 / 200.000 = 0.60
- coste_construcción = 120.000 + (12.000 × 0.60) = 127.200€
- Si valor catastral construcción = 90.000€
- Base amortización = max(127.200, 90.000) = 127.200€
- Amortización anual = 127.200 × 3% = 3.816€
- Si alquilado 183 días → amortización = 3.816 × (183/365) = 1.913,42€

### ¿Por qué se fusionan intervalos de contratos?

Si un propietario tiene dos contratos solapados (uno termina el 30/06 y otro
empieza el 15/06), los días del 15 al 30 de junio no deben contarse dos veces.
La función `_merge_rented_intervals` ordena los contratos por fecha de inicio
y fusiona los que se solapan, garantizando un conteo exacto de días únicos.

### ¿Cuándo NO aplica la reducción del 60%?

1. Si el rendimiento neto es **negativo** (no se reduce una pérdida).
2. Si el contrato no es de tipo **VIVIENDA_HABITUAL** (temporal, turístico, comercial).
3. Si hay mix de contratos: la reducción solo aplica a la **proporción de días
   bajo contrato VH** respecto al total de días alquilados.
