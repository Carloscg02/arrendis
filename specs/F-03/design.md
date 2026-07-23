# 🧩 F-03: Frontend Implementation — Diseño Técnico

> **Feature:** F-03 — Frontend Implementation (React + TypeScript SPA)  
> **Versión:** 1.0-DRAFT  
> **Fecha:** 2026-07-16  
> **Referencia:** [architecture.md](file:///home/carlos/rental-handler/docs/architecture.md)  
> **Dependencia:** [F-02 design.md](file:///home/carlos/rental-handler/specs/F-02/design.md) (API Implementation — ✅ done)

---

## 1. Objetivo de la Feature

F-03 implementa la **interfaz de usuario web** (SPA) usando React y TypeScript. Esta interfaz es el "cliente HTTP" que consume la API REST construida en F-02, permitiendo al usuario interactuar visualmente con todas las funcionalidades del sistema.

```
   Navegador (Chrome)
       │
   ┌───▼────────────────────┐
   │   FRONTEND (F-03)      │  ← Esto es lo que construimos ahora
   │   React + TypeScript   │
   │   Vite dev server      │
   └───┬────────────────────┘
       │ fetch() → HTTP/JSON
   ┌───▼────────────────────┐
   │   BACKEND (F-01 + F-02)│  ← Ya construido
   │   FastAPI + Uvicorn    │
   └────────────────────────┘
```

### Qué NO hace esta feature
- **No añade lógica de negocio**: las validaciones y cálculos viven en el backend.
- **No modifica el backend**: no se toca `backend/` ni `tests/`.
- **No incluye autenticación**: eso será una feature posterior.

---

## 2. Lenguaje Ubicuo — Extensiones para F-03

| Término (EN) | Traducción | Definición |
|---|---|---|
| **Component** | Componente | Pieza reutilizable de UI en React (un botón, un formulario, una tarjeta). |
| **Hook** | Hook | Función especial de React (`useState`, `useEffect`) que permite gestionar estado y efectos secundarios dentro de un componente. |
| **Service** | Servicio | Módulo TypeScript que encapsula las llamadas HTTP a la API. El componente no sabe la URL ni el formato — solo llama al servicio. |
| **State** | Estado | Los datos que un componente "recuerda" entre renderizados (ej: la lista de propiedades cargadas). |
| **Props** | Propiedades | Datos que un componente padre le pasa a un componente hijo (ej: los datos de una propiedad para que la tarjeta los muestre). |

---

## 3. Pantallas y Funcionalidades

La aplicación tendrá **2 pantallas principales** conectadas por navegación:

### 3.1 Pantalla: Lista de Propiedades (`/`)

La pantalla principal. Muestra todas las propiedades registradas como tarjetas (cards) y permite crear nuevas.

**Elementos de UI:**
- **Cabecera**: Título de la aplicación ("Gestión de Alquileres").
- **Botón "Nueva Propiedad"**: Abre un formulario modal para crear una propiedad.
- **Grid de tarjetas (PropertyCard)**: Cada tarjeta muestra el nombre, dirección, tipo y estado de la propiedad. Al hacer click, navega al detalle.
- **Estado vacío**: Si no hay propiedades, se muestra un mensaje invitando a crear la primera.

**Llamadas a la API:**
- `GET /api/properties` → Cargar la lista al montar la página.
- `POST /api/properties` → Crear una nueva propiedad desde el formulario.

### 3.2 Pantalla: Detalle de Propiedad (`/properties/:id`)

Muestra toda la información financiera de una propiedad.

**Elementos de UI:**
- **Cabecera con nombre de la propiedad** y botón para volver a la lista.
- **Tarjeta de resumen (Profit Card)**: Muestra el beneficio neto, total ingresos y total gastos.
- **Sección de Ingresos**: Lista de ingresos registrados + botón "Registrar Ingreso" que abre un formulario modal.
- **Sección de Gastos**: Lista de gastos registrados + botón "Registrar Gasto" que abre un formulario modal.
- **Botón "Eliminar Propiedad"**: Con confirmación antes de borrar.

**Llamadas a la API:**
- `GET /api/properties/{id}` → Cargar datos de la propiedad.
- `GET /api/properties/{id}/incomes` → Cargar lista de ingresos.
- `GET /api/properties/{id}/expenses` → Cargar lista de gastos.
- `GET /api/properties/{id}/profit` → Cargar el beneficio neto.
- `POST /api/incomes` → Registrar un ingreso.
- `POST /api/expenses` → Registrar un gasto.
- `DELETE /api/properties/{id}` → Eliminar la propiedad.

---

## 4. Arquitectura del Frontend

Dentro del frontend, aplicamos una separación de responsabilidades similar a la del backend: **no mezclamos la lógica de red con la lógica visual**.

```
frontend/src/
├── services/          # Capa de Comunicación (fetch → API)
│   └── api.ts         # Todas las llamadas HTTP centralizadas
│
├── types/             # TypeScript Interfaces (contratos de datos)
│   └── index.ts       # Property, Income, Expense, ProfitReport
│
├── components/        # Componentes reutilizables de UI
│   ├── PropertyCard.tsx
│   ├── PropertyForm.tsx
│   ├── IncomeForm.tsx
│   ├── ExpenseForm.tsx
│   └── Modal.tsx
│
├── pages/             # Pantallas completas (1 por ruta)
│   ├── PropertyList.tsx
│   └── PropertyDetail.tsx
│
├── App.tsx            # Enrutamiento (React Router)
├── main.tsx           # Punto de entrada (ReactDOM.render)
└── index.css          # Estilos globales
```

### 4.1 Capa de Servicios (`services/api.ts`)

Centraliza todas las llamadas HTTP. Los componentes nunca usan `fetch()` directamente.

```typescript
const API_BASE = "http://localhost:8000/api";

// ── Properties ──
export async function getProperties(): Promise<Property[]> {
  const res = await fetch(`${API_BASE}/properties`);
  return res.json();
}

export async function createProperty(data: PropertyCreateInput): Promise<Property> {
  const res = await fetch(`${API_BASE}/properties`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPropertyById(id: string): Promise<Property> {
  const res = await fetch(`${API_BASE}/properties/${id}`);
  if (!res.ok) throw new Error("Property not found");
  return res.json();
}

export async function deleteProperty(id: string): Promise<void> {
  await fetch(`${API_BASE}/properties/${id}`, { method: "DELETE" });
}

// ── Incomes ──
export async function getIncomes(propertyId: string): Promise<Income[]> {
  const res = await fetch(`${API_BASE}/properties/${propertyId}/incomes`);
  return res.json();
}

export async function createIncome(data: IncomeCreateInput): Promise<Income> {
  const res = await fetch(`${API_BASE}/incomes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Expenses ──
export async function getExpenses(propertyId: string): Promise<Expense[]> {
  const res = await fetch(`${API_BASE}/properties/${propertyId}/expenses`);
  return res.json();
}

export async function createExpense(data: ExpenseCreateInput): Promise<Expense> {
  const res = await fetch(`${API_BASE}/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Profit ──
export async function getProfitReport(propertyId: string): Promise<ProfitReport> {
  const res = await fetch(`${API_BASE}/properties/${propertyId}/profit`);
  return res.json();
}
```

### 4.2 Tipos TypeScript (`types/index.ts`)

Definen los contratos de datos que el frontend espera del backend. Se alinean con los Schemas Pydantic de F-02.

```typescript
// ── Tipos de respuesta (lo que devuelve la API) ──
export interface Address {
  street: string;
  city: string;
  postal_code: string;
  country: string;
}

export interface Property {
  id: string;
  name: string;
  address: Address;
  property_type: string;
  status: string;
}

export interface Income {
  id: string;
  property_id: string;
  amount: string;  // Viene como string del backend (Decimal serializado)
  currency: string;
  date: string;
  category: string;
  description: string;
}

export interface Expense {
  id: string;
  property_id: string;
  amount: string;
  currency: string;
  date: string;
  category: string;
  description: string;
}

export interface ProfitReport {
  property_id: string;
  net_profit: string;
  currency: string;
}

// ── Tipos de creación (lo que enviamos a la API) ──
export interface PropertyCreateInput {
  name: string;
  address: Address;
  property_type: string;
}

export interface IncomeCreateInput {
  property_id: string;
  amount: number;
  date: string;      // "YYYY-MM-DD"
  category: string;
  description?: string;
}

export interface ExpenseCreateInput {
  property_id: string;
  amount: number;
  date: string;
  category: string;
  description?: string;
}
```

---

## 5. Stack y Tooling del Frontend

| Herramienta | Propósito |
|---|---|
| **Vite** | Bundler ultrarrápido para desarrollo. Sirve los archivos del frontend en `http://localhost:5173`. |
| **React 19** | Librería de UI basada en componentes. |
| **TypeScript** | Tipado estático sobre JavaScript. Previene errores antes de ejecutar. |
| **React Router** | Navegación entre pantallas (`/` y `/properties/:id`) sin recargar la página. |
| **Vanilla CSS** | Estilos sin frameworks adicionales (ni Tailwind ni Bootstrap). Control total. |

### Inicialización del Proyecto

```bash
cd /home/carlos/rental-handler/frontend
npx -y create-vite@latest ./ --template react-ts
npm install
npm install react-router-dom
```

---

## 6. Comunicación Frontend ↔ Backend (CORS)

Cuando desarrollamos en local, el frontend corre en el puerto `5173` (Vite) y el backend en el `8000` (Uvicorn). Son "orígenes" diferentes.

Por defecto, los navegadores bloquean las peticiones HTTP entre orígenes distintos por seguridad. Esto se llama **CORS** (Cross-Origin Resource Sharing).

En F-02, ya configuramos FastAPI para permitir todas las conexiones:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

Gracias a esto, el frontend podrá hacer `fetch("http://localhost:8000/api/...")` sin que el navegador lo bloquee.

---

## 7. Estructura de Archivos (Completa)

```
frontend/                        # 🖥️ FRONTEND — React + TypeScript (F-03)
├── public/
│   └── vite.svg
├── src/
│   ├── services/
│   │   └── api.ts               # Llamadas HTTP centralizadas
│   ├── types/
│   │   └── index.ts             # Interfaces TypeScript (Property, Income, etc.)
│   ├── components/
│   │   ├── PropertyCard.tsx      # Tarjeta visual de propiedad
│   │   ├── PropertyForm.tsx      # Formulario de creación de propiedad
│   │   ├── IncomeForm.tsx        # Formulario de registro de ingreso
│   │   ├── ExpenseForm.tsx       # Formulario de registro de gasto
│   │   └── Modal.tsx             # Componente modal reutilizable
│   ├── pages/
│   │   ├── PropertyList.tsx      # Pantalla principal (lista de propiedades)
│   │   └── PropertyDetail.tsx    # Pantalla de detalle financiero
│   ├── App.tsx                   # Router principal
│   ├── main.tsx                  # Entry point (ReactDOM)
│   └── index.css                 # Sistema de diseño y estilos globales
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**Total: ~13 archivos de producción frontend.**

---

## 8. Especificación de Tests

> [!NOTE]
> Los tests del frontend se abordarán en una feature posterior o como extensión de F-03, una vez que el frontend esté funcional. Para esta primera implementación, la verificación se hará mediante pruebas manuales en el navegador y verificación de compilación TypeScript (`npm run build`).

### Verificación Mínima
```bash
# 1. Compila sin errores de TypeScript
cd frontend && npm run build

# 2. Levantar frontend y backend simultáneamente y verificar:
#    - Crear una propiedad desde la UI
#    - Ver la propiedad en la lista
#    - Navegar al detalle
#    - Registrar un ingreso y un gasto
#    - Ver el beneficio neto calculado
```

---

## 📚 El Rincón del Estudiante: ¿Cómo funciona una SPA (Single Page Application)?

### El Problema: Las Páginas Web Clásicas

En la web tradicional (como las páginas de los años 2000), **cada vez que hacías click en un enlace**, el navegador hacía una petición al servidor, el servidor generaba un archivo HTML completo nuevo, y el navegador recargaba toda la pantalla desde cero. Era lento y producía parpadeos constantes.

```
Click en "Ver Propiedad"
    → Navegador pide HTML al servidor
    → Servidor genera TODA la página de nuevo
    → Navegador descarga y repinta TODO
    → La pantalla parpadea durante la carga
```

### La Solución: SPA (Single Page Application)

En una SPA como la nuestra, **el servidor solo envía un HTML vacío y un archivo JavaScript grande (el bundle) la primera vez**. A partir de ahí:

1. React "toma el control" del navegador.
2. Cuando haces click en "Ver Propiedad", React **no recarga la página**. En su lugar:
   - Hace una llamada `fetch()` a la API del backend (solo pide los datos JSON, no HTML).
   - Recibe un JSON pequeño (ej: `{"name": "Piso Centro", "status": "available"}`).
   - Actualiza **solo la parte de la pantalla** que cambió.
3. La URL del navegador cambia (de `/` a `/properties/abc123`), pero **no hay recarga**. Esto lo gestiona React Router.

```
Click en "Ver Propiedad"
    → React intercepta el click (no recarga)
    → fetch("http://localhost:8000/api/properties/abc123")
    → Recibe JSON: { name: "Piso Centro", ... }
    → React actualiza SOLO el componente de detalle
    → La pantalla cambia instantáneamente, sin parpadeo
```

### Analogía: Restaurante vs. Comida a Domicilio

- **Web Clásica (Restaurante)**: Cada vez que quieres comer, sales de casa, conduces al restaurante, esperas a que te sienten, pides, comes y vuelves. Todo el viaje se repite cada vez.
- **SPA (Comida a Domicilio)**: Ya estás en casa. Solo llamas por teléfono (fetch), te traen solo la comida (JSON), y la pones en tu mesa (actualizas el componente). No te mueves de tu sitio (no recargas la página).

### ¿Cómo encaja esto en nuestra Arquitectura Hexagonal?

El Frontend es **otro Adaptador de Entrada más**, exactamente como FastAPI. Solo que en lugar de vivir en el servidor, vive en el navegador del usuario:

```
  ┌──────────────────────────┐
  │  Frontend React (F-03)   │  ← Adaptador de Entrada (en el navegador)
  │  Llama a fetch()         │
  └──────────┬───────────────┘
             │ HTTP/JSON
  ┌──────────▼───────────────┐
  │  FastAPI (F-02)          │  ← Adaptador de Entrada (en el servidor)
  │  Traduce HTTP → Use Case │
  └──────────┬───────────────┘
             │
  ┌──────────▼───────────────┐
  │  Dominio (F-01)          │  ← No cambia. No sabe que existe React.
  └──────────────────────────┘
```

### ¿Por qué separamos `services/api.ts` de los componentes?

Es el mismo principio del backend: **separación de responsabilidades**.

| Sin separación (malo) | Con separación (nuestro proyecto) |
|---|---|
| El componente `PropertyList.tsx` tiene `fetch("http://localhost:8000/api/properties")` escrito directamente dentro | El componente llama a `getProperties()` del servicio. No sabe la URL. |
| Si la URL de la API cambia, hay que buscar y cambiar en 10 archivos diferentes | Si la URL cambia, solo se modifica `api.ts` (un solo archivo) |
| Si quieres hacer tests del componente, necesitas mockear `fetch` en cada test | Puedes mockear el servicio entero con facilidad |

---

> [!IMPORTANT]
> **Este documento está en estado DRAFT.** Requiere aprobación humana antes de proceder a la creación del plan de implementación. Ningún código fuente debe generarse hasta recibir la orden explícita.
