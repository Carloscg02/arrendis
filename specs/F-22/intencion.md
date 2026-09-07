# Documento de Intención: Feature F-22

## Refactorización Canónica de Persistencia en FastAPI: Ciclo de Vida por Petición (`Depends` con `yield`) y Eliminación de `threading.local`

- **ID de Feature:** `F-22`
- **Estado:** Backlog / Preparación para Spec Futura
- **Documento de Contexto Técnico:** [`docs/guia_concurrencia_hilos_y_bases_de_datos.md`](file:///home/carlos/rental-handler/docs/guia_concurrencia_hilos_y_bases_de_datos.md)

---

## 1. Propósito y Audiencia de este Documento

Este documento **no es la especificación técnica definitiva (`design.md`)**, sino una guía de intención y preparación arquitectónica. Su objetivo es transmitir con total claridad al agente o ingeniero que asuma esta tarea en el futuro:
1. **Por qué** existe la situación actual y qué deuda técnica representa.
2. **Qué** se quiere lograr conceptualmente para hacer el código 100% canónico en FastAPI.
3. **Cuáles son las trampas y puntos críticos** (especialmente en los 335 tests con SQLite en memoria) que la futura especificación deberá resolver antes de tocar código.

---

## 2. El "Por Qué": Justificación y Deuda Técnica

### 2.1. El contexto de partida
Durante la resolución del incidente de concurrencia en la pantalla de detalle de propiedad (*"Piso Gran Vía"*), se descubrió que múltiples hilos del *worker threadpool* de FastAPI ejecutaban peticiones concurrentes (`Promise.all`) pisando los buffers de una única instancia compartida de `sqlite3.Connection`.

Para resolver el problema de inmediato sin alterar la firma de los repositorios ni romper la suite de tests existente, se introdujo aislamiento de conexión mediante `threading.local()` en [`backend/adapters/sqlite_adapter.py`](file:///home/carlos/rental-handler/backend/adapters/sqlite_adapter.py):
```python
self._local = threading.local()  # Cada hilo guarda su propia conexión SQLite
```

### 2.2. Por qué `threading.local()` es un antipatrón en FastAPI
Aunque resolvió eficazmente el fallo bajo las condiciones actuales, `threading.local()` arrastra limitaciones arquitectónicas serias en frameworks modernos:

1. **Peligro fatal ante endpoints asíncronos (`async def`):**
   Actualmente, todos nuestros endpoints en los routers están definidos con `def` síncrono (y por tanto corren en hilos separados del threadpool). Sin embargo, si en el futuro se introduce una ruta declarada con `async def`, **múltiples peticiones se ejecutarán concurrentemente en el MISMO hilo** (*Event Loop* principal).  
   Al correr en el mismo hilo, **todas las peticiones asíncronas compartirían la misma variable de `threading.local()`**, reviviendo de inmediato la colisión de cursores y la corrupción de datos. (En asyncio se requeriría `contextvars`, pero ni siquiera eso es lo idiomático).
2. **Ignora el sistema nativo de Inyección de Dependencias de FastAPI:**
   FastAPI cuenta con un mecanismo de primera clase (`Depends`) con soporte para generadores (`yield`). El patrón canónico consiste en abrir la conexión al inicio de la petición web y cerrarla limpiamente al emitir la respuesta HTTP (*Request-Scoped Lifecycle*), sin necesidad de que el código gestione hilos manualmente.

---

## 3. La "Idea" de la Refactorización

La meta de la Feature F-22 es alinear la persistencia del backend con el estándar oficial de FastAPI:

### 3.1. Ciclo de Vida por Petición (`Request-Scoped`) con `yield`
Sustituir el singleton global guardado en `app.state.db` por un generador canónico en [`backend/api/dependencies.py`](file:///home/carlos/rental-handler/backend/api/dependencies.py):

```python
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Generador canónico de conexión por petición.
    Abre la conexión al iniciar el request y la cierra al finalizar."""
    conn = create_sqlite_connection(...)
    try:
        yield conn
    finally:
        conn.close()
```

### 3.2. Eliminación de `threading.local`
- Eliminar `threading.local()` de [`backend/adapters/sqlite_adapter.py`](file:///home/carlos/rental-handler/backend/adapters/sqlite_adapter.py).
- Cada repositorio (`SQLitePropertyRepository`, `SQLiteExpenseRepository`, etc.) recibirá la conexión viva entregada por `Depends(get_db)` para la duración de esa petición HTTP concreta.
- Al no haber estado compartido entre peticiones, el código es inmune a colisiones tanto si el endpoint es `def` como si es `async def`.

---

## 4. Puntos Críticos y Trampas que la Futura Spec debe Resolver

El agente que redacte la especificación técnica (`specs/F-22/design.md`) debe prestar especial atención a este desafío:

### El reto de SQLite en Memoria (`:memory:`) en los Tests
- En disco (`data/rental.db`), abrir y cerrar conexiones por petición funciona trivialmente con el archivo SQLite en modo WAL.
- **Sin embargo, en los tests unitarios (`pytest`):**
  - Si una función hace `sqlite3.connect(":memory:")` en cada petición HTTP, **cada petición obtendrá una base de datos nueva, vacía y efímera**. Los datos creados en el setup del test desaparecerían antes de que el endpoint los lea.
- **Estrategias a evaluar en la futura spec:**
  1. **Uso de SQLite URI con caché compartida en tests:**  
     Utilizar `file:test_{uuid}?mode=memory&cache=shared` con una conexión ancla (*anchor connection*) viva durante la sesión del test para que todas las conexiones abiertas por `get_db()` apunten al mismo espacio en memoria.
  2. **Override de Dependencia en Fixtures de Pytest:**  
     En `tests/unit/backend/api/conftest.py`, configurar `app.dependency_overrides[get_db]` para que durante los tests entregue la conexión del fixture de prueba sin cerrarla prematuramente en el `finally`.

---

## 5. Criterios de Éxito para la Futura Implementación

Cuando esta feature se active para desarrollo:
1. **Spec formal:** Se deberá redactar [`specs/F-22/design.md`](file:///home/carlos/rental-handler/specs/F-22/design.md) detallando los cambios exactos en interfaces, lifespan, dependencias y fixtures de test.
2. **Cero regresiones:** Los **335 tests existentes** deben pasar al 100% sin modificar las aserciones de negocio.
3. **Persistencia canónica:** Ningún archivo de la aplicación debe importar o usar `threading.local()`.
4. **Verificación concurrente:** El test de estrés `test_concurrent_property_detail_requests` (50 rondas paralelas con `ThreadPoolExecutor`) debe continuar pasando con 0 errores (100% de éxito).
5. **Compatibilidad asíncrona:** Demostrar que un endpoint ficticio o migrado a `async def` opera de forma segura sin interferir con endpoints `def`.
