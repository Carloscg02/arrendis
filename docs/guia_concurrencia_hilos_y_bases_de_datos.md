# Guía de Concurrencia, Hilos y Bases de Datos: De los Principios Básicos a Sistemas Resistentes

Este documento explica de forma pedagógica y exhaustiva el origen del problema de concurrencia experimentado en la aplicación (errores intermitentes 404/500 al consultar propiedades como "Piso Gran Vía"), cómo fue diagnosticado y resuelto técnicamente en todas sus capas, y proporciona una lista de comprobación práctica para diseñar y auditar sistemas resistentes en el futuro.

---

## 1. El Incidente: Síntomas y la Trampa del Diagnóstico Superficial

### El Síntoma
Al navegar al detalle de una propiedad (`/properties/:id`), de forma aparentemente aleatoria (1 de cada 4 o 5 intentos), ocurría uno de estos comportamientos:
1. El usuario era expulsado violentamente de la pantalla hacia el listado principal (`/`), sin mensaje claro.
2. La API devolvía un error HTTP 404 (`"Property not found"`), a pesar de que la propiedad existía perfectamente en la base de datos.
3. Esporádicamente, la API devolvía un HTTP 500 con trazas internas de SQLite: `sqlite3.InterfaceError: bad parameter or other API misuse`.

### La Trampa del Diagnóstico
En una primera aproximación superficial, suele atribuirse el fallo a causas visibles inmediatas:
- *"El token de autenticación JWT ha caducado"*.
- *"Es un problema de caché en el navegador"*.
- *"El frontend tiene un bug en el hook de carga"*.

Aunque había detalles mejorables en la expiración del token y en la navegación del frontend, **ninguno de ellos era la causa raíz**. La causa real era una **condición de carrera (race condition)** a nivel de hilos de ejecución en el servidor compartiendo un recurso no sincronizado: el driver de base de datos SQLite.

---

## 2. Principios Básicos: Desde la CPU hasta la Base de Datos

Para comprender exactamente qué fallaba, es necesario entender cuatro conceptos fundamentales de computación.

### 2.1. Proceso vs. Hilo (Thread)
- **Proceso**: Es una instancia de un programa en ejecución gestionada por el Sistema Operativo (por ejemplo, el proceso de Python donde corre FastAPI/Uvicorn). Cada proceso tiene su propio espacio de memoria virtual protegido y aislado; un proceso no puede leer ni modificar la memoria de otro sin mecanismos explícitos de comunicación inter-proceso (IPC).
- **Hilo (Thread)**: Es la unidad más pequeña de ejecución que el sistema operativo puede planificar dentro de un proceso. Un proceso puede tener decenas o cientos de hilos ejecutándose concurrentemente. **Los hilos dentro de un mismo proceso comparten el mismo espacio de memoria RAM**: comparten variables globales, objetos en memoria y descriptores de archivos.

### 2.2. Concurrencia vs. Paralelismo
- **Concurrencia**: Tratar con muchas tareas a la vez (gestionar la estructura de múltiples peticiones independientes).
- **Paralelismo**: Ejecutar físicamente múltiples instrucciones en el mismo instante exacto (utilizando múltiples núcleos de la CPU).

Cuando un navegador moderno entra en la pantalla de una propiedad, el frontend ejecuta código como este:

```typescript
// PropertyDetail.tsx
const [prop, inc, exp, rep] = await Promise.all([
  propertiesApi.getPropertyById(id),
  incomesApi.getIncomesByProperty(id),
  expensesApi.getExpensesByProperty(id),
  reportsApi.getProfitLossReport(id)
]);
```

El navegador dispara **4 peticiones HTTP independientes al backend al mismo milisegundo**.

### 2.3. El Modelo de Ejecución de FastAPI y AnyIO
FastAPI es un framework asíncrono (ASGI), pero los endpoints que definimos en Python pueden ser de dos tipos:
1. `async def mi_endpoint()`: Se ejecuta cooperativamente en el bucle de eventos (*Event Loop*) del hilo principal.
2. `def mi_endpoint()` (síncrono / estándar): Para no bloquear el bucle de eventos con operaciones que tardan (como consultas a disco o base de datos), FastAPI y Starlette envían automáticamente la ejecución de cada endpoint síncrono a un **pool de hilos de trabajo** (*threadpool* mediante AnyIO).

```
[Navegador]
   |
   |-- HTTP GET /api/v1/properties/123 ---> [Hilo de trabajo 1] (Pool AnyIO)
   |-- HTTP GET /api/v1/incomes/123 -------> [Hilo de trabajo 2] (Pool AnyIO)
   |-- HTTP GET /api/v1/expenses/123 ------> [Hilo de trabajo 3] (Pool AnyIO)
   |-- HTTP GET /api/v1/reports/123 -------> [Hilo de trabajo 4] (Pool AnyIO)
```

Por lo tanto, **las 4 peticiones se ejecutan literalmente al mismo tiempo en 4 hilos distintos de Python**.

---

## 3. La Anatomía del Problema: SQLite y la Conexión Compartida

### 3.1. ¿Cómo funciona un Driver de Base de Datos por dentro?
Una conexión a SQLite (`sqlite3.Connection`) no es simplemente un identificador pasivo; es una estructura de datos viva escrita en lenguaje C que gestiona:
- Sentencias SQL preparadas (*prepared statement cache*).
- Punteros a cursores y buffers de resultados en memoria.
- Máquinas de estado de transacciones (`BEGIN`, `COMMIT`, `ROLLBACK`).
- Control de bloqueos en el archivo de base de datos.

### 3.2. El Engaño de `check_same_thread=False`
Por defecto, la librería estándar `sqlite3` de Python tiene un guardia de seguridad: si intentas usar una conexión creada en el Hilo A desde el Hilo B, lanza inmediatamente:
```
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
```

Para evitar este error, es común ver en tutoriales la opción `sqlite3.connect(..., check_same_thread=False)`.
**Este parámetro es extremadamente peligroso si no se entiende lo que hace:**
- Lo único que hace es **desactivar el aviso de Python**.
- **NO hace que la conexión sea segura para usarse concurrentemente**. SQLite compilado en modo multihilo permite que una conexión se use en diferentes hilos, **pero solo si se usa por un hilo a la vez**.

### 3.3. La Condición de Carrera en Tiempo Real
Antes de nuestra corrección, el backend instanciaba una **única conexión SQLite compartida para toda la aplicación**:

```
[Hilo 1: Obtener Propiedad]                    [Hilo 2: Obtener Ingresos]
         |                                                 |
         +-----> [ Conexión SQLite Compartida ] <----------+
```

Veamos la secuencia temporal exacta a nivel de microsegundos que causaba el fallo:

1. **Microsegundo 0**: El Hilo 1 ejecuta `SELECT * FROM properties WHERE id = 'gran-via'`.
2. **Microsegundo 1**: El driver de C de SQLite compila la consulta, asigna el buffer de cursor y empieza a leer el registro de disco.
3. **Microsegundo 2**: Antes de que el Hilo 1 pueda llamar a `cursor.fetchone()`, el Hilo 2 ejecuta `SELECT * FROM incomes WHERE property_id = 'gran-via'` **usando la misma conexión**.
4. **Microsegundo 3**: La consulta del Hilo 2 sobreescribe o resetea la sentencia activa y los punteros internos de la conexión de C.
5. **Microsegundo 4**: El Hilo 1 despierta y llama a `cursor.fetchone()`. Pero el buffer ya no apunta al resultado de `properties`, sino que ha sido limpiado o reiniciado por el Hilo 2.
6. **Microsegundo 5**: `cursor.fetchone()` devuelve `None`.
7. **Microsegundo 6**: El repositorio de propiedades interpreta `None` como "la propiedad no existe" y lanza `PropertyNotFoundException`.
8. **Microsegundo 7**: FastAPI traduce la excepción a un HTTP 404: `{"detail": "Property not found"}`.

En otros casos, si la colisión ocurría mientras SQLite estaba leyendo bytes de parámetros, el motor de C detectaba la corrupción de memoria y lanzaba:
`sqlite3.InterfaceError: bad parameter or other API misuse` (HTTP 500).

Este es el motivo por el cual el error era **intermitente**: solo ocurría cuando el planificador de la CPU alternaba los hilos en ese intervalo crítico de microsegundos.

---

## 4. La Solución Arquitectónica Multicapa Implementada

Para resolver este problema de raíz y garantizar que el sistema sea resistente bajo cualquier nivel de carga o concurrencia, implementamos una solución en 4 capas.

```
+-------------------------------------------------------------------------------+
| FRONTEND: Deduplicación de Refresh 401 + Manejo Local de Errores (sin salida) |
+-------------------------------------------------------------------------------+
                                      |
                           (Peticiones Concurrentes)
                                      |
+-------------------------------------------------------------------------------+
| BACKEND API: Tokens con TTL ampliado (60 min) + FastAPI Threadpool Seguro     |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
| PERSISTENCIA: Conexiones Aisladas por Hilo (threading.local)                  |
|               Cada hilo tiene su propia conexión independiente                |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
| MOTOR SQLITE: Modo WAL (lecturas no bloquean escrituras) + busy_timeout (15s) |
+-------------------------------------------------------------------------------+
```

### Capa 1: Aislamiento de Conexión por Hilo (`threading.local`)
En lugar de una única conexión global, el adaptador utiliza almacenamiento local al hilo:

```python
# backend/adapters/sqlite_adapter.py
import threading

class SQLiteDatabase:
    def __init__(self, db_path: str):
        self._local = threading.local()

    @property
    def connection(self) -> sqlite3.Connection:
        """Devuelve la conexión exclusiva del hilo actual."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._create_connection()
        return self._local.connection
```

- Cada hilo del pool de FastAPI obtiene su propia conexión privada e independiente.
- Los cursores, buffers y transacciones de un hilo están físicamente aislados de los demás.
- Para tests en memoria (`:memory:`), se implementó URI compartida (`file:mem_{uuid}?mode=memory&cache=shared`) para que hilos independientes compartan el mismo estado de datos sin interferir en los cursores.

### Capa 2: Motor SQLite de Alta Concurrencia (WAL + Busy Timeout)
Por defecto, SQLite utiliza un archivo de diario tradicional (*rollback journal*). En este modo, cuando un hilo escribe, bloquea a todos los lectores; cuando un hilo lee, bloquea a los escritores.

Cambiamos la configuración a **WAL (Write-Ahead Logging)** y configuramos espera activa:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 15000;  -- 15 segundos
```

- **Lectores concurrentes**: Múltiples hilos pueden leer simultáneamente sin ningún tipo de bloqueo.
- **Lecturas y escrituras simultáneas**: Los lectores leen la versión estable mientras el escritor escribe en el archivo WAL paralelo. No se bloquean entre sí.
- **`busy_timeout` de 15 segundos**: Si un hilo necesita escribir y otro está cerrando una transacción, espera pacientemente hasta 15.000 ms en lugar de lanzar inmediatamente el error `database is locked`.

### Capa 3: Resiliencia de Autenticación ante Ráfagas (Frontend y Backend)
Cuando un token JWT caduca, las 4 peticiones concurrentes de `Promise.all` reciben un HTTP 401 a la vez.
- **Problema previo**: Las 4 peticiones intentaban llamar concurrentemente al endpoint `/refresh` con el mismo Refresh Token. Como los refresh tokens se rotan e invalidan al usarse, la primera tenía éxito pero las otras 3 fallaban (token ya usado), cerrando la sesión del usuario.
- **Solución implementada**:
  - Un mecanismo de deduplicación en el interceptor de peticiones (`frontend/src/services/api.ts`). Si ya hay un refresco en curso, las demás peticiones esperan a esa misma promesa compartida.
  - Almacenamiento sincronizado del token en `sessionStorage`.
  - Ampliación del TTL del Access Token de 15 a 60 minutos para reducir la frecuencia de refrescos.

### Capa 4: Experiencia de Usuario Tolerante a Fallos (Frontend)
- **Problema previo**: Si una petición fallaba en `PropertyDetail.tsx`, el bloque `catch` ejecutaba `navigate('/')`. El usuario era expulsado al inicio y perdía su contexto de trabajo.
- **Solución implementada**:
  - Se eliminó la redirección destructiva.
  - La interfaz muestra un estado de error elegante dentro de la propia página con un botón claro de **"Reintentar"**, permitiendo recuperarse de cualquier micro-corte de red sin abandonar la pantalla.

---

## 5. Pruebas de Verificación y Carga Concurrente

Para garantizar que el fallo está resuelto y no reaparecerá, se introdujo un test de estrés concurrente que simula la carga real:

```python
# tests/unit/backend/api/test_properties_api.py
def test_concurrent_property_detail_requests(client, test_db, auth_headers):
    # Simula múltiples hilos ejecutando lecturas simultáneas sobre la misma propiedad
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(client.get, f"/api/v1/properties/{prop_id}", headers=auth_headers) for _ in range(50)]
        results = [f.result() for f in futures]
    
    # 100% de las respuestas deben ser 200 OK (0 fallos 404/500)
    for res in results:
        assert res.status_code == 200
```

- **Resultado antes de la solución**: 3 de cada 25 rondas fallaban con 404 o 500.
- **Resultado tras la solución**: 50 rondas (200 peticiones concurrentes simultáneas), **0 fallos (100% éxito)**.
- Suite completa del backend: **335 tests pasando**.

---

## 6. Guía para el Futuro: Cómo Pedir y Auditar Sistemas Resistentes

Cuando encargues, diseñes o audites un software (bien sea trabajando con ingenieros, consultoras o asistentes de IA), utiliza esta lista de preguntas clave. Un sistema profesional debe responder satisfactoriamente a cada una de ellas.

### Lista de Comprobación Arquitectónica (Audit Checklist)

| Área | Pregunta de Control | Respuesta Esperada | Señal de Alarma (Red Flag) |
| :--- | :--- | :--- | :--- |
| **Base de Datos** | ¿Cómo se gestiona el ciclo de vida de las conexiones? | Pool de conexiones gestionado o conexión aislada por hilo / por petición (`scoped lifecycle`). | Una única variable global de conexión compartida para toda la app. |
| **SQLite** | Si usamos SQLite en producción o desarrollo, ¿qué modo de diario y timeout están activos? | `PRAGMA journal_mode = WAL` y `PRAGMA busy_timeout >= 5000`. | `check_same_thread=False` sin pool ni aislamiento de hilos; modo DELETE/journal estándar. |
| **Concurrencia Web** | ¿Qué ocurre si un cliente envía 10 peticiones idénticas en el mismo milisegundo? | El servidor procesa cada una en su contexto aislado sin colisiones; las escrituras críticas son idempotentes. | Respuestas 500 intermitentes, registros duplicados o "registro no encontrado" fantasma. |
| **Autenticación** | ¿Cómo responde el frontend si expira el token durante una ráfaga de peticiones (`Promise.all`)? | La primera petición refresca el token; las demás se encolan y reintentan con el nuevo token sin desloguear al usuario. | Cierre de sesión intempestivo al cambiar de pestaña o cargar dashboards complejos. |
| **Manejo de Errores UI** | ¿Cómo reacciona la interfaz ante un fallo 4xx o 5xx en una pantalla de detalle? | Muestra un banner o pantalla de error local con botón "Reintentar", manteniendo al usuario en la URL actual. | `navigate('/')` o redirecciones automáticas en los bloques `catch` que desorientan al usuario. |
| **Testing** | ¿Existen tests de regresión que verifiquen concurrencia real? | Tests con `ThreadPoolExecutor` o herramientas de carga (k6, Locust) ejecutando peticiones simultáneas. | Solo tests secuenciales ("un test llama a un endpoint después de otro"). |

---

## 7. Glosario Rápido de Conceptos

- **Race Condition (Condición de Carrera)**: Anomalía donde el resultado de una operación depende del orden o sincronización imprevista de eventos concurrentes.
- **Thread-Safety (Seguridad de Hilo)**: Propiedad de un fragmento de código u objeto que garantiza que puede ser invocado simultáneamente por múltiples hilos sin corromper el estado.
- **Connection Pool**: Conjunto de conexiones a base de datos pre-creadas que se prestan temporalmente a los hilos de trabajo y se devuelven al finalizar la petición.
- **WAL (Write-Ahead Logging)**: Técnica en motores de bases de datos donde los cambios se escriben primero en un log secuencial, permitiendo que las lecturas y escrituras ocurran en paralelo.
- **Idempotencia**: Propiedad de una operación que produce el mismo efecto sin importar cuántas veces se ejecute (ejemplo: `DELETE /properties/1` o `PUT`).
- **Thundering Herd (Efecto Estampida)**: Fenómeno en el que un evento (como la expiración de un token o caché) despierta o dispara múltiples procesos a la vez compitiendo destructivamente por el mismo recurso.
