# 🛡️ Sistema de Autenticación y Seguridad (Shielded JWT)

Este documento describe en profundidad la arquitectura, los fundamentos técnicos y el flujo operativo del sistema de autenticación implementado en la plataforma **Gestión de Alquileres** a partir de la feature **F-06**.

---

## 1. Filosofía de Diseño: "Dividir el Poder"

En el desarrollo de aplicaciones web modernas (Single Page Applications como React), el manejo seguro de la identidad del usuario es un desafío crítico. Existen dos enfoques tradicionales, ambos con vulnerabilidades inherentes si se usan de forma ingenua:

1. **Almacenar tokens en `localStorage` / `sessionStorage`:** 
   - ❌ **Riesgo:** Si un atacante logra inyectar código JavaScript malicioso en la web (ataque **XSS** - *Cross-Site Scripting*), puede leer `localStorage`, robar el token y suplantar al usuario indefinidamente.
2. **Almacenar tokens en Cookies tradicionales:**
   - ❌ **Riesgo:** Si el navegador envía la cookie en cada petición automáticamente, un sitio web de terceros malicioso podría forzar al navegador del usuario a realizar acciones no deseadas en nuestra API (ataque **CSRF** - *Cross-Site Request Forgery*).

### La Solución: Híbrido de Doble Token (Shielded JWT)

Para lograr la máxima seguridad ("Seguridad Blindada"), hemos adoptado un patrón que **divide las responsabilidades y los vectores de ataque** utilizando dos tokens JWT con duraciones y mecanismos de transporte radicalmente diferentes:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SISTEMA DE DOBLE TOKEN                                 │
├──────────────────────────┬──────────────────────────────────────────────────────┤
│  ACCESS TOKEN (60 min*)  │  REFRESH TOKEN (7 días)                              │
├──────────────────────────┼──────────────────────────────────────────────────────┤
│ 📦 Viaja en: Body JSON   │ 🍪 Viaja en: Cookie HTTP (httpOnly + Secure + Lax)  │
│ 🧠 Guardado: Memoria JS  │ 🔒 Guardado: Navegador (Inaccesible para JS)         │
│ 🔑 Uso: Cabecera Bearer  │ 🔄 Uso: Renovar Access Token caducado en /refresh   │
└──────────────────────────┴──────────────────────────────────────────────────────┘
* Duración por defecto de 60 min (configurable mediante la variable ACCESS_TOKEN_EXPIRE_MINUTES).
```

#### ¿Por qué esta combinación es tan segura?
- **Inmunidad contra XSS (Robo de sesión persistente):** El **Refresh Token** (el de larga duración, 7 días) se guarda en una cookie marcada con la bandera `HttpOnly`. Esto significa que **el motor de JavaScript del navegador tiene prohibido leerla**. Si sufrimos un ataque XSS, el atacante nunca podrá robar tu Refresh Token. El **Access Token**, que sí es accesible por JS, reside **única y exclusivamente en memoria** (desaparece al cerrar la pestaña o recargar) y tiene una vida acotada.
- **Inmunidad contra CSRF:** Para las peticiones a la API de datos (propiedades, gastos, ingresos), exigimos que el token viaje en la cabecera HTTP `Authorization: Bearer <token>`. Los ataques CSRF no pueden inyectar cabeceras personalizadas sin ser bloqueados por la política CORS del navegador. Por tanto, nuestra API está protegida contra falsificación de peticiones.

---

## 2. Arquitectura Hexagonal y Desacoplamiento

Respetando estrictamente los principios de **Arquitectura Hexagonal** y **Domain-Driven Design (DDD)** del proyecto, la capa de dominio **no tiene dependencias externas**. No sabe qué es `bcrypt`, qué es `PyJWT`, ni qué es una cookie HTTP.

```
       ┌────────────────────────────────────────────────────────┐
       │             CAPA DE DOMINIO (Python Puro)              │
       │                                                        │
       │   Entidad: User(id, email, username, password_hash)    │
       │   Value Objects: Email, PasswordHash                   │
       │                                                        │
       │   Puertos (Interfaces ABC):                            │
       │    ├── UserRepository  ──(define CRUD)                 │
       │    ├── PasswordHasher  ──(define hash/verify)          │
       │    └── TokenService    ──(define creación/validación)  │
       └───────────▲───────────────────────────────▲────────────┘
                   │ implementa                    │ implementa
       ┌───────────┴───────────────┐   ┌───────────┴─────────────────┐
       │  ADAPTADOR PERSISTENCIA   │   │     ADAPTADOR DE AUTH       │
       │                           │   │  (backend/adapters/auth...) │
       │  SQLiteUserRepository     │   │                             │
       │  (Usa sqlite3 y SQL)      │   │  ├── BcryptPasswordHasher   │
       │                           │   │  └── JWTTokenService        │
       └───────────────────────────┘   └─────────────────────────────┘
```

### 2.1 Elementos del Dominio (`backend/domain/`)
- **`Email` (Value Object):** Garantiza inmutabilidad y que cualquier correo instanciado en el sistema sea válido (contenga `@` y dominio) y esté normalizado en minúsculas.
- **`PasswordHash` (Value Object):** Garantiza que jamás circule una contraseña en texto plano en las entidades del dominio. Solo acepta cadenas que cumplan con el formato de hash BCrypt (`$2b$...`).
- **`User` (Entidad):** Identificada por un `UUIDv4`. Agrupa el `Email`, el `PasswordHash` y el nombre de usuario (`username`).
- **Puertos de Salida (`ports.py`):** Contratos que el dominio exige para funcionar: `UserRepository`, `PasswordHasher` y `TokenService`.

### 2.2 Adaptadores Concretos (`backend/adapters/`)
- **`SQLiteUserRepository`:** Implementa la persistencia en la tabla `users` de SQLite. Maneja colisiones de correo único (`UNIQUE constraint`) lanzando errores limpios de negocio.
- **`BcryptPasswordHasher`:** Implementa el puerto utilizando la librería externa `bcrypt` con generación de salt segura (`bcrypt.gensalt()`).
- **`JWTTokenService`:** Implementa el puerto usando `PyJWT`. Firma los tokens con HMAC-SHA256 (`HS256`). Diferencia en el payload (`type: "access"` vs `type: "refresh"`) para evitar que un token de refresco sea usado accidentalmente o maliciosamente para consultar endpoints de datos.

---

## 3. Mecánica y Flujos HTTP

### 3.1 Flujo de Registro e Inicio de Sesión (`POST /api/auth/login`)

Cuando el usuario introduce sus credenciales correctas:
1. El backend verifica el hash con `bcrypt`.
2. Se generan ambos tokens.
3. El servidor responde con código `200 OK` devolviendo:
   - En el **Cuerpo JSON:** El `access_token` y los datos públicos del usuario (`id`, `email`, `username`).
   - En una cabecera **`Set-Cookie`:** El `refresh_token` configurado con las máximas medidas de seguridad:
     ```http
     Set-Cookie: refresh_token=eyJhbG...; HttpOnly; SameSite=Lax; Path=/api/auth; Max-Age=604800
     ```
     *(Nota: La opción `Path=/api/auth` restringe la cookie para que el navegador sólo la adjunte cuando se llame a endpoints de autenticación, evitando enviarla en cada foto o consulta de inmueble).*

### 3.2 Flujo de Refresco Silencioso (`POST /api/auth/refresh`)

Al abrir la aplicación por primera vez en el día, o cuando un Access Token caduca (60 minutos por defecto):
1. El frontend realiza una petición HTTP `POST /api/auth/refresh` con la opción `credentials: "include"`.
2. El navegador adjunta automáticamente la cookie `httpOnly` con el `refresh_token`.
3. El backend verifica la firma y caducidad del token de refresco.
4. Si es válido, el backend genera un **nuevo par de tokens (Rotación de Tokens)**, enviando una nueva cookie y devolviendo un nuevo `access_token` para que el frontend siga trabajando sin molestar al usuario.

---

## 4. Capa de Frontend (`AuthProvider`, Interceptor y Protección de Rutas)

En el lado del cliente (React + TypeScript), el sistema se gestiona sin contaminar los componentes visuales:

- **Almacenamiento Estricto en Memoria (`services/auth.ts`):** Existe una variable privada en memoria (`let accessToken: string | null = null;`). Ni `localStorage` ni `sessionStorage` se utilizan, impidiendo la extracción pasiva de credenciales ante vectores XSS.
- **Deduplicación de Refresco Concurrente (`refreshPromise`):** Tanto en `services/auth.ts` como en el interceptor `apiFetch` de `services/api.ts`, si múltiples peticiones reciben un 401 al mismo milisegundo (ej. en `Promise.all`), solo una ejecuta la petición a `/refresh` y las demás esperan y reutilizan el token obtenido.
- **`AuthProvider` (React Context):** Al montarse la aplicación, ejecuta un "refresco silencioso" en segundo plano (`useEffect`). Si el usuario tenía una cookie válida de días anteriores, recupera automáticamente su sesión sin pedirle contraseña.
- **Protección de Rutas (`ProtectedRoute` y `PublicOnlyRoute`):** Las rutas privadas (`/`, `/properties/:id`) exigen autenticación y redirigen a `/login` si no hay sesión activa. Las rutas públicas (`/login`, `/register`) redirigen al catálogo si ya estás autenticado.
- **Barra de Navegación (`AppHeader`):** Muestra el usuario conectado y proporciona el botón de cierre de sesión (`logout`), que revoca las credenciales y limpia la memoria.

---

## 5. ¿Cómo Testear y Verificar el Sistema Ahora Mismo?

Puedes comprobar el funcionamiento real del sistema de seguridad de tres formas diferentes:

### Método 1: Prueba Visual desde el Navegador (Recomendado)

1. **Asegúrate de tener los servidores corriendo:**
   - Terminal 1 (Backend): `uvicorn backend.api.main:app --reload --port 8000`
   - Terminal 2 (Frontend): `cd frontend && npm run dev`
2. **Abre tu navegador web** en [http://localhost:5173/register](http://localhost:5173/register).
3. **Crea una cuenta:**
   - Email: `carlos@ejemplo.com`
   - Usuario: `Carlos`
   - Contraseña: `MiPassword123!`
   - Confirmar: `MiPassword123!`
4. **Pulsa "Crear Cuenta".** Verás una notificación Toast en español de éxito y serás redirigido al catálogo.
5. **Comprueba la Cookie Blindada (DevTools):**
   - Pulsa `F12` (o clic derecho -> Inspeccionar) y ve a la pestaña **Aplicación** (Application) -> **Cookies** -> `http://localhost:5173` (o `http://localhost:8000`).
   - Verás la cookie `refresh_token`. Verifica que la columna **HttpOnly** está marcada con un check (`✓`). Esto confirma que JavaScript no puede tocarla.
6. **Prueba el Login:**
   - Navega manualmente a [http://localhost:5173/login](http://localhost:5173/login).
   - Introduce tus credenciales y pulsa "Iniciar Sesión".

---

### Método 2: Prueba vía Terminal con `cURL` (Para ver las cabeceras exactas)

Puedes simular peticiones HTTP desde tu terminal para ver cómo el backend emite los tokens y valida la seguridad:

**1. Registrar un usuario (y ver la cookie en la cabecera `Set-Cookie`):**
```bash
curl -i -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@rental.com", "username": "admin", "password": "securepassword"}'
```
*Observa en la respuesta la línea: `Set-Cookie: refresh_token=...; HttpOnly;...` y en el cuerpo JSON el `access_token`.*

**2. Probar un endpoint protegido sin token (Debe fallar con 401):**
```bash
curl -i http://localhost:8000/api/auth/me
```
*Resultado: `HTTP/1.1 401 Unauthorized` -> `{"detail":"No autenticado"}`.*

**3. Probar el endpoint protegido CON el Access Token:**
*(Copia el token que te devolvió el paso 1 y pégalo donde dice `<TU_TOKEN>`):*
```bash
curl -i http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TU_TOKEN>"
```
*Resultado: `HTTP/1.1 200 OK` -> Devuelve tus datos de usuario en JSON.*

---

### Método 3: Suite de Pruebas Automatizadas (`pytest`)

El proyecto cuenta con 94 pruebas automatizadas que cubren desde la lógica pura del dominio hasta la integración de la API con cookies reales:

```bash
cd /home/carlos/rental-handler
venv/bin/python -m pytest tests/ -v
```

Si deseas correr únicamente las pruebas específicas del sistema de autenticación para ver los casos cubiertos:
```bash
# Tests unitarios de dominio y casos de uso de Auth (aislados en memoria)
venv/bin/python -m pytest tests/unit/backend/domain/test_auth_value_objects.py tests/unit/backend/application/test_auth_use_cases.py -v

# Tests de integración e intercepción de endpoints y cookies de Auth
venv/bin/python -m pytest tests/integration/backend/api/test_auth_api.py -v
```

---

## 6. Estado de Implementación (F-06 y F-07)

La infraestructura de autenticación y seguridad se encuentra **100% implementada y en producción**:
1. **`ProtectedRoute` y `PublicOnlyRoute` (React Router):** Los accesos no autorizados al catálogo o al detalle de propiedades redirigen automáticamente a `/login`. Del mismo modo, usuarios ya autenticados que visiten `/login` o `/register` son redirigidos directamente al catálogo.
2. **Barra de Navegación (`AppHeader`):** Presente en la aplicación, muestra el usuario activo (`user.username`) y un botón funcional de **"Cerrar Sesión"** (`logout`), el cual invalida la cookie en backend y purga la memoria del frontend.
3. **Resistencia a Concurrencia y Ráfagas:** Interceptores de red con deduplicación de refresco de tokens para evitar colisiones 401 en llamadas paralelas (`Promise.all`).
