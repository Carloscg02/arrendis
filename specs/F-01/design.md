# 🧩 F-01: Domain Base — Diseño Técnico

> **Feature:** F-01 — Property Catalog and Listing (+ Domain Foundation)  
> **Versión:** 1.1  
> **Fecha:** 2026-07-08  
> **Última revisión:** 2026-07-08 — Alineado con architecture.md v1.1 (FastAPI, React+TS, pytest)  
> **Referencia:** [architecture.md](file:///home/carlos/gestion-alquiler/docs/architecture.md)

---

## 1. Lenguaje Ubicuo (Ubiquitous Language)

El Lenguaje Ubicuo es el vocabulario compartido entre desarrolladores y el negocio. Cada término tiene un significado preciso e invariable en todo el proyecto.

| Término (EN)     | Traducción        | Definición                                                                                         |
|-------------------|-------------------|----------------------------------------------------------------------------------------------------|
| **Property**      | Propiedad/Inmueble | Un bien inmueble que se alquila para obtener ingresos. Tiene dirección, nombre descriptivo y tipo. |
| **Tenant**        | Inquilino          | Persona que alquila una Property. Tiene nombre y datos de contacto.                                |
| **Income**        | Ingreso            | Dinero que entra asociado a una Property (alquiler mensual, depósito, etc.).                       |
| **Expense**       | Gasto              | Dinero que sale asociado a una Property (reparación, impuesto, seguro, comunidad, etc.).           |
| **Net Profit**    | Beneficio Neto     | Resultado de `Σ Incomes − Σ Expenses` para una Property en un periodo de tiempo.                  |
| **Money**         | Dinero             | Cantidad monetaria con precisión decimal. Siempre en EUR para este MVP.                            |
| **Address**       | Dirección          | Dirección postal completa de una Property.                                                         |
| **PropertyType**  | Tipo de Propiedad  | Clasificación: APARTMENT, HOUSE, COMMERCIAL, GARAGE, LAND.                                        |
| **PropertyStatus**| Estado             | Estado actual: AVAILABLE, RENTED, MAINTENANCE.                                                     |
| **IncomeCategory**| Categoría Ingreso  | Tipo de ingreso: RENT, DEPOSIT, OTHER.                                                             |
| **ExpenseCategory**| Categoría Gasto   | Tipo de gasto: REPAIR, TAX, INSURANCE, COMMUNITY_FEE, MORTGAGE, UTILITY, OTHER.                   |

---

## 2. Value Objects

### 2.1 Definición de Value Objects

| Value Object | Campos                                          | Reglas de Validación                                           |
|--------------|-------------------------------------------------|----------------------------------------------------------------|
| `Money`      | `amount: Decimal`, `currency: str`              | `amount >= 0`, `currency` es exactamente `"EUR"` (MVP)        |
| `Address`    | `street: str`, `city: str`, `postal_code: str`, `country: str` | Ningún campo puede estar vacío. `country` por defecto `"ES"`. |

### 2.2 Especificación Detallada

#### `Money`

```
Money(amount=Decimal("750.00"), currency="EUR")
```

- **Inmutable**: una vez creado, no se puede modificar. Usar `@dataclass(frozen=True)`.
- **Igualdad por valor**: `Money(100, "EUR") == Money(100, "EUR")` → `True`
- **Operaciones**: debe soportar `__add__` y `__sub__` entre Money del mismo currency.
- **Validación**: lanzar `ValueError` si `amount < 0` (salvo resultados internos con `_allow_negative=True`).
- **Representación**: `__repr__` → `"Money(750.00 EUR)"`

#### `Address`

```
Address(street="Calle Mayor 15, 3ºB", city="Madrid", postal_code="28013", country="ES")
```

- **Inmutable**: una vez creado, no se puede modificar. Usar `@dataclass(frozen=True)`.
- **Igualdad por valor**: dos direcciones con los mismos campos son iguales.
- **Validación**: lanzar `ValueError` si cualquier campo está vacío o solo contiene espacios.
- **Representación**: `__repr__` → `"Address(Calle Mayor 15, 3ºB, Madrid, 28013, ES)"`

---

## 3. Enumeraciones (Enums)

```python
# Estos son los valores exactos que deben usarse:

class PropertyType(Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    GARAGE = "garage"
    LAND = "land"

class PropertyStatus(Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"

class IncomeCategory(Enum):
    RENT = "rent"
    DEPOSIT = "deposit"
    OTHER = "other"

class ExpenseCategory(Enum):
    REPAIR = "repair"
    TAX = "tax"
    INSURANCE = "insurance"
    COMMUNITY_FEE = "community_fee"
    MORTGAGE = "mortgage"
    UTILITY = "utility"
    OTHER = "other"
```

---

## 4. Entidades

### 4.1 Definición de Entidades

| Entidad     | Identidad          | Campos                                                                                         |
|-------------|--------------------|-------------------------------------------------------------------------------------------------|
| `Property`  | `id: str` (UUID4)  | `name: str`, `address: Address`, `property_type: PropertyType`, `status: PropertyStatus`       |
| `Tenant`    | `id: str` (UUID4)  | `first_name: str`, `last_name: str`, `email: str`, `phone: str`                               |
| `Income`    | `id: str` (UUID4)  | `property_id: str`, `amount: Money`, `date: date`, `category: IncomeCategory`, `description: str` |
| `Expense`   | `id: str` (UUID4)  | `property_id: str`, `amount: Money`, `date: date`, `category: ExpenseCategory`, `description: str` |

### 4.2 Especificación Detallada

#### `Property`

```
Property(
    id="550e8400-e29b-41d4-a716-446655440000",
    name="Piso Centro Madrid",
    address=Address("Calle Mayor 15, 3ºB", "Madrid", "28013", "ES"),
    property_type=PropertyType.APARTMENT,
    status=PropertyStatus.AVAILABLE
)
```

- **Identidad**: se identifica por su `id` (UUID4). Dos Properties con el mismo `id` son la misma entidad, aunque tengan nombres diferentes.
- **Validación**:
  - `name` no puede estar vacío.
  - `id` debe ser un UUID4 válido (se genera automáticamente si no se proporciona).
  - `status` por defecto es `AVAILABLE`.
- **Igualdad**: por `id`, no por valores de campos. Implementar `__eq__` y `__hash__` basados únicamente en `id`.

#### `Tenant`

```
Tenant(
    id="...",
    first_name="María",
    last_name="García López",
    email="maria@email.com",
    phone="+34 612 345 678"
)
```

- **Validación**:
  - `first_name` y `last_name` no pueden estar vacíos.
  - `email` debe contener `@` (validación básica).
  - `phone` puede estar vacío (campo opcional).

#### `Income`

```
Income(
    id="...",
    property_id="550e8400-...",
    amount=Money(Decimal("750.00"), "EUR"),
    date=date(2026, 7, 1),
    category=IncomeCategory.RENT,
    description="Alquiler julio 2026"
)
```

- **Validación**:
  - `property_id` no puede estar vacío (referencia a una Property existente).
  - `amount` debe ser un `Money` válido (>= 0).
  - `description` puede estar vacía.
  - `date` es obligatorio.

#### `Expense`

```
Expense(
    id="...",
    property_id="550e8400-...",
    amount=Money(Decimal("120.00"), "EUR"),
    date=date(2026, 7, 5),
    category=ExpenseCategory.REPAIR,
    description="Reparación caldera"
)
```

- **Validación**: mismas reglas que `Income`, usando `ExpenseCategory`.

---

## 5. Puertos (Interfaces)

Estos son los contratos abstractos que el dominio define. Los adaptadores los implementan.

### 5.1 Puertos de Salida (Repositorios)

```python
class PropertyRepository(ABC):
    """Puerto de salida para persistir y recuperar Properties."""

    @abstractmethod
    def save(self, property: Property) -> None: ...

    @abstractmethod
    def find_by_id(self, property_id: str) -> Property | None: ...

    @abstractmethod
    def find_all(self) -> list[Property]: ...

    @abstractmethod
    def delete(self, property_id: str) -> None: ...


class IncomeRepository(ABC):
    """Puerto de salida para persistir y recuperar Incomes."""

    @abstractmethod
    def save(self, income: Income) -> None: ...

    @abstractmethod
    def find_by_property_id(self, property_id: str) -> list[Income]: ...

    @abstractmethod
    def delete(self, income_id: str) -> None: ...


class ExpenseRepository(ABC):
    """Puerto de salida para persistir y recuperar Expenses."""

    @abstractmethod
    def save(self, expense: Expense) -> None: ...

    @abstractmethod
    def find_by_property_id(self, property_id: str) -> list[Expense]: ...

    @abstractmethod
    def delete(self, expense_id: str) -> None: ...
```

### 5.2 Nota sobre TenantRepository

> [!NOTE]
> En el MVP, `Tenant` es una entidad definida pero su repositorio no es crítico para las funcionalidades F-01 a F-04. Se incluye en el dominio para completar el modelo, pero su repositorio se implementará cuando añadamos la funcionalidad de vincular inquilinos a propiedades.

---

## 6. Servicios de Dominio

### `ProfitCalculator`

```python
class ProfitCalculator:
    """Calcula el beneficio neto de una propiedad."""

    @staticmethod
    def calculate_net_profit(incomes: list[Income], expenses: list[Expense]) -> Money:
        """
        Retorna: Σ income.amount - Σ expense.amount

        - Si no hay ingresos ni gastos, retorna Money(0, "EUR").
        - El resultado PUEDE ser negativo (se pierde dinero).
          En ese caso, Money se crea con allow_negative=True internamente.
        """
        ...
```

> [!IMPORTANT]
> `ProfitCalculator` es un Servicio de Dominio, no una Entidad. No tiene identidad ni estado. Es lógica pura que opera sobre entidades. La diferencia: una Entidad **es** algo (una propiedad, un ingreso). Un Servicio **hace** algo (calcular beneficio).

> [!NOTE]
> **Nota de testing:** Los tests de este proyecto usan **pytest** (no `unittest`). Esto significa: funciones `test_*` sueltas (no clases), asserts directos (`assert x == y`), y fixtures con `@pytest.fixture`. Consulta [architecture.md](file:///home/carlos/gestion-alquiler/docs/architecture.md) §6 para todas las convenciones.

---

## 7. Casos de Uso (Application Layer)

Los casos de uso orquestan las operaciones. Reciben datos simples, crean entidades, y llaman a los puertos.

| Caso de Uso              | Entrada                                           | Salida           | Descripción                                    |
|--------------------------|----------------------------------------------------|------------------|-------------------------------------------------|
| `CreateProperty`         | name, street, city, postal_code, country, type     | `Property`       | Crea y persiste una nueva Property              |
| `ListProperties`         | *(ninguna)*                                        | `list[Property]` | Devuelve todas las Properties                   |
| `RecordIncome`           | property_id, amount, date, category, description   | `Income`         | Registra un ingreso vinculado a una Property    |
| `RecordExpense`          | property_id, amount, date, category, description   | `Expense`        | Registra un gasto vinculado a una Property      |
| `GetPropertyProfitReport`| property_id                                        | `Money`          | Calcula el Net Profit de una Property           |

Cada caso de uso:
1. Recibe **datos primitivos** (strings, numbers), NO entidades.
2. Crea las entidades y value objects internamente.
3. Llama a los repositorios (puertos) para persistir o consultar.
4. Retorna la entidad creada o el resultado.

---

## 📚 El Rincón del Estudiante: Domain-Driven Design

### ¿Qué es DDD?

Domain-Driven Design es una filosofía de diseño de software creada por Eric Evans (2003). Su idea central es: **el código debe ser un espejo del negocio**. Si el negocio habla de "propiedades", "inquilinos" e "ingresos", tu código tiene clases llamadas `Property`, `Tenant` e `Income`.

### Entidad vs. Value Object: La pregunta del millón

La diferencia fundamental es: **¿tiene identidad propia?**

#### 🏢 Entidad: "Soy único, aunque me cambien los datos"

```
Persona(id="ABC123", nombre="Carlos", edad=25)
         ↓ Un año después...
Persona(id="ABC123", nombre="Carlos", edad=26)

→ Sigue siendo la MISMA persona. La identidad (id) no cambió.
→ Aunque la edad cambió, es el mismo Carlos.
```

**Regla mental**: si puedes decir "este es **el mismo** X aunque sus datos cambien", es una Entidad.

Ejemplos en nuestro proyecto:
- `Property`: "El piso de la Calle Mayor" sigue siendo **el mismo piso** aunque le cambies el nombre.
- `Tenant`: "María García" sigue siendo **la misma inquilina** aunque cambie de email.
- `Income`: "El pago de julio" es **un pago específico** que pasó en una fecha concreta.

#### 💰 Value Object: "Soy mis datos. Si mis datos cambian, soy otro"

```
Money(amount=100, currency="EUR")
Money(amount=100, currency="EUR")

→ Son IGUALES. No hay "este billete de 100€" vs "aquel billete de 100€".
→ 100€ son 100€, punto.
```

**Regla mental**: si puedes decir "dos X con los mismos datos son **intercambiables**", es un Value Object.

Ejemplos en nuestro proyecto:
- `Money(750, "EUR")`: 750 euros son 750 euros. No importa "cuáles" 750 euros.
- `Address("Calle Mayor 15", "Madrid", "28013", "ES")`: La dirección es la dirección. No tiene "identidad propia".

#### La tabla comparativa

| Aspecto              | Entidad                     | Value Object                  |
|----------------------|-----------------------------|-------------------------------|
| **¿Tiene ID?**       | ✅ Sí (UUID, auto-increment) | ❌ No                          |
| **Igualdad**          | Por ID                      | Por valores de todos los campos |
| **¿Mutable?**        | Sí (puede cambiar estado)   | ❌ Inmutable                   |
| **¿Se puede reemplazar?** | No (es único)          | Sí (cualquier otro con mismos valores sirve) |
| **Ejemplo cotidiano** | Tu DNI (eres tú, único)     | Un billete de 20€ (cualquiera vale igual) |

### ¿Qué es un Puerto?

Un **Puerto** es una interfaz (en Python: una clase abstracta con `ABC`). Es un **contrato** que dice "necesito que alguien haga esto" sin decir cómo.

Piénsalo como un enchufe eléctrico en la pared. El enchufe define la forma (2 agujeros redondos en España), pero no sabe si el cable va a una central nuclear o a unos paneles solares.

```python
# PUERTO: define QUÉ necesito
class PropertyRepository(ABC):
    @abstractmethod
    def save(self, property: Property) -> None:
        ...
    # No dice nada sobre SQL, archivos, APIs, etc.
```

### ¿Qué es un Adaptador?

Un **Adaptador** es una implementación concreta de un Puerto. Es el "electrodoméstico" que se conecta al "enchufe".

```python
# ADAPTADOR: define CÓMO lo hago
class SQLitePropertyRepository(PropertyRepository):
    def save(self, property: Property) -> None:
        self.cursor.execute(
            "INSERT INTO properties (id, name, ...) VALUES (?, ?, ...)",
            (property.id, property.name, ...)
        )
```

### ¿Por qué complicarse con esto?

**Escenario real**: llevas 6 meses con SQLite y tu app crece. Ahora necesitas PostgreSQL.

- **Sin puertos/adaptadores**: Reescribes TODA la app. Las queries SQL están mezcladas con la lógica de negocio. Es un desastre.
- **Con puertos/adaptadores**: Creas `PostgreSQLPropertyRepository`, lo "enchufas", y listo. El dominio y los casos de uso no se enteran del cambio.

### ¿Qué es el Lenguaje Ubicuo?

Es el vocabulario que **todo el equipo** comparte: desarrolladores, diseñadores, el dueño del producto, y el propio código.

Si el equipo dice "propiedad", el código dice `Property`. No `RealEstate`, no `House`, no `Building`. **Property**, siempre. Esto elimina la ambigüedad y hace que el código sea legible como un documento de negocio.
