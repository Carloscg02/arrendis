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

### 2.3. ¿En qué momento exacto se crea un hilo en el código?
En la inmensa mayoría de aplicaciones web modernas, **el desarrollador jamás escribe `threading.Thread.start()` manualmente**. Los hilos no los crea nuestro código de negocio, sino el **servidor web subyacente (Uvicorn + AnyIO / Starlette)** mediante un **Pool de Hilos (*Worker ThreadPool*)**:

1. **Al iniciar el servidor (`uvicorn ...`):** Uvicorn arranca en el proceso principal de Python con un **hilo principal** (*Main Thread*), donde vive el bucle de eventos (*Event Loop*). En ese arranque, la librería AnyIO inicializa una cuadrilla de hilos durmientes (hasta 40 hilos por defecto en Python) esperando tareas.
2. **La detección del tipo de función:** Cuando una petición HTTP entra por la red (por ejemplo, `GET /api/properties/gran-via`), FastAPI examina la firma de la función en el router:
   ```python
   # backend/api/routes/properties.py
   @router.get("/{property_id}")
   def get_property(...):  # <-- Definida con 'def', NO con 'async def'
   ```
3. **El despacho al hilo:** FastAPI detecta que la función no es asíncrona. Sabe que si la ejecuta en el hilo principal congelará el bucle de eventos de todo el servidor mientras lee de SQLite. Por tanto, la delega inmediatamente a un hilo libre del pool:
   ```python
   # Lo que hace FastAPI y AnyIO por debajo de forma transparente:
   await anyio.to_thread.run_sync(get_property, ...)
   ```
4. **Activación:** Un hilo durmiente del pool (ej. `Thread-2`) despierta en ese microsegundo exacto, ejecuta la función, devuelve el resultado al cliente y vuelve a dormirse en el pool a la espera de la siguiente petición.

```
[Navegador]
   |
   |-- HTTP GET /api/v1/properties/123 ---> [Hilo del Pool 1] (AnyIO ThreadPool)
   |-- HTTP GET /api/v1/incomes/123 -------> [Hilo del Pool 2] (AnyIO ThreadPool)
   |-- HTTP GET /api/v1/expenses/123 ------> [Hilo del Pool 3] (AnyIO ThreadPool)
   |-- HTTP GET /api/v1/reports/123 -------> [Hilo del Pool 4] (AnyIO ThreadPool)
```

Por lo tanto, **las 4 peticiones simultáneas del navegador se ejecutan en 4 hilos distintos de Python al mismo tiempo**.

### 2.4. Concurrencia en un solo hilo vs. Paralelismo multihilo en FastAPI

#### Metáfora: El Restaurante
- **Modelo Asíncrono (`async def` - Concurrencia en 1 solo hilo): El Camarero Ágil**  
  Tienes un único camarero. Toma la comanda en la mesa 1, la lleva a la cocina y, **mientras el cocinero prepara el plato** (espera de red o I/O no bloqueante), el camarero no se queda esperando de pie: va a la mesa 2 a servir el agua y a la mesa 3 a tomar nota. Un solo camarero puede gestionar 100 mesas si las pausas son voluntarias (`await`).
- **Modelo Síncrono (`def` en ThreadPool - Paralelismo multihilo): El Ejército de Camareros**  
  Tienes una plantilla de camareros (pool de hilos). El camarero 1 va a la cocina y se queda esperando hasta que el plato esté terminado. Mientras tanto, el camarero 2 atiende la mesa 2 y el camarero 3 atiende la mesa 3 de forma totalmente independiente.

#### Motivo técnico de decisión: ¿Cuándo usar cada uno?
La decisión **no es por preferencia estética, sino por las librerías utilizadas para interactuar con la base de datos y el disco**:
- **¿Cuándo usar `async def` (1 solo hilo)?** Únicamente cuando **TODAS** las librerías en la ruta sean nativamente asíncronas y no bloqueantes (ej. `asyncpg` para PostgreSQL, `aiohttp` o `httpx` para llamadas HTTP, `aiosqlite`).
  - *Ventaja:* Mínimo consumo de RAM; puede mantener decenas de miles de conexiones abiertas (WebSockets, microservicios de streaming).
  - *Peligro mortal:* Si defines un endpoint como `async def` y dentro llamas a una función bloqueante tradicional (como `sqlite3`, `bcrypt` o `time.sleep()`), **congelas al camarero único**. Toda la web se paraliza para todos los usuarios del sistema.
- **¿Cuándo usar `def` (multihilo)?** Cuando utilizas la librería estándar de Python (`sqlite3`, algoritmos criptográficos intensivos como `bcrypt`, o librerías de generación de PDFs con `reportlab`). FastAPI te protege enviando cada petición a un hilo independiente para que las esperas en disco no congelen el servidor.
- *El precio a pagar:* Al haber múltiples hilos corriendo simultáneamente en el mismo proceso compartiendo memoria, **cualquier recurso común (como el driver de SQLite) debe estar aislado o protegido contra colisiones (*Thread-Safe*)**.

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

#### Análisis Crítico de Arquitectura: ¿Es `threading.local()` una buena práctica en FastAPI?

En frameworks clásicos síncronos (como Flask o Django tradicional), `threading.local()` era el mecanismo estándar para aislar conexiones. Sin embargo, en el diseño idiomático de **FastAPI**, el uso directo de `threading.local()` se considera un **antipatrón / solución de transición** por dos motivos fundamentales:

1. **Peligro ante funciones asíncronas (`async def`):**  
   Si en el futuro se introducen endpoints declarados con `async def`, múltiples peticiones concurrentes se ejecutan dentro del **mismo hilo** del bucle de eventos (*Event Loop*), pausándose y reanudándose con `await`. Como todas esas peticiones comparten el mismo hilo de ejecución, **¡compartirían exactamente la misma conexión en `threading.local`!**, reintroduciendo la colisión de cursores y la corrupción de transacciones. (En el paradigma asíncrono de Python no se usa `threading.local`, sino `contextvars`).
2. **FastAPI ya ofrece un patrón nativo superior: Ciclo de vida por petición (`Depends` con `yield`):**  
   El patrón canónico que recomienda el diseño de FastAPI es delegar la gestión al sistema de inyección de dependencias:
   ```python
   def get_db():
       conn = sqlite3.connect("rental.db")
       try:
           yield conn  # Se inyecta en el endpoint para esta petición concreta
       finally:
           conn.close()  # FastAPI la cierra automáticamente al terminar la respuesta HTTP
   ```
   Con este patrón, cada petición HTTP (sea síncrona o asíncrona) recibe una conexión limpia y privada que se destruye al finalizar, sin necesidad de manipular hilos a bajo nivel.

**¿Por qué se utilizó `threading.local()` en nuestra solución inmediata?**  
Por el contexto histórico del código: el backend tenía desde sus inicios un singleton global en `app.state.db` y 335 tests con base de datos en memoria (`:memory:`). Cambiar el ciclo de vida a nivel global requería reestructurar fixtures y el lifespan. Como todos nuestros endpoints actuales son síncronos (`def`), `threading.local()` permitió solucionar la carrera crítica de "Piso Gran Vía" de inmediato sin romper ningún test existente.

> [!NOTE]  
> Para resolver esta deuda técnica y alinear la persistencia al 100% con el estándar canónico de FastAPI, se ha creado la tarea de refactorización **F-22** en el backlog (ver su documento de intención en [`specs/F-22/intencion.md`](file:///home/carlos/rental-handler/specs/F-22/intencion.md)).

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
  - Almacenamiento seguro del Access Token exclusivamente en memoria JS (sin persistencia en storage).
  - Ampliación del TTL del Access Token de 15 a 60 minutos para reducir la frecuencia de refrescos.

### Capa 4: Experiencia de Usuario Tolerante a Fallos (Frontend)
- **Problema previo**: Si una petición fallaba en `PropertyDetail.tsx`, el bloque `catch` ejecutaba `navigate('/')`. El usuario era expulsado al inicio y perdía su contexto de trabajo.
- **Solución implementada**:
  - Se eliminó la redirección destructiva.
  - La interfaz muestra un estado de error elegante dentro de la propia página con un botón claro de **"Reintentar"**, permitiendo recuperarse de cualquier micro-corte de red sin abandonar la pantalla.

---

## 5. ¿Y si migramos a otra base de datos? SQLite vs. PostgreSQL y el "Connection Pool"

Una duda frecuente tras analizar este problema es: *¿Usamos múltiples hilos porque SQLite es gratuita o simple? Si migramos a una base de datos más robusta (como PostgreSQL), ¿se cambiaría a concurrencia en un solo hilo?*

La respuesta es **no**, y comprender la relación entre hilos, bases de datos y pools aclara cómo funcionan las arquitecturas profesionales en backend.

### 5.1. El mito del coste: SQLite vs. PostgreSQL
Prácticamente todas las grandes bases de datos de la industria (**PostgreSQL, MySQL, MariaDB**) son **100% gratuitas y de código abierto**, exactamente igual que SQLite.

La decisión de usar SQLite en el proyecto no fue por coste ni por limitación, sino por su **modelo de despliegue**:
- **SQLite es una base de datos embebida:** No requiere instalar servicios de fondo, ni abrir puertos de red, ni configurar usuarios o contraseñas. Todo vive en un único archivo (`rental.db`) que se lee a velocidad de memoria local.
- **PostgreSQL es una base de datos cliente-servidor:** Requiere un proceso demonio en red (puerto 5432), gestión de usuarios, copias de seguridad remotas y configuración de red.

### 5.2. ¿Por qué los múltiples hilos seguirán existiendo en PostgreSQL?
Tener múltiples hilos (o múltiples procesos) **no es un defecto ni un compromiso; es la forma natural de aprovechar el procesador**:
- Los servidores modernos cuentan con 4, 8, 16 o más núcleos de CPU (*cores*).
- Si tu backend funcionara en un único hilo, solo aprovecharía 1 núcleo y dejaría el 85% de la potencia de la CPU desaprovechada.
- Para atender a decenas o cientos de usuarios a la vez en paralelo, el backend **debe** procesar peticiones simultáneas en múltiples hilos o procesos.

### 5.3. ¿Cómo resuelve PostgreSQL la concurrencia? El "Connection Pool" (Piscina de Conexiones)
En nuestra solución actual con SQLite, tuvimos que aislar las conexiones manualmente en Python mediante `threading.local()` porque SQLite es una librería embebida que accede a un archivo local compartido en el mismo proceso.

En PostgreSQL (y MySQL), la gestión de concurrencia es nativa gracias al patrón **Connection Pool**:

```
[ Hilo de Trabajo 1 ]   [ Hilo de Trabajo 2 ]   [ Hilo de Trabajo 3 ]
         |                       |                       |
         v                       v                       v
┌─────────────────────────────────────────────────────────────────────┐
│                    CONNECTION POOL (Ej: 20 conexiones)              │
│  [Conn 1: Ocupada]     [Conn 2: Ocupada]     [Conn 3: Ocupada]     │
│  [Conn 4: Libre]       [Conn 5: Libre]       ...                   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   | (Sockets TCP / Red)
                                   v
             [ Servidor Externo PostgreSQL (Puerto 5432) ]
```

1. La aplicación abre al iniciar un cupo fijo de conexiones de red (ej. 20 conexiones TCP).
2. Cuando el **Hilo 1** atiende a un usuario, pide una conexión prestada del pool.
3. El **Hilo 2** toma otra conexión simultáneamente.
4. Cada hilo ejecuta su consulta sin interferir jamás en los buffers de los demás.
5. Al terminar la petición HTTP, el hilo devuelve la conexión limpia al pool para el siguiente usuario.

### 5.4. Concurrencia de Escritura: Bloqueo de Archivo vs. Bloqueo por Fila
Aquí reside la gran ventaja de PostgreSQL frente a SQLite en alta concurrencia:
- **SQLite (WAL):** Admite **ilimitados lectores concurrentes** y **un único escritor simultáneo a la vez en toda la base de datos**. Si dos usuarios guardan una factura al mismo instante exacto, uno escribe primero y el segundo espera unos milisegundos (`busy_timeout`).
- **PostgreSQL:** Dispone de **bloqueo a nivel de fila (*row-level locking*)**. Si 50 usuarios editan 50 contratos distintos a la vez, las 50 escrituras se completan en paralelo al mismo milisegundo sin esperas, porque el motor bloquea únicamente el registro afectado, no la base de datos entera.

### 5.5. Tabla Comparativa: SQLite Actual vs. PostgreSQL con Pool

| Característica | Nuestra Solución Actual (SQLite WAL) | Si Migramos a PostgreSQL |
| :--- | :--- | :--- |
| **Tipo de Arquitectura** | Embebida (archivo local en disco) | Cliente-Servidor (servicio en red) |
| **Coste de Licencia** | Gratis (Dominio Público) | Gratis (Open Source) |
| **Modelo de Hilos en Backend** | Múltiples hilos (FastAPI ThreadPool) | Múltiples hilos (FastAPI ThreadPool) o Procesos Workers |
| **Mecanismo de Aislamiento** | `threading.local` (1 conexión por hilo) | `ConnectionPool` gestionado (ej. `psycopg_pool`) |
| **Lecturas Concurrentes** | Ilimitadas y ultrarrápidas (en memoria/disco local) | Ilimitadas (vía sockets de red) |
| **Escrituras Concurrentes** | Secuenciales con espera activa (`busy_timeout`) | Masivas en paralelo (bloqueo por fila) |
| **Mantenimiento Operativo** | Cero (basta con copiar el archivo `.db`) | Medio (gestionar servidor, backups, credenciales) |

---

## 6. Pruebas de Verificación y Carga Concurrente

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

## 7. Guía para el Futuro: Cómo Pedir y Auditar Sistemas Resistentes

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

## 8. Glosario Rápido de Conceptos

- **Race Condition (Condición de Carrera)**: Anomalía donde el resultado de una operación depende del orden o sincronización imprevista de eventos concurrentes.
- **Thread-Safety (Seguridad de Hilo)**: Propiedad de un fragmento de código u objeto que garantiza que puede ser invocado simultáneamente por múltiples hilos sin corromper el estado.
- **Connection Pool**: Conjunto de conexiones a base de datos pre-creadas que se prestan temporalmente a los hilos de trabajo y se devuelven al finalizar la petición.
- **WAL (Write-Ahead Logging)**: Técnica en motores de bases de datos donde los cambios se escriben primero en un log secuencial, permitiendo que las lecturas y escrituras ocurran en paralelo.
- **Idempotencia**: Propiedad de una operación que produce el mismo efecto sin importar cuántas veces se ejecute (ejemplo: `DELETE /properties/1` o `PUT`).
- **Thundering Herd (Efecto Estampida)**: Fenómeno en el que un evento (como la expiración de un token o caché) despierta o dispara múltiples procesos a la vez compitiendo destructivamente por el mismo recurso.
