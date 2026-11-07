# 🔑 Épica E-06: Autenticación Social Federada con Google OAuth2

> **Versión:** 2.0  
> **Estado:** 📋 Backlog / Especificación de Visión y Dominio Lista  
> **Fecha de actualización:** 2026-10-10  
> **Dependencias previas:** F-06 (Autenticación JWT) ✅, E-04 (Launch Readiness & Blindaje Web) ✅  

---

## 1. Objetivo de Negocio y Justificación

Proporcionar a **Arrendis** un flujo de autenticación e inicio de sesión moderno y sin fricción mediante **Google OAuth2 / OIDC (Google Identity Services)**, permitiendo a propietarios particulares y colaboradores acceder a la plataforma con un solo clic, reduciendo drásticamente la tasa de abandono en el registro por fatiga de contraseñas (*Password Fatigue*).

### ¿Qué problemas resuelve esta épica?

1. **Fricción y abandono en el alta de usuarios:** Recordar contraseñas adicionales y rellenar formularios largos desmotiva al usuario en su primera toma de contacto con la aplicación.
2. **Validación automática de email:** Con Google Identity Services, la identidad y el correo electrónico del usuario ya vienen verificados directamente por Google, evitando cuentas falsas y flujos engorrosos de activación vía email.
3. **Mantenimiento y unificación del modelo de seguridad:** Los usuarios registrados con Google se integran de manera transparente con el esquema de tokens JWT nativos (Access Token en memoria + Refresh Token en cookie `HttpOnly` blindada) y la política de aislamiento multi-inquilino de Arrendis.

---

## 2. Límites del Subdominio (Bounded Context)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ÉPICA E-06: AUTENTICACIÓN SOCIAL FEDERADA CON GOOGLE OAUTH2            │
│                                                                        │
│   [ F-44: Extensión del Modelo de Dominio de Usuario (auth_provider) ] │
│   [ F-45: Integración Google Identity Services y Verificación OIDC ]   │
│   [ F-46: Experiencia UI de Login/Registro Social en Atelier ]        │
└────────────────────────────────────────────────────────────────────────┘
```

### ✅ Lo que ENTRA en esta épica:
- **Modelo de Dominio y Persistencia de Usuario:**
  - Incorporación del campo `auth_provider: str = 'local' | 'google'` (y `google_id: Optional[str]`) en la entidad `User` y migración de esquema en `SQLiteUserRepository`.
  - Política de vinculación (*account linking*): si un usuario se registra con Google y su email coincide con una cuenta local previa, se valida y unifica respetando el aislamiento de datos.
- **Autenticación con Google (OAuth2 / OIDC):**
  - Puerto de infraestructura `OAuthVerifierPort` desacoplado del framework.
  - Adaptador `GoogleOAuthVerifierAdapter` que valida criptográficamente el `id_token` de Google mediante certificados públicos oficiales (`https://www.googleapis.com/oauth2/v3/certs`) o `google-auth`, verificando `aud` (Client ID) para evitar ataques de *Confused Deputy*.
  - Endpoint en backend `/api/auth/google` que procesa el token de Google y expide la dupla habitual de JWT Access Token y Refresh Cookie de Arrendis.
- **Frontend & UX (Atelier Editorial):**
  - Botón oficial *Sign in with Google* integrado de forma nativa en `/login` y `/register`, adaptado armónicamente al diseño editorial Atelier y accesible en PWA/móvil.

### ❌ Lo que NO entra en esta épica:
- Auditoría, eventos de seguridad y métricas operativas (desacoplado formalmente a **Épica E-08: Monitoreo, Trazabilidad y Auditoría**).
- Otros proveedores sociales (Apple ID, GitHub, Microsoft).
- Gestión de permisos y roles organizacionales enterprise (RBAC complejo).

---

## 3. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Federated Identity** | Mecanismo que delega la verificación de la identidad del usuario en un proveedor externo de confianza (Google) mediante OpenID Connect (OIDC). |
| **Google ID Token** | Token JWT emitido y firmado criptográficamente por los servidores de Google que certifica la identidad y el correo electrónico verificado del usuario. |
| **auth_provider** | Indicador en la entidad `User` que identifica el origen de la credencial (`'local'` para email/password, `'google'` para autenticación federada). |
| **Confused Deputy Prevention** | Validación estricta en backend que comprueba que el claim `aud` del token coincide con el `GOOGLE_CLIENT_ID` registrado de Arrendis, evitando la reutilización de tokens firmados para otras aplicaciones. |

---

## 4. Arquitectura Técnica de la Solución

```
[ Navegador Web / PWA ]
       │
       ├─► 1. Clic en "Continuar con Google" (Google Identity Services SDK)
       ├─► 2. Recibe Google ID Token firmado por accounts.google.com
       │
       ▼ 3. POST /api/auth/google { "id_token": "..." }
┌────────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend (Hexagonal)                                            │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ GoogleOAuthVerifierAdapter (OAuthVerifierPort)               │    │
│   │ - Valida firma criptográfica con certificados de Google      │    │
│   │ - Valida aud == GOOGLE_CLIENT_ID (Anti-Confused Deputy)      │    │
│   └──────────────────────────────┬───────────────────────────────┘    │
│                                  │ Retorna { email, sub, name }       │
│   ┌──────────────────────────────▼───────────────────────────────┐    │
│   │ GoogleAuthUseCase (Application)                              │    │
│   │ - Busca o provisiona User en SQLiteUserRepository           │    │
│   │ - Emite Access JWT + Refresh Cookie propios de Arrendis      │    │
│   └──────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Desglose de Features

### 1. `F-44`: Extensión del Modelo de Dominio de Usuario (`auth_provider` y `google_id`)
- Extensión de la entidad `User` en `backend/domain/entities.py` con atributos para proveedor de autenticación.
- Migración de esquema en `SQLiteUserRepository` manteniendo retrocompatibilidad total con usuarios locales existentes (`auth_provider DEFAULT 'local'`).
- Pruebas unitarias de entidad y persistencia en repositorio.

### 2. `F-45`: Integración Google Identity Services y Verificación Criptográfica OIDC
- Creación de puerto `OAuthVerifierPort` en `backend/domain/ports.py`.
- Adaptador `GoogleOAuthVerifierAdapter` en `backend/infrastructure/auth/` con verificación de firmas públicas y expiración.
- Caso de uso `GoogleAuthUseCase` y endpoint HTTP `POST /api/auth/google`.
- Emisión de cookies blindadas (`HttpOnly`, `SameSite=Lax/Strict`, `Secure`) y tokens estándar de sesión.

### 3. `F-46`: Experiencia UI de Login/Registro Social en Atelier
- Carga asíncrona segura de Google Identity Services SDK en frontend sin degradar Core Web Vitals.
- Componente `<GoogleSignInButton />` integrado en pantallas `/login` y `/register`.
- Manejo elegante de errores de red, permisos denegados o fallos de verificación con toasts Atelier.

---

## 6. Criterios de Aceptación Globales de la Épica

- [ ] Un usuario nuevo puede registrarse y quedar autenticado con Google en menos de 2 segundos sin rellenar formularios manuales.
- [ ] Un usuario registrado previamente con contraseña que inicie sesión con su misma cuenta de Google accede a sus propiedades sin duplicar inquilino ni perder datos.
- [ ] Toda petición a `/api/auth/google` sin un `id_token` válido o con `aud` no coincidente devuelve `401 Unauthorized` de forma inmediata.
- [ ] El flujo es 100% responsive y opera correctamente tanto en navegador de escritorio como en PWA móvil.
- [ ] La cobertura de tests de use case y endpoint para Google Auth alcanza el 100% de los escenarios críticos (éxito, token inválido, token expirado).
