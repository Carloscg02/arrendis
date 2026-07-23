# 🧩 F-02: API REST Implementation — Diseño Técnico

> **Feature:** F-02 — API Implementation (FastAPI como Adaptador de Entrada)  
> **Versión:** 1.0-DRAFT  
> **Fecha:** 2026-07-08  
> **Referencia:** [architecture.md](file:///home/carlos/rental-handler/docs/architecture.md)  
> **Dependencia:** [F-01 design.md](file:///home/carlos/rental-handler/specs/F-01/design.md) (Domain Foundation — ✅ done)

---

## 1. Objetivo de la Feature

F-02 implementa el **Adaptador de Entrada HTTP** usando FastAPI. Su única responsabilidad es traducir peticiones HTTP a llamadas de Casos de Uso (definidos en F-01) y formatear las respuestas.

```
  Petición HTTP → [FastAPI Router] → [Caso de Uso] → [Dominio] → [Puerto] → [SQLite Adapter]
                   ^^^^^^^^^^^^^^
                   Esto es lo que construimos en F-02.
```

### Qué NO hace esta feature
- **No añade lógica de negocio**: las reglas de validación viven en el Dominio (F-01).
- **No modifica el dominio**: no se toca `backend/domain/` ni `backend/application/`.
- **No incluye frontend**: eso será una feature posterior.

---

## 2. Lenguaje Ubicuo — Extensiones para F-02

Estos términos nuevos aparecen exclusivamente en la capa de API:

| Término (EN)        | Traducción         | Definición                                                                                     |
|----------------------|--------------------|------------------------------------------------------------------------------------------------|
| **Schema**           | Esquema            | Modelo Pydantic que define la forma de un request o response HTTP. Es un DTO (Data Transfer Object), NO una entidad de dominio. |
| **Router**           | Enrutador          | Módulo FastAPI que agrupa endpoints de un mismo recurso (e.g., todos los endpoints de Properties). |
| **Dependency**       | Dependencia        | Función que FastAPI inyecta en los endpoints. Se usa para proveer repositorios y casos de uso. |
| **Lifespan**         | Ciclo de vida      | Bloque `async` que gestiona el setup (crear conexión BD) y teardown (cerrar conexión) de la app FastAPI. |

---

## 3. Schemas (Pydantic DTOs)

Los Schemas son la **frontera de traducción** entre el mundo HTTP (JSON) y el dominio. Nunca exponemos entidades de dominio directamente en la API.

### 3.1 Property Schemas

```python
class AddressSchema(BaseModel):
    """Representación JSON de una dirección."""
    street: str
    city: str
    postal_code: str
    country: str = "ES"

class PropertyCreate(BaseModel):
    """Request body para crear una propiedad."""
    name: str
    address: AddressSchema
    property_type: str  # Valor del enum: "apartment", "house", etc.

class PropertyResponse(BaseModel):
    """Response body con los datos de una propiedad."""
    id: str
    name: str
    address: AddressSchema
    property_type: str
    status: str
```

### 3.2 Income Schemas

```python
class IncomeCreate(BaseModel):
    """Request body para registrar un ingreso."""
    property_id: str
    amount: Decimal
    date: date
    category: str        # Valor del enum: "rent", "deposit", "other"
    description: str = ""

class IncomeResponse(BaseModel):
    """Response body con los datos de un ingreso."""
    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str
```

### 3.3 Expense Schemas

```python
class ExpenseCreate(BaseModel):
    """Request body para registrar un gasto."""
    property_id: str
    amount: Decimal
    date: date
    category: str        # Valor del enum: "repair", "tax", etc.
    description: str = ""

class ExpenseResponse(BaseModel):
    """Response body con los datos de un gasto."""
    id: str
    property_id: str
    amount: Decimal
    currency: str
    date: date
    category: str
    description: str
```

### 3.4 Profit Report Schema

```python
class ProfitReportResponse(BaseModel):
    """Response body con el beneficio neto de una propiedad."""
    property_id: str
    net_profit: Decimal
    currency: str
```

> [!IMPORTANT]
> **¿Por qué no exponemos las entidades de dominio directamente?** Porque el dominio es nuestro y puede cambiar sin avisar a los clientes HTTP. Los Schemas actúan como **contrato estable** con el exterior. Si mañana añadimos un campo interno a `Property`, los clientes de la API no se rompen porque `PropertyResponse` sigue igual.

---

## 4. Endpoints (API Contract)

Todos los endpoints usan el prefijo `/api`.

### 4.1 Properties

| Método | Ruta                            | Request Body      | Response              | Status | Descripción                   |
|--------|---------------------------------|--------------------|-----------------------|--------|-------------------------------|
| POST   | `/api/properties`               | `PropertyCreate`   | `PropertyResponse`    | 201    | Crear una propiedad           |
| GET    | `/api/properties`               | —                  | `list[PropertyResponse]` | 200 | Listar todas las propiedades  |
| GET    | `/api/properties/{property_id}` | —                  | `PropertyResponse`    | 200    | Obtener una propiedad por ID  |
| DELETE | `/api/properties/{property_id}` | —                  | `{"detail": "..."}` | 200    | Eliminar una propiedad        |

### 4.2 Incomes

| Método | Ruta                                          | Request Body    | Response            | Status | Descripción                    |
|--------|-----------------------------------------------|-----------------|---------------------|--------|--------------------------------|
| POST   | `/api/incomes`                                | `IncomeCreate`  | `IncomeResponse`    | 201    | Registrar un ingreso           |
| GET    | `/api/properties/{property_id}/incomes`       | —               | `list[IncomeResponse]` | 200 | Listar ingresos de una propiedad |

### 4.3 Expenses

| Método | Ruta                                          | Request Body     | Response              | Status | Descripción                    |
|--------|-----------------------------------------------|------------------|-----------------------|--------|--------------------------------|
| POST   | `/api/expenses`                               | `ExpenseCreate`  | `ExpenseResponse`     | 201    | Registrar un gasto             |
| GET    | `/api/properties/{property_id}/expenses`      | —                | `list[ExpenseResponse]` | 200 | Listar gastos de una propiedad |

### 4.4 Profit Report

| Método | Ruta                                          | Request Body | Response                | Status | Descripción                      |
|--------|-----------------------------------------------|--------------|-------------------------|--------|----------------------------------|
| GET    | `/api/properties/{property_id}/profit`        | —            | `ProfitReportResponse`  | 200    | Beneficio neto de una propiedad  |

### 4.5 Manejo de Errores

| Escenario                        | HTTP Status | Response Body                                          |
|----------------------------------|-------------|--------------------------------------------------------|
| Propiedad no encontrada          | 404         | `{"detail": "Property '{id}' not found"}`              |
| Datos de request inválidos       | 422         | Automático de Pydantic (FastAPI lo genera por defecto) |
| Valor de enum no válido          | 400         | `{"detail": "Invalid value for field: ..."}`           |

---

## 5. Inyección de Dependencias

FastAPI usa su sistema de `Depends()` para inyectar los repositorios y casos de uso en cada endpoint. Esto mantiene la separación de responsabilidades y facilita el testing.

### 5.1 Patrón de Inyección

```python
# dependencies.py — Funciones que proveen los repositorios concretos

from fastapi import Request

def get_db(request: Request) -> SQLiteConnection:
    """Retorna la conexión a BD almacenada en app.state durante el lifespan."""
    return request.app.state.db

def get_property_repo(request: Request) -> SQLitePropertyRepository:
    return SQLitePropertyRepository(get_db(request))

def get_income_repo(request: Request) -> SQLiteIncomeRepository:
    return SQLiteIncomeRepository(get_db(request))

def get_expense_repo(request: Request) -> SQLiteExpenseRepository:
    return SQLiteExpenseRepository(get_db(request))
```

### 5.2 Uso en un Endpoint

```python
@router.post("", response_model=PropertyResponse, status_code=201)
def create_property(
    body: PropertyCreate,
    property_repo: PropertyRepository = Depends(get_property_repo),
):
    use_case = CreatePropertyUseCase(property_repo)
    prop = use_case.execute(
        name=body.name,
        street=body.address.street,
        city=body.address.city,
        postal_code=body.address.postal_code,
        country=body.address.country,
        property_type=body.property_type,
    )
    return _entity_to_response(prop)
```

> [!NOTE]
> **¿Por qué no inyectamos el Use Case directamente?** Porque los Use Cases son objetos simples que reciben repositorios en su constructor. Es más limpio instanciarlos en el endpoint (1 línea) que crear una dependency factory para cada uno. Los repositorios sí se inyectan porque dependen de `app.state.db`.

---

## 6. Lifespan (Ciclo de Vida de la App)

El lifespan de FastAPI gestiona la conexión a la base de datos:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # SETUP: crear conexión y guardarla en app.state
    db = SQLiteConnection("data/rental.db")
    app.state.db = db
    yield
    # TEARDOWN: cerrar conexión
    db.close()
```

---

## 7. CORS (Cross-Origin Resource Sharing)

Como el frontend React correrá en un puerto diferente (e.g., 5173), necesitamos habilitar CORS:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # En producción, restringir al dominio del frontend
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. Estructura de Archivos

```
backend/api/                     # 🌐 ADAPTADOR DE ENTRADA — FastAPI (F-02)
├── __init__.py
├── main.py                      # App FastAPI, lifespan, CORS, include_router
├── schemas.py                   # Pydantic models (Request/Response DTOs)
├── dependencies.py              # Funciones de inyección de dependencias
└── routes/                      # Routers organizados por recurso
    ├── __init__.py
    ├── properties.py            # Endpoints CRUD de Properties + Profit Report
    ├── incomes.py               # Endpoints de Incomes
    └── expenses.py              # Endpoints de Expenses

tests/backend/api/               # ✅ TESTS de la capa API (patrón espejo)
├── test_properties_api.py       # Tests de endpoints Properties
├── test_incomes_api.py          # Tests de endpoints Incomes
└── test_expenses_api.py         # Tests de endpoints Expenses
```

**Total: 8 archivos de producción + 3 archivos de test = 11 archivos nuevos.**

---

## 9. Especificación de Tests

Los tests de API usan `httpx.AsyncClient` o `TestClient` de Starlette con una base de datos SQLite `:memory:`, inyectada a través de `app.dependency_overrides`.

### 9.1 test_properties_api.py (7 tests)

| ID     | Test                                   | Verifica                                           |
|--------|----------------------------------------|----------------------------------------------------|
| AP-01  | `test_create_property`                 | POST 201, devuelve PropertyResponse con UUID        |
| AP-02  | `test_create_property_invalid_type`    | POST 400 con property_type inválido                |
| AP-03  | `test_create_property_empty_name`      | POST 400/422 con nombre vacío                      |
| AP-04  | `test_list_properties_empty`           | GET 200, lista vacía `[]`                           |
| AP-05  | `test_list_properties_after_create`    | POST + GET, lista contiene la propiedad creada     |
| AP-06  | `test_get_property_by_id`              | POST + GET /{id}, devuelve datos correctos         |
| AP-07  | `test_get_property_not_found`          | GET /{id_inexistente} → 404                        |

### 9.2 test_incomes_api.py (4 tests)

| ID     | Test                                   | Verifica                                           |
|--------|----------------------------------------|----------------------------------------------------|
| AI-01  | `test_record_income`                   | POST 201, devuelve IncomeResponse                  |
| AI-02  | `test_record_income_invalid_property`  | POST con property_id inexistente → 404             |
| AI-03  | `test_list_incomes_by_property`        | POST income + GET /{property_id}/incomes → lista   |
| AI-04  | `test_get_profit_report`               | POST income + POST expense + GET /profit → cálculo |

### 9.3 test_expenses_api.py (3 tests)

| ID     | Test                                   | Verifica                                           |
|--------|----------------------------------------|----------------------------------------------------|
| AE-01  | `test_record_expense`                  | POST 201, devuelve ExpenseResponse                 |
| AE-02  | `test_record_expense_invalid_property` | POST con property_id inexistente → 404             |
| AE-03  | `test_list_expenses_by_property`       | POST expense + GET /{property_id}/expenses → lista |

**Total: 14 tests de la capa API.**

---

## 📚 El Rincón del Estudiante: ¿Qué es un DTO y por qué separar Schemas de Entidades?

### El Problema

Imagina que tu API devuelve directamente la entidad `Property` de tu dominio:

```python
@router.get("/api/properties")
def list_properties():
    return property_repo.find_all()  # ← Devuelve entidades de dominio directamente 😱
```

Esto parece cómodo, pero tiene un problema grave: **el dominio y la API quedan acoplados**. Si mañana añades un campo interno a `Property` (e.g., `_internal_score`), se filtra automáticamente al JSON que reciben tus clientes.

### La Solución: DTOs (Data Transfer Objects)

Un DTO es un "sobre" que contiene exactamente los datos que quieres enviar/recibir por la red. En FastAPI, los DTOs se implementan como Pydantic `BaseModel` (Schemas).

```
   Entidad (Dominio)          Schema (API)
   ─────────────────          ────────────
   Property                   PropertyResponse
   ├── id: str                ├── id: str
   ├── name: str              ├── name: str
   ├── address: Address  →→→  ├── address: AddressSchema
   ├── property_type: Enum    ├── property_type: str     ← Se aplana el enum
   └── status: Enum           └── status: str            ← Se aplana el enum
```

### ¿Por qué es importante?

| Sin DTOs | Con DTOs |
|----------|----------|
| El dominio cambia → la API se rompe | El dominio cambia → la API se mantiene estable |
| Campos internos se filtran al exterior | Solo expones lo que decides |
| Los clientes dependen de tu implementación interna | Los clientes dependen del contrato de la API |

### La Regla de Oro

> **El Dominio no sabe que la API existe. La API no expone las tripas del Dominio.**

Cada capa habla su propio idioma:
- El **Dominio** habla en entidades, value objects y enums.
- La **API** habla en JSON, strings y schemas Pydantic.
- La **traducción** ocurre en los endpoints (entity → schema, schema → primitives → use case).

### ¿Qué pasa en `backend/api/main.py` y cómo escucha la app las peticiones externas?

En `main.py` instanciamos el objeto principal de la API: `app = FastAPI()`. Sin embargo, en Python puro, esta línea solo crea una estructura de datos en memoria (un mapa de rutas y middleware). Por sí sola, **esta aplicación de Python no sabe escuchar la red**. 

Para que la aplicación pueda recibir peticiones del exterior, necesitamos una pieza de infraestructura clave: un **servidor de aplicaciones ASGI**.

#### 1. Uvicorn: El Servidor de Red (ASGI)
En Python, el estándar para levantar servidores web asíncronos y modernos es **ASGI** (Asynchronous Server Gateway Interface). El programa que usamos para ello es **Uvicorn**.

Cuando ejecutamos en la terminal:
```bash
uvicorn backend.api.main:app --reload
```
Ocurre lo siguiente:
1. **Importación**: Uvicorn arranca como un proceso del sistema operativo, busca el módulo `backend.api.main` y carga el objeto `app`.
2. **Apertura de Sockets (Escucha)**: Uvicorn solicita al sistema operativo abrir un "puerto de red" (por defecto el puerto `8000` en tu IP local `127.0.0.1`). A partir de ese momento, Uvicorn es el que "escucha" los paquetes TCP crudos que entran por el puerto 8000.
3. **Recepción y Conversión**: Cuando un cliente (como el navegador o el futuro Frontend) envía datos, Uvicorn lee la petición HTTP en formato texto crudo, la parsea y la traduce al estándar ASGI (un diccionario estructurado de Python).

#### 2. FastAPI: El Enrutador y Traductor Interno
Una vez traducida la petición por Uvicorn:
1. **Enrutamiento**: Uvicorn le pasa la petición en formato ASGI a nuestra instancia `app` de FastAPI. FastAPI busca en su mapa de rutas si tiene un endpoint que coincida (por ejemplo, `POST /api/properties`).
2. **Procesamiento**: Si lo encuentra, FastAPI valida que los datos de entrada cuadren con el Schema (DTO), inyecta las dependencias necesarias de base de datos (`Depends(get_property_repo)`) y ejecuta la función de Python que programamos en las rutas.
3. **Respuesta**: La función genera la respuesta, FastAPI la valida contra el Schema de salida, la convierte en un JSON plano y se la devuelve a Uvicorn.
4. **Respuesta a la Red**: Uvicorn toma ese JSON, le añade las cabeceras HTTP de respuesta correspondientes, lo convierte en texto y lo envía de vuelta a través del socket al exterior.

#### Analogía del Mundo Real
- **Uvicorn** es el **portero de un edificio**. Está en la entrada principal (puerto 8000), recibe a los carteros (peticiones HTTP), y traduce las instrucciones al idioma del edificio.
- **FastAPI** es el **recepcionista interno**. Recibe el paquete que le entregó el portero, valida los papeles (Schemas), busca en la agenda interna a qué oficina (endpoint/Caso de Uso) debe enviarlo y te entrega la respuesta de vuelta.

---

> [!IMPORTANT]
> **Este documento está en estado DRAFT.** Requiere aprobación humana antes de proceder a la creación del plan de implementación. Ningún código fuente debe generarse hasta recibir la orden explícita.
