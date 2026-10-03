# 🔑 Épica E-06: Identidad Avanzada, Control de Cuentas y Observabilidad de Usuarios

> **Versión:** 1.0  
> **Estado:** Roadmap Definido / Especificaciones Iniciales Listas  
> **Fecha:** 2026-10-03  
> **Dependencias previas:** F-06 (Autenticación JWT) ✅, E-04 (Launch Readiness & Blindaje Web) ✅  

---

## 1. Objetivo de Negocio y Justificación

Proporcionar a **Arrendis** un sistema maduro de gestión de identidades, autenticación federada moderna (Google OAuth2), control administrativo granular sobre la activación y suspensión de cuentas de usuario (`is_active`), y registro de auditoría de actividad para garantizar la seguridad y supervisión del ciclo de vida del usuario.

### ¿Qué problemas resuelve esta épica?

1. **Fricción en el alta de usuarios (Password Fatigue):** Los usuarios y familiares prefieren autenticarse con un solo clic utilizando su cuenta de Google en lugar de tener que recordar otra contraseña y confirmar registros largos.
2. **Falta de control administrativo sobre quién accede a la plataforma:** Actualmente, cualquier persona que acceda a `/register` puede crearse una cuenta y empezar a crear registros en la base de datos de producción. El administrador necesita poder habilitar/deshabilitar cuentas (`is_active`) o poner la plataforma en modo lista de espera / acceso restringido por invitación.
3. **Puntos ciegos sobre actividad sospechosa o fallos de acceso:** No existe un registro de auditoría (*Audit Log*) que registre intentos de inicio de sesión fallidos, altas de usuarios, o cambios de estado de cuentas para responder ante incidentes de seguridad o dar soporte a usuarios con problemas de acceso.

---

## 2. Límites del Subdominio (Bounded Context)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ÉPICA E-06: IDENTIDAD AVANZADA Y CONTROL DE CUENTAS                    │
│                                                                        │
│   [ F-44: Control Administrativo y Estado de Cuentas (is_active) ]     │
│   [ F-45: Autenticación Social Federada con Google OAuth2 ]           │
│   [ F-46: Registro de Auditoría de Accesos y Métricas de Usuarios ]    │
└────────────────────────────────────────────────────────────────────────┘
```

### ✅ Lo que ENTRA en esta épica:
- **Modelo de Dominio y Persistencia de Usuario:**
  - Incorporación del campo `is_active: bool = True` (o configurable por defecto a `False` en modo lista de espera/invitación) y `auth_provider: str = 'local' | 'google'` en la entidad `User` y en la tabla `users` de SQLite.
  - Validación de estado activo en los casos de uso de autenticación (`LoginUserUseCase`, `RefreshTokenUseCase` y autenticación por bearer token). Si `is_active == False`, se bloquea el acceso con código `403 Forbidden`.
  - Capacidad administrativa (vía comando CLI o endpoint protegido) para activar, desactivar o consultar el estado de cuentas.
- **Autenticación con Google (OAuth2 / OIDC):**
  - Integración en frontend del botón oficial de Google Identity Services (*Sign in with Google*).
  - Endpoint en backend `/api/auth/google` que valida criptográficamente el `id_token` de Google (mediante clave pública de Google / `google-auth` library) sin comprometer secretos del cliente.
  - Creación automática o vinculación de usuario existente por correo electrónico y emisión de tokens JWT habituales de Arrendis.
- **Auditoría y Métricas:**
  - Tabla de auditoría `user_audit_events` (marcas de tiempo, evento: `LOGIN_SUCCESS`, `LOGIN_FAILED`, `REGISTER`, `DEACTIVATED`, IP anonimizada y User-Agent).
  - Endpoint de métricas de actividad básica para el administrador.

### ❌ Lo que NO entra en esta épica:
- Pasarelas de pago o suscripciones monetizadas (Stripe).
- Roles complejos multi-organización (RBAC jerárquico enterprise): Arrendis opera con usuarios particulares propietarios de inmuebles.

---

## 3. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Federated Identity** | Mecanismo que delega la autenticación de usuarios en un proveedor de identidad de confianza externo (Google) mediante protocolos abiertos (OIDC / OAuth 2.0). |
| **Google ID Token** | Token JWT firmado criptográficamente por los servidores de Google que certifica la identidad y el correo electrónico verificado del usuario. |
| **is_active** | Indicador booleano que determina si un usuario tiene permiso activo para interactuar con la plataforma o si se encuentra suspendido/pendiente de aprobación. |
| **Soft Suspension / Ban** | Estado donde la cuenta de usuario se conserva intacta en la base de datos pero se le deniega el acceso a la API mediante un código `403 Forbidden`. |
| **Audit Log** | Registro inmutable de eventos de seguridad que permite trazar cuándo y desde dónde se produjeron inicios de sesión o modificaciones de estado. |

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
│   │ GoogleOAuthAdapter (Valida firma con google.oauth2.id_token) │    │
│   └──────────────────────────────┬───────────────────────────────┘    │
│                                  │ Extrae email verificado            │
│   ┌──────────────────────────────▼───────────────────────────────┐    │
│   │ GoogleLoginUseCase (Application)                             │    │
│   │ - Busca o crea User en SQLiteUserRepository                   │    │
│   │ - Verifica que user.is_active == True                        │    │
│   │ - Emite Access JWT + Refresh Cookie propios de Arrendis      │    │
│   │ - Registra evento en AuditLogRepository                      │    │
│   └──────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Desglose de Features Propuestas

### 1. `F-44`: Control Administrativo del Estado de Cuentas (`is_active`) y Política de Acceso
- Ampliación de la entidad `User` en `backend/domain/entities.py` con el atributo `is_active: bool = True`.
- Migración de esquema en `SQLiteUserRepository` añadiendo columna `is_active INTEGER DEFAULT 1`.
- Validación en use cases de autenticación y dependencias (`get_current_user`): usuarios inactivos reciben `HTTP 403 Forbidden: Cuenta inactiva o pendiente de aprobación`.
- Script / comando CLI administrativo `python -m backend.manage_users` para listar usuarios y conmutar su estado `is_active`.

### 2. `F-45`: Autenticación Social Federada con Google OAuth2 (Google Identity Services)
- Puerto de infraestructura `OAuthVerifierPort` y adaptador `GoogleOAuthVerifierAdapter` que valida el `id_token` utilizando la librería oficial o verificación criptográfica JWT contra los certificados públicos de Google (`https://www.googleapis.com/oauth2/v3/certs`).
- Endpoint `/api/auth/google` que procesa el token y retorna los JWTs nativos de Arrendis.
- Integración en frontend del botón oficial de Google en las páginas de Login y Registro (`<GoogleLoginButton />`) respetando el estilo editorial Atelier.

### 3. `F-46`: Registro de Auditoría de Accesos y Métricas Operativas de Usuarios
- Entidad `UserAuditEvent` y tabla SQLite `user_audit_log` para registrar eventos relevantes de ciclo de vida.
- Almacenamiento seguro de direcciones IP con anonimización / hashing para cumplimiento con el RGPD.
- Endpoint administrativo protegido `/api/admin/metrics` para consultar totales de usuarios activos, registros semanales e incidentes de acceso.

---

## 6. Criterios de Aceptación Globales de la Épica

- [ ] Un usuario con `is_active = False` no puede iniciar sesión ni realizar peticiones autenticadas a ningún endpoint de la API.
- [ ] Un usuario puede registrarse o iniciar sesión mediante el botón "Continuar con Google" de forma transparente en menos de 2 segundos.
- [ ] Los usuarios dados de alta mediante Google comparten el mismo modelo de datos y aislamiento que los usuarios locales.
- [ ] Cada inicio de sesión exitoso o fallido queda registrado en el log de auditoría con marca de tiempo e IP.
- [ ] Todos los tests unitarios y de integración de usuarios y autenticación pasan al 100%.
