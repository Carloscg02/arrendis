# Especificación F-04: Rediseño Premium del Frontend

## 1. Visión General

Transformar la interfaz funcional de F-03 en una experiencia **PropTech Premium** utilizando los principios de la skill `design-taste-frontend`. El objetivo es pasar de una UI "que funciona" a una UI "que enamora", sin alterar la lógica de negocio ni los contratos con la API.

**Design Read:** *"Reading this as: panel de gestión inmobiliaria para propietarios particulares, con un lenguaje visual limpio tipo Linear/Stripe, leaning toward CSS custom properties + Inter + micro-animaciones con motion/react."*

**Dials:**

| Dial | Valor | Justificación |
|---|---|---|
| `DESIGN_VARIANCE` | 7 | Moderno con toques asimétricos, pero estructurado (sector financiero) |
| `MOTION_INTENSITY` | 6 | Transiciones suaves y feedback táctil, sin exagerar |
| `VISUAL_DENSITY` | 4 | Espacios generosos — los datos financieros necesitan respirar |

---

## 2. Lenguaje Ubicuo

| Término | Definición en este proyecto |
|---|---|
| **Design Tokens** | Variables CSS (colores, tipografía, radios, sombras) centralizadas en `:root` que definen toda la identidad visual |
| **Glass Panel** | Componente visual con fondo semi-transparente + `backdrop-filter: blur()` + borde sutil, heredado de F-03 |
| **Toast / Notificación** | Mensaje emergente temporal (3-5s) que reemplaza a los `alert()` nativos del navegador para feedback contextual |
| **Skeleton Loader** | Placeholder animado que replica la forma del contenido mientras se cargan datos de la API |
| **Micro-interacción** | Animación sutil (< 300ms) que da feedback al usuario: hover en botones, transiciones de entrada, press effect |
| **Estado Vacío (Empty State)** | Vista diseñada que se muestra cuando no hay datos, con mensaje orientativo y CTA para empezar |
| **Focus Ring** | Indicador visual de foco en inputs y botones para navegación por teclado (accesibilidad) |

---

## 3. Sistema de Diseño (Design Tokens Concretos)

### 3.1 Paleta de Colores

Dirección estética: **"Cobalt + Slate"** — azul profundo contra grises fríos, con acento esmeralda para acciones positivas. Evita el "AI purple" y el "beige+brass" por defecto.

| Token | Hex | Uso |
|---|---|---|
| `--bg-primary` | `#0c1222` | Fondo principal de la aplicación |
| `--bg-secondary` | `#111827` | Fondo de secciones alternas |
| `--panel-bg` | `rgba(17, 24, 39, 0.80)` | Fondo de Glass Panels |
| `--panel-border` | `rgba(255, 255, 255, 0.08)` | Bordes sutiles de paneles |
| `--accent-primary` | `#10b981` | CTA principal, indicadores positivos (ingresos) |
| `--accent-primary-hover` | `#059669` | Hover del acento principal |
| `--accent-secondary` | `#3b82f6` | Enlaces, badges informativas, detalles secundarios |
| `--danger` | `#ef4444` | Acciones destructivas (eliminar), indicadores negativos (gastos) |
| `--danger-hover` | `#dc2626` | Hover de acciones destructivas |
| `--text-primary` | `#f1f5f9` | Texto principal (contraste ≥ 15:1 sobre fondo) |
| `--text-secondary` | `#94a3b8` | Texto secundario (contraste ≥ 4.8:1 sobre fondo) |
| `--text-muted` | `#64748b` | Texto terciario — solo decorativo, nunca información crítica |
| `--toast-success-bg` | `rgba(16, 185, 129, 0.15)` | Fondo de toast de éxito |
| `--toast-error-bg` | `rgba(239, 68, 68, 0.15)` | Fondo de toast de error |

### 3.2 Tipografía

| Elemento | Fuente | Peso | Tamaño | Tracking |
|---|---|---|---|---|
| Títulos de página (h1) | Inter | 700 | `2rem` / `2.5rem` (desktop) | `-0.025em` |
| Subtítulos (h2, h3) | Inter | 600 | `1.25rem` / `1.5rem` | `-0.015em` |
| Cuerpo | Inter | 400 | `1rem` | `0` |
| Labels de formulario | Inter | 500 | `0.875rem` | `0.01em` |
| Badges / Tags | Inter | 600 | `0.75rem` | `0.05em` |
| Importes financieros | Inter | 700 | `2.5rem` / `3rem` | `-0.02em` |

> **Nota:** Se mantiene Inter como fuente del proyecto. El reviewer recomendó Geist como alternativa, pero Inter ya está integrada y es apropiada para dashboards financieros (legibilidad de cifras). La skill `design-taste-frontend` permite Inter cuando el brief es "standard / Linear-style".

### 3.3 Esquinas y Sombras

| Token | Valor | Uso |
|---|---|---|
| `--radius-xl` | `20px` | Paneles principales, profit card |
| `--radius-lg` | `12px` | Cards de propiedades, modales |
| `--radius-md` | `8px` | Inputs, selects, textareas |
| `--radius-sm` | `6px` | Badges, botones pequeños |
| `--radius-pill` | `999px` | Badges de estado |
| `--shadow-card` | `0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -2px rgba(0,0,0,0.2)` | Elevación base |
| `--shadow-card-hover` | `0 20px 25px -5px rgba(0,0,0,0.4), 0 8px 10px -6px rgba(0,0,0,0.3)` | Elevación en hover |
| `--shadow-modal` | `0 25px 50px -12px rgba(0,0,0,0.6)` | Sombra del modal |

### 3.4 Transiciones

| Propiedad | Duración | Easing |
|---|---|---|
| Hover de botones | `150ms` | `ease-out` |
| Hover de cards | `250ms` | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Entrada de modales | `300ms` | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Fade-in de toasts | `200ms` | `ease-out` |
| Fade-out de toasts | `300ms` | `ease-in` |
| Press effect (`:active`) | `100ms` | `ease-in` |

---

## 4. Requisitos de Negocio (Invariables)

- **RN-01:** Mantener TODA la funcionalidad existente: CRUD de propiedades, registro de ingresos/gastos, informe de beneficio.
- **RN-02:** Preservar la localización completa en español.
- **RN-03:** No modificar ningún contrato de la API del backend (schemas, endpoints, respuestas).
- **RN-04:** No alterar la arquitectura hexagonal ni el dominio.

---

## 5. Desglose de Componentes a Rediseñar

### 5.1 Componentes Existentes a Modificar

| Componente | Archivo | Cambios |
|---|---|---|
| **PropertyList** | `pages/PropertyList.tsx` | Skeleton loaders durante carga. Empty state con ilustración/icono y CTA. Toast en lugar de `alert()` al crear propiedad |
| **PropertyDetail** | `pages/PropertyDetail.tsx` | Dashboard con 3 KPI cards separadas (Ingresos Totales, Gastos Totales, Beneficio Neto). Toasts para feedback. Confirmación de borrado con modal estilizado en lugar de `window.confirm()` |
| **PropertyCard** | `components/PropertyCard.tsx` | Efecto hover con elevación progresiva + scale sutil. Icono de tipo de propiedad (en lugar de solo badge texto) |
| **PropertyForm** | `components/PropertyForm.tsx` | Inputs con focus ring visible. Placeholder como hint (no como label). Botón con estado de carga (spinner) |
| **IncomeForm** | `components/IncomeForm.tsx` | Mismas mejoras que PropertyForm |
| **ExpenseForm** | `components/ExpenseForm.tsx` | Mismas mejoras que PropertyForm |
| **Modal** | `components/Modal.tsx` | Animación de entrada (scale + fade). Cierre con tecla `Escape`. Trap de foco para accesibilidad |

### 5.2 Componentes Nuevos a Crear

| Componente | Archivo | Responsabilidad |
|---|---|---|
| **Toast / ToastProvider** | `components/Toast.tsx` | Sistema de notificaciones contextuales. Variantes: `success`, `error`, `info`. Auto-dismiss a los 4 segundos. Posición: esquina superior derecha |
| **KPICard** | `components/KPICard.tsx` | Tarjeta individual de métrica financiera con icono, label, valor formateado y color contextual |
| **SkeletonLoader** | `components/SkeletonLoader.tsx` | Esqueleto animado que replica la forma de PropertyCard y de las tablas de datos |
| **ConfirmDialog** | `components/ConfirmDialog.tsx` | Modal de confirmación estilizado que reemplaza a `window.confirm()` |

### 5.3 Archivo de Estilos

| Archivo | Cambios |
|---|---|
| `index.css` | Refactorizar completamente aplicando los Design Tokens de la Sección 3. Añadir clases para Toast, KPICard, SkeletonLoader, ConfirmDialog. Añadir animaciones `@keyframes` para skeleton pulse, toast slide-in/out. Añadir estados `:active` con press effect (`scale(0.98)`) en todos los botones. Añadir media queries explícitas para `< 768px` |

---

## 6. Dependencias

| Paquete | Versión | Justificación | Acción |
|---|---|---|---|
| `motion` | `^12.x` | Animaciones de entrada en modales, hover physics, scroll-reveal. Import: `motion/react` | `npm install` |

> **Nota:** No se añade librería de iconos ni de toasts de terceros. Los toasts se implementan como componente propio (más ligero, más control). Los iconos se resuelven con emojis/unicode ya presentes o SVG inline mínimos.

---

## 7. Especificación de Tests

> **Importante:** F-04 es un rediseño visual. Los tests existentes (58 unit + integration) NO deben romperse. Se añaden verificaciones específicas de UI.

| ID | Tipo | Qué Verifica |
|---|---|---|
| **V-01** | Build | `npm run build` en `frontend/` termina con código de salida 0 |
| **V-02** | Grep | `grep -r "alert(" frontend/src/` devuelve 0 resultados (cero `alert()` nativos) |
| **V-03** | Grep | `grep -r "window.confirm" frontend/src/` devuelve 0 resultados |
| **V-04** | Backend | `cd /home/carlos/rental-handler && venv/bin/python -m pytest tests/ -v` — los 58 tests existentes pasan |
| **V-05** | Visual | Todos los botones tienen estados `:hover`, `:active` y `:focus-visible` distinguibles |
| **V-06** | A11y | Texto principal sobre fondo: ratio de contraste ≥ 4.5:1 (WCAG AA) |
| **V-07** | A11y | Labels de formulario sobre fondo de input: ratio ≥ 4.5:1 |
| **V-08** | Responsive | La UI es navegable sin scroll horizontal en viewport de 375px de ancho |
| **V-09** | Idioma | Toda la interfaz visible está en español. Verificable con inspección manual |

### Comandos de Verificación (ejecutar en orden)

```bash
# V-01: Build exitoso
cd /home/carlos/rental-handler/frontend && npm run build

# V-02: Cero alert() nativos
grep -rn "alert(" /home/carlos/rental-handler/frontend/src/ && echo "FAIL: alert() encontrado" || echo "PASS"

# V-03: Cero window.confirm
grep -rn "window.confirm" /home/carlos/rental-handler/frontend/src/ && echo "FAIL: window.confirm encontrado" || echo "PASS"

# V-04: Tests backend intactos
cd /home/carlos/rental-handler && venv/bin/python -m pytest tests/ -v
```

---

## 8. Restricciones de la Skill `design-taste-frontend`

Reglas explícitas que el implementador DEBE respetar:

- ❌ **No AI purple/violet** como color por defecto.
- ❌ **No beige + brass + espresso** (la paleta premium-consumer baneada).
- ❌ **No Inter como fuente de display si hay alternativa mejor** — en nuestro caso, Inter se justifica por coherencia con F-03 y adecuación a dashboard financiero.
- ❌ **No placeholder-as-label** en formularios. Label siempre encima del input.
- ❌ **No sombras pure-black** sobre fondos claros (usar sombras tintadas al tono del fondo).
- ❌ **No `h-screen`** para secciones full-height. Usar `min-h-[100dvh]` o equivalente CSS.
- ✅ **Press effect** en `:active` de todos los botones (`scale(0.98)` o `translateY(1px)`).
- ✅ **Focus ring visible** en todos los elementos interactivos.
- ✅ **Skeleton loaders** en lugar de texto "Cargando..." genérico.
- ✅ **Toasts contextuales** en lugar de `alert()`.
- ✅ **Un único tema (dark)** en toda la aplicación, sin inversiones de sección.

---

## 📚 El Rincón del Estudiante

### ¿Por qué rediseñamos ahora y no lo hicimos perfecto desde el principio?

**Analogía del mundo real: El chasis y la carrocería de un coche.**

Imagina que estás construyendo un coche. Primero montas el chasis (motor, transmisión, frenos) — eso fue F-01 (dominio) y F-02 (API). Después le pones una carrocería funcional para poder probarlo en la carretera — eso fue F-03 (frontend funcional). Ahora que sabes que el coche arranca, frena y gira correctamente, puedes llevar esa carrocería al taller de pintura y diseño para convertirla en algo que la gente quiera comprar.

En ingeniería de software esto sigue el mantra:
> **"Make it work → Make it right → Make it beautiful"**

Si hubiésemos invertido horas en diseño premium antes de saber si la API respondía bien o si el flujo de datos era correcto, habríamos arriesgado tener que rehacer todo ese trabajo visual.

### Comparativa: UI Genérica (Slop) vs. UI con Design Tokens

| Aspecto | ❌ Sin sistema de diseño (Slop) | ✅ Con Design Tokens (F-04) |
|---|---|---|
| Colores | Cada componente elige su propio `#hex` a mano | Todos usan `var(--accent-primary)` → cambio global en 1 línea |
| Errores | `alert("Error creating property")` — bloquea al usuario | Toast contextual que desaparece solo y no interrumpe |
| Carga de datos | Texto plano "Cargando..." | Skeleton loader que anticipa la forma del contenido |
| Feedback táctil | El botón no reacciona al clic | Press effect `scale(0.98)` + transición suave → sensación física |
| Accesibilidad | Sin indicador de foco, imposible navegar con teclado | Focus ring visible en TODOS los elementos interactivos |

### Ejemplo de código: `alert()` vs. Toast

**Antes (F-03 — Slop):**
```tsx
// PropertyList.tsx
const handleCreateProperty = async (data: PropertyCreateInput) => {
  try {
    await createProperty(data);
    setIsModalOpen(false);
    loadProperties();
  } catch (error: any) {
    alert(error.message || "Error al crear la propiedad");  // ← Bloquea la UI
  }
};
```

**Después (F-04 — Premium):**
```tsx
// PropertyList.tsx
import { useToast } from "../components/Toast";

const handleCreateProperty = async (data: PropertyCreateInput) => {
  try {
    await createProperty(data);
    setIsModalOpen(false);
    loadProperties();
    toast.success("Propiedad creada correctamente");      // ← Feedback positivo no intrusivo
  } catch (error: any) {
    toast.error(error.message || "Error al crear la propiedad");  // ← Feedback de error contextual
  }
};
```

### ¿Qué son los Design Tokens?

Son las "constantes" de tu sistema visual. En lugar de escribir `color: #10b981` en 47 sitios diferentes, defines **una vez** `--accent-primary: #10b981` en `:root` y luego la usas en todo tu CSS como `color: var(--accent-primary)`. Si mañana decides que tu acento sea azul, cambias **una sola línea** y toda la aplicación se actualiza.

| Concepto de programación | Equivalente visual |
|---|---|
| Constante (`const API_URL = "..."`) | Design Token (`--accent-primary: #10b981`) |
| Función reutilizable | Componente reutilizable (`<Toast>`, `<KPICard>`) |
| Test unitario | Verificación de contraste (WCAG AA ≥ 4.5:1) |
| Inyección de dependencias | `var()` de CSS — el componente no sabe qué color tendrá, lo recibe del sistema |
