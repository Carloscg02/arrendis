# 🏛️ Épica E-01: Sistema de Fiscalidad y Declaración de Impuestos

> **Versión:** 1.0  
> **Estado:** En Descubrimiento (Discovery)  
> **Fecha:** 2026-08-01  
> **Dependencia previa:** F-08 (Multi-tenancy) — las propiedades deben estar vinculadas a un usuario antes de generar informes fiscales por propietario.

---

## 1. Objetivo de Negocio

Que el propietario pueda generar un **"Borrador Fiscal en PDF"** anual por cada propiedad. Este informe agrupará los ingresos por naturaleza, calculará automáticamente las amortizaciones, sumará los gastos categorizados por tipo fiscal y aplicará las reducciones legales pertinentes, sirviendo como un resumen listo para trasladar a **Renta Web (AEAT)**.

### ¿Qué problema resuelve?

Hoy, un propietario que alquila un piso tiene que:
1. Abrir una hoja de Excel y listar todos los recibos de alquiler del año.
2. Buscar el recibo del IBI para sacar el valor catastral de la construcción.
3. Desempolvar la escritura de compraventa para calcular qué porcentaje del precio fue suelo y qué porcentaje fue construcción.
4. Calcular manualmente el 3% de amortización sobre el mayor de los dos valores.
5. Clasificar cada gasto (¿fue una reparación o una mejora?) para saber si lo deduce este año o lo amortiza.
6. Aplicar la reducción del 50-90% si corresponde.
7. Trasladar todo a Renta Web casilla por casilla.

**Con este sistema**, todo ese trabajo se automatiza: el usuario introduce los datos de su propiedad una vez, registra ingresos y gastos durante el año, y al final pulsa un botón para obtener el PDF con todo calculado.

---

## 2. Límites del Subdominio (Bounded Context)

### ✅ Lo que ENTRA en esta épica
- Datos catastrales y de adquisición de cada propiedad (valor suelo, valor construcción, gastos de compra).
- Naturaleza fiscal de los ingresos (Renta vs. Fianza).
- Categorización fiscal de los gastos (Conservación/Reparación vs. Mejora/Ampliación).
- Cálculo automático de la amortización anual (regla del 3%).
- Contratos de arrendamiento con flag de reducción por vivienda habitual.
- Aplicación de reducciones por vivienda habitual (50%, 70%, 90%).
- Generación del informe/borrador fiscal anual en PDF.

### ❌ Lo que NO ENTRA (fuera de alcance)
- Integración directa con la API de la AEAT (presentación telemática).
- Fiscalidad de propiedades fuera de España.
- Fiscalidad de personas jurídicas (sociedades). Solo personas físicas.
- IVA en alquileres comerciales (primera iteración solo vivienda).
- Gestión de múltiples propietarios sobre una misma propiedad (pro indiviso).
- Cálculo de ganancias patrimoniales por venta del inmueble.

---

## 3. Lenguaje Ubicuo del Subdominio

| Término | Definición |
|---|---|
| **FiscalYear** | Ejercicio fiscal. Período del 1 de enero al 31 de diciembre de un año natural. Es la unidad temporal sobre la que se calculan todos los datos fiscales. |
| **CadastralBreakdown** | Value Object que desglosa el Valor Catastral Total de una propiedad en dos partes: `land_value` (suelo) y `construction_value` (construcción). Se obtiene del recibo del IBI. |
| **AcquisitionCost** | Value Object que representa el coste total de adquisición de un inmueble, desglosado en: precio de compra (separado en suelo y construcción), impuestos de transmisión (ITP), gastos de notaría, registro y gestoría. |
| **IncomeNature** | Clasificación fiscal de un ingreso: `RENT` (renta computable como ingreso fiscal) o `DEPOSIT` (fianza, NO computa como ingreso salvo retención por impago/desperfectos). |
| **DepositRetention** | Evento que ocurre al finalizar un contrato cuando se retiene total o parcialmente una fianza por impago o desperfectos. En ese momento, el importe retenido pasa a computar como ingreso fiscal del ejercicio en que se retiene. |
| **TaxCategory** | Categoría semántica estable para clasificar gastos a efectos fiscales. Ejemplos: `REPAIR`, `INSURANCE`, `COMMUNITY_FEE`, `PROPERTY_TAX`, `MORTGAGE_INTEREST`, `UTILITY`, `MANAGEMENT_FEE`, `IMPROVEMENT`. |
| **DeductibleExpense** | Gasto de conservación o reparación (`TaxCategory.REPAIR`, `INSURANCE`, etc.) que es deducible al 100% en el ejercicio fiscal en curso. |
| **ImprovementExpense** | Gasto de mejora o ampliación (`TaxCategory.IMPROVEMENT`) que NO se deduce de golpe sino que se suma al valor de adquisición de la construcción y se amortiza año a año. |
| **AmortizationBasis** | Base sobre la que se calcula la amortización anual. Es el **mayor** entre: (a) el coste de adquisición imputable a la construcción (precio construcción + gastos de compra proporcionales) y (b) el valor catastral de la construcción. **Nunca incluye el suelo.** |
| **AnnualAmortization** | Gasto deducible calculado como el **3% de la AmortizationBasis**, prorrateado por los días del año en que la propiedad estuvo arrendada. |
| **LeaseContract** | Entidad que representa un contrato de arrendamiento. Vincula un inquilino con una propiedad, con fechas de inicio/fin y un flag `qualifies_for_housing_reduction`. |
| **HousingReduction** | Reducción porcentual que se aplica sobre el rendimiento neto positivo de un alquiler destinado a vivienda habitual del inquilino. Puede ser del 50%, 70% o 90% según las condiciones de la Ley de Vivienda. |
| **NetTaxableIncome** | Rendimiento neto reducido por propiedad: `Ingresos Computables − Gastos Deducibles − Amortización`, con la reducción por vivienda habitual aplicada si procede. Es el número final que el propietario traslada a la declaración. |
| **FiscalReport** | Agregado raíz que consolida toda la información fiscal de una propiedad para un ejercicio: ingresos por naturaleza, gastos por categoría, amortización, reducciones y rendimiento neto. Es la fuente de datos del PDF final. |

---

## 4. Modelo de Dominio

### 4.1 Diagrama de Entidades y Value Objects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SUBDOMINIO DE FISCALIDAD                               │
│                                                                             │
│   Value Objects (inmutables):                                               │
│   ┌─────────────────────┐  ┌──────────────────────────────────────────┐     │
│   │ CadastralBreakdown  │  │ AcquisitionCost                         │     │
│   │                     │  │                                          │     │
│   │ land_value: Decimal │  │ purchase_price: Decimal                  │     │
│   │ construction_value  │  │ construction_portion: Decimal            │     │
│   │             Decimal │  │ land_portion: Decimal                    │     │
│   └─────────────────────┘  │ transfer_tax (ITP): Decimal              │     │
│                             │ notary_fees: Decimal                     │     │
│                             │ registry_fees: Decimal                   │     │
│                             └──────────────────────────────────────────┘     │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ Enumeraciones                                                        │  │
│   │                                                                      │  │
│   │ IncomeNature:  RENT | DEPOSIT                                        │  │
│   │                                                                      │  │
│   │ TaxCategory:   REPAIR | INSURANCE | COMMUNITY_FEE | PROPERTY_TAX     │  │
│   │                MORTGAGE_INTEREST | UTILITY | MANAGEMENT_FEE           │  │
│   │                IMPROVEMENT | OTHER_DEDUCTIBLE                         │  │
│   │                                                                      │  │
│   │ ReductionTier: STANDARD_50 | AFFORDABLE_70 | SOCIAL_90               │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Entidad:                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ LeaseContract                                                        │  │
│   │                                                                      │  │
│   │ id: UUID                                                             │  │
│   │ property_id: str               (FK → Property)                       │  │
│   │ tenant_name: str                                                     │  │
│   │ start_date: date                                                     │  │
│   │ end_date: date | None                                                │  │
│   │ monthly_rent: Decimal                                                │  │
│   │ deposit_amount: Decimal                                              │  │
│   │ qualifies_for_housing_reduction: bool                                │  │
│   │ reduction_tier: ReductionTier                                        │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Agregado Raíz (construido, no persistido):                                │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ FiscalReport                                                         │  │
│   │                                                                      │  │
│   │ property_id: str                                                     │  │
│   │ fiscal_year: int                                                     │  │
│   │ rental_incomes: list[Income]      ← Solo naturaleza RENT             │  │
│   │ deposit_retentions: list[Income]  ← Fianzas retenidas                │  │
│   │ deductible_expenses: list[Expense]                                   │  │
│   │ improvement_expenses: list[Expense]                                  │  │
│   │ amortization: Decimal             ← Calculada por servicio           │  │
│   │ gross_income: Decimal                                                │  │
│   │ total_deductions: Decimal                                            │  │
│   │ net_income_before_reduction: Decimal                                 │  │
│   │ housing_reduction: Decimal                                           │  │
│   │ net_taxable_income: Decimal       ← El número final                  │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Servicios de Dominio (Python puro, cero dependencias):                    │
│   ┌──────────────────────────┐  ┌─────────────────────────────────────┐    │
│   │ AmortizationCalculator   │  │ TaxableIncomeCalculator             │    │
│   │                          │  │                                     │    │
│   │ calculate(               │  │ calculate(                          │    │
│   │   cadastral,             │  │   incomes,                          │    │
│   │   acquisition,           │  │   expenses,                         │    │
│   │   improvements,          │  │   amortization,                     │    │
│   │   days_rented,           │  │   reduction_tier                    │    │
│   │   total_days             │  │ ) → FiscalReport                    │    │
│   │ ) → Decimal              │  │                                     │    │
│   └──────────────────────────┘  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Relación con el Dominio Existente

El subdominio fiscal **extiende** el dominio actual sin romperlo:

```
Entidades existentes (F-01 a F-07):        Extensiones fiscales (E-01):
┌────────────┐                              ┌─────────────────────────────┐
│  Property  │ ◄──── se enriquece con ────► │ CadastralBreakdown          │
│  (id, name,│                              │ AcquisitionCost             │
│   address) │                              └─────────────────────────────┘
└────────────┘
      │                                     ┌─────────────────────────────┐
      ├── Income  ◄── se enriquece con ───► │ IncomeNature (RENT|DEPOSIT) │
      │                                     └─────────────────────────────┘
      │                                     ┌─────────────────────────────┐
      └── Expense ◄── se enriquece con ───► │ TaxCategory (REPAIR|...)    │
                                            └─────────────────────────────┘
```

**Estrategia de extensión:** Añadir campos opcionales a las entidades y tablas existentes, con valores por defecto que mantienen la compatibilidad con features anteriores. Las propiedades creadas antes de E-01 seguirán funcionando sin datos fiscales; el informe simplemente indicará "datos fiscales incompletos".

---

## 5. Reglas de Negocio Detalladas

### RN-01: Naturaleza de los Ingresos

```
┌──────────────────────────────────────────────────────────────────────┐
│  INGRESO REGISTRADO                                                  │
│                                                                      │
│  ¿Naturaleza = RENT?                                                 │
│  ├── SÍ → Computa como ingreso fiscal en el año del cobro            │
│  └── NO (DEPOSIT / Fianza)                                           │
│       ├── ¿Se devuelve íntegra al finalizar? → NO computa nunca      │
│       └── ¿Se retiene total o parcialmente?                          │
│            → Computa como ingreso en el año de la retención           │
│               (Se registra un evento DepositRetention)               │
└──────────────────────────────────────────────────────────────────────┘
```

### RN-02: Cálculo de la Amortización (Regla del 3%)

```python
# PSEUDOCÓDIGO — Servicio de Dominio (Python puro)
def calculate_amortization(
    cadastral: CadastralBreakdown,
    acquisition: AcquisitionCost,
    accumulated_improvements: Decimal,
    days_rented: int,
    total_days_in_year: int,  # 365 o 366
) -> Decimal:
    """
    Amortización anual = 3% × AmortizationBasis × (días alquilado / días del año)
    
    AmortizationBasis = max(
        coste_adquisicion_construccion,   ← precio_construccion + gastos_compra_proporcionales + mejoras
        valor_catastral_construccion       ← del recibo del IBI
    )
    
    ⚠️ NUNCA se incluye el valor del suelo.
    """
    # Proporción de gastos de compra atribuible a la construcción
    total_purchase = acquisition.construction_portion + acquisition.land_portion
    if total_purchase > 0:
        construction_ratio = acquisition.construction_portion / total_purchase
    else:
        construction_ratio = Decimal("0.5")  # Fallback 50/50 si no hay desglose

    acquisition_expenses = (
        acquisition.transfer_tax
        + acquisition.notary_fees
        + acquisition.registry_fees
    )
    proportional_expenses = acquisition_expenses * construction_ratio

    acquisition_construction_cost = (
        acquisition.construction_portion
        + proportional_expenses
        + accumulated_improvements
    )

    amortization_basis = max(
        acquisition_construction_cost,
        cadastral.construction_value,
    )

    annual_amortization = amortization_basis * Decimal("0.03")

    # Prorrateo por días alquilados
    return (annual_amortization * days_rented / total_days_in_year).quantize(
        Decimal("0.01")
    )
```

### RN-03: Reparaciones vs. Mejoras

| Concepto | TaxCategory | Tratamiento Fiscal | Ejemplo |
|---|---|---|---|
| **Conservación / Reparación** | `REPAIR` | Deducible 100% en el ejercicio | Pintar paredes, arreglar grifo, cambiar cerradura |
| **Mejora / Ampliación** | `IMPROVEMENT` | Se suma al valor de adquisición de la construcción y se amortiza (3% anual) | Instalar aire acondicionado, reformar cocina, cerrar terraza |

**Regla de dominio:** Al generar el `FiscalReport`, los gastos con `TaxCategory.IMPROVEMENT` **no** aparecen en la columna de gastos deducibles del año. En su lugar, se suman a `AcquisitionCost.construction_portion` para incrementar la `AmortizationBasis` de años futuros.

### RN-04: Tabla de Categorías Fiscales Semánticas

| TaxCategory | Descripción | Deducible Directo |
|---|---|---|
| `REPAIR` | Conservación y reparación | ✅ Sí (100%) |
| `INSURANCE` | Seguros (hogar, impago) | ✅ Sí |
| `COMMUNITY_FEE` | Cuota de comunidad de propietarios | ✅ Sí |
| `PROPERTY_TAX` | IBI y tasas municipales | ✅ Sí |
| `MORTGAGE_INTEREST` | Intereses de hipoteca (NO capital) | ✅ Sí |
| `UTILITY` | Suministros pagados por propietario | ✅ Sí |
| `MANAGEMENT_FEE` | Honorarios de gestión/administración | ✅ Sí |
| `LEGAL_FEE` | Gastos jurídicos (abogados, procuradores) | ✅ Sí |
| `OTHER_DEDUCTIBLE` | Otros gastos deducibles no categorizados | ✅ Sí |
| `IMPROVEMENT` | Mejoras y ampliaciones | ❌ No (se amortiza) |

### RN-05: Reducciones por Vivienda Habitual

```
┌──────────────────────────────────────────────────────────────────────┐
│  ¿El contrato tiene qualifies_for_housing_reduction = true?          │
│  │                                                                   │
│  ├── NO → Sin reducción. Rendimiento neto = resultado directo.       │
│  └── SÍ → Aplicar reducción según tier:                              │
│       │                                                              │
│       ├── STANDARD_50  → Reducción del 50% (caso general)            │
│       ├── AFFORDABLE_70 → Reducción del 70% (zona tensionada +       │
│       │                    bajada de renta ≥ 5%)                      │
│       └── SOCIAL_90    → Reducción del 90% (alquiler social,         │
│                           jóvenes 18-35 en zona tensionada)           │
│                                                                      │
│  ⚖️ JURISPRUDENCIA: Alquiler a estudiantes (ej. 10 meses)            │
│     SÍ da derecho a reducción. El criterio es "residencia             │
│     efectiva y permanente durante la vigencia del contrato",          │
│     no que sea todo el año natural.                                  │
│                                                                      │
│  ⚠️ La reducción SOLO se aplica sobre rendimiento neto POSITIVO.     │
│     Si hay pérdidas, no hay reducción (no se amplifica la pérdida).  │
└──────────────────────────────────────────────────────────────────────┘
```

### RN-06: Fórmula Final del Rendimiento Neto Reducido

```
Rendimiento Neto Reducido =
    (Σ Rentas del año + Σ Fianzas retenidas en el año)
  − (Σ Gastos Deducibles del año)
  − (Amortización Anual prorrateada)
  − (Reducción por vivienda habitual, si aplica y si el neto es positivo)
```

---

## 6. Directiva de Arquitectura: Desacoplamiento AEAT

> **Principio:** El dominio habla en **categorías semánticas estables**. La AEAT habla en **casillas numeradas que cambian con cada ejercicio**.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  DOMINIO (Python puro)              PRESENTACIÓN (Generador de PDF)          │
│                                                                              │
│  TaxCategory.INSURANCE      ──►     { "INSURANCE": "Casilla 0114" }          │
│  TaxCategory.REPAIR         ──►     { "REPAIR": "Casilla 0115" }             │
│  TaxCategory.COMMUNITY_FEE  ──►     { "COMMUNITY_FEE": "Casilla 0116" }     │
│                                                                              │
│  El diccionario de mapeo vive       Si la AEAT cambia las casillas en 2027,  │
│  en el adaptador de salida          solo actualizas el diccionario.           │
│  (capa de presentación / PDF).      El dominio NO cambia ni una línea.        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

En términos de Arquitectura Hexagonal:
- **Puerto de salida:** `FiscalReportRenderer` (interfaz abstracta que define cómo se "renderiza" un `FiscalReport`).
- **Adaptador concreto:** `AEATPdfRenderer` (implementa el puerto generando un PDF con el mapeo a casillas del ejercicio vigente).

---

## 7. Desglose en Features SDD

Siguiendo el principio de entregas pequeñas e integrables, la épica se divide en las siguientes features atómicas, ordenadas por dependencia:

```
  F-08                F-09               F-10               F-11
  Multi-tenancy  ──►  Datos Fiscales ──► Contratos de   ──► Clasificación
  (prerequisito)      de Propiedad       Arrendamiento      Fiscal de
                      (catastral +                          Gastos e
                       adquisición)                          Ingresos

                                              │                  │
                                              ▼                  ▼
                                          F-12                F-13
                                          Motor de         ──► Informe Fiscal
                                          Cálculo Fiscal       y Generación
                                          (amortización,       de PDF
                                           reducciones,
                                           rendimiento neto)
```

### Feature F-09: Datos Fiscales de Propiedad (Catastral + Adquisición)

**Alcance:** Extender la entidad `Property` y su persistencia para almacenar el desglose catastral (`CadastralBreakdown`) y los datos de adquisición (`AcquisitionCost`). Crear los Value Objects de dominio. Añadir formulario en el frontend para introducir estos datos en la ficha de cada propiedad.

**Entregable:** El usuario puede abrir una propiedad, ir a una nueva pestaña "Datos Fiscales" y rellenar valores catastrales y de adquisición. Se persiste en SQLite.

### Feature F-10: Contratos de Arrendamiento (Lease Contracts)

**Alcance:** Crear la entidad `LeaseContract` con su repositorio, caso de uso y endpoints CRUD. Incluye el campo `qualifies_for_housing_reduction` y `reduction_tier`. Añadir la sección de contratos en la vista de detalle de cada propiedad en el frontend.

**Entregable:** El usuario puede registrar contratos de arrendamiento asociados a una propiedad, indicando fechas, renta mensual, fianza y si aplica reducción por vivienda habitual.

### Feature F-11: Clasificación Fiscal de Gastos e Ingresos

**Alcance:** Extender `Income` con `IncomeNature` (RENT | DEPOSIT) y `Expense` con `TaxCategory`. Migrar los datos existentes asignando valores por defecto (`RENT` para ingresos, `OTHER_DEDUCTIBLE` para gastos). Actualizar formularios del frontend para incluir los selectores fiscales.

**Entregable:** Al registrar un ingreso o gasto, el usuario selecciona su naturaleza/categoría fiscal. Los datos existentes migran con valores por defecto.

### Feature F-12: Motor de Cálculo Fiscal (Amortización, Reducciones, Rendimiento Neto)

**Alcance:** Implementar los servicios de dominio `AmortizationCalculator` y `TaxableIncomeCalculator` en Python puro. Crear el agregado `FiscalReport`. Exponer un endpoint `GET /api/properties/{id}/fiscal-report?year=2026` que retorne el informe completo en JSON.

**Entregable:** El backend calcula automáticamente la amortización, clasifica ingresos y gastos, aplica reducciones y devuelve el rendimiento neto reducido para un ejercicio fiscal concreto. Testeado exhaustivamente con `pytest`.

### Feature F-13: Informe Fiscal y Generación de PDF (Borrador AEAT)

**Alcance:** Crear el puerto `FiscalReportRenderer` y su adaptador `AEATPdfRenderer` (usando una librería como `reportlab` o `weasyprint`). Incluir el diccionario de mapeo de categorías semánticas a casillas AEAT. Añadir un botón "Descargar Borrador Fiscal" en la vista de detalle del frontend.

**Entregable:** El usuario puede descargar un PDF con el borrador fiscal de una propiedad para un año, listo para trasladar a Renta Web.

---

## 8. Resumen de Dependencias entre Features

| Feature | Depende de | Capa Principal |
|---|---|---|
| **F-08** Multi-tenancy | F-07 ✅ | Backend (Dominio + Persistencia + API) |
| **F-09** Datos Fiscales Propiedad | F-08 | Backend + Frontend |
| **F-10** Contratos Arrendamiento | F-08 | Backend + Frontend |
| **F-11** Clasificación Fiscal | F-08 | Backend + Frontend |
| **F-12** Motor de Cálculo | F-09 + F-10 + F-11 | Backend (Dominio puro) |
| **F-13** Informe PDF | F-12 | Backend (Adaptador) + Frontend |

---

## 📚 El Rincón del Estudiante: Fiscalidad de Alquileres para Desarrolladores

### ¿Qué es un "Rendimiento del Capital Inmobiliario"?

Cuando alquilas un piso, Hacienda (AEAT) considera que estás obteniendo una renta. A esa renta le llama "Rendimiento del Capital Inmobiliario". Es como tu "beneficio" por ser propietario, pero calculado según unas reglas muy específicas que no siempre coinciden con tu beneficio real contable.

### La Amortización: el gasto que no pagas pero puedes deducir

Imagina que compraste un piso por 200.000€. Hacienda asume que ese edificio se "desgasta" con el uso y el tiempo (como un coche). Ese desgaste teórico se llama **amortización**, y te permite deducir un gasto que en realidad no estás pagando a nadie.

```
Precio compra: 200.000€
├── Suelo:         80.000€  ← El suelo NO se desgasta. No se amortiza.
└── Construcción: 120.000€  ← El edificio SÍ se desgasta. 3% anual.

Amortización anual = 120.000 × 3% = 3.600€/año de gasto deducible "gratis"
```

¿Por qué el suelo no? Porque un terreno no se deteriora. En 100 años seguirá siendo un terreno. Pero un edificio sí necesita mantenimiento, envejece y eventualmente necesita ser reconstruido.

### Reparación vs. Mejora: ¿por qué importa?

| Acción | ¿Qué es? | Tratamiento fiscal |
|---|---|---|
| Pintar las paredes | **Reparación** — devuelves algo a su estado original | Deduces los 800€ enteros este año |
| Instalar aire acondicionado | **Mejora** — añades algo que no existía | NO deduces los 2.000€ este año. Se suman al valor del piso y se amortizan al 3% (60€/año durante 33 años) |

Es la diferencia entre "arreglar lo roto" y "hacer el piso mejor de lo que era".

### ¿Por qué separamos el Dominio de las Casillas de la AEAT?

La AEAT publica cada año un formulario para la declaración de la renta. Cada campo tiene un número de "casilla" (ej: casilla 0104 = "Ingresos íntegros"). Pero estos números **cambian** de un año a otro cuando la AEAT reorganiza el formulario.

Si nuestro código de dominio dijera `TaxCategory.CASILLA_0104`, tendríamos que modificar la lógica de negocio cada vez que la AEAT cambie un número. Con nuestro enfoque:

```
ESTABLE (dominio):    TaxCategory.INSURANCE    → "Es un seguro. Siempre será un seguro."
VARIABLE (PDF):       casilla_map["INSURANCE"]  → "0114" (en 2025), "0120" (en 2027, quizá)
```

Es exactamente el mismo principio de la Arquitectura Hexagonal que ya conoces: el dominio no sabe ni le importa cómo se presenta la información al exterior. Si la AEAT cambia sus casillas, solo actualizas un diccionario en el adaptador de PDF. El dominio, los tests y los cálculos permanecen intactos.
