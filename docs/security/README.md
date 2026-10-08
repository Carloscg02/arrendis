# 🛡️ Centro de Ciberseguridad, Blindaje Web y Pentesting de Arrendis

Bienvenido al centro neurálgico de seguridad de **Arrendis (Rental Handler API)**.  
Este directorio reúne la documentación técnica, los fundamentos teóricos, los informes de auditoría y las instrucciones operativas necesarias para comprender cómo está blindada la plataforma y cómo cualquier agente de IA o ingeniero de software puede re-ejecutar, auditar y extender las pruebas de penetración (pentesting).

---

## 📑 Índice de Documentación de Seguridad

| Documento | Descripción | Estado |
| :--- | :--- | :---: |
| **[`README.md`](README.md)** | Este documento: Contexto evolutivo, capas de defensa y manual de pentesting para agentes. | 🟢 Activo |
| **[`seguridad_web_e04_launch_hardening.md`](seguridad_web_e04_launch_hardening.md)** | Especificación técnica y teoría de seguridad de la **Épica E-04 (Launch Readiness & Web Hardening)**: Cabeceras defensivas, cookies seguras, rate limiting y RGPD. | 🟢 Implementado |
| **[`auditoria_seguridad_develop.md`](auditoria_seguridad_develop.md)** | Informe exhaustivo de la auditoría y pentesting posterior sobre `develop`: Los 7 hallazgos (SEC-01 a SEC-07), su análisis dinámico y sus resoluciones aplicadas. | 🟢 100% Resuelto |

---

## 🏛️ Contexto y Evolución de la Seguridad en Arrendis

La seguridad de Arrendis no se construyó en un único paso improvisado, sino a través de **dos fases metodológicas complementarias** que culminaron en un blindaje de Defensa en Profundidad (*Defense-in-Depth*):

```
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 1: ÉPICA E-04 (Launch Readiness & Web Hardening)                 │
│                                                                        │
│  - Cabeceras defensivas OWASP (nosniff, DENY, CSP, Referrer, Perms)   │
│  - Cookies de refresco con flag Secure dinámico según entorno          │
│  - Sonda ligera de disponibilidad (/api/health)                       │
│  - Rate Limiting multinivel (Tier 1: Auth, Tier 2: Heavy, Tier 3: Global)
│  - Páginas de cumplimiento RGPD (/privacy, /terms) y aviso Early Access│
│  - Desindexación de rutas privadas en robots.txt y sitemap.xml         │
│  - Resiliencia de navegación (404 Atelier) y accesibilidad a11y        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   │ Verificación en develop
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 2: AUDITORÍA Y PENTESTING DINÁMICO EN DEVELOP (OWASP Top 10)     │
│                                                                        │
│  - Evaluación SAST + DAST con Skillsets de Pentesting Autónomo         │
│  - Descubrimiento de 7 vectores de riesgo (SEC-01 a SEC-07)            │
│  - Remediación aislada commit a commit en develop y ramas activas       │
│  - Creación de suite permanente de pentest (test_security_pentest.py)  │
│  - 100% de hallazgos mitigados con 0 regresiones en la suite global    │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Fase 1: Épica E-04 (Launch Readiness & Web Hardening)
El objetivo de la **Épica E-04** fue transformar Arrendis de un "prototipo funcional en desarrollo" a un producto con nivel de madurez apto para producción comercial (*General Availability*):
1. **Cabeceras HTTP de Seguridad ([`SecurityHeadersMiddleware`](file:///home/carlos/rental-handler/backend/api/middleware/security.py)):** Inyección automática de `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`, `Referrer-Policy: strict-origin-when-cross-origin` y `Permissions-Policy`.
2. **Cookies de Sesión Blindadas:** La cookie `refresh_token` conmuta automáticamente a `Secure=True` cuando el servidor detecta `ENVIRONMENT=production` o `COOKIE_SECURE=true`.
3. **Sonda de Salud Desacoplada ([`/api/health`](file:///home/carlos/rental-handler/backend/api/routes/health.py)):** Endpoint público sin autenticación que realiza un ping ultrarrápido a SQLite (`SELECT 1`) para monitorización externa (Cloudflare, Uptime Kuma, Docker).
4. **Protección contra Abuso y Fuerza Bruta ([`RateLimitMiddleware`](file:///home/carlos/rental-handler/backend/api/middleware/rate_limit.py)):** Limitación de tasa en memoria por ventana deslizante estructurada en 3 niveles (*Tiered Throttling*):
   - **Tier 1 (Autenticación sensible):** Máximo 10 req/min por IP en `/api/auth/login` y `/api/auth/register`.
   - **Tier 2 (Computación pesada de IA):** Máximo 30 req/min por IP en `/api/properties/{id}/valuation`.
   - **Tier 3 (Global API):** Máximo 100 req/min por IP para el resto de rutas `/api/*`.
5. **Cumplimiento Normativo y Legal RGPD:** Rutas públicas `/privacy` y `/terms` con tipografía editorial Atelier, adaptadas al marco de protección de datos de inmuebles, inquilinos e IRPF de la Unión Europea.

*Para consultar los fundamentos teóricos detallados y los ataques específicos que mitiga cada control, ver [`seguridad_web_e04_launch_hardening.md`](seguridad_web_e04_launch_hardening.md).*

---

### Fase 2: Auditoría y Pentesting Dinámico en `develop`
Una vez integrada la Épica E-04 en `develop`, se realizó una auditoría ofensiva simulando un atacante externo sin contexto previo (black-box y white-box) apoyada en los skillsets de seguridad (`api-security-testing`, `owasp-top-10-testing`, `find-security-vulnerabilities-in-code`).

La prueba identificó **7 hallazgos** que fueron categorizados, demostrados empíricamente con scripts dinámicos y remediados uno a uno:

| ID | Severidad | Vulnerabilidad Identificada | Remediación Aplicada |
| :--- | :---: | :--- | :--- |
| **SEC-01** | 🔴 Crítica | Clave secreta JWT predeterminada hardcodeada | Lectura obligatoria de `JWT_SECRET` / `JWT_SECRET_KEY` del entorno y bloqueo de arranque con `RuntimeError` en prod/staging. |
| **SEC-02** | 🟠 Alta | Confusión de tokens (Refresh token usable en endpoints de Access) | `verify_token` ahora exige `expected_type` ("access" o "refresh") y rechaza tokens cruzados con 401. |
| **SEC-03** | 🟠 Alta | CORS permisivo sobre comodín multinquilino `*.pages.dev` | Regex acotado exclusivamente a subdominios del proyecto (`rental-handler-*.pages.dev`, `arrendis*.pages.dev`, dominios `.com`/`.es`) y variable `CORS_ALLOWED_ORIGINS`. |
| **SEC-04** | 🟡 Media | Evasión de Rate Limiting mediante IP Spoofing (`X-Forwarded-For`) | `_get_client_ip` solo confía en cabeceras de proxy si la conexión directa proviene de un proxy inverso confiable (`TRUSTED_PROXIES` o `TRUST_PROXY_HEADERS`). |
| **SEC-05** | 🟡 Media | Secreto de Webhook por defecto y vulnerable a timing attacks | Comparación en tiempo constante con `secrets.compare_digest` y obligatoriedad de secreto seguro en entornos de producción. |
| **SEC-06** | 🔵 Baja | Subida de facturas PDF sin límite de tamaño en RAM | Función `_read_bounded_invoice_file` con corte en streaming (máx. 10 MB) que devuelve HTTP 413 sin saturar la memoria del servidor. |
| **SEC-07** | 🔵 Baja | Validación superficial de imágenes dependiente de cabecera MIME | Validación estricta por firmas binarias reales (*magic bytes* para JPEG `\xFF\xD8\xFF` y PNG `\x89PNG\r\n\x1a\n`) y derivación de extensión según contenido. |

*Para consultar los payloads de ataque, respuestas dinámicas y pruebas de regresión, ver [`auditoria_seguridad_develop.md`](auditoria_seguridad_develop.md).*

---

## 🧪 Guía para Agentes y Desarrolladores: Cómo Ejecutar el Pentesting

Si necesitas solicitar a otro agente de IA (o ejecutar tú mismo) una revisión o re-ejecución del pentesting en el repositorio, sigue esta guía estandarizada.

### 1. Ejecución Rápida de la Suite de Pentest Automatizado

El proyecto incluye una suite dedicada de pruebas de penetración automatizadas en [`tests/unit/backend/api/test_security_pentest.py`](file:///home/carlos/rental-handler/tests/unit/backend/api/test_security_pentest.py).

Ejecuta el siguiente comando desde la raíz del proyecto:

```bash
# Ejecutar exclusivamente la suite de pentesting automatizado
venv/bin/pytest tests/unit/backend/api/test_security_pentest.py -v
```

#### ¿Qué verifica cada uno de los 13 tests?
1. `test_pentest_sqli_login_payloads`: Inyecta 7 variantes de payloads SQLi (`' OR '1'='1`, `UNION SELECT`, `; DROP TABLE`) en `/api/auth/login` y valida que nunca se produzca un error 500 ni se filtren trazas o mensajes del driver SQLite.
2. `test_pentest_path_traversal_static_files`: Intenta saltar del directorio de imágenes mediante secuencias `../../../../etc/passwd` y caracteres codificados por URL (`%2e%2e%2f`), verificando que se devuelva 400/404 sin exponer archivos del sistema.
3. `test_pentest_xss_injection_in_auth_input`: Envía payloads XSS (`<script>`, `<svg onload>`, `javascript:`) en campos de registro y comprueba que la API responda estrictamente con `application/json` sin reflejar HTML ejecutable.
4. `test_pentest_jwt_tampering_rejection`: Prueba tokens con algoritmo `none`, firmas truncadas y caracteres aleatorios, verificando el rechazo unánime con HTTP 401.
5. `test_pentest_all_error_responses_have_security_headers`: Verifica que incluso ante errores 404, 401 y 405 se mantengan las cabeceras defensivas OWASP (`nosniff`, `DENY`, `CSP`, etc.).
6. `test_pentest_jwt_secret_configured_rejects_default_dev_secret`: Demuestra que un token forjado con la clave secreta por defecto de desarrollo es rechazado cuando hay una clave segura configurada.
7. `test_pentest_jwt_service_blocks_default_secret_in_production`: Comprueba que en entornos `production` o `staging` el servidor aborta el inicio con `RuntimeError` si falta la clave o se usa la predeterminada.
8. `test_pentest_token_type_confusion_rejection`: Comprueba que un `refresh_token` es rechazado si se envía como Bearer token en `/api/auth/me`, y que un `access_token` es rechazado si se envía como cookie a `/api/auth/refresh`.
9. `test_pentest_cors_rejects_unauthorized_pages_dev`: Simula un ataque cross-origin desde `https://evil-attacker.pages.dev` y valida que no se emita la cabecera `Access-Control-Allow-Origin`, mientras que subdominios del proyecto (`https://rental-handler.pages.dev` o `https://app.arrendis.com`) sí son autorizados.
10. `test_pentest_rate_limit_spoofed_x_forwarded_for_from_untrusted_client`: Conecta desde una IP no confiable rotando cabeceras `X-Forwarded-For` y demuestra que la protección por IP directa bloquea el ataque en el intento 11 con HTTP 429.
11. `test_pentest_webhook_secret_constant_time_and_production_protection`: Valida el rechazo con 401 ante secretos erróneos y la denegación con 503 ante configuraciones inseguras en producción.
12. `test_pentest_oversized_pdf_upload_rejected_413`: Intenta subir un archivo PDF de más de 10 MB a `/api/expenses/upload-invoice` y valida que se interrumpa la lectura devolviendo HTTP 413.
13. `test_pentest_image_upload_content_type_spoofing_rejected`: Intenta subir un script malicioso declarando `Content-Type: image/jpeg` y valida que el analizador de magic bytes lo rechace con HTTP 400 ("Firma de archivo inválida").

---

### 2. Ejecución de la Suite Completa de Tests de Regresión

Para certificar que ninguna remediación de seguridad o cambio en el código ha roto la lógica de negocio (tasaciones, cálculos fiscales, subidas de facturas, contratos, etc.):

```bash
# Ejecutar todos los tests unitarios y de integración
venv/bin/pytest tests/ -v
```

> **Nota técnica para agentes:**
> El fixture `client` de `test_security_pentest.py` y `test_f40_rate_limiting.py` ejecuta `default_rate_limiter.reset()` antes y después de cada test. Si agregas nuevas pruebas de API que hagan muchas peticiones consecutivas, asegúrate de llamar a `default_rate_limiter.reset()` para evitar falsos positivos de `429 Too Many Requests`.

---

### 3. Prompt Recomendado para Pedir un Pentesting a Otro Agente

Si abres una nueva sesión con otro agente de IA y deseas que audite la seguridad del proyecto, puedes proporcionarle estas instrucciones:

```markdown
Eres un Auditor de Ciberseguridad / Pentester experto en aplicaciones web (FastAPI + React) y OWASP Top 10.
Tu objetivo es realizar una auditoría de seguridad y pruebas de penetración sobre la plataforma Arrendis.

Antes de comenzar:
1. Revisa la documentación en `docs/security/README.md`, `docs/security/seguridad_web_e04_launch_hardening.md` y `docs/security/auditoria_seguridad_develop.md` para conocer los controles defensivos existentes y los hallazgos ya mitigados.
2. Ejecuta la suite de pruebas de pentesting existente con `venv/bin/pytest tests/unit/backend/api/test_security_pentest.py -v`.
3. Evalúa los vectores de ataque según OWASP Top 10:2025 y OWASP API Security Top 10:2023:
   - Control de acceso a nivel de objeto (BOLA / IDOR)
   - Flujos de autenticación y caducidad de tokens
   - Rate limiting y protección contra abuso
   - Validación e ingestión segura de archivos (PDFs e imágenes)
   - Mitigación de SSRF e inyecciones
4. Si encuentras algún vector vulnerable no cubierto, proporciona una prueba de concepto (PoC) reproducible, implementa la remediación de forma aislada sin romper los tests existentes, agrega un test en `test_security_pentest.py` y actualiza la documentación en `docs/security/auditoria_seguridad_develop.md`.
```

---

## 🔒 Variables de Entorno Críticas de Seguridad

En entornos de producción o staging, asegúrate de configurar las siguientes variables de entorno:

| Variable | Valor Recomendado | Propósito |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Activa el forzado estricto de seguridad (HSTS, cookies seguras, bloqueo de secretos por defecto). |
| `JWT_SECRET` | Clave aleatoria de 64 caracteres hex | Firma y verificación criptográfica de Access y Refresh Tokens. |
| `INBOUND_WEBHOOK_SECRET` | Token secreto aleatorio | Autenticación del webhook de facturas entrantes por email. |
| `CORS_ALLOWED_ORIGINS` | `https://arrendis.com,https://app.arrendis.com` | Lista blanca de orígenes adicionales autorizados para peticiones cross-origin con credenciales. |
| `TRUSTED_PROXIES` | IPs de Caddy / Nginx / Cloudflare | Lista de proxies inversos confiables para la interpretación segura de cabeceras `X-Forwarded-For`. |
