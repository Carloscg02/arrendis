# 📋 Requisitos de Negocio y Sistema: F-39
# Cabeceras HTTP de Seguridad, Cookies Seguras de Producción y Endpoint de Salud (/api/health)

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Especificado  
> **Fecha:** 2026-10-03  
> **Formato:** Notación EARS (Easy Approach to Requirements Syntax)  

---

## 1. Requisitos del Sistema (EARS)

### R-39.1: Cabeceras de Seguridad Obligatorias (Ubiquitous)
El sistema **DEBERÁ** inyectar en todas las respuestas HTTP salientes de la API las cabeceras de protección del navegador:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`

### R-39.2: Protección HSTS Condicional (Event-Driven / State-Driven)
**CUANDO** la variable de entorno `ENVIRONMENT` sea `"production"` o `"staging"`, **O CUANDO** `FORCE_HSTS` sea `"1"`, el sistema **DEBERÁ** inyectar la cabecera:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### R-39.3: Cookies Seguras en Producción (State-Driven)
**CUANDO** el entorno sea `"production"`, `"staging"` o la variable `COOKIE_SECURE` sea `"true"`, el sistema **DEBERÁ** asignar el atributo `secure=True` a la cookie `refresh_token` en operaciones de login, registro, refresco y logout (`/api/auth/*`).
**EN CASO CONTRARIO** (desarrollo local o testing), el sistema **DEBERÁ** mantener `secure=False` para permitir la persistencia sobre HTTP plano (`http://localhost:5173`).

### R-39.4: Endpoint de Salud de la Plataforma (Ubiquitous)
El sistema **DEBERÁ** exponer el endpoint `GET /api/health` accesible públicamente sin requerir cabecera de autenticación (`Authorization`).

### R-39.5: Respuesta Saludable (State-Driven)
**CUANDO** el proceso de FastAPI esté activo y la base de datos SQLite responda exitosamente a la comprobación de integridad (`check_health()`), el endpoint `GET /api/health` **DEBERÁ** retornar código de estado `200 OK` con payload:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

### R-39.6: Respuesta Degradada por Fallo de Base de Datos (Event-Driven)
**SI** ocurre un fallo o pérdida de conectividad con SQLite durante la comprobación, el endpoint `GET /api/health` **DEBERÁ** retornar código de estado `503 Service Unavailable` con payload:
```json
{
  "status": "degraded",
  "database": "disconnected",
  "error": "Database connectivity check failed"
}
```

### R-39.7: Disciplina de Secretos en Documentación (Ubiquitous)
La documentación del repositorio y las especificaciones **DEBERÁN** abstenerse de contener cadenas literales coincidentes con delimitadores de claves criptográficas privadas (`BEGIN ... PRIVATE KEY`), empleando delimitadores ofuscados o descriptivos.

---

## 2. Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Inyección de cabeceras de seguridad en cualquier ruta
  Dado que el servidor FastAPI está en ejecución
  Cuando un cliente realiza una petición GET a cualquier endpoint ("/api/health" o ruta inexistente "/api/inexistente")
  Entonces la respuesta debe incluir "X-Content-Type-Options: nosniff"
  Y la respuesta debe incluir "X-Frame-Options: DENY"
  Y la respuesta debe incluir "Referrer-Policy: strict-origin-when-cross-origin"
  Y la respuesta debe incluir "Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()"

Escenario: Activación de HSTS en entorno de producción
  Dado que la variable de entorno ENVIRONMENT está configurada como "production"
  Cuando un cliente realiza una petición a la API
  Entonces la respuesta debe incluir "Strict-Transport-Security: max-age=31536000; includeSubDomains"

Escenario: Cookie refresh_token con flag Secure en producción
  Dado que la variable de entorno ENVIRONMENT es "production"
  Cuando un usuario inicia sesión con éxito en "/api/auth/login"
  Entonces la cabecera Set-Cookie debe contener "refresh_token"
  Y debe incluir el atributo "Secure"
  Y debe incluir el atributo "HttpOnly"
  Y debe tener "SameSite=lax"

Escenario: Comprobación de salud sin autenticación
  Dado que un monitor externo (Cloudflare / Docker / Uptime Kuma) sondea el servicio
  Cuando realiza una petición GET a "/api/health" sin token Bearer
  Entonces el código de respuesta debe ser 200 OK
  Y el cuerpo JSON debe indicar status "healthy" y database "connected"

Escenario: Comprobación de salud ante fallo de base de datos
  Dado que la base de datos no está disponible
  Cuando un cliente realiza una petición GET a "/api/health"
  Entonces el código de respuesta debe ser 503 Service Unavailable
  Y el cuerpo JSON debe indicar status "degraded" y database "disconnected"
```
