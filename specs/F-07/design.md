# Especificación F-07: Frontend Route Protection and Auth Header (UI Guards & Navigation)

## 1. Visión General

Complementar la infraestructura de autenticación construida en **F-06** con dos piezas fundamentales del frontend:

1. **`ProtectedRoute`** — Componente envoltorio que intercepta el acceso a rutas privadas (`/`, `/properties/:id`) y redirige automáticamente a `/login` si el usuario no está autenticado.
2. **`AppHeader`** (Barra de Navegación) — Encabezado persistente visible en todas las rutas protegidas que muestra la identidad del usuario activo y un botón elegante de **"Cerrar Sesión"** (`logout`).

**Alcance:** Exclusivamente Frontend (React + TypeScript). **No se modifica el backend ni el dominio.**

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **ProtectedRoute** | Componente React que actúa como *guardia de ruta*. Envuelve rutas que requieren autenticación. Si `isAuthenticated` es `false`, redirige a `/login` con `<Navigate>`. |
| **PublicOnlyRoute** | Componente React que envuelve rutas públicas (`/login`, `/register`). Si el usuario ya está autenticado, redirige a `/` para evitar que vea formularios de auth innecesariamente. |
| **AppHeader** | Componente React que renderiza una barra de navegación fija en la parte superior de la aplicación. Muestra el logo, el nombre del usuario y un botón de logout. |
| **AuthGuard** | Concepto general que engloba `ProtectedRoute` + `PublicOnlyRoute`: el sistema que decide qué puede ver cada usuario según su estado de autenticación. |
| **Loading Screen** | Pantalla de espera con spinner que se muestra durante el refresco silencioso inicial (`AuthProvider.loading === true`) para evitar un flash de redirección a login cuando la sesión se está recuperando. |

---

## 3. Componentes Nuevos

### 3.1 `ProtectedRoute` — `frontend/src/components/ProtectedRoute.tsx`

```typescript
interface ProtectedRouteProps {
  children: ReactNode;
}
```

**Lógica:**
1. Lee `isAuthenticated` y `loading` del contexto `useAuth()`.
2. Si `loading === true` → renderiza un **Loading Screen** con spinner (reutilizando el estilo del design system existente).
3. Si `loading === false && !isAuthenticated` → renderiza `<Navigate to="/login" replace />`.
4. Si `loading === false && isAuthenticated` → renderiza `{children}` (la ruta protegida).

### 3.2 `PublicOnlyRoute` — `frontend/src/components/PublicOnlyRoute.tsx`

```typescript
interface PublicOnlyRouteProps {
  children: ReactNode;
}
```

**Lógica:**
1. Lee `isAuthenticated` y `loading` del contexto `useAuth()`.
2. Si `loading === true` → renderiza el **Loading Screen**.
3. Si `loading === false && isAuthenticated` → renderiza `<Navigate to="/" replace />` (ya estás logueado, no necesitas ver login/register).
4. Si `loading === false && !isAuthenticated` → renderiza `{children}`.

### 3.3 `AppHeader` — `frontend/src/components/AppHeader.tsx`

Barra de navegación premium, glassmorphism, fija en la parte superior:

```typescript
// No recibe props — consume useAuth() internamente
export default function AppHeader() { ... }
```

**Elementos visuales:**
- **Logo + Nombre de app** (izquierda): Icono 🏠 + "Gestión de Alquileres" con link a `/`.
- **Info de usuario** (derecha): Avatar circular con inicial del username + nombre de usuario + botón "Cerrar Sesión".
- **Animaciones**: Fade-in al montar, hover suave en el botón de logout.
- **Responsive**: En móvil, el nombre de la app se acorta y el username se oculta, quedando solo el avatar y el botón de logout.

---

## 4. Cambios en Archivos Existentes

### 4.1 `App.tsx` — Reestructuración de Rutas

```tsx
<Routes>
  {/* Rutas protegidas — requieren autenticación */}
  <Route path="/" element={
    <ProtectedRoute>
      <AppHeader />
      <PropertyList />
    </ProtectedRoute>
  } />
  <Route path="/properties/:id" element={
    <ProtectedRoute>
      <AppHeader />
      <PropertyDetail />
    </ProtectedRoute>
  } />

  {/* Rutas públicas — redirigen a / si ya estás logueado */}
  <Route path="/login" element={
    <PublicOnlyRoute>
      <Login />
    </PublicOnlyRoute>
  } />
  <Route path="/register" element={
    <PublicOnlyRoute>
      <Register />
    </PublicOnlyRoute>
  } />
</Routes>
```

### 4.2 `index.css` — Nuevos Estilos

Añadir secciones CSS para:
- `.app-header` — Barra fija con glassmorphism.
- `.app-header__logo`, `.app-header__user`, `.app-header__avatar` — Sub-componentes del header.
- `.app-header__logout-btn` — Botón de logout estilizado.
- `.loading-screen` — Pantalla de carga fullscreen durante el refresco silencioso.
- Ajustar `.page-container` con `padding-top` para no tapar contenido debajo del header fijo.

### 4.3 `services/api.ts` — Interceptor con Auto-Refresh

Modificar `handleResponse` para implementar un interceptor transparente de 401:
1. Si la respuesta es `401 Unauthorized`, intentar un `refresh()` silencioso.
2. Si el refresh tiene éxito, repetir la petición original con el nuevo access token.
3. Si el refresh falla, limpiar la sesión y redirigir a `/login`.

Esto garantiza que las llamadas a la API no fallen por tokens expirados de forma visible para el usuario.

### 4.4 `services/auth.ts` — Añadir función `clearSession()`

Añadir una función pública `clearSession()` que limpie el access token de memoria, útil para el interceptor cuando el refresh falla.

---

## 5. Flujos de Usuario

### 5.1 Flujo: Usuario NO autenticado intenta acceder a `/`

```
1. BrowserRouter monta la ruta `/`
2. ProtectedRoute lee isAuthenticated = false, loading = false
3. ProtectedRoute renderiza <Navigate to="/login" replace />
4. Usuario ve la página de login
```

### 5.2 Flujo: Usuario autenticado intenta acceder a `/login`

```
1. BrowserRouter monta la ruta `/login`
2. PublicOnlyRoute lee isAuthenticated = true
3. PublicOnlyRoute renderiza <Navigate to="/" replace />
4. Usuario ve el catálogo (con AppHeader visible)
```

### 5.3 Flujo: App se carga con sesión previa (cookie válida)

```
1. AuthProvider se monta → loading = true
2. ProtectedRoute muestra Loading Screen (spinner)
3. AuthProvider ejecuta refresh() silencioso → éxito
4. loading = false, isAuthenticated = true
5. ProtectedRoute renderiza children (catálogo + AppHeader)
```

### 5.4 Flujo: Logout desde AppHeader

```
1. Usuario hace clic en "Cerrar Sesión"
2. AppHeader llama logout() del AuthProvider
3. AuthProvider llama authService.logout() (borra cookie + limpia memoria)
4. user = null → isAuthenticated = false
5. ProtectedRoute detecta el cambio → <Navigate to="/login" />
```

### 5.5 Flujo: Access Token expira durante uso (Interceptor)

```
1. Usuario llama a GET /api/properties → 401
2. handleResponse detecta 401
3. Intenta refresh() silencioso
4. Éxito → guarda nuevo access token → repite la petición original
5. El usuario no nota ninguna interrupción
```

---

## 6. Especificación de Tests

> **Nota:** F-07 es una feature puramente de frontend. No hay cambios en el backend ni en el dominio, por lo que no se requieren tests unitarios de dominio ni tests de integración de API. Los tests se centran en verificación de build y tests E2E manuales.

### Verificaciones de Build y Regresión

| ID | Qué Verifica |
|---|---|
| **V-01** | `npm run build` en el frontend → exit 0 (sin errores de TypeScript) |
| **V-02** | `venv/bin/python -m pytest tests/ -v` → todos los tests existentes siguen pasando (no regresión) |

### Verificaciones Manuales (Checklist E2E)

| ID | Qué Verifica |
|---|---|
| **E2E-01** | Navegar a `/` sin estar logueado → redirige a `/login` |
| **E2E-02** | Navegar a `/properties/123` sin estar logueado → redirige a `/login` |
| **E2E-03** | Hacer login → redirige a `/` y se ve el AppHeader con nombre de usuario |
| **E2E-04** | Estando logueado, navegar a `/login` → redirige automáticamente a `/` |
| **E2E-05** | Estando logueado, navegar a `/register` → redirige automáticamente a `/` |
| **E2E-06** | Clic en "Cerrar Sesión" en AppHeader → redirige a `/login`, el header desaparece |
| **E2E-07** | Cerrar y reabrir pestaña con cookie válida → sesión se recupera automáticamente, se ve el catálogo |
| **E2E-08** | AppHeader muestra el nombre de usuario correctamente |

### Comandos de Verificación

```bash
# V-01: Build frontend
cd /home/carlos/rental-handler/frontend && npm run build

# V-02: Tests backend (regresión)
cd /home/carlos/rental-handler && venv/bin/python -m pytest tests/ -v
```

---

## 7. Requisitos No Funcionales

- **RN-01:** No se introduce ningún cambio en el backend. F-07 es 100% frontend.
- **RN-02:** El Loading Screen debe ser visualmente coherente con el design system existente (dark mode, Outfit font, colores del tema).
- **RN-03:** El AppHeader debe ser fijo (`position: fixed`) para que siempre esté visible al hacer scroll.
- **RN-04:** El AppHeader debe ser responsive: en pantallas < 768px, mostrar solo el avatar y el botón de logout.
- **RN-05:** La transición entre estados (loading → authenticated / not authenticated) debe ser suave, sin flashes de contenido.
- **RN-06:** Los tests existentes (94+ tests de pytest) no deben romperse.
- **RN-07:** El interceptor de 401 no debe crear bucles infinitos (si el refresh también falla con 401, no reintentar).

---

## 📚 El Rincón del Estudiante

### ¿Qué es un "Route Guard" y por qué lo necesitamos?

Imagina que tu aplicación web es un **edificio de oficinas**. Tiene una puerta principal (la URL `/`), salas de reuniones (URLs como `/properties/123`), y un vestíbulo público (la URL `/login`).

Sin guardias, cualquier persona que conozca la URL podría entrar directamente a cualquier sala. Un *Route Guard* es como un **guardia de seguridad en el ascensor**: antes de dejarte subir a una planta, te pide el carnet (tu token de autenticación). Si no lo tienes, te redirige al vestíbulo.

```
┌─────────────────────────────────────────────┐
│              SIN Route Guard                │
│                                             │
│  URL /properties/123  →  Se muestra la      │
│                          página (cualquiera  │
│                          puede ver los datos)│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│              CON Route Guard                │
│                                             │
│  URL /properties/123  →  ¿Autenticado?      │
│                          ├── ✅ Sí → Página  │
│                          └── ❌ No → /login  │
└─────────────────────────────────────────────┘
```

### ProtectedRoute vs PublicOnlyRoute: dos caras de la misma moneda

| Componente | ¿Qué protege? | ¿A quién deja pasar? | ¿A dónde redirige? |
|---|---|---|---|
| `ProtectedRoute` | Rutas privadas (`/`, `/properties/:id`) | Solo usuarios autenticados | → `/login` |
| `PublicOnlyRoute` | Rutas de auth (`/login`, `/register`) | Solo usuarios NO autenticados | → `/` |

¿Por qué necesitamos `PublicOnlyRoute`? Sin él, un usuario que ya tiene sesión activa podría visitar `/login` y ver un formulario de login innecesario. Peor aún, podría intentar loguearse con otra cuenta y crear confusión. `PublicOnlyRoute` dice: "Si ya estás dentro, no necesitas volver a la puerta".

### ¿Qué es el "Loading Screen" y por qué es crucial?

Cuando abres la app por primera vez, el `AuthProvider` necesita hacer un `refresh()` silencioso para saber si tienes una cookie válida de una sesión anterior. Esto tarda unos milisegundos. Sin un Loading Screen, pasa esto:

```
❌ SIN Loading Screen:
1. App se carga → isAuthenticated = false (aún no hemos comprobado la cookie)
2. ProtectedRoute ve false → redirige a /login
3. refresh() termina → "¡Ah, sí tenía sesión!"
4. Pero ya estamos en /login → flash molesto, mala experiencia
```

```
✅ CON Loading Screen:
1. App se carga → loading = true
2. ProtectedRoute ve loading → muestra spinner
3. refresh() termina → isAuthenticated = true, loading = false
4. ProtectedRoute ve autenticado → muestra el catálogo
5. Transición suave, sin flashes
```

### El patrón Interceptor: Renovación silenciosa del Access Token

El Access Token dura solo 15 minutos. Sin un interceptor, pasaría esto:

```
❌ SIN Interceptor:
1. Usuario trabaja durante 20 minutos
2. Hace clic en "Ver propiedad"
3. API responde 401 (token expirado)
4. Error en pantalla → usuario confundido
5. Tiene que cerrar sesión y volver a entrar
```

```
✅ CON Interceptor:
1. Usuario trabaja durante 20 minutos
2. Hace clic en "Ver propiedad"
3. API responde 401 → interceptor detecta el error
4. Interceptor llama a /api/auth/refresh (usando la cookie httpOnly)
5. Backend devuelve nuevo access token
6. Interceptor repite la petición original con el nuevo token
7. El usuario ve la propiedad sin notar nada
```

Es como si el guardia de seguridad, al ver tu carnet caducado, te acompañara automáticamente a renovarlo y te dejara pasar sin que tú tuvieras que hacer nada.

### ¿Qué es el glassmorphism del AppHeader?

El *glassmorphism* es una tendencia de diseño moderno que simula un cristal translúcido. Se consigue combinando:

```css
.app-header {
  background: rgba(10, 10, 10, 0.75);   /* Fondo semi-transparente */
  backdrop-filter: blur(24px);            /* Difumina lo que hay detrás */
  border-bottom: 1px solid rgba(255, 255, 255, 0.06); /* Borde sutil */
}
```

El resultado es un header que parece flotar sobre el contenido de la página, creando una sensación de profundidad y modernidad. Usamos las variables del design system existente (`--panel-bg`, `--panel-border`, `--bg-secondary`) para que sea coherente con el resto de la aplicación.
