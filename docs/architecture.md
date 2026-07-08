# 🏗️ Architecture Document — Gestión de Alquileres

> **Versión:** 1.1  
> **Autor:** Spec Author (SDD Pipeline)  
> **Estado:** Aprobado con revisiones  
> **Fecha:** 2026-07-08  
> **Última revisión:** 2026-07-08 — FastAPI, React+TS, pytest

---

## 1. Visión General del Proyecto

**Gestión de Alquileres** es una plataforma para administrar propiedades en alquiler. Permite llevar un catálogo de inmuebles, registrar ingresos y gastos por propiedad, y calcular la rentabilidad neta de cada una.

### Funcionalidades Principales (MVP)

| ID   | Funcionalidad               | Descripción                                                        |
|------|-----------------------------|--------------------------------------------------------------------|
| F-01 | Property Catalog & Listing  | CRUD de propiedades con datos básicos (dirección, tipo, estado)    |
| F-02 | Income Tracking             | Registrar pagos de alquiler vinculados a una propiedad             |
| F-03 | Expense Tracking            | Registrar gastos (reparaciones, impuestos, seguros) por propiedad  |
| F-04 | Net Profit Calculation      | Calcular beneficio neto: `Σ Ingresos − Σ Gastos` por propiedad    |

---

## 2. Stack Tecnológico

```
┌─────────────────────────────────────────────┐
│              FRONTEND                       │
│        TypeScript + React                   │
│   SPA que consume la API REST del backend   │
└──────────────────┬──────────────────────────┘
                   │ HTTP / JSON (REST API)
┌──────────────────▼──────────────────────────┐
│              BACKEND                        │
│      Python + FastAPI (único framework      │
│      permitido para la capa de API)         │
│      Dominio: Python puro (stdlib)          │
└──────────────────┬──────────────────────────┘
                   │ sqlite3 (stdlib)
┌──────────────────▼──────────────────────────┐
│             BASE DE DATOS                   │
│              SQLite 3                       │
│     Archivo local: data/rental.db           │
└─────────────────────────────────────────────┘
```

### ¿Por qué este stack?

| Decisión                 | Razón                                                                                                  |
|--------------------------|--------------------------------------------------------------------------------------------------------|
| **FastAPI**              | Único framework permitido. Moderno, rápido, con tipado nativo y docs auto-generadas (Swagger/OpenAPI). Es un **Adaptador de Entrada** en nuestra Arquitectura Hexagonal — la lógica de negocio sigue siendo Python puro. |
| **Dominio en Python puro** | Sin "magia" de frameworks en el núcleo. Cada línea de lógica de negocio es tuya y la entiendes.       |
| **React + TypeScript**   | El estándar de la industria para SPAs. TypeScript añade seguridad de tipos que previene errores en el frontend. |
| **SQLite**               | Viene incluido en Python (`import sqlite3`). Cero instalación. Un solo archivo `.db`. Perfecto para aprender SQL sin montar un servidor de base de datos. |
| **pytest**               | El framework de testing más usado en Python. Más conciso y potente que `unittest`. Fixtures, parametrize y asserts legibles. |

---

## 3. Arquitectura Hexagonal (Puertos y Adaptadores)

### 3.1 El Diagrama

```
                    ┌─────────────────────────────────┐
                    │         ADAPTADORES DE           │
                    │          ENTRADA (IN)             │
                    │  ┌───────────┐  ┌─────────────┐  │
                    │  │  FastAPI  │  │    CLI       │  │
                    │  │  (REST)   │  │  (futuro)    │  │
                    │  └─────┬─────┘  └──────┬───────┘  │
                    │        │               │          │
                    │  ┌─────▼───────────────▼───────┐  │
                    │  │    PUERTOS DE ENTRADA (IN)   │  │
                    │  │   (Casos de Uso / Contratos) │  │
                    │  └─────────────┬────────────────┘  │
                    │               │                    │
                    │  ┌────────────▼─────────────────┐  │
                    │  │     NÚCLEO DE DOMINIO        │  │
                    │  │                              │  │
                    │  │  Entidades: Property, Tenant │  │
                    │  │  Value Objects: Money,       │  │
                    │  │    Address                    │  │
                    │  │  Servicios: ProfitCalculator  │  │
                    │  │                              │  │
                    │  │  ⚡ CERO dependencias         │  │
                    │  │     externas aquí             │  │
                    │  └────────────┬─────────────────┘  │
                    │               │                    │
                    │  ┌────────────▼─────────────────┐  │
                    │  │   PUERTOS DE SALIDA (OUT)    │  │
                    │  │   (Interfaces / Contratos)   │  │
                    │  └─────────────┬────────────────┘  │
                    │        ┌───────┴────────┐         │
                    │  ┌─────▼─────┐  ┌───────▼──────┐  │
                    │  │  SQLite   │  │ PostgreSQL   │  │
                    │  │ Adapter   │  │  Adapter     │  │
                    │  │ (actual)  │  │  (futuro)    │  │
                    │  └───────────┘  └──────────────┘  │
                    │       ADAPTADORES DE SALIDA (OUT)  │
                    └─────────────────────────────────────┘
```

### 3.2 Estructura de Carpetas

```
backend/
├── domain/                  # 🧠 NÚCLEO — La lógica de negocio pura
│   ├── __init__.py
│   ├── entities.py          # Property, Tenant, Income, Expense
│   ├── value_objects.py     # Money, Address
│   ├── services.py          # ProfitCalculator
│   └── ports.py             # Interfaces (ABCs) que definen contratos
│
├── adapters/                # 🔌 ADAPTADORES DE SALIDA — Implementaciones concretas
│   ├── __init__.py
│   └── sqlite_adapter.py   # Implementación de los puertos con SQLite
│
├── api/                     # 🌐 ADAPTADOR DE ENTRADA — FastAPI
│   ├── __init__.py
│   ├── main.py              # App FastAPI, lifespan, CORS
│   ├── routes/              # Routers organizados por recurso
│   │   ├── __init__.py
│   │   ├── properties.py    # Endpoints CRUD de Properties
│   │   ├── incomes.py       # Endpoints de Incomes
│   │   └── expenses.py      # Endpoints de Expenses
│   └── schemas.py           # Pydantic models (request/response DTOs)
│
├── application/             # 🎯 CASOS DE USO — Orquestación
│   ├── __init__.py
│   └── use_cases.py         # CreateProperty, RecordIncome, etc.
│
└── __init__.py

frontend/                    # 🖥️ FRONTEND — React + TypeScript
└── (se inicializará con Vite + React + TS)

tests/                       # ✅ TESTS — pytest
├── conftest.py              # Fixtures compartidas (fake repos, db :memory:)
├── test_entities.py         # Tests del dominio
├── test_value_objects.py    # Tests de Value Objects
├── test_services.py         # Tests de servicios de dominio
├── test_use_cases.py        # Tests de casos de uso
└── test_sqlite_adapter.py   # Tests de integración con SQLite

data/
└── (rental.db se crea aquí en runtime)
```

### 3.3 La Regla de Dependencia

```
Las dependencias SIEMPRE apuntan hacia adentro:

  Adaptadores ──➤ Puertos ──➤ Dominio

  NUNCA al revés:

  Dominio ✘──➤ Adaptadores   ← PROHIBIDO
  Dominio ✘──➤ sqlite3       ← PROHIBIDO
  Dominio ✘──➤ import fastapi ← PROHIBIDO
```

El dominio **nunca importa nada externo**. Ni `sqlite3`, ni `fastapi`, ni ninguna librería. Solo Python puro (`dataclasses`, `abc`, `decimal`, `uuid`, `datetime`).

FastAPI vive **fuera** del dominio, en `backend/api/`. Es un Adaptador de Entrada que traduce peticiones HTTP a llamadas de Casos de Uso.

---

## 4. Flujo de una Operación: "Crear una Propiedad"

```
1. [Adaptador IN]  →  Recibe datos (desde CLI, HTTP, o test)
2. [Caso de Uso]   →  CreatePropertyUseCase.execute(name, address, ...)
3. [Dominio]       →  Crea la entidad Property con validaciones
4. [Puerto OUT]    →  Llama a PropertyRepository.save(property)
5. [Adaptador OUT] →  SQLitePropertyRepository escribe en rental.db
6. [Retorno]       →  Se devuelve la Property creada
```

---

## 5. ¿Cómo nos protege esto para el futuro?

### Escenario: Migrar de SQLite a PostgreSQL

```diff
  # Solo tocas UN archivo:
- backend/adapters/sqlite_adapter.py
+ backend/adapters/postgresql_adapter.py

  # El dominio NO cambia ni una línea.
  # Los casos de uso NO cambian ni una línea.
  # Los tests del dominio SIGUEN pasando igual.
```

| Lo que cambias                         | Lo que NO cambias                |
|----------------------------------------|----------------------------------|
| `sqlite_adapter.py` → `pg_adapter.py` | `entities.py` (0 cambios)        |
| Cadena de conexión                     | `value_objects.py` (0 cambios)   |
| Queries SQL específicas de PostgreSQL  | `services.py` (0 cambios)        |
|                                        | `use_cases.py` (0 cambios)       |
|                                        | `test_entities.py` (0 cambios)   |

**El 80% de tu código se queda exactamente igual.** Eso es el poder de la Arquitectura Hexagonal.

---

## 6. Convenciones del Proyecto

| Aspecto              | Convención                                                  |
|----------------------|-------------------------------------------------------------|
| Lenguaje del código  | Inglés (nombres de clases, variables, funciones)            |
| Lenguaje docs        | Español (documentación, comentarios explicativos)           |
| Formato de IDs       | UUID v4 (generados con `uuid.uuid4()`)                      |
| Formato monetario    | `Decimal` con 2 decimales, siempre en céntimos de EUR       |
| Fechas               | `datetime.date` para fechas, `datetime.datetime` para timestamps |
| Tests                | `pytest` — tests unitarios y de integración                 |
| API Framework        | `FastAPI` — único framework permitido para endpoints HTTP   |
| Frontend             | `React` + `TypeScript` (inicializado con Vite)              |
| Type hints           | Obligatorios en todas las funciones públicas                |

---

## 📚 El Rincón del Estudiante: Arquitectura Hexagonal

### ¿Qué problema resuelve?

Imagina que construyes una casa y los cables eléctricos están soldados directamente a cada electrodoméstico. Si quieres cambiar la lavadora, tienes que romper la pared. **Eso** es una arquitectura acoplada.

La Arquitectura Hexagonal dice: **pon enchufes (puertos) en la pared**. Cualquier electrodoméstico (adaptador) que tenga el enchufe correcto puede conectarse.

### Los tres conceptos clave

#### 🧠 1. El Dominio (El Núcleo)

Es la **lógica de negocio pura**. Las reglas que serían verdad aunque no existieran los ordenadores:
- "Una propiedad tiene una dirección"
- "El beneficio neto es ingresos menos gastos"
- "Un alquiler no puede tener precio negativo"

El dominio **no sabe** si los datos vienen de una web, de un terminal, o de un archivo Excel. **No le importa.**

#### 🔌 2. Los Puertos (Los Enchufes)

Son **interfaces** (contratos abstractos). Definen **qué** se necesita, pero no **cómo** se hace:

```python
# Esto es un Puerto (una interfaz abstracta)
class PropertyRepository(ABC):
    @abstractmethod
    def save(self, property: Property) -> None:
        """Guarda una propiedad. No dice DÓNDE ni CÓMO."""
        ...

    @abstractmethod
    def find_by_id(self, id: str) -> Property | None:
        """Busca una propiedad. No dice en qué base de datos."""
        ...
```

El dominio habla con los puertos. **Nunca** con las implementaciones concretas.

#### 🔧 3. Los Adaptadores (Los Electrodomésticos)

Son las **implementaciones concretas** que se "enchufan" a los puertos:

```python
# Esto es un Adaptador — implementa el puerto con SQLite
class SQLitePropertyRepository(PropertyRepository):
    def save(self, property: Property) -> None:
        # AQUÍ sí usamos sqlite3
        self.cursor.execute("INSERT INTO properties ...")

    def find_by_id(self, id: str) -> Property | None:
        self.cursor.execute("SELECT * FROM properties WHERE id = ?", (id,))
        ...
```

### ¿Por qué "Hexagonal"?

El nombre viene porque el diagrama original de Alistair Cockburn (2005) dibujaba el dominio como un hexágono, con los puertos en cada cara. No tiene nada que ver con el número 6 — es solo una forma visual de representar que el dominio tiene **múltiples caras** por donde se puede conectar con el mundo exterior.

### La Analogía Final

```
🏠 Tu Casa (Dominio)
    │
    ├── 🔌 Enchufe de cocina (Puerto) ← 🍳 Horno eléctrico (Adaptador SQLite)
    │                                  ← 🍳 Horno de gas (Adaptador PostgreSQL)
    │
    ├── 🔌 Enchufe del salón (Puerto)  ← 📺 TV Samsung (Adaptador CLI)
    │                                  ← 📺 TV LG (Adaptador HTTP API)
    │
    └── La casa NO cambia cuando cambias el horno o la TV.
        Solo necesitas que el enchufe sea compatible.
```

---

## 📚 El Rincón del Estudiante: ¿Por qué FastAPI encaja en la Arquitectura Hexagonal?

Un error común es pensar que usar un framework rompe la arquitectura limpia. **No es así**, si lo colocas en el lugar correcto.

FastAPI es un **Adaptador de Entrada**. Su trabajo es:
1. Recibir una petición HTTP (`POST /api/properties`)
2. Validar los datos con Pydantic (schemas)
3. Llamar al Caso de Uso correspondiente (`CreatePropertyUseCase.execute(...)`)
4. Devolver la respuesta HTTP

```
  Petición HTTP → [FastAPI Router] → [Caso de Uso] → [Dominio] → [Puerto] → [SQLite Adapter]
                   ^^^^^^^^^^^^
                   Solo vive aquí.
                   El dominio no sabe que FastAPI existe.
```

Si mañana quisieras cambiar FastAPI por Flask, solo reescribirías `backend/api/`. El dominio, los casos de uso y los adaptadores de salida no cambiarían ni una línea. **Exactamente el mismo principio que con la base de datos, pero para la entrada.**

---

> [!IMPORTANT]
> **Documento revisado v1.1.** Aprobado con los cambios solicitados: FastAPI, React+TypeScript, pytest.
