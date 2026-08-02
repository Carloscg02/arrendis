# F-10 — Contratos de Arrendamiento (Lease Contracts)

> **Épica:** E-01 Fiscalidad  
> **Dependencias:** F-09 (Datos Fiscales de Propiedad)  
> **Estado:** Pendiente de aprobación

---

## 1. Objetivo

Permitir al usuario registrar los contratos de alquiler de cada propiedad, indicando fechas,
tipo de arrendamiento (vivienda habitual, temporal, turístico, comercial) y datos básicos
del inquilino. Esta información es **imprescindible** para el motor fiscal (F-12) que necesita:

- **Días de alquiler efectivo** en el año fiscal (para prorratear gastos).
- **Tipo de contrato** (para aplicar o no la reducción del 60% por vivienda habitual).
- **NIF del inquilino** (para cumplimentar la declaración modelo D-100).

---

## 2. Lenguaje Ubicuo (Nuevos Términos)

| Término | Definición |
|---|---|
| **LeaseContract** | Entidad que representa un contrato de arrendamiento entre el propietario y un inquilino para una propiedad concreta, durante un periodo de tiempo. |
| **LeaseType** | Clasificación fiscal del contrato: `VIVIENDA_HABITUAL` (larga duración, uso residencial — apto para reducción fiscal), `TEMPORAL` (uso estacional o temporal), `TURISTICO` (alquiler vacacional), `COMERCIAL` (uso no residencial). |
| **Días de Ocupación** | Número de días dentro de un año fiscal en que la propiedad estuvo efectivamente alquilada según sus contratos. Se usa para prorratear gastos deducibles. |
| **NIF del Inquilino** | Número de Identificación Fiscal del arrendatario. Obligatorio para la declaración de la renta del propietario. |

---

## 3. Modelo de Dominio

### 3.1 Nuevo Enum — `LeaseType`

Se añade en `backend/domain/entities.py` junto a los demás enums:

```python
class LeaseType(Enum):
    """Clasificación fiscal del tipo de arrendamiento."""
    VIVIENDA_HABITUAL = "vivienda_habitual"   # Larga duración, vivienda — reducción 60%
    TEMPORAL = "temporal"                       # Estacional / temporal
    TURISTICO = "turistico"                     # Alquiler vacacional
    COMERCIAL = "comercial"                     # Local comercial / oficina
```

### 3.2 Nueva Entidad — `LeaseContract`

```python
@dataclass
class LeaseContract:
    """Contrato de arrendamiento de un inmueble.

    Identidad basada en el campo `id` (UUID4).
    Un contrato vincula una propiedad con un inquilino durante un periodo.
    """
    property_id: str
    tenant_name: str
    tenant_nif: str
    start_date: date
    monthly_rent: Money
    lease_type: LeaseType
    end_date: date | None = None  # None = contrato indefinido / en vigor
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.property_id or not self.property_id.strip():
            raise ValueError("El property_id no puede estar vacío.")
        if not self.tenant_name or not self.tenant_name.strip():
            raise ValueError("El nombre del inquilino no puede estar vacío.")
        if not self.tenant_nif or not self.tenant_nif.strip():
            raise ValueError("El NIF del inquilino no puede estar vacío.")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError(
                f"La fecha de fin ({self.end_date}) no puede ser anterior "
                f"a la fecha de inicio ({self.start_date})."
            )

    @property
    def is_active(self) -> bool:
        """Un contrato está activo si no tiene fecha de fin o ésta es futura."""
        if self.end_date is None:
            return True
        return self.end_date >= date.today()

    def rented_days_in_year(self, fiscal_year: int) -> int:
        """Calcula los días de alquiler efectivo dentro de un año fiscal.

        Este método es clave para el motor fiscal (F-12): permite prorratear
        los gastos deducibles en proporción a los días realmente alquilados.

        Args:
            fiscal_year: Año fiscal (ej. 2025).

        Returns:
            Número de días de alquiler dentro de ese año (0–366).
        """
        year_start = date(fiscal_year, 1, 1)
        year_end = date(fiscal_year, 12, 31)

        effective_start = max(self.start_date, year_start)
        effective_end = min(self.end_date or year_end, year_end)

        if effective_start > effective_end:
            return 0
        return (effective_end - effective_start).days + 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LeaseContract):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

#### Decisiones de diseño:

- **Sin entidad `Tenant` separada (por ahora).** La entidad `Tenant` ya existe en el dominio pero
  no tiene repositorio, casos de uso ni API. Para F-10 almacenamos `tenant_name` y `tenant_nif`
  directamente en el contrato. Si en el futuro se necesita un CRUD de inquilinos completo
  (con histórico, múltiples contratos, etc.), se puede extraer sin romper nada.
- **Sin campo `status` explícito.** El estado se deriva de las fechas (`is_active`).
  Si el inquilino se va antes de tiempo, simplemente se actualiza `end_date` al día de salida.
- **`rented_days_in_year` es lógica de dominio pura** — no depende de nada externo.
  El motor fiscal (F-12) llamará a este método para cada contrato de la propiedad.

---

## 4. Puerto (Interfaz de Repositorio)

### 4.1 Nuevo Puerto — `LeaseContractRepository`

Se añade en `backend/domain/ports.py`:

```python
class LeaseContractRepository(ABC):
    """Puerto de salida para persistir y recuperar LeaseContracts."""

    @abstractmethod
    def save(self, contract: LeaseContract) -> None:
        """Guarda o actualiza un contrato."""
        ...

    @abstractmethod
    def find_by_id(self, contract_id: str) -> LeaseContract | None:
        """Busca un contrato por su id. Retorna None si no existe."""
        ...

    @abstractmethod
    def find_by_property_id(self, property_id: str) -> list[LeaseContract]:
        """Retorna todos los contratos de una propiedad (ordenados por start_date desc)."""
        ...

    @abstractmethod
    def delete(self, contract_id: str) -> None:
        """Elimina un contrato por su id."""
        ...
```

---

## 5. Casos de Uso

### 5.1 `CreateLeaseContractUseCase`

```
Entrada: user_id, property_id, tenant_name, tenant_nif, start_date,
         end_date?, monthly_rent (Decimal), lease_type (str)
Proceso:
  1. Verificar que la propiedad existe y pertenece al user_id.
  2. Crear Money(monthly_rent, "EUR").
  3. Crear LeaseContract con LeaseType(lease_type).
  4. Persistir via LeaseContractRepository.save().
Salida:  LeaseContract creado.
Error:   ValueError si la propiedad no existe o no pertenece al usuario.
```

### 5.2 `ListLeaseContractsUseCase`

```
Entrada: user_id, property_id
Proceso:
  1. Verificar que la propiedad existe y pertenece al user_id.
  2. Buscar contratos via LeaseContractRepository.find_by_property_id().
Salida:  list[LeaseContract]
Error:   ValueError si la propiedad no existe o no pertenece al usuario.
```

### 5.3 `UpdateLeaseContractUseCase`

```
Entrada: user_id, contract_id, tenant_name?, tenant_nif?, start_date?,
         end_date?, monthly_rent?, lease_type?
Proceso:
  1. Buscar contrato por id.
  2. Verificar que la propiedad del contrato pertenece al user_id.
  3. Actualizar los campos proporcionados (merge con valores actuales).
  4. Re-validar la entidad (post_init).
  5. Persistir via save() (INSERT OR REPLACE).
Salida:  LeaseContract actualizado.
Error:   ValueError si el contrato no existe o la propiedad no pertenece al usuario.
```

### 5.4 `DeleteLeaseContractUseCase`

```
Entrada: user_id, contract_id
Proceso:
  1. Buscar contrato por id.
  2. Verificar que la propiedad del contrato pertenece al user_id.
  3. Eliminar via LeaseContractRepository.delete().
Salida:  None
Error:   ValueError si el contrato no existe o la propiedad no pertenece al usuario.
```

---

## 6. Adaptador SQLite

### 6.1 Nueva Tabla — `lease_contracts`

```sql
CREATE TABLE IF NOT EXISTS lease_contracts (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    tenant_name TEXT NOT NULL,
    tenant_nif TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT DEFAULT NULL,
    monthly_rent_amount TEXT NOT NULL,
    monthly_rent_currency TEXT NOT NULL DEFAULT 'EUR',
    lease_type TEXT NOT NULL,
    FOREIGN KEY (property_id) REFERENCES properties(id)
)
```

> **Nota:** No hay migración `ALTER TABLE` esta vez — es una tabla nueva con `CREATE TABLE IF NOT EXISTS`.

### 6.2 `SQLiteLeaseContractRepository`

Implementa `LeaseContractRepository`. Métodos:

- **`save(contract)`**: `INSERT OR REPLACE` con serialización de `Money.amount` a TEXT.
- **`find_by_id(contract_id)`**: SELECT + `_row_to_entity`.
- **`find_by_property_id(property_id)`**: SELECT con `ORDER BY start_date DESC` + lista de `_row_to_entity`.
- **`delete(contract_id)`**: DELETE.
- **`_row_to_entity(row)`**: Reconstruye `LeaseContract` con `Money(Decimal(...))` y `LeaseType(...)`.

### 6.3 Actualizar `delete` de `SQLitePropertyRepository`

Al eliminar una propiedad, se deben eliminar también sus contratos asociados:

```diff
 def delete(self, property_id: str) -> None:
     # ...imagen...
     self._conn.execute("DELETE FROM incomes WHERE property_id = ?", (property_id,))
     self._conn.execute("DELETE FROM expenses WHERE property_id = ?", (property_id,))
+    self._conn.execute("DELETE FROM lease_contracts WHERE property_id = ?", (property_id,))
     self._conn.execute("DELETE FROM properties WHERE id = ?", (property_id,))
     self._conn.commit()
```

### 6.4 Registrar en `SQLiteConnection._create_tables`

Añadir la creación de la tabla `lease_contracts` en el método `_create_tables`.

---

## 7. API REST

### 7.1 Nuevos Schemas (Pydantic)

```python
class LeaseContractCreate(BaseModel):
    tenant_name: str
    tenant_nif: str
    start_date: date
    end_date: date | None = None
    monthly_rent: float   # Se convierte a Decimal en el Use Case
    lease_type: str        # Valor del enum LeaseType

class LeaseContractUpdate(BaseModel):
    tenant_name: str | None = None
    tenant_nif: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    monthly_rent: float | None = None
    lease_type: str | None = None

class LeaseContractResponse(BaseModel):
    id: str
    property_id: str
    tenant_name: str
    tenant_nif: str
    start_date: date
    end_date: date | None
    monthly_rent: str      # Decimal serializado como string
    currency: str
    lease_type: str
    is_active: bool
```

### 7.2 Nuevos Endpoints

| Método | Ruta | Descripción | Request Body | Response |
|---|---|---|---|---|
| `POST` | `/api/properties/{property_id}/contracts` | Crear contrato | `LeaseContractCreate` | `LeaseContractResponse` (201) |
| `GET` | `/api/properties/{property_id}/contracts` | Listar contratos de una propiedad | — | `list[LeaseContractResponse]` (200) |
| `PUT` | `/api/contracts/{contract_id}` | Actualizar un contrato | `LeaseContractUpdate` | `LeaseContractResponse` (200) |
| `DELETE` | `/api/contracts/{contract_id}` | Eliminar un contrato | — | 204 No Content |

> **Decisión de rutas:** Crear y listar contratos van anidados bajo `/properties/{id}/contracts`
> porque siempre necesitan el contexto de la propiedad. Actualizar y eliminar van en
> `/contracts/{id}` porque el contrato ya tiene su `property_id` internamente.

### 7.3 Nuevo Router

Se crea un archivo nuevo `backend/api/routes/contracts.py` con su propio `APIRouter`,
que se registra en `backend/api/main.py`.

---

## 8. Frontend

### 8.1 Tipos TypeScript

```typescript
export interface LeaseContract {
  id: string;
  property_id: string;
  tenant_name: string;
  tenant_nif: string;
  start_date: string;
  end_date: string | null;
  monthly_rent: string;
  currency: string;
  lease_type: string;
  is_active: boolean;
}

export interface LeaseContractInput {
  tenant_name: string;
  tenant_nif: string;
  start_date: string;
  end_date?: string | null;
  monthly_rent: number;
  lease_type: string;
}
```

### 8.2 Servicio API

Añadir en `frontend/src/services/api.ts`:

```typescript
export const getLeaseContracts = (propertyId: string): Promise<LeaseContract[]> => { ... }
export const createLeaseContract = (propertyId: string, data: LeaseContractInput): Promise<LeaseContract> => { ... }
export const updateLeaseContract = (contractId: string, data: Partial<LeaseContractInput>): Promise<LeaseContract> => { ... }
export const deleteLeaseContract = (contractId: string): Promise<void> => { ... }
```

### 8.3 Nuevo Componente — `ContractSection`

Componente que se integra en `PropertyDetail` como una tercera pestaña "📋 Contratos":

- Lista de contratos con badge de estado (🟢 Activo / 🔴 Finalizado).
- Indicador visual del tipo de contrato (con colores diferenciados).
- Botón "+ Nuevo Contrato" que abre un modal con formulario.
- Cada contrato tiene acciones: Editar / Eliminar.

### 8.4 Nuevo Componente — `ContractForm`

Formulario modal para crear/editar contratos:

- Campos: Nombre del inquilino, NIF, Fecha inicio, Fecha fin (opcional), Renta mensual, Tipo de contrato (select).
- Validación en cliente: nombre y NIF obligatorios, fecha inicio obligatoria, renta > 0.

### 8.5 Integración en `PropertyDetail`

Actualizar el sistema de tabs existente para incluir la pestaña de contratos:

```diff
- const [activeTab, setActiveTab] = useState<"dashboard" | "fiscal">("dashboard");
+ const [activeTab, setActiveTab] = useState<"dashboard" | "fiscal" | "contracts">("dashboard");
```

Añadir el botón de tab y el contenido condicional.

---

## 9. Tests

### 9.1 Tests Unitarios

| ID | Archivo | Descripción |
|---|---|---|
| T-U-10-01 | `test_entities.py` | LeaseContract se crea correctamente con todos los campos |
| T-U-10-02 | `test_entities.py` | LeaseContract rechaza property_id vacío |
| T-U-10-03 | `test_entities.py` | LeaseContract rechaza tenant_name vacío |
| T-U-10-04 | `test_entities.py` | LeaseContract rechaza tenant_nif vacío |
| T-U-10-05 | `test_entities.py` | LeaseContract rechaza end_date anterior a start_date |
| T-U-10-06 | `test_entities.py` | `is_active` retorna True si end_date es None |
| T-U-10-07 | `test_entities.py` | `is_active` retorna True si end_date es futura |
| T-U-10-08 | `test_entities.py` | `is_active` retorna False si end_date es pasada |
| T-U-10-09 | `test_entities.py` | `rented_days_in_year` con contrato completo en el año |
| T-U-10-10 | `test_entities.py` | `rented_days_in_year` con contrato parcial (empieza mitad de año) |
| T-U-10-11 | `test_entities.py` | `rented_days_in_year` con contrato fuera del año fiscal → 0 |
| T-U-10-12 | `test_entities.py` | `rented_days_in_year` con contrato indefinido (end_date=None) |
| T-U-10-13 | `test_lease_use_cases.py` | CreateLeaseContractUseCase crea contrato correctamente |
| T-U-10-14 | `test_lease_use_cases.py` | CreateLeaseContractUseCase rechaza propiedad inexistente |
| T-U-10-15 | `test_lease_use_cases.py` | CreateLeaseContractUseCase rechaza propiedad de otro usuario |
| T-U-10-16 | `test_lease_use_cases.py` | ListLeaseContractsUseCase retorna contratos de la propiedad |
| T-U-10-17 | `test_lease_use_cases.py` | UpdateLeaseContractUseCase actualiza campos parciales |
| T-U-10-18 | `test_lease_use_cases.py` | DeleteLeaseContractUseCase elimina contrato existente |
| T-U-10-19 | `test_lease_use_cases.py` | DeleteLeaseContractUseCase rechaza contrato de otro usuario |

### 9.2 Tests de Integración

| ID | Archivo | Descripción |
|---|---|---|
| T-I-10-01 | `test_sqlite_adapter.py` | SQLiteLeaseContractRepository save + find_by_id |
| T-I-10-02 | `test_sqlite_adapter.py` | SQLiteLeaseContractRepository find_by_property_id (orden DESC) |
| T-I-10-03 | `test_sqlite_adapter.py` | SQLiteLeaseContractRepository delete |
| T-I-10-04 | `test_sqlite_adapter.py` | Eliminar propiedad cascada también elimina sus contratos |
| T-I-10-05 | `test_contracts_api.py` | POST crea contrato y retorna 201 |
| T-I-10-06 | `test_contracts_api.py` | GET lista contratos de una propiedad |
| T-I-10-07 | `test_contracts_api.py` | PUT actualiza contrato existente |
| T-I-10-08 | `test_contracts_api.py` | DELETE elimina contrato y retorna 204 |
| T-I-10-09 | `test_contracts_api.py` | POST rechaza propiedad de otro usuario (404) |
| T-I-10-10 | `test_contracts_api.py` | Contrato response incluye is_active calculado |

---

## 10. Archivos Afectados (Resumen)

| Acción | Archivo |
|---|---|
| ✏️ Modificar | `backend/domain/entities.py` — nuevo enum `LeaseType` + nueva entidad `LeaseContract` |
| ✏️ Modificar | `backend/domain/ports.py` — nuevo puerto `LeaseContractRepository` |
| ✏️ Modificar | `backend/application/use_cases.py` — 4 nuevos casos de uso |
| ✏️ Modificar | `backend/adapters/sqlite_adapter.py` — nueva tabla + `SQLiteLeaseContractRepository` + cascada en delete |
| ✏️ Modificar | `backend/api/schemas.py` — 3 nuevos schemas |
| 🆕 Crear | `backend/api/routes/contracts.py` — nuevo router con 4 endpoints |
| ✏️ Modificar | `backend/api/main.py` — registrar nuevo router |
| ✏️ Modificar | `frontend/src/types/index.ts` — nuevos tipos |
| ✏️ Modificar | `frontend/src/services/api.ts` — nuevos métodos |
| 🆕 Crear | `frontend/src/components/ContractForm.tsx` — formulario de contrato |
| 🆕 Crear | `frontend/src/components/ContractSection.tsx` — sección lista + acciones |
| ✏️ Modificar | `frontend/src/pages/PropertyDetail.tsx` — nueva pestaña "Contratos" |
| ✏️ Modificar | `frontend/src/index.css` — estilos para contratos |
| ✏️ Modificar | `tests/unit/backend/domain/test_entities.py` — tests T-U-10-01 a T-U-10-12 |
| 🆕 Crear | `tests/unit/backend/application/test_lease_use_cases.py` — tests T-U-10-13 a T-U-10-19 |
| ✏️ Modificar | `tests/integration/backend/adapters/test_sqlite_adapter.py` — tests T-I-10-01 a T-I-10-04 |
| 🆕 Crear | `tests/integration/backend/api/test_contracts_api.py` — tests T-I-10-05 a T-I-10-10 |

---

## 11. 📚 Rincón del Estudiante

### ¿Por qué almacenar el inquilino directamente en el contrato y no usar la entidad Tenant existente?

En el código ya existe una entidad `Tenant` con `first_name`, `last_name`, `email`, `phone`.
Sin embargo, esta entidad **no tiene repositorio, ni casos de uso, ni API**. Está "huérfana".

Para F-10, lo que el motor fiscal necesita del inquilino son solo dos datos: su **nombre** y su **NIF**.
Crear un CRUD completo de inquilinos (con su propio repositorio, endpoints, formulario frontend)
solo para almacenar dos campos sería **sobreingeniería** en esta etapa.

> **Principio YAGNI (You Aren't Gonna Need It):** No construyas funcionalidad que no necesitas
> ahora mismo. Si en el futuro se requiere un historial de inquilinos, se puede refactorizar
> fácilmente extrayendo los datos del contrato a una entidad `Tenant` propia.

### ¿Por qué `is_active` es una propiedad derivada y no un campo almacenado?

Almacenar un campo `status` crea un riesgo: si el usuario no actualiza el estado manualmente
cuando un contrato vence, los datos quedan inconsistentes. Al derivar el estado de las fechas:

- **Siempre es correcto:** Si `end_date` ya pasó, el contrato está inactivo. Punto.
- **Menos mantenimiento:** No necesitamos un job nocturno que marque contratos como "expirados".
- **Si el inquilino se va antes:** Simplemente actualizamos `end_date` al día de salida.

### ¿Por qué `rented_days_in_year` vive en la entidad y no en un servicio?

Porque es una operación que solo depende de los datos internos del contrato (`start_date`,
`end_date`) y de un parámetro externo simple (el año fiscal). No necesita acceder a repositorios
ni a servicios externos. Según DDD, este tipo de cálculo "puro" pertenece a la entidad.

El motor fiscal (F-12) simplemente iterará los contratos de una propiedad y sumará los días:

```python
total_rented_days = sum(
    contract.rented_days_in_year(2025) 
    for contract in contracts
)
```

### ¿Por qué se crea un router separado (`contracts.py`) en vez de añadir a `properties.py`?

El archivo `properties.py` ya gestiona propiedades, imágenes y datos fiscales.
Añadir contratos ahí violaría el **Principio de Responsabilidad Única (SRP)**. Un router
por recurso REST mantiene el código organizado y facilita que diferentes desarrolladores
trabajen en paralelo sin conflictos.
