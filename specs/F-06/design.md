# Especificación F-06: Secure Login System (Shielded JWT)

## 1. Visión General

Implementar un sistema de autenticación completo basado en **JWT de doble token** (Access Token + Refresh Token) que proteja los endpoints existentes de la API y permita que solo usuarios registrados accedan a la plataforma.

**Principio de diseño: "Dividir el poder".**
- El **Access Token** es de corta vida (15 min), se devuelve en el body JSON y el frontend lo almacena **solo en memoria** (variable JavaScript). Si un atacante roba el token, tiene una ventana de solo 15 minutos.
- El **Refresh Token** es de larga vida (7 días), se devuelve en una **cookie `httpOnly` + `Secure`**, invisible para JavaScript. El navegador lo envía automáticamente, pero ningún script puede leerlo.

**Alcance:** Backend (Dominio → Persistencia → API) + Frontend (Login/Register UI + interceptor de tokens).

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **User** | Entidad del dominio que representa a un usuario registrado en la plataforma. Tiene identidad (UUID), email único y hash de contraseña. |
| **Email** | Value Object que encapsula y valida una dirección de correo electrónico. Inmutable. |
| **PasswordHash** | Value Object que encapsula un hash bcrypt de la contraseña. Nunca almacena la contraseña en texto plano. Expone un método `verify(plain_password)` para comparar. |
| **Access Token** | JWT de corta duración (15 min) que contiene el `user_id` en su payload (`sub`). Se envía en el header `Authorization: Bearer <token>` de cada petición protegida. |
| **Refresh Token** | JWT de larga duración (7 días) que permite obtener un nuevo Access Token sin volver a pedir credenciales. Viaja exclusivamente en una cookie `httpOnly`. |
| **Token Pair** | El conjunto de Access Token + Refresh Token generados juntos tras un login o un refresh exitoso. |
| **UserRepository** | Puerto de salida que define cómo persistir y recuperar entidades `User`. |
| **TokenService** | Puerto de salida que define cómo generar y verificar tokens JWT. Permite desacoplar la implementación concreta (PyJWT) del dominio. |
| **PasswordHasher** | Puerto de salida que define cómo hashear y verificar contraseñas. Permite desacoplar bcrypt del dominio. |

---

## 3. Cambios en el Dominio

### 3.1 Nuevos Value Objects — `backend/domain/value_objects.py`

#### `Email`
```python
@dataclass(frozen=True)
class Email:
    """Dirección de correo electrónico validada e inmutable."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or "@" not in self.value or "." not in self.value.split("@")[-1]:
            raise ValueError(f"Email no válido: '{self.value}'")
        # Normalizar a minúsculas
        object.__setattr__(self, "value", self.value.strip().lower())
```

#### `PasswordHash`
```python
@dataclass(frozen=True)
class PasswordHash:
    """Hash bcrypt de una contraseña. Nunca almacena texto plano."""
    hash_value: str

    def __post_init__(self) -> None:
        if not self.hash_value or not self.hash_value.startswith("$2b$"):
            raise ValueError("PasswordHash debe ser un hash bcrypt válido.")
```

### 3.2 Nueva Entidad — `backend/domain/entities.py`

```python
@dataclass
class User:
    """Representa un usuario registrado en la plataforma.

    Identidad basada en el campo `id` (UUID4).
    """
    email: Email
    password_hash: PasswordHash
    username: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.username or not self.username.strip():
            raise ValueError("El nombre de usuario (username) no puede estar vacío.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

### 3.3 Nuevos Puertos — `backend/domain/ports.py`

#### `UserRepository`
```python
class UserRepository(ABC):
    """Puerto de salida para persistir y recuperar Users."""

    @abstractmethod
    def save(self, user: User) -> None:
        """Guarda un nuevo usuario."""
        ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        """Busca un usuario por su id."""
        ...

    @abstractmethod
    def find_by_email(self, email: str) -> User | None:
        """Busca un usuario por su email (normalizado a minúsculas)."""
        ...
```

#### `PasswordHasher`
```python
class PasswordHasher(ABC):
    """Puerto de salida para hashear y verificar contraseñas."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Genera un hash bcrypt a partir de la contraseña en texto plano."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña contra un hash almacenado."""
        ...
```

#### `TokenService`
```python
class TokenService(ABC):
    """Puerto de salida para generar y verificar tokens JWT."""

    @abstractmethod
    def create_access_token(self, user_id: str) -> str:
        """Genera un Access Token JWT con expiración corta (15 min)."""
        ...

    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        """Genera un Refresh Token JWT con expiración larga (7 días)."""
        ...

    @abstractmethod
    def verify_token(self, token: str) -> str | None:
        """Verifica un token y retorna el user_id (sub). None si es inválido/expirado."""
        ...
```

---

## 4. Casos de Uso — `backend/application/use_cases.py`

### 4.1 `RegisterUserUseCase`

```python
class RegisterUserUseCase:
    """Caso de uso: registrar un nuevo usuario."""

    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher) -> None:
        ...

    def execute(self, email: str, username: str, password: str) -> User:
        """
        1. Validar que el email no esté registrado.
        2. Hashear la contraseña con el PasswordHasher.
        3. Crear la entidad User con Email y PasswordHash.
        4. Persistir y retornar.

        Raises:
            ValueError: Si el email ya está registrado.
        """
```

### 4.2 `LoginUserUseCase`

```python
class LoginUserUseCase:
    """Caso de uso: autenticar usuario y generar Token Pair."""

    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        ...

    def execute(self, email: str, password: str) -> tuple[User, str, str]:
        """
        1. Buscar usuario por email.
        2. Verificar contraseña con PasswordHasher.
        3. Generar Access Token + Refresh Token con TokenService.
        4. Retornar (user, access_token, refresh_token).

        Raises:
            ValueError: Si las credenciales son incorrectas (mensaje genérico para seguridad).
        """
```

### 4.3 `RefreshTokenUseCase`

```python
class RefreshTokenUseCase:
    """Caso de uso: renovar el Access Token usando el Refresh Token."""

    def __init__(self, user_repo: UserRepository, tokens: TokenService) -> None:
        ...

    def execute(self, refresh_token: str) -> tuple[str, str]:
        """
        1. Verificar el Refresh Token con TokenService.
        2. Buscar el usuario por user_id extraído del token.
        3. Generar nuevo Token Pair.
        4. Retornar (new_access_token, new_refresh_token).

        Raises:
            ValueError: Si el token es inválido, expirado o el usuario no existe.
        """
```

### 4.4 `GetCurrentUserUseCase`

```python
class GetCurrentUserUseCase:
    """Caso de uso: obtener el usuario actual a partir de un Access Token."""

    def __init__(self, user_repo: UserRepository, tokens: TokenService) -> None:
        ...

    def execute(self, access_token: str) -> User:
        """
        1. Verificar el Access Token.
        2. Buscar y retornar el usuario.

        Raises:
            ValueError: Si el token es inválido o el usuario no existe.
        """
```

---

## 5. Cambios en Persistencia

### 5.1 Tabla SQL — `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
```

### 5.2 `SQLiteUserRepository` — `backend/adapters/sqlite_adapter.py`

Implementa `UserRepository`:
- `save()`: INSERT con manejo de UNIQUE constraint (email duplicado → error descriptivo).
- `find_by_id()`: SELECT por id.
- `find_by_email()`: SELECT por email (normalizado a minúsculas).

### 5.3 `BcryptPasswordHasher` — `backend/adapters/auth_adapter.py` (nuevo archivo)

Implementa `PasswordHasher` usando la librería `bcrypt`:
- `hash()`: `bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()`
- `verify()`: `bcrypt.checkpw(password.encode(), hashed.encode())`

**Dependencia nueva:** `bcrypt` (pip install bcrypt).

### 5.4 `JWTTokenService` — `backend/adapters/auth_adapter.py`

Implementa `TokenService` usando la librería `PyJWT`:
- Constructor recibe `secret_key: str` (leído de variable de entorno o fallback para desarrollo).
- `create_access_token()`: payload `{"sub": user_id, "exp": now + 15min, "type": "access"}`.
- `create_refresh_token()`: payload `{"sub": user_id, "exp": now + 7days, "type": "refresh"}`.
- `verify_token()`: `jwt.decode(token, secret_key, algorithms=["HS256"])`, retorna `sub` o `None` si expirado/inválido.

**Dependencia nueva:** `PyJWT` (pip install PyJWT).

---

## 6. Cambios en la API

### 6.1 Nuevos Schemas — `backend/api/schemas.py`

```python
class UserRegisterRequest(BaseModel):
    email: str
    username: str
    password: str   # Texto plano — se hashea en el use case

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

### 6.2 Nuevo Router — `backend/api/routes/auth.py`

```
POST /api/auth/register
  Body: UserRegisterRequest
  Response 201: TokenResponse
  Set-Cookie: refresh_token (httpOnly, Secure, SameSite=Lax, Path=/api/auth, Max-Age=7d)

POST /api/auth/login
  Body: UserLoginRequest
  Response 200: TokenResponse
  Set-Cookie: refresh_token (httpOnly, Secure, SameSite=Lax, Path=/api/auth, Max-Age=7d)

POST /api/auth/refresh
  Cookie: refresh_token (enviada automáticamente por el navegador)
  Response 200: TokenResponse (nuevo access_token)
  Set-Cookie: refresh_token (nuevo, rotado)

POST /api/auth/logout
  Response 200: {"message": "Sesión cerrada"}
  Set-Cookie: refresh_token="" (Max-Age=0 para borrarla)

GET /api/auth/me
  Header: Authorization: Bearer <access_token>
  Response 200: UserResponse
```

### 6.3 Middleware de Autenticación — `backend/api/dependencies.py`

Crear una dependencia `get_current_user` que:
1. Lee el header `Authorization: Bearer <token>`.
2. Verifica el Access Token con `TokenService`.
3. Busca el usuario con `UserRepository`.
4. Retorna el `User` o lanza `HTTPException(401)`.

```python
async def get_current_user(
    authorization: str = Header(None),
    db: SQLiteConnection = Depends(get_db),
) -> User:
    ...
```

### 6.4 Proteger Endpoints Existentes

Por ahora, los endpoints existentes **NO** se protegerán para no romper la funcionalidad actual. La protección se activará en una feature futura (F-07). En F-06 solo se construye la infraestructura de autenticación y se expone el endpoint `GET /api/auth/me` como prueba de concepto de endpoint protegido.

### 6.5 Configuración de Cookies en `main.py`

- Configurar CORS para permitir credenciales (`allow_credentials=True`).
- Restringir `allow_origins` de `["*"]` a `["http://localhost:5173"]` (Vite dev server).

---

## 7. Cambios en el Frontend

### 7.1 Nuevos Tipos — `frontend/src/types/index.ts`

```typescript
export interface UserResponse {
  id: string;
  email: string;
  username: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  username: string;
  password: string;
}
```

### 7.2 Servicio de Autenticación — `frontend/src/services/auth.ts` (nuevo)

```typescript
let accessToken: string | null = null;

export function getAccessToken(): string | null { return accessToken; }
export function setAccessToken(token: string | null): void { accessToken = token; }

export async function register(data: RegisterInput): Promise<TokenResponse> { ... }
export async function login(data: LoginInput): Promise<TokenResponse> { ... }
export async function refresh(): Promise<TokenResponse> { ... }
export async function logout(): Promise<void> { ... }
export async function getMe(): Promise<UserResponse> { ... }
```

- Las llamadas a `/api/auth/login`, `/register` y `/refresh` incluyen `credentials: "include"` para que el navegador envíe/reciba cookies.
- Todas las demás llamadas autenticadas incluyen el header `Authorization: Bearer ${accessToken}`.

### 7.3 Interceptor en `api.ts`

Modificar `handleResponse` o crear un wrapper que:
1. Si la respuesta es `401`, intente llamar a `refresh()`.
2. Si el refresh tiene éxito, repita la petición original con el nuevo token.
3. Si el refresh falla, redirija a `/login`.

### 7.4 Páginas Nuevas

#### `frontend/src/pages/Login.tsx`
- Formulario con email + contraseña.
- Botón "Iniciar Sesión".
- Link "¿No tienes cuenta? Regístrate".
- Toast de error si credenciales incorrectas.

#### `frontend/src/pages/Register.tsx`
- Formulario con email + nombre de usuario + contraseña + confirmar contraseña.
- Validación: contraseñas coinciden.
- Botón "Crear Cuenta".
- Link "¿Ya tienes cuenta? Inicia Sesión".

### 7.5 Rutas en `App.tsx`

```tsx
<Route path="/login" element={<Login />} />
<Route path="/register" element={<Register />} />
```

### 7.6 Contexto de Autenticación — `frontend/src/components/AuthProvider.tsx`

```typescript
interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  login: (data: LoginInput) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
}
```

- Al montar la app, intenta un `refresh()` silencioso para recuperar la sesión.
- Si falla, el usuario queda como no autenticado.

---

## 8. Especificación de Tests

### Tests Unitarios — Dominio

| ID | Qué Verifica |
|---|---|
| **TU-01** | `Email("user@test.com")` se crea correctamente y se normaliza a minúsculas |
| **TU-02** | `Email("invalid")` lanza `ValueError` |
| **TU-03** | `Email("")` lanza `ValueError` |
| **TU-04** | `PasswordHash("$2b$12$...")` se crea correctamente |
| **TU-05** | `PasswordHash("plain_text")` lanza `ValueError` |
| **TU-06** | `User` se crea con email, password_hash y username válidos |
| **TU-07** | `User(username="")` lanza `ValueError` |
| **TU-08** | Dos `User` con el mismo `id` son iguales |

### Tests Unitarios — Casos de Uso

| ID | Qué Verifica |
|---|---|
| **TU-09** | `RegisterUserUseCase` crea usuario y retorna `User` |
| **TU-10** | `RegisterUserUseCase` con email duplicado lanza `ValueError` |
| **TU-11** | `LoginUserUseCase` con credenciales correctas retorna `(User, access, refresh)` |
| **TU-12** | `LoginUserUseCase` con email inexistente lanza `ValueError` |
| **TU-13** | `LoginUserUseCase` con contraseña incorrecta lanza `ValueError` |
| **TU-14** | `RefreshTokenUseCase` con token válido retorna nuevo par de tokens |
| **TU-15** | `RefreshTokenUseCase` con token expirado/inválido lanza `ValueError` |
| **TU-16** | `GetCurrentUserUseCase` con token válido retorna el `User` |

### Tests de Integración — API

| ID | Qué Verifica |
|---|---|
| **TI-01** | `POST /api/auth/register` con datos válidos → 201, response tiene `access_token` + `user`, y la respuesta incluye `Set-Cookie` con `refresh_token` |
| **TI-02** | `POST /api/auth/register` con email duplicado → 400 |
| **TI-03** | `POST /api/auth/login` con credenciales correctas → 200, response tiene `access_token` + `Set-Cookie` |
| **TI-04** | `POST /api/auth/login` con credenciales incorrectas → 401 |
| **TI-05** | `POST /api/auth/refresh` con cookie refresh válida → 200, nuevo `access_token` |
| **TI-06** | `POST /api/auth/refresh` sin cookie → 401 |
| **TI-07** | `GET /api/auth/me` con Access Token válido → 200, retorna `UserResponse` |
| **TI-08** | `GET /api/auth/me` sin token → 401 |
| **TI-09** | `POST /api/auth/logout` → 200, borra cookie |

### Verificaciones de Regresión

| ID | Qué Verifica |
|---|---|
| **V-01** | `npm run build` → exit 0 |
| **V-02** | `pytest tests/ -v` → todos los tests (existentes + nuevos) pasan |
| **V-03** | Los endpoints existentes de properties/incomes/expenses siguen funcionando sin autenticación |

### Comandos de Verificación

```bash
# V-01: Build frontend
cd /home/carlos/rental-handler/frontend && npm run build

# V-02: Tests completos
cd /home/carlos/rental-handler && venv/bin/python -m pytest tests/ -v

# V-03: Regresión manual de endpoints
curl http://localhost:8000/api/properties  # debe retornar 200
```

---

## 9. Requisitos No Funcionales

- **RN-01:** La contraseña NUNCA se almacena en texto plano. Solo el hash bcrypt.
- **RN-02:** El Access Token NUNCA se persiste en `localStorage` ni `sessionStorage`. Solo en memoria JavaScript.
- **RN-03:** El Refresh Token SOLO viaja en cookies `httpOnly` + `Secure` + `SameSite=Lax`.
- **RN-04:** Los mensajes de error de login NO revelan si el email existe o no ("Credenciales incorrectas" genérico).
- **RN-05:** El dominio no importa ni `bcrypt`, ni `PyJWT`, ni ninguna librería de auth. Todo va por puertos.
- **RN-06:** Los endpoints existentes NO se rompen. La protección con auth se hará en una feature futura (F-07).

---

## 📚 El Rincón del Estudiante

### ¿Por qué dos tokens y no uno? La analogía del hotel

Imagina que llegas a un hotel:

1. **El Registro** es el Login. Muestras tu DNI (email + contraseña) y te dan dos cosas:
   - **La tarjeta de la habitación** (Access Token): la llevas encima. Abre puertas rápidamente. Pero si la pierdes, alguien podría usarla. Por eso caduca al final del día (15 min en nuestro caso).
   - **Un brazalete de huésped** (Refresh Token): lo llevas en la muñeca (cookie httpOnly, invisible). No puedes quitártelo fácilmente. Cuando tu tarjeta caduca, solo tienes que ir a recepción, enseñar el brazalete, y te dan una tarjeta nueva sin volver a mostrar el DNI.

2. **¿Por qué no una sola tarjeta que dure mucho?** Porque si alguien la roba (ataque XSS), tendría acceso total durante todo ese tiempo. Con dos tokens, si roban el Access Token (que está en JS), solo tienen 15 minutos. El Refresh Token en la cookie `httpOnly` es inaccesible para scripts maliciosos.

### Comparativa: Estrategias de almacenamiento de tokens

| Estrategia | Access Token en... | Refresh Token en... | Seguridad XSS | Seguridad CSRF | Nuestro caso |
|---|---|---|---|---|---|
| **Todo en localStorage** | localStorage | localStorage | ❌ Vulnerable | ✅ Inmune | ❌ No |
| **Todo en cookies** | cookie httpOnly | cookie httpOnly | ✅ Protegido | ❌ Necesita CSRF token | ❌ No |
| **Híbrido (Shielded)** | Memoria JS | cookie httpOnly | ✅ Protegido | ✅ SameSite=Lax | ✅ Elegimos esta |

### ¿Qué es un Puerto de Auth y por qué no importar bcrypt directamente?

```python
# ❌ SIN PUERTOS — El dominio depende de bcrypt
# backend/domain/entities.py
import bcrypt  # ← PROHIBIDO en el dominio

class User:
    def verify_password(self, password):
        return bcrypt.checkpw(...)  # Acoplado a una librería externa
```

```python
# ✅ CON PUERTOS — El dominio define el contrato, el adaptador lo implementa
# backend/domain/ports.py
class PasswordHasher(ABC):
    @abstractmethod
    def verify(self, plain: str, hashed: str) -> bool: ...

# backend/adapters/auth_adapter.py
import bcrypt  # ← Solo aquí, en el adaptador

class BcryptPasswordHasher(PasswordHasher):
    def verify(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
```

Si mañana quisieras cambiar bcrypt por argon2 (un algoritmo más moderno), solo cambiarías `auth_adapter.py`. Los casos de uso, el dominio y los tests unitarios no cambiarían ni una línea.

### Anatomía de un JWT

Un JWT tiene 3 partes separadas por puntos: `xxxxx.yyyyy.zzzzz`

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTcyMjAwMH0.firma_secreta
│                      │                                                 │
└─ Header              └─ Payload (datos)                                └─ Firma
   {"alg": "HS256"}       {"sub": "user-123", "exp": 1722000}              HMAC-SHA256
```

- El **Header** dice qué algoritmo se usa para firmar.
- El **Payload** contiene los datos (quién eres, cuándo expira). NO está encriptado — cualquiera puede leerlo (está solo en base64). Por eso NUNCA pones la contraseña aquí.
- La **Firma** garantiza que nadie ha modificado el payload. Solo el servidor que conoce la `secret_key` puede generarla. Si alguien cambia el payload, la firma no coincide y el token se rechaza.
