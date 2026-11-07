# Modulo: Autenticacion, Identidad y Seguridad (`auth-and-security`)

> Subsistema funcional vertical responsable de la gestion de usuarios, credenciales, sesiones JWT, politicas de blindaje HTTP y rate limiting.

---

## 1. Responsabilidad y Alcance de Negocio
- Registro y autenticacion local con hashing seguro de contraseñas (`bcrypt`).
- Generacion y rotacion de tokens de sesion (`JWT`) con transporte seguro en cookies HTTP-only.
- Resolucion de usuario autenticado en dependencias de FastAPI (`get_current_user`).
- Gestion de direccion de reenvio de correo para automatizacion de facturas (`forwarding_email`).
- Blindaje perimetral: middleware de cabeceras de seguridad OWASP (CSP, HSTS, X-Content-Type) y rate limiting con ventana deslizante.

---

## 2. Artefactos del Corte Vertical
- **Dominio**:
  - Entidad: `User` (`backend/domain/entities.py`)
  - Puertos: `UserRepository`, `PasswordHasherPort`, `TokenServicePort` (`backend/domain/ports.py`)
- **Aplicacion (Casos de Uso)**:
  - `RegisterUserUseCase`, `LoginUserUseCase`, `RefreshTokenUseCase`, `GetCurrentUserUseCase`, `UpdateForwardingEmailUseCase` (`backend/application/use_cases.py`)
- **Adaptadores de Infraestructura**:
  - `SQLiteUserRepository` (`backend/adapters/sqlite_adapter.py`)
  - `BcryptPasswordHasherAdapter`, `PyJWTTokenServiceAdapter` (`backend/adapters/auth_adapter.py`)
- **API & Endpoints**:
  - Rutas: `backend/api/routes/auth.py` (`POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`, `PUT /api/auth/forwarding-email`)
  - Middlewares: `backend/api/middleware/security.py`, `backend/api/middleware/rate_limit.py`
- **Frontend**:
  - Vistas: `Login.tsx`, `Register.tsx`
  - Contexto & Guardias: `AuthProvider.tsx`, `ProtectedRoute.tsx`, `PublicOnlyRoute.tsx`
