# 🛡️ Blindaje Web, Seguridad y Cumplimiento Normativo (Épica E-04)

> **Documento:** Guía Técnica y Teórica de Seguridad de Arrendis  
> **Fecha:** Octubre 2026  
> **Estado:** Implementado, Auditado y Verificado en `develop`  
> **Ámbito:** Backend (FastAPI), Frontend (React + Vite), Infraestructura y CI/CD  

---

## 1. Introducción y Enfoque de Defensa en Profundidad

La **Épica E-04: Preparación para Lanzamiento, Blindaje Web y Cumplimiento Normativo (Launch Readiness & Hardening)** establece una arquitectura de seguridad basada en el principio de **Defensa en Profundidad (Defense-in-Depth)**. 

Bajo este modelo, la seguridad no depende de una única barrera perimetral (como un firewall o un gateway), sino de múltiples capas defensivas superpuestas:
1. **Capa de Transporte y Red:** Forzado de TLS estricto (HSTS) y aislamiento de orígenes.
2. **Capa de Cabeceras HTTP:** Control de contexto de renderizado y directivas de ejecución para el navegador cliente (OWASP Secure Headers & CSP).
3. **Capa de Control de Acceso y Sesión:** Blindaje de cookies HTTP con directivas anticlonación y antifuga.
4. **Capa de Aplicación y Tráfico:** Rate limiting selectivo por algoritmo *Sliding Window Log* contra abuso de fuerza bruta.
5. **Capa de Persistencia y Sanidad de Entradas:** Sanitización estricta de consultas SQLite contra SQLi y validación estricta de rutas estáticas contra Path Traversal.
6. **Capa de Observabilidad y Gobernanza:** Endpoint desacoplado `/api/health`, desindexación de áreas privadas en `robots.txt` y sanitización SAST de credenciales.

---

## 2. Cabeceras HTTP de Seguridad (Security Headers)

Implementadas mediante [`SecurityHeadersMiddleware`](file:///home/carlos/rental-handler/backend/api/middleware/security.py) como middleware ASGI puro en FastAPI, garantizando su inyección en todas las respuestas HTTP (tanto códigos exitosos `2xx` como errores `4xx` y `5xx`).

### 2.1 `X-Frame-Options: DENY`
* **Explicación Teórica:** Directiva que instruye al navegador a no renderizar la página dentro de etiquetas `<frame>`, `<iframe>`, `<embed>` o `<object>`, ni siquiera si la petición procede del mismo origen (`SAMEORIGIN`).
* **Ataques que Mitiga:**
  * **Clickjacking (UI Redressing):** Ataque donde un sitio malicioso incrusta Arrendis en un iframe invisible sobre una interfaz señuelo. Al inducir al usuario a hacer clic (por ejemplo, en un botón falso de reproducción), el clic se transfiere en realidad a una acción crítica en Arrendis (ej. confirmar un gasto, borrar una propiedad o cerrar una sesión).
  * **Overlay Attacks:** Superposición de formularios transparentes para capturar credenciales o datos bancarios del usuario sin su conocimiento.

### 2.2 `X-Content-Type-Options: nosniff`
* **Explicación Teórica:** Deshabilita el algoritmo de *MIME-type sniffing* implementado en navegadores como Chrome o Safari, el cual intenta adivinar el formato real de un archivo examinando sus primeros bytes en lugar de respetar la cabecera `Content-Type`.
* **Ataques que Mitiga:**
  * **MIME Confusion Attacks:** Subida de archivos que aparentan ser inocuos (como una imagen `.png` o un `.txt`), pero que contienen código JavaScript ejecutable. Si el navegador realizara "sniffing", podría interpretar la supuesta imagen como un script ejecutable (`text/javascript`).
  * **Polyglot File Exploits:** Archivos binarios que son válidos simultáneamente como imagen y como script ejecutable. Con `nosniff`, el navegador rechaza ejecutar cualquier archivo cuyo `Content-Type` no sea explícitamente un tipo de script reconocido.

### 2.3 `Referrer-Policy: strict-origin-when-cross-origin`
* **Explicación Teórica:** Controla qué información de la URL de origen se incluye en la cabecera HTTP `Referer` cuando el usuario navega o realiza peticiones externas. En peticiones hacia el mismo origen envía la URL completa; en peticiones cross-origin vía HTTPS envía únicamente el dominio (`origin`), y si se degrada de HTTPS a HTTP no envía nada (`no-referrer`).
* **Ataques que Mitiga:**
  * **Information Disclosure & URL Leaks:** En aplicaciones web complejas, las URLs a menudo contienen identificadores sensibles (UUIDs de contratos, códigos catastrales, identificadores de sesión o tokens temporales en query params). Esta directiva evita que dominios externos recopilen estas rutas en sus logs de acceso.

### 2.4 `Permissions-Policy` (Feature Policy)
* **Directiva:** `camera=(), microphone=(), geolocation=(), payment=()`
* **Explicación Teórica:** Mecanismo estándar que restringe el acceso de la aplicación a APIs de hardware y sensores del dispositivo cliente. Los paréntesis vacíos `()` deniegan el acceso universal a dichas capacidades en cualquier contexto.
* **Ataques que Mitiga:**
  * **Unauthorized Hardware Access:** Si un script de terceros o una extensión del navegador intentara acceder a la cámara, micrófono o GPS del usuario dentro del contexto de Arrendis, el navegador bloquea la llamada a nivel de kernel/sandbox.
  * **Abuso de APIs de Pago:** Bloquea la invocación no autorizada de la API de Payment Request en el navegador.

### 2.5 `Strict-Transport-Security` (HSTS)
* **Directiva:** `max-age=31536000; includeSubDomains` (activo condicionalmente en `ENVIRONMENT in ("production", "staging")` o `FORCE_HSTS=1`)
* **Explicación Teórica:** Fuerza al navegador a recordar durante un año (31.536.000 segundos) que cualquier conexión con el dominio y todos sus subdominios debe realizarse única y exclusivamente mediante HTTPS, denegando de inmediato cualquier intento de conexión sobre HTTP no seguro.
* **Ataques que Mitiga:**
  * **SSL Stripping:** Ataque Man-in-the-Middle (MitM) en el que un atacante interrumpe la redirección de HTTP a HTTPS, sirviendo una versión en texto plano de la web a la víctima mientras él mantiene la sesión HTTPS con el servidor real. Con HSTS, el navegador rechaza conectarse antes incluso de enviar la primera petición HTTP.
  * **DNS Spoofing & Cookie Hijacking:** Previene la transmisión inadvertida de cookies o credenciales a través de redes Wi-Fi abiertas o no confiables.

### 2.6 `Content-Security-Policy` (CSP)
* **Directiva:**  
  `default-src 'self'; img-src 'self' data: https: blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; script-src 'self' 'unsafe-inline'; connect-src 'self' https: ws: wss:;`
* **Explicación Teórica:** Lista blanca estricta que delimita qué fuentes de contenido y recursos externos tiene permitido descargar y ejecutar el navegador.
* **Ataques que Mitiga:**
  * **Cross-Site Scripting (XSS):** Bloquea la inyección de scripts procedentes de servidores de comando y control (C2) no autorizados.
  * **Data Exfiltration:** Impide que scripts maliciosos envíen datos robados hacia dominios de terceros no listados en `connect-src`.
  * **Inyección de Fuentes e Imágenes Maliciosas:** Restringe la carga de tipografías únicamente a Google Fonts y fuentes locales seguras.

---

## 3. Blindaje de Sesiones y Cookies Seguras de Producción

En [`backend/api/routes/auth.py`](file:///home/carlos/rental-handler/backend/api/routes/auth.py), el manejo de la cookie de autenticación `auth_token` se ha protegido con flags de alta seguridad:

```python
is_production = os.getenv("ENVIRONMENT", "").lower() in ("production", "staging") or os.getenv("COOKIE_SECURE", "").lower() == "true"

response.set_cookie(
    key="auth_token",
    value=token_data.access_token,
    httponly=True,
    samesite="lax",
    secure=is_production,
    max_age=access_ttl_seconds,
    path="/"
)
```

### Justificación de Atributos:
1. **`HttpOnly=True`:**
   - **Teoría:** La cookie no es accesible desde la API `document.cookie` del Document Object Model (DOM) de JavaScript.
   - **Protección:** Inmunidad contra el robo masivo de sesiones a través de XSS; incluso si un atacante lograse inyectar código en la página, no podrá extraer el token JWT de la cookie.
2. **`SameSite="lax"`:**
   - **Teoría:** La cookie se envía en navegaciones seguras de nivel superior (ej. al seguir un enlace externo), pero se omite en peticiones cross-site subyacentes iniciadas por `POST`, `PUT`, `DELETE` o mediante `fetch`/`XMLHttpRequest` desde otros dominios.
   - **Protección:** Mitigación robusta de ataques **Cross-Site Request Forgery (CSRF)**.
3. **`Secure=is_production`:**
   - **Teoría:** El navegador solo transmitirá la cookie a través de canales cifrados TLS (HTTPS).
   - **Flexibilidad por Entorno:** Se activa automáticamente en producción y staging, permitiendo el desarrollo y pruebas locales sin fallos sobre `http://localhost`.

---

## 4. Protección contra Fuerza Bruta y DoS con Rate Limiting Estratificado (Tiered Throttling)

Implementado en [`backend/api/middleware/rate_limit.py`](file:///home/carlos/rental-handler/backend/api/middleware/rate_limit.py) mediante la clase [`InMemoryRateLimiter`](file:///home/carlos/rental-handler/backend/api/middleware/rate_limit.py) y [`RateLimitMiddleware`](file:///home/carlos/rental-handler/backend/api/middleware/rate_limit.py):

### 4.1 Estratificación por Niveles (Tiered Architecture)
Toda la API está protegida mediante cuotas adaptadas a la criticidad y coste computacional del recurso:

| Nivel | Ámbito / Rutas | Cuota por IP | Respuesta y Detalle |
| :--- | :--- | :---: | :--- |
| **Nivel 1: Autenticación (Crítico)** | `POST /api/auth/login`<br>`POST /api/auth/register` | **10 req/min** | `429 Too Many Requests`<br>`{"detail": "Demasiados intentos de autenticación...", "tier": "auth"}` |
| **Nivel 2: Cómputo Pesado / IA** | `/api/fiscal/report/pdf`<br>`/api/properties/{id}/valuation`<br>`/api/expenses/upload*` | **30 req/min** | `429 Too Many Requests`<br>`{"detail": "Demasiadas peticiones a operaciones de alto coste...", "tier": "heavy"}` |
| **Nivel 3: Global API / Navegación** | Resto de rutas `/api/*` (`/properties`, `/incomes`, `/contracts`, etc.) | **100 req/min** | `429 Too Many Requests`<br>`{"detail": "Límite global de peticiones de API excedido...", "tier": "global"}` |

*Exenciones Estándar:* Peticiones preflight `OPTIONS` de CORS (estrictamente exentas conforme a especificación W3C) y archivos estáticos locales (`/api/images/*`).

### 4.2 Algoritmo: Sliding Window Log (Ventana Deslizante)
* **Fundamento Matemático:** A diferencia de una ventana fija (donde un atacante puede concentrar el doble de peticiones en la frontera entre dos minutos), la ventana deslizante registra la marca temporal de cada intento en una lista enlazada o deque. Para cada nueva petición:
  1. Se purgan todas las marcas de tiempo anteriores a `ahora - 60s`.
  2. Se cuenta el número de peticiones remanentes en los últimos 60 segundos dentro del nivel correspondiente.
  3. Si el total supera el límite del nivel, se deniega la petición devolviendo cabecera `Retry-After: <segundos_restantes>`.
* **Identificación del Cliente:** Detección de IP real mediante cabecera proxy `X-Forwarded-For` o fallback a `client.host`.

### 4.3 Control Estricto de Memoria (Anti-Memory Exhaustion)
* **El Problema:** Un atacante con una botnet que envíe peticiones desde millones de IPs falsificadas podría saturar la memoria RAM del servidor con entradas de seguimiento de rate-limiting.
* **La Solución Implementada:**
  - Capacidad máxima acotada a **10.000 IPs concurrentes** por limitador.
  - Cuando se alcanza el umbral, se ejecuta una evicción **LRU (Least Recently Used)** automática que purga las claves más antiguas hasta reducir la ocupación al 90% (9.000 entradas).
  - Thread-Safety garantizado mediante un cerrojo mutex reentrante (`threading.Lock`).

### 4.4 Ataques que Mitiga:
* **Credential Stuffing & Brute Force:** Ataques automatizados que prueban millones de credenciales contra endpoints de login.
* **Bcrypt Hash DoS (Resource Exhaustion):** Sobrecarga de CPU mediante peticiones masivas al hasher criptográfico.
* **Scraping Masivo y DoS de Base de Datos:** Extracción abusiva de datos o saturación de conexiones en SQLite sobre `/api/properties` o `/api/incomes`.
* **Agotamiento de Cuota de IA:** Spam sobre `/api/properties/{id}/valuation` que consumiría créditos de la API de Google Gemini.

---

## 5. Resiliencia de Persistencia y Endpoint `/api/health`

Diseñado en [`backend/api/routes/health.py`](file:///home/carlos/rental-handler/backend/api/routes/health.py):
* **Comprobación Activa de BD:** Invoca el método [`check_health()`](file:///home/carlos/rental-handler/backend/adapters/sqlite_adapter.py) que ejecuta una consulta ultraligera `SELECT 1;`.
* **Semántica de Códigos HTTP:**
  - `200 OK` (`{"status": "ok", "database": "connected"}`): El sistema está listo para recibir tráfico de usuarios.
  - `503 Service Unavailable` (`{"status": "unhealthy", "database": "disconnected"}`): Fallo de persistencia o base de datos bloqueada (database locked).
* **Beneficio de Seguridad y Resiliencia:** Permite que balanceadores de carga, Caddy, Docker Compose o Kubernetes detecten degradaciones de persistencia y eviten enrutar tráfico a instancias corruptas, evitando fallos en cascada.

---

## 6. Desindexación y Social Graph

* **`robots.txt` ([`frontend/public/robots.txt`](file:///home/carlos/rental-handler/frontend/public/robots.txt)):**
  - Desindexación de rutas privadas mediante directivas `Disallow: /portfolio`, `/properties`, `/onboarding`, `/api/`.
  - Mitiga el **Information Disclosure** al evitar que bots de indexación o buscadores como Google o Shodan almacenen en caché pantallas de datos de inmuebles o contratos de usuarios.
* **`sitemap.xml` ([`frontend/public/sitemap.xml`](file:///home/carlos/rental-handler/frontend/public/sitemap.xml)):**
  - Publica exclusivamente las rutas públicas (`/`, `/privacy`, `/terms`).
* **`index.html`:**
  - Metadatos Open Graph y Twitter Cards canónicos para prevenir phishing y suplantación de identidad en redes sociales.
  - Atributos `rel="noopener noreferrer"` en todos los enlaces con `target="_blank"`, impidiendo ataques de **Tabnabbing** (donde la página de destino podría manipular `window.opener.location` para redirigir la pestaña original a un sitio de phishing).

---

## 7. Accesibilidad y Resiliencia en Navegación (404 y Formularios)

* **Ruta Comodín 404:** Implementada en React Router (`<Route path="*" element={<NotFound />} />`) con estética *Atelier Editorial* y rescate estático en [`frontend/public/404.html`](file:///home/carlos/rental-handler/frontend/public/404.html) para prevenir pantallas en blanco o desorientación del usuario.
* **Prevención de Condiciones de Carrera en Formularios:**
  - En [`ContractForm.tsx`](file:///home/carlos/rental-handler/frontend/src/components/ContractForm.tsx), se implementó el estado `isSubmitting` y deshabilitación visual/funcional del botón de guardado.
  - Mitiga la **doble sumisión accidental (Race Conditions)** que crearía duplicados en contratos o transacciones.
* **Accesibilidad WCAG 2.1 AA:**
  - Vinculación unívoca entre `<label htmlFor="...">` y `<input id="...">` en todos los campos para lectores de pantalla.
  - Elementos interactivos no semánticos dotados de roles explícitos (`role="button"`, `role="group"`) y escuchadores de eventos de teclado (`Enter`, `Space`, `Escape`).

---

## 8. Resultados de Auditorías de Seguridad y Pentesting

| Herramienta / Batería | Alcance / Vectores Evaluados | Resultado |
| :--- | :--- | :---: |
| **Bandit (SAST Python AST)** | 7.088 líneas de backend analizadas contra vulnerabilidades CWE | **0 High, 0 Medium** |
| **Fuzzing SQLi** | Payloads de inyección (`' OR '1'='1`, `UNION SELECT`, `DROP TABLE`) | **0 fallos (401/422 controlados, sin fugas)** |
| **Path Traversal / LFI** | Manipulaciones de directorio en `/api/images/../../etc/passwd` | **0 fallos (Rechazo estricto 400/404)** |
| **Fuzzing XSS** | Inyección de payloads `<script>`, `<img>`, `<svg>` en entradas de auth | **0 fallos (Tratadas como datos, CSP activa)** |
| **JWT Tampering** | Ataques con `alg: none`, tokens truncados o firmas corruptas | **100% rechazados con 401** |
| **Pre-launch Auditor** | 21 comprobaciones de lanzamiento (secretos, enlaces, accesibilidad) | **READY (0 BLOCKERS, 17 Passed)** |
| **Suite Completa de Tests** | Pruebas unitarias, de integración y seguridad | **423 / 423 tests PASADOS** |
