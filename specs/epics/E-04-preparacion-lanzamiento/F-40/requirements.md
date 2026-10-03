# 📋 Requisitos de Negocio y Sistema: F-40
# Protección contra Fuerza Bruta y Rate Limiting en Endpoints de Autenticación

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Especificado  
> **Fecha:** 2026-10-03  
> **Formato:** Notación EARS (Easy Approach to Requirements Syntax)  

---

## 1. Requisitos del Sistema (EARS)

### R-40.1: Protección Focalizada en Rutas Críticas de Autenticación (Ubiquitous)
El sistema **DEBERÁ** aplicar limitación de tasa (*rate limiting*) exclusivamente sobre las peticiones HTTP `POST /api/auth/login` y `POST /api/auth/register`. Las demás rutas del sistema (consultas de propiedades, contratos, estimaciones, health check) **NO DEBERÁN** verse afectadas por esta cuota estricta.

### R-40.2: Umbral de Peticiones y Ventana Deslizante (State-Driven)
**CUANDO** una dirección IP cliente realice peticiones a las rutas de autenticación, el sistema **DEBERÁ** contabilizar los intentos en una ventana temporal deslizante de 60 segundos, permitiendo un umbral máximo de 10 peticiones dentro de dicha ventana.

### R-40.3: Bloqueo con HTTP 429 y Cabecera Retry-After (Event-Driven)
**SI** una misma dirección IP supera las 10 peticiones en la ventana de 60 segundos, el sistema **DEBERÁ** rechazar inmediatamente la petición entrante con el código de estado `429 Too Many Requests`, retornando la cabecera estándar `Retry-After: <segundos>` indicando el tiempo restante hasta que expire el intento más antiguo, y un cuerpo JSON informativo:
```json
{
  "detail": "Demasiados intentos de autenticación. Por favor, inténtelo de nuevo más tarde.",
  "retry_after": 45
}
```

### R-40.4: Mitigación de Fuga y Consumo Descontrolado de Memoria (Ubiquitous)
El limitador de tasa en memoria **DEBERÁ** purgar activamente los registros temporales expirados (>60s) en cada evaluación y **DEBERÁ** contar con una política de saneamiento (*eviction*) que impida el crecimiento arbitrario del mapa en memoria ante ataques con IPs rotativas distribuidas (máximo 10.000 entradas concurrentes).

### R-40.5: Identificación Precisa de IP tras Proxies Inversos (Ubiquitous)
El sistema **DEBERÁ** extraer la dirección IP real del cliente evaluando la cabecera `X-Forwarded-For` (primer hop público de confianza proporcionado por Cloudflare o proxy inverso) o, en su defecto, el `client.host` directo de la conexión.

### R-40.6: Conmutación y Aislamiento para Suites de Test (State-Driven)
**CUANDO** la variable de entorno `RATE_LIMIT_ENABLED` sea `"0"` o `"false"`, o cuando se esté ejecutando la suite de testing automatizada (`TESTING="1"`), el middleware **DEBERÁ** permitir la ejecución sin throttling por defecto, disponiendo de un mecanismo explícito para habilitarlo durante las pruebas unitarias de seguridad de la propia feature.

---

## 2. Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Peticiones legítimas dentro del umbral permitido
  Dado que un usuario realiza hasta 10 intentos de login en un minuto
  Cuando envía credenciales a "/api/auth/login"
  Entonces el sistema procesa la petición normalmente retornando 200 OK o 401 si las credenciales son incorrectas

Escenario: Detección y bloqueo por fuerza bruta (intento 11)
  Dado que una misma dirección IP ya ha alcanzado el límite de 10 peticiones en 60 segundos
  Cuando envía la petición número 11 a "/api/auth/login" o "/api/auth/register"
  Entonces el sistema responde con código HTTP 429 Too Many Requests
  Y la respuesta incluye la cabecera "Retry-After" con un número entero positivo de segundos
  Y el cuerpo JSON contiene "Demasiados intentos de autenticación"

Escenario: Restablecimiento del acceso tras expirar la ventana de tiempo
  Dado que una dirección IP fue bloqueada con código 429
  Cuando transcurre el tiempo especificado en "Retry-After"
  Y el usuario realiza una nueva petición de autenticación
  Entonces el sistema procesa la petición y responde con normalidad (200 o 401)

Escenario: Rutas no críticas no se ven afectadas
  Dado que una IP ha realizado más de 10 peticiones a "/api/properties" o "/api/health"
  Cuando envía una nueva petición a "/api/properties"
  Entonces el sistema responde con 200 OK sin aplicar el código 429
```
