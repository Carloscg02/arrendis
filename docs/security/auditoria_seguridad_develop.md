# Informe de Auditoría de Ciberseguridad — Rama `develop`

**Proyecto:** Gestión de Alquileres (Rental Handler API / Arrendis)  
**Entorno auditado:** Rama `develop` (`/home/carlos/rental-handler`) y rama `feature/e-06-identidad-acceso`  
**Metodología:** OWASP Top 10:2025, OWASP API Security Top 10:2023, Strix Skillsets (`find-security-vulnerabilities-in-code`, `api-security-testing`)  
**Fecha de evaluación:** 5 y 6 de octubre de 2026  
**Auditor:** Antigravity Autonomous Security Agent  
**Estado General:** 🟢 **100% DE HALLAZGOS REMEDIADOS (7 de 7 resueltos y verificados con pruebas automatizadas)**

---

## 1. Resumen Ejecutivo

Se ha completado la auditoría exhaustiva de seguridad sobre la rama `develop` de la plataforma Arrendis, evaluando análisis estático de código fuente (SAST), pruebas dinámicas sobre API en memoria (DAST) y pruebas de penetración automatizadas (Pentesting).

Los **7 hallazgos detectados han sido completamente remediados y blindados** con pruebas de regresión en `tests/unit/backend/api/test_security_pentest.py`. La suite completa pasa al 100% (434 tests pasando en `develop`, 473 tests pasando en `feature/e-06-identidad-acceso`).

### Resumen de Hallazgos por Severidad

| Severidad | Total Detectados | Estado Actual | Verificación |
| :--- | :---: | :---: | :--- |
| 🔴 **Crítica** | 1 | 🟢 **1 Resuelta** | Pentest automatizado pasando |
| 🟠 **Alta** | 2 | 🟢 **2 Resueltas** | Pentest automatizado pasando |
| 🟡 **Media** | 2 | 🟢 **2 Resueltas** | Pentest automatizado pasando |
| 🔵 **Baja / Informativa** | 2 | 🟢 **2 Resueltas** | Pentest automatizado pasando |
| **TOTAL** | **7** | 🟢 **7 Resueltas (100%)** | **0 Regresiones en la suite** |

---

## 2. Matriz de Hallazgos

| ID | Severidad | Categoría OWASP | Componente Afectado | Vulnerabilidad | Estado |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **SEC-01** | 🔴 **Crítica** | A02:2021 Cryptographic Failures / A07:2021 Auth | `backend/adapters/auth_adapter.py` + `dependencies.py` | Clave secreta JWT predeterminada (`dev-secret-key-change-in-production`) no sobreescrita por variables de entorno en producción. | 🟢 Resuelta |
| **SEC-02** | 🟠 **Alta** | A01:2021 Broken Access Control / A07:2021 Auth | `backend/adapters/auth_adapter.py` + `ports.py` + `use_cases.py` | Confusión de tipo de token: los Refresh Tokens (vida útil 7 días) eran aceptados en endpoints como Access Tokens. | 🟢 Resuelta |
| **SEC-03** | 🟠 **Alta** | A05:2021 Security Misconfiguration | `backend/api/main.py` | Configuración CORS permisiva con credenciales sobre comodín multinquilino (`*.pages.dev`). | 🟢 Resuelta |
| **SEC-04** | 🟡 **Media** | A04:2021 Insecure Design / API4:2023 Rate Limit | `backend/api/middleware/rate_limit.py` | Evasión de limitador de tasa mediante cabecera `X-Forwarded-For` arbitraria (IP Spoofing). | 🟢 Resuelta |
| **SEC-05** | 🟡 **Media** | A02:2021 Cryptographic Failures / Webhooks | `backend/api/routes/webhooks.py` | Secreto de webhook predeterminado y comparación no resistente a ataques de temporización (`!=`). | 🟢 Resuelta |
| **SEC-06** | 🔵 **Baja** | API4:2023 Unrestricted Resource Consumption | `backend/api/routes/expenses.py` + `webhooks.py` | Falta de límite de tamaño en subida de facturas PDF en memoria (`await file.read()`). | 🟢 Resuelta |
| **SEC-07** | 🔵 **Baja** | A08:2021 Software and Data Integrity Failures | `backend/api/routes/properties.py` | Validación de imágenes dependiente únicamente de la cabecera `Content-Type` sin comprobar magic bytes. | 🟢 Resuelta |

---

## 3. Detalle de Vulnerabilidades y Resoluciones Aplicadas

### SEC-01: Clave secreta JWT predeterminada y falsificación de tokens (🔴 Crítica) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
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
  4. Se añadieron pruebas de pentesting en `tests/unit/backend/api/test_security_pentest.py` (`test_pentest_jwt_secret_configured_rejects_default_dev_secret` y `test_pentest_jwt_service_blocks_default_secret_in_production`).

---

### SEC-02: Confusión de tipo de Token / Scope Bypassed (🟠 Alta) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
- **Ubicación:** `backend/adapters/auth_adapter.py`, `backend/domain/ports.py`, `backend/application/use_cases.py` y `backend/api/dependencies.py`
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
  5. Se añadió la prueba de pentesting `test_pentest_token_type_confusion_rejection` demostrando que un refresh token en `Authorization: Bearer` es rechazado con **HTTP 401**, y un access token en la cookie `/api/auth/refresh` también es rechazado con **HTTP 401**.

---

### SEC-03: CORS permisivo sobre dominio multinquilino con credenciales (🟠 Alta) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
- **Ubicación:** `backend/api/main.py:80-105`
- **Mecánica original:**
  `allow_origin_regex=r"^https://.*\.arrendis\.(com|es)$|^https://.*\.pages\.dev$"` con `allow_credentials=True`.
  Cualquier persona puede publicar un sitio gratuito en Cloudflare Pages (`https://atacante.pages.dev`). Al estar permitido el comodín con credenciales, la web del atacante podía consultar la API y leer datos privados de cualquier víctima autenticada.
- **Impacto:** Robo de información de sesión y datos personales mediante ataques CSRF/CORS cross-origin.
- **Resolución aplicada:**
  1. Se acotó el regex en `main.py` para permitir únicamente los subdominios legítimos del proyecto en Cloudflare Pages:
     `r"^https://([a-zA-Z0-9-]+\.)*arrendis\.(com|es)$|^https://(arrendis|rental-handler)(-[a-zA-Z0-9]+)?\.pages\.dev$"`
  2. Se añadió soporte para orígenes dinámicos autorizados mediante la variable `CORS_ALLOWED_ORIGINS`.
  3. Se añadió la prueba `test_pentest_cors_rejects_unauthorized_pages_dev` en `test_security_pentest.py`, confirmando que orígenes como `https://evil-attacker.pages.dev` no reciben cabecera `Access-Control-Allow-Origin`, mientras que `https://rental-handler.pages.dev` y `https://app.arrendis.com` son autorizados correctamente.

---

### SEC-04: Evasión de Rate Limiting por Spoofing de IP (🟡 Media) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
- **Ubicación:** `backend/api/middleware/rate_limit.py:179-215`
- **Mecánica original:**
  `_get_client_ip` tomaba ciegamente el valor de `X-Forwarded-For` enviado por cualquier cliente sin comprobar si la conexión directa provenía de un proxy inverso confiable.
- **Impacto:** En un ataque de fuerza bruta contra `/api/auth/login`, el atacante solo necesitaba enviar una cabecera `X-Forwarded-For` distinta en cada intento para resetear el límite de 10 peticiones/minuto.
- **Resolución aplicada:**
  1. `_get_client_ip` ahora extrae primero la IP de conexión TCP directa (`scope["client"][0]`).
  2. Solo interpreta `CF-Connecting-IP` o `X-Forwarded-For` si la conexión directa proviene de un proxy confiable (localhost, subredes de proxy configuradas en `TRUSTED_PROXIES` o si `TRUST_PROXY_HEADERS=true`).
  3. Si un cliente directo no confiable envía `X-Forwarded-For`, la cabecera es ignorada y se aplica el límite sobre su IP directa real.
  4. Se añadió la prueba `test_pentest_rate_limit_spoofed_x_forwarded_for_from_untrusted_client` confirmando que intentos con IPs rotadas en `X-Forwarded-For` desde un cliente no confiable son bloqueados con **HTTP 429 Too Many Requests**.

---

### SEC-05: Secreto por defecto y vulnerabilidad a Timing Attacks en Webhook (🟡 Media) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
- **Ubicación:** `backend/api/routes/webhooks.py:38-60`
- **Mecánica original:**
  Si no se definía `INBOUND_WEBHOOK_SECRET` en producción, se aceptaba el secreto de desarrollo conocido (`dev-inbound-secret`). Además, la comparación `!=` clásica de strings era vulnerable a ataques de temporización (timing attacks).
- **Impacto:** Ingesta no autorizada de facturas o inferencia de caracteres del secreto por análisis de latencia.
- **Resolución aplicada:**
  1. Se implementó comparación en tiempo constante usando `secrets.compare_digest(x_webhook_secret, configured_secret)`.
  2. En entornos `production` o `staging`, el webhook exige que `INBOUND_WEBHOOK_SECRET` esté configurado y no sea el secreto de desarrollo, respondiendo con `HTTP 503` en caso contrario.
  3. Se añadió la prueba `test_pentest_webhook_secret_constant_time_and_production_protection` validando tanto el rechazo con 401 de secretos erróneos como el bloqueo con 503 ante configuraciones inseguras en producción.

---

### SEC-06: Falta de límite de tamaño en subida de facturas (🔵 Baja) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
- **Ubicación:** `backend/api/routes/expenses.py:45-60, 145-175` y `backend/api/routes/webhooks.py:50-70`
- **Mecánica original:**
  `await file.read()` leía ficheros arbitrariamente grandes en memoria sin límite de bytes, permitiendo ataques de denegación de servicio por agotamiento de RAM (OOM Crash).
- **Impacto:** Subidas maliciosas de ficheros gigantes (>500MB) podían provocar la caída del proceso Uvicorn.
- **Resolución aplicada:**
  1. Se implementó la función auxiliar `_read_bounded_invoice_file` que lee únicamente hasta `MAX_INVOICE_FILE_SIZE + 1` bytes (10 MB por defecto, configurable mediante variable de entorno).
  2. Si el fichero supera el límite, se corta la lectura de inmediato y se retorna **HTTP 413 (Content Too Large)** sin volcar el contenido completo en la memoria del servidor.
  3. Se aplicó tanto a subidas individuales (`/api/expenses/upload-invoice`), como a lotes (`/api/expenses/upload-invoices`) y adjuntos de webhooks.
  4. Se añadió la prueba `test_pentest_oversized_pdf_upload_rejected_413` confirmando el rechazo inmediato con HTTP 413.

---

### SEC-07: Validación superficial de tipo de fichero en imágenes (🔵 Baja) — [🟢 RESUELTA]

- **Estado:** 🟢 **Resuelta**. Parcheada y blindada con tests de pentesting.
- **Ubicación:** `backend/api/routes/properties.py:215-255`
- **Mecánica original:**
  La validación dependía exclusivamente de la cabecera enviada por el cliente `file.content_type in ["image/jpeg", "image/png"]`, permitiendo subir scripts o binarios ejecutables simplemente cambiando la cabecera MIME.
- **Impacto:** Potencial evasión de filtros y subida de archivos maliciosos disfrazados de imágenes.
- **Resolución aplicada:**
  1. Se implementó `_validate_image_magic_bytes(content: bytes)` que comprueba los primeros bytes del archivo (firmas binarias / magic bytes):
     - JPEG: `\xFF\xD8\xFF`
     - PNG: `\x89PNG\r\n\x1a\n`
  2. La extensión final del archivo guardado en disco (`.jpg` o `.png`) se determina a partir de la firma binaria validada, nunca de la cabecera del cliente.
  3. Se añadió lectura acotada de memoria (máximo 5 MB) con respuesta HTTP 413 si se excede.
  4. Se añadió la prueba `test_pentest_image_upload_content_type_spoofing_rejected` verificando que scripts o contenidos no binarios con cabecera `image/jpeg` son rechazados con **HTTP 400 Bad Request** ("Firma de archivo inválida").

---

## 4. Controles de Seguridad Positivos Validados

Durante la auditoría también se confirmaron múltiples controles de seguridad nativos implementados con rigor:

1. **Prevención de Inyección SQL:** Todas las consultas en `backend/adapters/sqlite_adapter.py` emplean consultas parametrizadas con marcadores `?`. No se hallaron concatenaciones directas en DML.
2. **Control de Acceso Objeto a Objeto (Anti-IDOR / BOLA):**
   - Las consultas de propiedades, contratos, gastos e ingresos filtran estrictamente por `user_id = current_user.id`.
   - Los endpoints de borrado (`delete_expense`, `delete_income`, `delete_property`) verifican que el recurso pertenezca al usuario antes de proceder.
3. **Cabeceras HTTP Defensivas:** `SecurityHeadersMiddleware` aplica de forma consistente `nosniff`, `DENY` en `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy` y `Permissions-Policy`.
4. **Prevención de SSRF en Enriquecimiento de IA:** El resolvedor de redirecciones de Google Search Grounding (`backend/adapters/valuation/search_grounding.py`) restringe las peticiones únicamente a URLs que contienen `"grounding-api-redirect"` y deshabilita redirecciones automáticas arbitrarias.
5. **Aislamiento de CUPS en Webhooks:** El webhook de correo entrante restringe el CUPS extraído únicamente a las propiedades cuyo propietario coincide con el remitente autenticado.

---

## 5. Resultado Final y Estado de Verificación

Todas las vulnerabilidades identificadas en la auditoría inicial han sido completamente solventadas, aplicadas en ambas ramas de desarrollo (`develop` y `feature/e-06-identidad-acceso`), y cubiertas por una suite de pentesting automatizada permanente.

- **Suite de Pentesting (`test_security_pentest.py`):** 13/13 pruebas exitosas (0 fallos).
- **Suite global `develop` (`rental-handler`):** 434/434 pruebas exitosas (0 fallos).
- **Suite global `feature/e-06-identidad-acceso`:** 473/473 pruebas exitosas (0 fallos).
