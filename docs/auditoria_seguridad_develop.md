# Informe de Auditoría de Ciberseguridad — Rama `develop`

**Proyecto:** Gestión de Alquileres (Rental Handler API)  
**Entorno auditado:** Rama `develop` (`/home/carlos/rental-handler`)  
**Metodología:** OWASP Top 10:2025, OWASP API Security Top 10:2023, Strix Skillsets (`find-security-vulnerabilities-in-code`, `api-security-testing`)  
**Fecha de evaluación:** 5 de octubre de 2026  
**Auditor:** Antigravity Autonomous Security Agent  

---

## 1. Resumen Ejecutivo

Se ha realizado una auditoría exhaustiva de seguridad sobre la rama `develop` de la plataforma de gestión de alquileres, evaluando tanto el análisis estático de código fuente (SAST) como pruebas dinámicas sobre la API FastAPI montada en memoria (DAST).

### Resumen de Hallazgos por Severidad

| Severidad | Total | Estado |
| :--- | :---: | :--- |
| 🔴 **Crítica** | 1 | Confirmado dinámicamente |
| 🟠 **Alta** | 2 | Confirmado dinámicamente |
| 🟡 **Media** | 2 | Confirmado dinámicamente |
| 🔵 **Baja / Informativa** | 2 | Verificado en código |

---

## 2. Matriz de Hallazgos

| ID | Severidad | Categoría OWASP | Componente Afectado | Vulnerabilidad | Estado |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **SEC-01** | 🔴 **Crítica** | A02:2021 Cryptographic Failures / A07:2021 Auth | `backend/adapters/auth_adapter.py` + `dependencies.py` | Clave secreta JWT predeterminada (`dev-secret-key-change-in-production`) no sobreescrita por variables de entorno en producción. | 🟢 Resuelta |
| **SEC-02** | 🟠 **Alta** | A01:2021 Broken Access Control / A07:2021 Auth | `backend/adapters/auth_adapter.py` | Confusión de tipo de token: los Refresh Tokens (vida útil 7 días) son aceptados como Access Tokens. | 🟢 Resuelta |
| **SEC-03** | 🟠 **Alta** | A05:2021 Security Misconfiguration | `backend/api/main.py` | Configuración CORS permisiva con credenciales sobre comodín multinquilino (`*.pages.dev`). | ⏳ Pendiente |
| **SEC-04** | 🟡 **Media** | A04:2021 Insecure Design / API4:2023 Rate Limit | `backend/api/middleware/rate_limit.py` | Evasión de limitador de tasa mediante cabecera `X-Forwarded-For` arbitraria (IP Spoofing). | ⏳ Pendiente |
| **SEC-05** | 🟡 **Media** | A02:2021 Cryptographic Failures / Webhooks | `backend/api/routes/webhooks.py` | Secreto de webhook predeterminado y comparación no resistente a ataques de temporización (`!=`). | ⏳ Pendiente |
| **SEC-06** | 🔵 **Baja** | API4:2023 Unrestricted Resource Consumption | `backend/api/routes/expenses.py` | Falta de límite de tamaño en subida de facturas PDF en memoria (`await file.read()`). | ⏳ Pendiente |
| **SEC-07** | 🔵 **Baja** | A08:2021 Software and Data Integrity Failures | `backend/api/routes/properties.py` | Validación de imágenes dependiente únicamente de la cabecera `Content-Type` sin comprobar magic bytes. | ⏳ Pendiente |

---

## 3. Detalle de Vulnerabilidades y Pruebas de Verificación

### SEC-01: Clave secreta JWT predeterminada y falsificación de tokens (🔴 Crítica) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentest automatizados.
- **Ubicación:** `backend/adapters/auth_adapter.py:19` y `backend/api/dependencies.py:81`
- **Mecánica original:**
  En `auth_adapter.py`, el constructor `JWTTokenServiceAdapter` definía una clave por defecto, y `dependencies.py` nunca leía `os.getenv("JWT_SECRET")` ni `os.getenv("JWT_SECRET_KEY")`.
- **Impacto:** Cualquier atacante externo podía generar tokens falsificados con la clave fija de desarrollo y acceder como cualquier usuario sin credenciales.
- **Resultado de la prueba dinámica original:**
  > Se forjó un token JWT con `sub = <id_usuario_real>` usando la clave por defecto. La petición a `GET /api/auth/me` respondió con **HTTP 200 OK** y devolvió los datos del usuario.
- **Resolución aplicada:**
  1. `get_token_service()` en `dependencies.py` y `auth_adapter.py` ahora leen de forma prioritaria `JWT_SECRET` (y `JWT_SECRET_KEY`) desde el entorno.
  2. En entornos `production` o `staging`, el servidor valida obligatoriamente que la clave esté configurada y no sea la de desarrollo, abortando con `RuntimeError` en caso de omisión.
  3. Se inyectó `ENVIRONMENT=production` automáticamente en `cicd/docker-compose.prod.yml`.
  4. Se añadieron pruebas de pentesting en `tests/unit/backend/api/test_security_pentest.py` que verifican el rechazo de tokens forjados con la clave de desarrollo (429/429 tests pasando).

---

### SEC-02: Confusión de tipo de Token / Scope Bypassed (🟠 Alta) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentest automatizados.
- **Ubicación:** `backend/adapters/auth_adapter.py:44`, `backend/domain/ports.py:197`, `backend/application/use_cases.py:396` y `backend/api/dependencies.py:102`
- **Mecánica original:**
  El método `verify_token` decodificaba el token pero solo extraía `payload.get("sub")`. No validaba si el claim `"type"` era `"access"` o `"refresh"`.
- **Impacto:** Los tokens de refresco (diseñados para viajar solo en cookies HTTP-only a `/api/auth/refresh` y válidos durante 7 días) podían ser usados en la cabecera `Authorization: Bearer <refresh_token>` en cualquier ruta de la API, ampliando la ventana de exposición en caso de filtración de tokens.
- **Resultado de la prueba dinámica original:**
  > Se envió un `refresh_token` generado por el sistema como cabecera `Authorization: Bearer <refresh_token>` a `GET /api/auth/me`. La API lo aceptó con **HTTP 200 OK**.
- **Resolución aplicada:**
  1. Se añadió el parámetro `expected_type: str = "access"` a la interfaz `TokenServicePort.verify_token(...)` y su implementación `JWTTokenServiceAdapter`.
  2. Si `expected_type` no coincide exactamente con `payload.get("type")`, `verify_token` retorna `None` inmediatamente (rechazo seguro).
  3. `RefreshTokenUseCase` valida obligatoriamente `expected_type="refresh"`.
  4. `GetCurrentUserUseCase` y la dependencia FastAPI `get_current_user` validan obligatoriamente `expected_type="access"`.
  5. Se añadió la prueba de pentesting `test_pentest_token_type_confusion_rejection` en `tests/unit/backend/api/test_security_pentest.py` demostrando que un refresh token en `Authorization: Bearer` es rechazado con **HTTP 401**, y un access token en la cookie `/api/auth/refresh` también es rechazado con **HTTP 401**. (429/429 tests en develop y 469/469 en e-06 pasando).

---

### SEC-03: CORS permisivo sobre dominio multinquilino con credenciales (🟠 Alta)

- **Ubicación:** `backend/api/main.py:92-96`
- **Mecánica:**
  ```python
  allow_origin_regex=r"^https://.*\.arrendis\.(com|es)$|^https://.*\.pages\.dev$",
  allow_credentials=True,
  ```
  `*.pages.dev` es un dominio público compartido de Cloudflare Pages. Cualquier usuario en el mundo puede desplegar un sitio web gratuito bajo `https://nombre-aleatorio.pages.dev`.
- **Impacto:** Un atacante puede alojar un sitio web en `https://attacker.pages.dev` y realizar peticiones `fetch()` con `credentials: "include"` contra la API de Arrendis. Dado que la cabecera `Access-Control-Allow-Origin` refleja el origen atacante y `Access-Control-Allow-Credentials: true` está habilitado, el navegador del usuario víctima compartirá cookies de sesión y permitirá al atacante leer respuestas privadas.
- **Resultado de la prueba dinámica:**
  > Petición con `Origin: https://evil-attacker.pages.dev` devolvió:
  > `Access-Control-Allow-Origin: https://evil-attacker.pages.dev`
  > `Access-Control-Allow-Credentials: true`
- **Remediación:**
  Restringir el regex únicamente a los subdominios legítimos del proyecto en Cloudflare Pages:
  ```python
  allow_origin_regex=r"^https://.*\.arrendis\.(com|es)$|^https://rental-handler-[a-z0-9]+\.pages\.dev$",
  ```

---

### SEC-04: Evasión de Rate Limiting por Spoofing de IP (🟡 Media)

- **Ubicación:** `backend/api/middleware/rate_limit.py:179-188`
- **Mecánica:**
  ```python
  def _get_client_ip(self, scope: Scope) -> str:
      headers = dict(scope.get("headers", []))
      x_forwarded_for = headers.get(b"x-forwarded-for")
      if x_forwarded_for:
          ip_str = x_forwarded_for.decode("latin1").split(",")[0].strip()
          if ip_str:
              return ip_str
      client = scope.get("client")
      return client[0] if client else "127.0.0.1"
  ```
  Se confía ciegamente en el valor proporcionado por el cliente en `X-Forwarded-For` sin verificar si la conexión directa proviene de un proxy inverso de confianza (reverse proxy).
- **Impacto:** En un ataque de fuerza bruta contra `/api/auth/login`, el atacante solo necesita alterar el valor de `X-Forwarded-For` en cada intento para resetear el contador de la ventana deslizante por IP, anulando el límite de 10 peticiones/minuto.
- **Resultado de la prueba dinámica:**
  > Se enviaron 15 intentos consecutivos de login variando la cabecera `X-Forwarded-For: 203.0.113.i`. Ninguno fue bloqueado con HTTP 429; todos respondieron 401.
- **Remediación:**
  Obtener la IP de la conexión TCP directa (`scope["client"]`) por defecto, y solo interpretar `X-Forwarded-For` (o `CF-Connecting-IP`) si la IP del cliente directo pertenece a un CIDR de proxy confiable (e.g. Cloudflare / Nginx interno).

---

### SEC-05: Secreto por defecto y vulnerabilidad a Timing Attacks en Webhook (🟡 Media)

- **Ubicación:** `backend/api/routes/webhooks.py:38-43`
- **Mecánica:**
  ```python
  configured_secret = os.getenv("INBOUND_WEBHOOK_SECRET", "dev-inbound-secret")
  if configured_secret and x_webhook_secret != configured_secret:
      raise HTTPException(status_code=401, ...)
  ```
- **Impacto:** Si la variable no se define en producción, se acepta el secreto de desarrollo conocido. Además, la comparación `!=` estándar entre cadenas es susceptible a ataques de temporización (timing attacks).
- **Remediación:**
  ```python
  import hmac
  configured_secret = os.getenv("INBOUND_WEBHOOK_SECRET")
  if not configured_secret or not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, configured_secret):
      raise HTTPException(status_code=401, detail="No autorizado")
  ```

---

### SEC-06: Falta de límite de tamaño en subida de facturas (🔵 Baja)

- **Ubicación:** `backend/api/routes/expenses.py:133, 155`
- **Mecánica:**
  `pdf_bytes = await file.read()` lee el fichero completo a memoria sin verificar previamente el tamaño ni limitar la lectura en streaming.
- **Impacto:** Subidas de ficheros gigantescos (>500MB) pueden provocar agotamiento de memoria (OOM crash) en el proceso de Uvicorn.
- **Remediación:**
  Establecer un límite estricto (ej. 15 MB) antes de procesar el buffer en memoria.

---

### SEC-07: Validación superficial de tipo de fichero en imágenes (🔵 Baja)

- **Ubicación:** `backend/api/routes/properties.py:230`
- **Mecánica:**
  Solo se evalúa `file.content_type in ["image/jpeg", "image/png"]`. Esta cabecera es declarada por el cliente y no garantiza que el contenido sea una imagen real.
- **Impacto:** Permite subir ficheros con contenido malicioso bajo extensión `.png` o `.jpg`. Si bien `nosniff` mitiga la ejecución, es una buena práctica verificar los magic bytes del archivo.

---

## 4. Controles de Seguridad Positivos Validados

Durante la auditoría también se confirmaron múltiples controles de seguridad implementados con rigor:

1. **Prevención de Inyección SQL:** Todas las consultas en `backend/adapters/sqlite_adapter.py` emplean consultas parametrizadas con marcadores `?`. No se hallaron concatenaciones directas en DML.
2. **Control de Acceso Objeto a Objeto (Anti-IDOR / BOLA):**
   - Las consultas de propiedades, contratos, gastos e ingresos filtran estrictamente por `user_id = current_user.id`.
   - Los endpoints de borrado (`delete_expense`, `delete_income`, `delete_property`) verifican que el recurso pertenezca al usuario antes de proceder.
3. **Cabeceras HTTP Defensivas:** `SecurityHeadersMiddleware` aplica de forma consistente `nosniff`, `DENY` en `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy` y `Permissions-Policy`.
4. **Prevención de SSRF en Enriquecimiento de IA:** El resolvedor de redirecciones de Google Search Grounding (`backend/adapters/valuation/search_grounding.py`) restringe las peticiones únicamente a URLs que contienen `"grounding-api-redirect"` y deshabilita redirecciones automáticas arbitrarias.
5. **Aislamiento de CUPS en Webhooks:** El webhook de correo entrante restringe el CUPS extraído únicamente a las propiedades cuyo propietario coincide con el remitente autenticado.

---

## 5. Plan de Remediación Priorizado

1. **Inmediato (P0):**
   - Modificar `get_token_service()` para inyectar `JWT_SECRET_KEY` desde entorno y validar `expected_type="access"` en `verify_token()`.
   - Ajustar el regex de CORS para eliminar el comodín `^https://.*\.pages\.dev$`.
2. **A corto plazo (P1):**
   - Asegurar el webhook con `hmac.compare_digest` y exigir que `INBOUND_WEBHOOK_SECRET` sea obligatorio en entornos no locales.
   - Ajustar la resolución de IP en `RateLimitMiddleware` para evitar spoofing vía `X-Forwarded-For`.
3. **Mantenimiento (P2):**
   - Añadir límite de tamaño a las subidas de PDFs en `expenses.py`.
   - Añadir comprobación de magic bytes en la subida de imágenes.
