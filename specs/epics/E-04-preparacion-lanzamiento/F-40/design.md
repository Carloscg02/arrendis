# 📐 Especificación Técnica: F-40
# Protección contra Fuerza Bruta y Rate Limiting en Endpoints de Autenticación

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** En Revisión Técnica (Gate de Arquitectura)  
> **Fecha:** 2026-10-03  
> **Autor:** Tech Lead & Orquestador Arrendis  

---

## 1. Contexto y Delimitación de Alcance

### 1.1. Contexto
En el estado actual de la plataforma, los endpoints de autenticación (`/api/auth/login` y `/api/auth/register`) no disponen de ningún mecanismo de control de frecuencia de peticiones (*rate limiting* / *throttling*). Un atacante malintencionado o un script automatizado puede lanzar miles de combinaciones de usuario/contraseña por segundo (ataque de fuerza bruta / credential stuffing) o inundar la base de datos registrando cuentas basura sin restricción alguna.

Para blindar la plataforma antes del lanzamiento a producción (General Availability) se requiere una capa defensiva en memoria que restrinja el flujo de peticiones abusivas sin degradar la experiencia de usuarios legítimos y sin comprometer el consumo de RAM del servidor.

### 1.2. Delimitación (Qué entra y qué NO entra)
- **✅ ENTRA:**
  - Limitador en memoria basado en el algoritmo de **Ventana Deslizante (Sliding Window Log)** con política estricta de mitigación de fugas de memoria (*TTL cleanup + capacity bound LRU eviction*).
  - Middleware ASGI / FastAPI `RateLimitMiddleware` aplicado exclusivamente a `POST /api/auth/login` y `POST /api/auth/register`.
  - Umbral: máximo **10 peticiones por minuto por IP**.
  - Respuesta HTTP semántica con código `429 Too Many Requests`, cabecera estándar `Retry-After: <segundos>` y cuerpo JSON con mensaje y tiempo de espera.
  - Extracción confiable de la IP del cliente considerando proxies inversos (`X-Forwarded-For` o `client.host`).
  - Flag de entorno `RATE_LIMIT_ENABLED` para desactivación transparente durante tests de integración del resto de la plataforma, permitiendo su activación explícita en la suite de seguridad de F-40.
  - Suite de tests unitarios y de integración en `tests/unit/backend/api/test_f40_rate_limiting.py`.
- **❌ NO ENTRA:**
  - Rate limiting global para toda la API (se reserva para la capa de borde / CDN en Cloudflare).
  - Captcha visual o reCAPTCHA en el frontend (fuera de alcance en esta fase).
  - Bloqueo permanente de IPs a nivel de firewall del sistema operativo (`fail2ban` o `iptables`).

---

## 2. Lenguaje Ubicuo

| Término | Definición Formal en el Dominio |
|---|---|
| **Rate Limiting** | Técnica de control de tráfico que limita la frecuencia y volumen de peticiones que un cliente (identificado por su IP) puede ejecutar contra un servicio en un intervalo de tiempo. |
| **Ventana Deslizante (Sliding Window Log)** | Algoritmo de control de flujo que almacena las marcas de tiempo (*timestamps*) de peticiones recientes y calcula en tiempo real si el recuento dentro de los últimos $T$ segundos supera el límite permitido $N$. |
| **Fuerza Bruta (Brute Force Attack)** | Intento automatizado y masivo de adivinar credenciales de acceso probando diccionarios de contraseñas contra un endpoint de login. |
| **HTTP 429 Too Many Requests** | Código de estado HTTP estándar definido por la RFC 6585 que indica que el cliente ha enviado demasiadas peticiones en un periodo de tiempo determinado. |
| **Cabecera Retry-After** | Cabecera HTTP que indica al cliente la cantidad de segundos que debe esperar antes de volver a intentar la operación. |
| **Eviction Policy (Política de Desalojo)** | Mecanismo de gestión de memoria que expulsa o purga entradas del diccionario en memoria cuando se alcanza el límite de capacidad máximo (10.000 IPs), evitando ataques de denegación de servicio por agotamiento de RAM (*OOM - Out of Memory*). |

---

## 3. Diseño Técnico Detallado

### 3.1. Algoritmo y Gestor de Estado: `InMemoryRateLimiter`
Ubicación: `backend/api/middleware/rate_limit.py`.  
Para evitar la complejidad de Redis en esta fase monocontenedor y mantener la ligereza de Arrendis, se diseña un limitador en memoria thread-safe con saneamiento continuo:

```python
import time
from collections import OrderedDict
from threading import Lock

class InMemoryRateLimiter:
    """
    Limitador de tasa por ventana deslizante con protección de memoria.
    
    Mantiene un registro de timestamps por clave (IP).
    Aplica purga pasiva de timestamps expirados y desalojo LRU si
    se alcanza la capacidad máxima (max_keys) para prevenir OOM.
    """

    def __init__(self, limit: int = 10, window_seconds: int = 60, max_keys: int = 10000):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._records: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = Lock()

    def is_rate_limited(self, key: str, now: float | None = None) -> tuple[bool, int]:
        """
        Evalúa si la clave excede el límite en la ventana.
        Retorna (is_limited: bool, retry_after: int).
        """
        current_time = now if now is not None else time.time()
        cutoff = current_time - self.window_seconds

        with self._lock:
            # 1. Obtener o inicializar registro
            timestamps = self._records.get(key, [])
            
            # 2. Filtrar timestamps expirados fuera de la ventana
            valid_timestamps = [t for t in timestamps if t > cutoff]

            # 3. Comprobar si supera el límite
            if len(valid_timestamps) >= self.limit:
                # El tiempo de espera es el tiempo hasta que expire el intento más antiguo que satura el cupo
                oldest_timestamp = valid_timestamps[0]
                retry_after = max(1, int(oldest_timestamp + self.window_seconds - current_time) + 1)
                self._records[key] = valid_timestamps
                self._records.move_to_end(key)
                return True, retry_after

            # 4. Registrar la nueva petición
            valid_timestamps.append(current_time)
            self._records[key] = valid_timestamps
            self._records.move_to_end(key)

            # 5. Prevención de Fuga de Memoria (Eviction Policy)
            if len(self._records) > self.max_keys:
                self._cleanup_memory(cutoff)

            return False, 0

    def _cleanup_memory(self, cutoff: float) -> None:
        """Purga claves con marcas expiradas y desaloja las más antiguas (LRU)."""
        to_delete = [
            k for k, timestamps in self._records.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for k in to_delete:
            del self._records[k]

        # Si aún excede tras purgar expirados, eliminar el 10% más antiguo (FIFO/LRU)
        while len(self._records) > self.max_keys:
            self._records.popitem(last=False)

    def reset(self) -> None:
        """Reinicia el estado en memoria (útil para tests)."""
        with self._lock:
            self._records.clear()
```

### 3.2. Middleware ASGI: `RateLimitMiddleware`
Ubicación: `backend/api/middleware/rate_limit.py`.  
Intercepta peticiones dirigidas a `/api/auth/login` y `/api/auth/register` emitidas mediante el método `POST`:

```python
import os
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import JSONResponse

class RateLimitMiddleware:
    """Middleware ASGI para throttling en endpoints de autenticación."""

    PROTECTED_PATHS = {
        "/api/auth/login",
        "/api/auth/register",
    }

    def __init__(self, app: ASGIApp, limiter: InMemoryRateLimiter | None = None) -> None:
        self.app = app
        self.limiter = limiter or InMemoryRateLimiter(limit=10, window_seconds=60)

    def _is_enabled(self) -> bool:
        # Desactivado por defecto si TESTING="1", salvo que se fuerce con FORCE_RATE_LIMIT="1"
        if os.getenv("FORCE_RATE_LIMIT") == "1":
            return True
        if os.getenv("TESTING") == "1":
            return False
        return os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")

    def _get_client_ip(self, scope: Scope) -> str:
        headers = dict(scope.get("headers", []))
        x_forwarded_for = headers.get(b"x-forwarded-for")
        if x_forwarded_for:
            # Tomar la primera IP de la cadena (cliente original)
            ip_str = x_forwarded_for.decode("latin1").split(",")[0].strip()
            if ip_str:
                return ip_str
        client = scope.get("client")
        return client[0] if client else "127.0.0.1"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] == "POST":
            path = scope.get("path", "").rstrip("/")
            if path in self.PROTECTED_PATHS and self._is_enabled():
                client_ip = self._get_client_ip(scope)
                is_limited, retry_after = self.limiter.is_rate_limited(client_ip)
                if is_limited:
                    response = JSONResponse(
                        status_code=429,
                        headers={"Retry-After": str(retry_after)},
                        content={
                            "detail": "Demasiados intentos de autenticación. Por favor, inténtelo de nuevo más tarde.",
                            "retry_after": retry_after,
                        },
                    )
                    await response(scope, receive, send)
                    return

        await self.app(scope, receive, send)
```

### 3.3. Representación Visual en Frontend (Wireframe ASCII)
Cuando el frontend recibe un código 429 desde `/api/auth/login`, el formulario muestra un aviso Atelier Editorial de advertencia sin emojis, respetando `DESIGN.md`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          INICIO DE SESIÓN                              │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ [!] ACCESO TEMPORALMENTE LIMITADO                                  │ │
│ │ Demasiados intentos fallidos desde esta conexión.                  │ │
│ │ Podrá intentar de nuevo en 42 segundos.                            │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ Correo electrónico                                                     │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ usuario@ejemplo.com                                                │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ Contraseña                                                             │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ ••••••••••••••••                                                   │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ [ Acceder (Deshabilitado temporalmente) ]                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Plan de Pruebas y Verificación

### 4.1. Tests Unitarios del Limitador (`tests/unit/backend/api/test_f40_rate_limiting.py`)
1. `test_rate_limiter_allows_under_limit`:
   - Enviar 10 peticiones consecutivas con la misma IP.
   - Todas retornan `is_limited == False`.
2. `test_rate_limiter_blocks_on_11th_request`:
   - Enviar la petición 11 dentro de la misma ventana.
   - Retorna `is_limited == True` y `retry_after > 0`.
3. `test_rate_limiter_resets_after_window_expires`:
   - Simular paso del tiempo (`now = current_time + 61`).
   - La petición subsiguiente es permitida (`is_limited == False`).
4. `test_rate_limiter_memory_eviction`:
   - Configurar `max_keys = 5`.
   - Insertar 10 IPs distintas con timestamps expirados y activos.
   - Comprobar que el tamaño total del diccionario `_records` nunca supera `max_keys` y que la memoria permanece acotada.

### 4.2. Tests de Integración HTTP en FastAPI
5. `test_auth_login_rate_limiting_http_429`:
   - Con `FORCE_RATE_LIMIT="1"`, realizar 10 POST a `/api/auth/login` con credenciales inválidas.
   - Verificar que la petición 11 responde `429 Too Many Requests`.
   - Verificar cabecera `Retry-After`.
   - Verificar schema del cuerpo `{ "detail": "...", "retry_after": ... }`.
6. `test_auth_register_rate_limiting_http_429`:
   - Comprobar que `/api/auth/register` comparte o respeta la misma cuota de protección.
7. `test_unprotected_routes_not_throttled`:
   - Con `FORCE_RATE_LIMIT="1"`, realizar 15 peticiones GET a `/api/properties` y `/api/health`.
   - Comprobar que ninguna es bloqueada con 429.
8. `test_x_forwarded_for_ip_extraction`:
   - Enviar cabecera `X-Forwarded-For: 203.0.113.195, 198.51.100.1` y verificar que el limitador rastrea la IP cliente real `203.0.113.195`.

---

## 5. 📚 El Rincón del Estudiante

### ¿Por qué proteger un login con Rate Limiting?
Imagina que un atacante contrata una máquina que prueba 50 contraseñas por segundo. Con una lista de las 100.000 contraseñas más comunes de internet (como *"123456"*, *"password"*, *"arrendis2026"*), el atacante tardaría apenas media hora en entrar en la cuenta de cualquier usuario que haya elegido una clave débil.

El **Rate Limiting** es el portero de una discoteca exclusiva:
- Si entras con tu entrada, pasas inmediatamente.
- Si intentas colarte y te pillan 10 veces seguidas en menos de un minuto, el portero te dice: *"Te quedas fuera 60 segundos hasta que te calmes"*. Al reducir la velocidad de 50 intentos por segundo a 10 intentos por minuto, probar 100.000 combinaciones pasaría de tardar 30 minutos a tardar **casi 7 días ininterrumpidos**, haciendo que el ataque resulte completamente inviable para el delincuente.

### ¿Cómo funciona la Ventana Deslizante (Sliding Window Log)?
A diferencia de una ventana fija (que cuenta peticiones de 12:00 a 12:01 y se reinicia bruscamente a 0, permitiendo que un atacante lance 10 peticiones a las 12:00:59 y otras 10 a las 12:01:01), la **ventana deslizante** mira siempre hacia atrás exactamente los últimos 60 segundos desde el instante exacto actual.

```
                  Ventana de 60 segundos
             ┌──────────────────────────────┐
  ───●───●───┼──────●───●───●──────────●────┼───▶ Tiempo
    12:00:05 │   12:00:15       12:00:45    │   12:01:00 (Ahora)
 (Expiradas) │    (Se cuentan: 4 peticiones)│
```

### Código del Proyecto: Antes vs. Después en `backend/api/middleware/rate_limit.py`

#### 🔴 Enfoque Ingenuo Vulnerable a Fugas de Memoria (Memory Leak):
```python
# ⚠️ Almacén sin límite de tamaño: en un ataque DDoS con IPs falsificadas,
# este diccionario acumula millones de claves hasta colapsar el servidor (OOM Kill).
records = {}

def is_limited(ip):
    now = time.time()
    if ip not in records:
        records[ip] = []
    records[ip].append(now)  # Nunca se borran los viejos -> Memoria infinita
    return len(records[ip]) > 10
```

#### 🟢 Enfoque Blindado con Eviction y Desalojo LRU (Arrendis):
```python
# ✅ OrderedDict acotado a 10.000 entradas con purga activa de timestamps:
class InMemoryRateLimiter:
    def __init__(self, limit=10, window_seconds=60, max_keys=10000):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._records = OrderedDict()

    def is_rate_limited(self, key):
        # 1. Purgar marcas expiradas de la IP
        # 2. Comprobar si len >= 10
        # 3. Si _records supera 10.000 entradas, desaloja las IPs más antiguas (LRU)
        ...
```

### Comparativa: Con vs. Sin Rate Limiting F-40

| Vector de Riesgo | Sin F-40 (Estado Inicial) | Con F-40 (Blindaje Implementado) |
|---|---|---|
| **Ataque de Diccionario / Fuerza Bruta** | Ilimitados intentos por segundo contra `/api/auth/login`. | Bloqueado con HTTP 429 al superar 10 intentos por minuto por IP. |
| **Agotamiento de CPU en Bcrypt** | El hashing masivo de contraseñas satura los cores del servidor. | El servidor rechaza las peticiones abusivas en milisegundos antes de calcular el hash. |
| **Registro Masivo de Spam** | Un bot puede generar miles de usuarios falsos por segundo. | `/api/auth/register` throttled a 10 registros por minuto por IP. |
| **Consumo de Memoria RAM** | Riesgo de OOM si se acumulan IPs sin política de caducidad. | Diccionario acotado a 10.000 IPs con desalojo LRU automático. |
| **Impacto en Tests Unitarios** | Los tests de negocio podrían recibir 429 espurios al correr rápido. | Desactivado transparentemente si `TESTING=1`, activable con `FORCE_RATE_LIMIT=1`. |
