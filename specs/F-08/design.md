# 🏗️ Especificación Técnica — F-08: User Property Ownership and Data Isolation (Multi-tenancy)

> **Feature:** F-08  
> **Estado:** Draft (Paso 1 del pipeline SDD)  
> **Autor:** Tech Lead (Antigravity)  

---

## 1. Objetivo y Alcance
Actualmente, la plataforma gestiona las propiedades de forma global. Cualquier persona que llame a la API puede ver y editar todas las propiedades registradas. 
El objetivo de esta feature es implementar **Multi-tenancy de tipo "aislamiento lógico por filas" (Row-level isolation)**. Cada propiedad pertenecerá a un único usuario (propietario) y el sistema garantizará que los usuarios solo puedan acceder y operar sobre sus propios datos.

**Alcance:**
- Modificar la entidad `Property` para incluir la propiedad del usuario.
- Proteger todos los endpoints de la API (`/api/properties`, `/api/incomes`, `/api/expenses`, `/api/profit`) para exigir un usuario autenticado.
- Asegurar los Casos de Uso para que validen la autoría antes de realizar operaciones de lectura o escritura.

---

## 2. Lenguaje Ubicuo (Ubiquitous Language)

| Término | Definición |
|---|---|
| **Multi-tenancy** | Arquitectura donde una única instancia de la aplicación sirve a múltiples "inquilinos" (usuarios/propietarios), manteniendo sus datos aislados de forma segura. |
| **Row-level isolation** | Técnica de multi-tenancy donde todos los usuarios comparten las mismas tablas de base de datos, pero cada registro (fila) tiene una columna `user_id` que identifica a su dueño. |
| **Owner (Propietario)** | El `User` que crea y administra una `Property`. En nuestro dominio actual, el owner se identifica mediante su `user_id`. |
| **Unauthorized Access (403)** | Situación donde un usuario autenticado intenta acceder a un recurso (ej. un `Property`) que pertenece a otro `user_id`. |

---

## 3. Diseño de Dominio

### 3.1. Modificación de Entidades (`backend/domain/entities.py`)

La entidad `Property` es nuestro Agregado Raíz. Al asignarle un dueño, todos sus elementos dependientes (Incomes, Expenses, Tenants) quedarán indirectamente protegidos bajo su paraguas.

```python
@dataclass
class Property:
    name: str
    address: Address
    property_type: PropertyType
    user_id: str                        # 🆕 NUEVO CAMPO REQUERIDO: Identificador del propietario
    status: PropertyStatus = PropertyStatus.AVAILABLE
    image_filename: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la propiedad (name) no puede estar vacío.")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("El user_id del propietario no puede estar vacío.")
```

*Nota sobre las entidades dependientes (`Income`, `Expense`):* Siguiendo los principios DDD, no es necesario añadir `user_id` a cada ingreso y gasto. Su seguridad se garantiza validando que el `property_id` pertenece al usuario antes de añadir o consultar registros.

---

## 4. Contratos y Casos de Uso (Capa de Aplicación)

Los puertos (interfaces de repositorios) y los Casos de Uso deben actualizarse para exigir el `user_id`.

### 4.1. Puertos (Repositories)
- `PropertyRepository.list_properties(user_id: str) -> list[Property]`
- `PropertyRepository.get_property(property_id: str) -> Property | None` *(Nota: la validación de propiedad se hará en el Caso de Uso)*

### 4.2. Casos de Uso
Todos los casos de uso relacionados con el catálogo y la contabilidad requerirán ahora el `user_id` de quien realiza la petición.

1. **`CreatePropertyUseCase`**: Recibe `user_id` y lo asigna a la nueva entidad.
2. **`ListPropertiesUseCase`**: Recibe `user_id` y llama a `repo.list_properties(user_id)`.
3. **Casos de Uso de Modificación (`RecordIncomeUseCase`, `RecordExpenseUseCase`, `GetProfitReportUseCase`)**:
   - Pasos internos:
     1. Buscar la propiedad por `property_id`.
     2. Si no existe, lanzar `PropertyNotFoundError`.
     3. 🆕 **NUEVO:** Si `property.user_id != request_user_id`, lanzar una excepción de dominio (ej. `PropertyNotFoundError` para no revelar la existencia de la propiedad, o `UnauthorizedError`).
     4. Proceder con el registro del ingreso/gasto.

---

## 5. Diseño de API (Adaptadores de Entrada)

Todos los endpoints en `backend/api/routes/` que interactúan con las propiedades dejarán de ser públicos.

**Cambio Global en Routers:**
Se inyectará la dependencia de seguridad de FastAPI a nivel de función de ruta:
`current_user: User = Depends(get_current_user)`

Ejemplo de endpoint protegido (`backend/api/routes/properties.py`):
```python
@router.get("/", response_model=list[PropertyResponse])
def get_properties(
    current_user: User = Depends(get_current_user),
    use_case: ListPropertiesUseCase = Depends(get_list_properties_use_case)
):
    # Ahora pasamos el ID del usuario al caso de uso
    return use_case.execute(user_id=current_user.id)
```

---

## 6. Persistencia (Adaptadores de Salida)

**`backend/adapters/sqlite_adapter.py`**:
- Modificar el método de inicialización de tablas (`CREATE TABLE IF NOT EXISTS properties`) para añadir la columna `user_id TEXT NOT NULL`.
- Actualizar los métodos `save` y `list_properties` para incluir el filtro y guardado de `user_id`.
- *Estrategia de Migración:* Dado que estamos en desarrollo temprano (y usando SQLite local), podemos dropear la tabla `properties` actual o añadir la columna con un valor por defecto si SQLite lo requiere, pero al ser desarrollo, un reinicio de la DB `rental.db` es aceptable.

---

## 7. Especificación de Tests

Se deberán crear/actualizar los siguientes tests en `pytest`:

**Unitarios (Dominio/Aplicación):**
- `test_property_creation_without_user_id_raises_error`: Verifica que no se puede instanciar una `Property` huérfana.
- `test_record_income_unauthorized_user`: Verifica que el caso de uso levanta una excepción si un usuario intenta añadir ingresos a la propiedad de otro.

**Integración (API / SQLite):**
- `test_list_properties_isolated`: Crear propiedades de "User A" y "User B". Hacer GET `/api/properties` con el token de "User A" y verificar que la lista **solo** contiene las suyas.
- `test_create_property_unauthenticated`: Verifica que hacer un POST sin token devuelve `401 Unauthorized`.
- `test_record_expense_for_others_property`: Un POST a `/api/expenses` con un `property_id` ajeno debe devolver `404 Not Found` (para no confirmar existencia) o `403 Forbidden`.

---

## 8. 📚 El Rincón del Estudiante

### ¿Qué es el "Multi-tenancy" (Multitenencia)?

Imagina un edificio de oficinas (tu aplicación). 
- **Single-tenant:** Cada empresa (usuario) tiene su propio edificio físico independiente. Tienen su propio servidor, su propia base de datos separada. Máxima seguridad, pero carísimo de mantener.
- **Multi-tenant:** Varias empresas comparten el mismo edificio (el mismo servidor y la misma base de datos). 

En nuestra arquitectura, estamos implementando multi-tenancy mediante **Aislamiento Lógico por Filas (Row-level isolation)**. Esto significa que los datos de "Carlos" y de "Ana" viven mezclados en la misma tabla de SQLite, pero cada fila lleva una "etiqueta" (`user_id`).

### ¿Por qué proteger en el Caso de Uso y no solo en la API?

Podríamos tener la tentación de poner este código en el endpoint de FastAPI:
```python
# Mal enfoque (lógica en el controlador)
prop = repo.get(property_id)
if prop.user_id != current_user.id:
    raise HTTPException(403)
use_case.record_income(property_id, amount)
```

**¿Por qué está mal en Arquitectura Hexagonal?**
Porque si mañana creamos un script de consola (CLI) para registrar ingresos masivos leyendo de un CSV, ese script llamará directamente al Caso de Uso, ¡saltándose FastAPI! Si la seguridad estaba en FastAPI, el script podría añadir ingresos a propiedades ajenas por error.

**La regla de oro:** La seguridad lógica de los datos (a quién pertenece qué) es una **Regla de Negocio**, por tanto, debe vivir en el **Caso de Uso** (Aplicación) o en el **Dominio**. La API de FastAPI solo debe encargarse de saber *quién* es el usuario (leer el token), pasárselo al Caso de Uso, y traducir los errores del dominio a códigos HTTP (como 403 o 404).
