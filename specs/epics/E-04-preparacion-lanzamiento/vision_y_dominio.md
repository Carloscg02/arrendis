# 🛡️ Épica E-04: Preparación para Lanzamiento, Blindaje Web y Cumplimiento Normativo (Launch Readiness & Hardening)

> **Versión:** 1.0  
> **Estado:** Especificación Completa / Lista para Implementación  
> **Fecha:** 2026-10-03  
> **Dependencias previas:** E-01 (Fiscalidad), E-02 (Suministros), E-03 (Valoración Mercado), E-05 (Versión Móvil PWA)  
> **Herramienta de auditoría y verificación:** `pre-launch` ([~/pre-launch](file:///home/carlos/pre-launch))

---

## 1. Objetivo de Negocio y Justificación

Garantizar que **Arrendis** pase del estado de "prototipo funcional en desarrollo" a un estado de **preparación para producción comercial (*General Availability / GA Readiness*)**, con un blindaje exhaustivo de seguridad de red, cumplimiento estricto del marco legal europeo (RGPD y LSSI), presencia visual óptima en motores de búsqueda y redes sociales, y resiliencia total frente a errores de navegación de usuarios reales.

### ¿Qué problemas resuelve esta épica?

1. **Vulnerabilidades de red y cabeceras inseguras:** FastAPI no inyectaba cabeceras de seguridad HTTP estándar (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `HSTS`, `Referrer-Policy`), y la cookie de sesión `refresh_token` viajaba con el flag `secure=False` hardcodeado, lo que exponía la sesión en entornos web de producción.
2. **Exposición a ataques de fuerza bruta en autenticación:** Los endpoints `/api/auth/login` y `/api/auth/register` carecían de limitación de tasa (*rate limiting* / throttling), permitiendo ataques automatizados de diccionario o saturación de cuentas.
3. **Vacío legal y riesgo sancionador por RGPD:** Arrendis recopila datos especialmente sensibles de propietarios e inquilinos (nombres, DNI/NIF, direcciones de inmuebles, contratos de arrendamiento, importes de alquiler y cuentas bancarias). La ausencia de una Política de Privacidad (`/privacy`) y unos Términos de Servicio (`/terms`) exponía la plataforma a infracciones graves de la normativa europea de protección de datos.
4. **Falta de tarjetas sociales y riesgo de indexación indebida (SEO/Robots):** Al compartir la URL por canales de mensajería (WhatsApp, Telegram, LinkedIn), la previsualización no mostraba imagen corporativa ni descripción atractiva (falta de Open Graph y Twitter Cards). Además, sin un `robots.txt` explícito, los rastreadores web podían intentar indexar rutas protegidas (`/portfolio`, `/properties/*`, `/api/*`).
5. **Puntos ciegos de navegación y accesibilidad (Pantallas en blanco):** React Router no disponía de ruta comodín (`*`) para rutas no encontradas (404), provocando que URLs mal escritas mostrasen una pantalla en blanco. Asimismo, existían inputs sin etiquetas accesibles (`id`/`aria-label`) y elementos interactivos no semánticos (`<div onClick>`).
6. **Ausencia de endpoint de monitorización (*Health Check*):** No existía una sonda ligera (`/api/health`) para que servicios externos (Cloudflare, Uptime Kuma, Docker) pudiesen monitorizar la disponibilidad del backend y la conectividad con SQLite sin realizar peticiones de autenticación.

---

## 2. Límites del Subdominio (Bounded Context)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ÉPICA E-04: LAUNCH READINESS & BLINDAJE WEB                            │
│                                                                        │
│   [ F-39: Cabeceras HTTP, Cookies Seguras & /api/health ]              │
│   [ F-40: Rate Limiting & Anti-Fuerza Bruta en Auth ]                  │
│   [ F-41: Marco Legal RGPD, Términos & Aviso Early Access ]            │
│   [ F-42: SEO, Robots.txt, Sitemap & Social Graph ]                    │
│   [ F-43: Página 404 Atelier Editorial & Accesibilidad a11y ]          │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Aislamiento Arquitectónico
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ ÉPICA E-06: IDENTIDAD AVANZADA Y CONTROL DE CUENTAS (Separada)         │
│   - Autenticación Google OAuth2                                        │
│   - Control administrativo is_active (aprobación/suspensión)          │
│   - Métricas y registro de auditoría de usuarios                       │
└────────────────────────────────────────────────────────────────────────┘
```

### ✅ Lo que ENTRA en esta épica:
- **Seguridad HTTP & Cookies:** Middleware en FastAPI para inyección de cabeceras de seguridad (`nosniff`, `DENY`, `strict-origin-when-cross-origin`, `HSTS` en producción), parametrización segura de cookies según entorno, y limpieza de falsos positivos en documentación técnica.
- **Sonda de Salud:** Endpoint `/api/health` en FastAPI que verifique estado del servidor y conectividad con la base de datos.
- **Protección contra Abuso:** Middleware/mecanismo de limitación de peticiones (*rate limiting*) en endpoints de autenticación (`/api/auth/login`, `/api/auth/register`) con código `429 Too Many Requests`.
- **Marco Legal y Cumplimiento:** Páginas públicas estáticas `/privacy` y `/terms` con diseño Atelier Editorial, cláusulas RGPD adaptadas al dominio inmobiliario de Arrendis, y disclaimer de versión preliminar / Early Access (cálculos fiscales no vinculantes).
- **SEO & Social Sharing:** `robots.txt` desindexando el área privada y API, `sitemap.xml` para rutas públicas, etiquetas Open Graph y Twitter Cards en `index.html`, y corrección del atributo `lang="es"`.
- **Resiliencia & a11y:** Ruta comodín 404 en React Router con diseño editorial de rescate, corrección de accesibilidad en `ContractForm.tsx`, atributos `rel="noopener noreferrer"` en enlaces salientes y prevención de doble envío en formularios críticos.

### ❌ Lo que NO ENTRA (asignado a E-06 o fases posteriores):
- **Integración con Google OAuth2:** Requiere configuración externa en Google Cloud Console y flujo de redirección; se aisla en la Épica E-06.
- **Modificación del modelo `User` con `is_active`:** El control administrativo de activación de cuentas se implementará en la Épica E-06.
- **Suscripciones de pago o pasarelas Stripe:** Fuera de alcance en esta fase.

---

## 3. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Launch Readiness** | Conjunto de criterios técnicos, legales y operativos que una aplicación debe satisfacer antes de ser accesible a usuarios finales en producción. |
| **Security Headers** | Cabeceras de respuesta HTTP (`X-Content-Type-Options`, `X-Frame-Options`, `HSTS`, `CSP`) que instruyen al navegador para mitigar ataques de clickjacking, sniffing y downgrade. |
| **Secure Cookie** | Atributo de cookie HTTP que garantiza que la cookie solo se transmitirá a través de conexiones cifradas HTTPS. |
| **Rate Limiting** | Técnica de control de tráfico que limita la frecuencia de peticiones permitidas a un cliente o dirección IP en una ventana de tiempo determinada. |
| **Health Check Endpoint** | Ruta ligera no autenticada (`/api/health`) que reporta el estado operativo del servicio y sus dependencias críticas (ej. SQLite). |
| **RGPD / GDPR** | Reglamento General de Protección de Datos de la Unión Europea que regula el tratamiento y privacidad de los datos personales. |
| **Open Graph Protocol** | Estándar de metadatos (`og:*`) introducido en el `<head>` que permite a redes sociales y apps de mensajería generar tarjetas enriquecidas al compartir enlaces. |
| **Catch-All 404 Route** | Ruta de fallback en React Router (`path="*"`) que intercepta cualquier URL no coincidente para ofrecer una pantalla de navegación guiada. |
| **Placeholder Discipline** | Norma de ingeniería que prohíbe la invención de datos legales (direcciones fiscales, números de registro mercantil) en plantillas legales, utilizando marcadores explícitos. |

---

## 4. Arquitectura Técnica de la Épica

```
[ Cliente Web / Navegador / Bot ]
            │
            ├─► Solicita /robots.txt o /sitemap.xml ──────► Archivos estáticos en frontend/public
            ├─► Solicita ruta inexistente (/xyz) ─────────► React Router Catch-All: <NotFoundPage /> (Atelier)
            ├─► Solicita /privacy o /terms ───────────────► Componentes <PrivacyPolicy /> / <TermsOfService />
            │
            ▼ Peticiones HTTPS a /api/*
┌────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application (backend/api/main.py)                              │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ Middleware 1: SecurityHeadersMiddleware                      │    │
│   │ (Inyecta X-Content-Type-Options, X-Frame-Options, HSTS, etc.)│    │
│   └──────────────────────────────┬───────────────────────────────┘    │
│                                  │                                    │
│   ┌──────────────────────────────▼───────────────────────────────┐    │
│   │ Middleware 2: RateLimitMiddleware (Auth Endpoints)          │    │
│   │ (Control de ventana deslizante por IP en /login y /register) │    │
│   └──────────────────────────────┬───────────────────────────────┘    │
│                                  │                                    │
│   ┌──────────────────────────────▼───────────────────────────────┐    │
│   │ Router: /api/health (Sonda de estado y ping a SQLite)        │    │
│   │ Router: /api/auth/* (Cookies con Secure=True en producción)  │    │
│   └──────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Desglose de Features

### 1. `F-39`: Blindaje de Cabeceras HTTP de Seguridad, Cookies Seguras de Producción y Endpoint de Salud (`/api/health`)
- Middleware en FastAPI para inyectar cabeceras recomendadas por OWASP (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, y HSTS).
- Parametrización dinámica del flag `secure` en cookies de refresco (`backend/api/routes/auth.py`), activándose según `ENVIRONMENT=production` o `COOKIE_SECURE=true`.
- Creación del endpoint `/api/health` que ejecuta una consulta simple a SQLite (`SELECT 1`) y retorna `{ "status": "healthy", "database": "connected" }`.
- Remediación del falso positivo de clave privada en [docs/plan_cicd_produccion.md](file:///home/carlos/rental-launch-prep/docs/plan_cicd_produccion.md#L54).

### 2. `F-40`: Protección contra Fuerza Bruta y Rate Limiting en Endpoints de Autenticación
- Implementación de limitador de tasa en memoria (*Token Bucket* / ventana deslizante por IP) aplicado exclusivamente a `/api/auth/login` y `/api/auth/register`.
- Umbral conservador: máximo 10 intentos por minuto por IP antes de retornar código `429 Too Many Requests` con cabecera `Retry-After`.
- Exclusión estricta de tests en memoria para no ralentizar la suite de pruebas unitarias.

### 3. `F-41`: Marco Legal y Cumplimiento Normativo RGPD (Páginas `/privacy`, `/terms` y Aviso Early Access)
- Creación de rutas públicas `/privacy` y `/terms` en React con diseño editorial Atelier (Newsreader, Space Mono).
- Redacción rigurosa de Política de Privacidad detallando categorías de datos recopiladas en Arrendis (emails, inmuebles, datos bancarios/fiscales de contratos) y derechos ARCO.
- Redacción de Términos y Condiciones delimitando la naturaleza de los cálculos fiscales (estimaciones orientativas no vinculantes).
- Adición de aviso discreto en el pie de página y landing page sobre versión preliminar / *Early Access*.

### 4. `F-42`: Descubrimiento Web, SEO, Social Graph y Crawling (`robots.txt`, `sitemap.xml`, Open Graph, Twitter Cards)
- Creación de `frontend/public/robots.txt` permitiendo rutas públicas y bloqueando explícitamente `/portfolio`, `/properties/`, `/onboarding`, `/api/`.
- Creación de `frontend/public/sitemap.xml` con las rutas públicas activas.
- Configuración de metadatos en `frontend/index.html`: `lang="es"`, `<meta name="description">`, Open Graph (`og:image`, `og:title`, `og:description`, `og:url`) y Twitter Cards con la identidad visual corporativa.
- Corrección de enlaces externos con `rel="noopener noreferrer"` en [MarketValuationPanel.tsx](file:///home/carlos/rental-launch-prep/frontend/src/components/MarketValuationPanel.tsx).

### 5. `F-43`: Resiliencia de Navegación (Página 404 Personalizada Atelier Editorial) y Accesibilidad en Formularios
- Creación del componente `NotFound.tsx` y adición de la ruta comodín `<Route path="*" element={<NotFound />} />` en [App.tsx](file:///home/carlos/rental-launch-prep/frontend/src/App.tsx).
- Corrección de accesibilidad en [ContractForm.tsx](file:///home/carlos/rental-launch-prep/frontend/src/components/ContractForm.tsx) (asociación de `id`/`htmlFor` y `aria-label`).
- Sustitución de elementos interactivos no semánticos (`<div onClick>`) por componentes `<button>` accesibles.
- Deshabilitación de botones de submit durante operaciones de red en formularios clave para prevenir doble envío.

---

## 6. Criterios de Aceptación Globales de la Épica

- [ ] La herramienta `pre-launch` ejecutada sobre el repositorio reporta **0 BLOCKERS** y **0 WARNINGS de severidad HIGH**.
- [ ] Todas las respuestas del backend incluyen cabeceras de seguridad HTTP estándar.
- [ ] La cookie `refresh_token` utiliza `Secure=True` cuando la variable de entorno indique producción.
- [ ] El endpoint `/api/health` retorna `200 OK` con información del estado del servicio y la base de datos.
- [ ] Los endpoints `/api/auth/login` y `/api/auth/register` bloquean con `429 Too Many Requests` ante ráfagas excesivas de peticiones.
- [ ] Existen las rutas `/privacy` y `/terms` completamente accesibles y formateadas con la estética Atelier Editorial.
- [ ] El archivo `robots.txt` desindexa las rutas protegidas de la aplicación y el `sitemap.xml` expone las páginas públicas.
- [ ] Al compartir la URL de Arrendis en redes de mensajería (WhatsApp, Telegram) se visualiza la tarjeta social con imagen y descripción.
- [ ] Una URL inexistente muestra la página 404 personalizada con enlace de rescate hacia el inicio o la cartera.
- [ ] La suite completa de tests de backend (`pytest`) y la compilación de frontend (`npm run build`) se ejecutan con éxito al 100%.
