# 📐 Especificación Técnica: F-39
# Cabeceras HTTP de Seguridad, Cookies Seguras de Producción y Endpoint de Salud (/api/health)

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Revisado con Enmiendas Arquitectónicas  
> **Fecha:** 2026-10-03  
> **Autor:** Tech Lead & Orquestador Arrendis  

---

## 1. Contexto y Delimitación de Alcance

### 1.1. Contexto
Arrendis se prepara para su puesta en producción comercial (General Availability). Como parte de las auditorías automatizadas del toolkit `pre-launch`, se identificaron tres vectores de vulnerabilidad y deuda técnica en la capa de transporte y red:
1. **Falta de cabeceras HTTP de seguridad:** Las respuestas del backend en FastAPI no inyectan cabeceras estándar de protección de navegador (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `HSTS`), dejando la plataforma expuesta a ataques de MIME-sniffing, clickjacking y downgrade de protocolo.
2. **Cookies de sesión inseguras en producción:** La cookie `refresh_token` emitida en `/api/auth/login`, `/api/auth/register`, `/api/auth/refresh` y `/api/auth/logout` tiene el flag `secure=False` hardcodeado, lo que permitiría que navegadores la transmitan en texto plano sobre HTTP no cifrado en entornos públicos.
3. **Ausencia de sonda de salud (Health Check):** Los orquestadores de despliegue, balanceadores y herramientas de uptime (Cloudflare, Docker healthcheck, Uptime Kuma) no disponen de una ruta `/api/health` ligera para monitorizar el estado del servidor y la conexión a la base de datos sin requerir autenticación JWT.
4. **Falsos positivos de secretos en documentación:** La documentación técnica (`docs/plan_cicd_produccion.md` y `specs/F-24/plan_cicd_produccion.md`) contiene cadenas de ejemplo con encabezados de clave privada que activan alertas de severidad `BLOCKER` en escáneres estáticos de secretos.

### 1.2. Delimitación (Qué entra y qué NO entra)
- **✅ ENTRA:**
  - Middleware ASGI puro `SecurityHeadersMiddleware` para inyectar cabeceras OWASP recomendadas en toda respuesta HTTP (incluyendo códigos de error 404/500) sin interferir con fuentes externas (Google Fonts), Vite HMR ni endpoints de la API.
  - Activación condicional de `Strict-Transport-Security` (HSTS) en entornos de producción y pre-producción (`ENVIRONMENT` en `"production"`, `"staging"` o `FORCE_HSTS="1"`).
  - Parametrización dinámica del flag `secure` en cookies de refresco (`backend/api/routes/auth.py`), tanto al establecerla como al eliminarla en `/logout`, activándose cuando `ENVIRONMENT` esté en `("production", "staging")` o `COOKIE_SECURE=true`.
  - Método hexagonal `check_health() -> bool` en el adaptador `SQLiteConnection`.
  - Endpoint `/api/health` desacoplado que invoca `db.check_health()`, sin requerir autenticación, retornando estado 200 OK con payload `HealthResponse` o 503 Service Unavailable con `HealthDegradedResponse`.
  - Sanitización de los falsos positivos de claves privadas en la documentación técnica respetando la *Placeholder Discipline*.
  - Suite de tests automatizados en `tests/unit/backend/api/test_f39_security_and_health.py`.
- **❌ NO ENTRA:**
  - Rate limiting contra fuerza bruta (asignado a F-40).
  - Páginas legales y compliance RGPD (asignado a F-41).
  - Gestión de roles de usuario o flags `is_active` (asignado a E-06).

---

## 2. Lenguaje Ubicuo

| Término | Definición Formal en el Dominio |
|---|---|
| **Security Headers** | Conjunto de directivas HTTP enviadas por el servidor en las respuestas para obligar al navegador del cliente a restringir comportamientos inseguros (ej. sniffing de tipos, incrustación en iframes). |
| **MIME Sniffing** | Vulnerabilidad donde el navegador intenta adivinar el tipo MIME de un archivo ignorando la cabecera `Content-Type`, lo que puede llevar a ejecución de scripts maliciosos. Mitigado por `X-Content-Type-Options: nosniff`. |
| **Clickjacking** | Técnica de engaño visual donde una página web maliciosa incrusta a Arrendis dentro de un `<iframe>` invisible para secuestrar clics del usuario. Mitigado por `X-Frame-Options: DENY`. |
| **HSTS (HTTP Strict Transport Security)** | Cabecera que ordena a los navegadores recordar que el dominio SOLO debe ser visitado mediante HTTPS cifrado, impidiendo ataques Man-in-the-Middle (MitM) de degradación SSL/TLS. |
| **Secure Cookie Flag** | Atributo de directiva `Set-Cookie` que prohíbe taxativamente al navegador enviar la cookie a través de conexiones HTTP no cifradas. |
| **Liveness & Readiness Probe** | Endpoint no autenticado (`/api/health`) que permite a los sistemas de infraestructura verificar la vitalidad del proceso y su capacidad inmediata para atender tráfico validando dependencias críticas (SQLite). |
| **Placeholder Discipline** | Norma de ingeniería que prohíbe taxativamente escribir patrones sintácticos literales de credenciales o certificados en documentación o código, utilizando marcadores ofuscados para prevenir alarmas en herramientas SAST. |

---

## 3. Diseño Técnico Detallado

### 3.1. Middleware ASGI de Cabeceras de Seguridad (`SecurityHeadersMiddleware`)
Ubicación: `backend/api/middleware/security.py`.  
Se utiliza un middleware ASGI puro que intercepta el mensaje `http.response.start` para mutar las cabeceras HTTP de respuesta sin la penalización de rendimiento de `BaseHTTPMiddleware`:

```python
import os
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

                env = os.getenv("ENVIRONMENT", "").lower()
                force_hsts = os.getenv("FORCE_HSTS", "") == "1"
                if env in ("production", "staging") or force_hsts:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            await send(message)

        await self.app(scope, receive, send_with_security_headers)
```

> **Compatibilidad con Vite y Google Fonts:**  
> No se inyecta una directiva CSP restrictiva a nivel de FastAPI en esta fase. Como se comprobó en `frontend/index.html`, el proyecto consume Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) y módulos Vite (`main.tsx`). La directiva CSP estricta se delegará al proxy inverso (Caddy/Cloudflare), garantizando que las cabeceras de aplicación no rompan Vite HMR, estilos ni fuentes tipográficas.

### 3.2. Adaptador Hexagonal: Comprobación de Salud en `SQLiteConnection`
Ubicación: `backend/adapters/sqlite_adapter.py`.  
Para respetar el principio de Arquitectura Hexagonal y no exponer sentencias SQL (`SELECT 1`) en la capa de transporte HTTP (routers de FastAPI), se dota a `SQLiteConnection` de un método de sondeo de salud:

```python
def check_health(self) -> bool:
    """Verifica la conectividad activa con la base de datos SQLite."""
    try:
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        return row is not None and row[0] == 1
    except Exception:
        return False
```

### 3.3. Endpoint de Salud `/api/health` y Schemas Pydantic
Ubicación: `backend/api/schemas.py` y `backend/api/routes/health.py`.

#### Schemas Pydantic (`backend/api/schemas.py`):
```python
class HealthResponse(BaseModel):
    status: str = "healthy"
    database: str = "connected"
    version: str = "0.1.0"

class HealthDegradedResponse(BaseModel):
    status: str = "degraded"
    database: str = "disconnected"
    error: str
```

#### Router `/api/health` (`backend/api/routes/health.py`):
```python
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from backend.adapters.sqlite_adapter import SQLiteConnection
from backend.api.dependencies import get_db
from backend.api.schemas import HealthResponse, HealthDegradedResponse

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get(
    "",
    response_model=HealthResponse,
    responses={
        200: {"model": HealthResponse},
        503: {"model": HealthDegradedResponse},
    },
)
def get_health(db: SQLiteConnection = Depends(get_db)):
    is_healthy = db.check_health()
    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthDegradedResponse(
                status="degraded",
                database="disconnected",
                error="Database connectivity check failed",
            ).model_dump(),
        )
    return HealthResponse(status="healthy", database="connected", version="0.1.0")
```

### 3.4. Parametrización de Cookies Seguras en `auth.py`
En `backend/api/routes/auth.py`:
```python
def _is_cookie_secure() -> bool:
    env = os.getenv("ENVIRONMENT", "development").lower()
    cookie_secure_env = os.getenv("COOKIE_SECURE", "").lower()
    return env in ("production", "staging") or cookie_secure_env in ("true", "1", "yes")

def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_is_cookie_secure(),
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )
```
Y en el endpoint de logout:
```python
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
        httponly=True,
        secure=_is_cookie_secure(),
        samesite="lax",
    )
    return {"message": "Sesión cerrada correctamente"}
```

### 3.5. Sanitización de la Documentación CI/CD (Placeholder Discipline)
En los archivos:
- `docs/plan_cicd_produccion.md` (línea 54)
- `specs/F-24/plan_cicd_produccion.md` (línea 54)

Sustituir el patrón que dispara la alerta por una indicación descriptiva y segura:
```markdown
| `ORACLE_SSH_KEY` | El contenido de texto completo de tu archivo de clave privada `.key` (abierto con bloc de notas o editor de texto, incluyendo los bloques delimitadores de inicio y fin de la clave privada). |
```

---

## 4. Plan de Pruebas y Verificación

### 4.1. Tests Unitarios e Integración (`tests/unit/backend/api/test_f39_security_and_health.py`)
1. `test_security_headers_present_on_200_ok`:
   - Realizar una petición a `/api/health`.
   - Verificar `X-Content-Type-Options == "nosniff"`.
   - Verificar `X-Frame-Options == "DENY"`.
   - Verificar `Referrer-Policy == "strict-origin-when-cross-origin"`.
   - Verificar `Permissions-Policy == "camera=(), microphone=(), geolocation=(), payment=()"`.
2. `test_security_headers_present_on_404_error`:
   - Realizar una petición a una ruta inexistente `/api/ruta_no_existente`.
   - Comprobar que incluso en respuestas 404 las cabeceras de seguridad se inyectan correctamente.
3. `test_hsts_header_in_production_environment`:
   - Con `ENVIRONMENT="production"` (o `FORCE_HSTS="1"`), verificar que `Strict-Transport-Security` está presente con `max-age=31536000; includeSubDomains`.
   - Con `ENVIRONMENT="development"` y `FORCE_HSTS="0"`, verificar que la cabecera no se inyecta.
4. `test_auth_cookie_secure_flag_dev_vs_prod`:
   - Con `ENVIRONMENT="development"`, registrarse/hacer login y verificar en `Set-Cookie` que no contiene `; Secure`.
   - Con `ENVIRONMENT="production"` o `COOKIE_SECURE="true"`, comprobar que `Set-Cookie` incluye `; Secure`.
5. `test_auth_logout_cookie_attributes`:
   - Ejecutar POST a `/api/auth/logout` y verificar que la cabecera `Set-Cookie` de borrado respeta `path="/api/auth"` y el flag `Secure` según el entorno.
6. `test_health_endpoint_without_auth`:
   - Realizar una petición GET a `/api/health` **sin** cabecera `Authorization`.
   - Verificar status code `200` y payload `{"status": "healthy", "database": "connected", "version": "0.1.0"}`.
7. `test_health_endpoint_degraded_when_db_down`:
   - Mockear `SQLiteConnection.check_health` para retornar `False`.
   - Realizar petición GET a `/api/health`.
   - Verificar status code `503` y payload `{"status": "degraded", "database": "disconnected", "error": "Database connectivity check failed"}`.

### 4.2. Verificación SAST y Toolkit Pre-launch
- Ejecutar: `python3 /home/carlos/pre-launch/scripts/cli.py audit-secrets /home/carlos/rental-launch-prep`
- Debe retornar: `findings_count: 0`, `blockers_count: 0`, `status: PASS`.

---

## 5. 📚 El Rincón del Estudiante

### ¿Por qué las cabeceras HTTP son el primer escudo de una aplicación web?
Imagina que envías una carta confidencial por correo postal dentro de un sobre transparente. Cualquiera que lo toque en el camino puede mirar a contraluz o manipular el contenido. Las cabeceras HTTP de seguridad son como los sellos de lacre y las marcas de agua oficiales que le dicen al mensajero (el navegador) exactamente cómo debe tratar el paquete y qué tiene estrictamente prohibido hacer.

### 1. `X-Content-Type-Options: nosniff`
- **La analogía del mundo real:** Vas a una farmacia y compras una botella etiquetada como "Agua Destilada". No quieres que el farmacéutico diga: *"Huele raro, creo que es jarabe para la tos, voy a cambiarle el tapón y tomármela"*. Quieres que confíe ciegamente en la etiqueta del fabricante.
- **En la web:** Sin esta cabecera, si un atacante sube una imagen con código JavaScript malicioso incrustado, un navegador antiguo podría decir *"Esto parece JavaScript en lugar de un PNG, voy a ejecutarlo"* (MIME sniffing). Con `nosniff`, el navegador está obligado a respetar estrictamente el `Content-Type` enviado por FastAPI.

### 2. `X-Frame-Options: DENY`
- **La analogía del mundo real:** Tienes una tienda física con escaparate de cristal. Un timador coloca un panel transparente idéntico justo delante de tu botón de alarma, pero con un cartel que dice *"Pulse aquí para ganar 100€"*. Cuando un cliente pulsa, en realidad está activando tu alarma. Esto es el **Clickjacking**.
- **En la web:** Si permites que tu aplicación se cargue dentro de una etiqueta `<iframe src="https://arrendis.com">` en un sitio malicioso, el atacante puede hacer la ventana invisible y colocar sus propios botones encima para que el usuario transfiera fondos o borre inmuebles sin darse cuenta. `DENY` prohíbe terminantemente incrustar Arrendis en cualquier frame.

### 3. Código del Proyecto: Antes vs. Después en `backend/api/routes/auth.py`

#### 🔴 Antes (Inseguro - Flag hardcodeado a `False`):
```python
# backend/api/routes/auth.py (Línea 26)
def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # ⚠️ Inseguro en producción: viaja en claro sobre redes Wi-Fi públicas
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )
```

#### 🟢 Después (Blindado y Dinámico según Entorno):
```python
# backend/api/routes/auth.py (Refactor F-39)
def _is_cookie_secure() -> bool:
    env = os.getenv("ENVIRONMENT", "development").lower()
    cookie_secure_env = os.getenv("COOKIE_SECURE", "").lower()
    return env in ("production", "staging") or cookie_secure_env in ("true", "1", "yes")

def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_is_cookie_secure(),  # ✅ True en prod/staging, False en localhost
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )
```

### 4. Código del Proyecto: Sonda Hexagonal de Salud en `backend/adapters/sqlite_adapter.py`

#### 🔴 Enfoque Acoplado Rechazado (SQL raw en capa HTTP):
```python
# ⚠️ Violación Arquitectónica: el router HTTP manipula SQL directamente
@router.get("/api/health")
def health(db = Depends(get_db)):
    cursor = db.connection.cursor()
    cursor.execute("SELECT 1")
    ...
```

#### 🟢 Enfoque Hexagonal Aprobado (Puerto y Adaptador):
```python
# backend/adapters/sqlite_adapter.py (Adaptador secundario)
def check_health(self) -> bool:
    try:
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        return row is not None and row[0] == 1
    except Exception:
        return False

# backend/api/routes/health.py (Adaptador primario HTTP desacoplado)
@router.get("")
def get_health(db: SQLiteConnection = Depends(get_db)):
    if not db.check_health():
        return JSONResponse(status_code=503, content={"status": "degraded", ...})
    return {"status": "healthy", "database": "connected", "version": "0.1.0"}
```

### Comparativa: Con vs. Sin Arquitectura de Seguridad F-39

| Vector de Riesgo | Sin F-39 (Estado Inicial) | Con F-39 (Blindaje Implementado) |
|---|---|---|
| **Ataque de Clickjacking** | Cualquier web externa puede cargar `/` o `/portfolio` en un iframe invisible. | El navegador bloquea la carga en iframes con error `X-Frame-Options: DENY`. |
| **Robo de Token de Refresco** | Si el usuario entra por HTTP, la cookie viaja en claro por la red. | El navegador rechaza enviar la cookie a menos que la conexión sea HTTPS estricto. |
| **Manejo de MIME Malicioso** | Los navegadores pueden reinterpretar respuestas y ejecutar scripts. | El navegador respeta el tipo de contenido exacto (`nosniff`). |
| **Monitorización de Uptime** | No hay forma limpia de chequear la base de datos sin token JWT. | `/api/health` responde en milisegundos con estado del servidor y SQLite. |
| **Auditoría CI/CD** | Escáneres de secretos fallan con `BLOCKER` por texto de ejemplo de clave RSA. | Cero alertas en auditorías de código abierto y cumplimiento SAST. |
