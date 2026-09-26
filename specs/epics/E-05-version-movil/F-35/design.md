# 📐 Especificación Técnica — F-35: Manifiesto PWA, Service Worker con Vite y Pantalla de Carga (Standalone + Splash Screen)

> **Feature:** F-35  
> **Título:** Manifiesto PWA, Service Worker con Vite y Pantalla de Carga (Standalone + Splash Screen)  
> **Épica:** E-05 — Experiencia Móvil y Distribución Multiplataforma (PWA y Capacitor)  
> **Estado:** En Especificación Técnica  
> **Fecha:** 2026-09-26  
> **Dependencias:** F-34 (Optimización Táctil y Viewport Seguro) ⏳  
> **Normativa de diseño:** Directrices Atelier Editorial y leyes anti-slop en [`DESIGN.md`](file:///home/carlos/rental-launch-prep/DESIGN.md)

---

## 1. Contexto y Justificación

Para que **Arrendis** sea tratada por iOS y Android como una aplicación instalable de primera clase y no como una simple pestaña de navegador, se requiere la infraestructura técnica de una **Progressive Web App (PWA)**:
1. **Web App Manifest (`manifest.webmanifest`):** Define cómo se presenta la app en el sistema operativo: nombre formal, icono en la pantalla de inicio, color del marco del sistema (`theme_color`) y modo de ejecución `standalone` (sin barra de URL ni botones de navegación del navegador).
2. **Service Worker Automatizado:** Controlado mediante `vite-plugin-pwa` para precachear el shell de la aplicación (código compilado HTML/JS/CSS, tipografías y recursos gráficos básicos), permitiendo tiempos de arranque casi instantáneos incluso con conexiones móviles 3G/4G inestables.
3. **Identidad Gráfica y Pantallas de Carga (*Splash Screen*):** Iconografía canónica en alta resolución (192x192, 512x512 y versiones *maskable*) con la estética Atelier Editorial: lienzo de papel tiza (`#f9f7f5`) y monograma Arrendis en granate (`#6b0008`).

### ¿Qué ENTRA en esta feature?
- Adición y configuración de `vite-plugin-pwa` en `frontend/package.json` y `frontend/vite.config.ts`.
- Definición canónica del Manifiesto Web con metadatos de marca Arrendis:
  - `name: "Arrendis — Gestión Patrimonial"`
  - `short_name: "Arrendis"`
  - `display: "standalone"`
  - `background_color: "#f9f7f5"`
  - `theme_color: "#6b0008"`
  - `orientation: "portrait-primary"`
- Generación de los iconos SVG y PNG adaptativos (`pwa-192x192.png`, `pwa-512x512.png`, `apple-touch-icon.png`, `maskable-icon-512x512.png`).
- Configuración de Workbox en Vite PWA:
  - Caché estática (*Stale-While-Revalidate* o precache de assets de compilación).
  - **Exclusión explícita de rutas de backend (`/api/*`)**: Las llamadas a FastAPI nunca deben ser servidas desde la caché del Service Worker para evitar inconsistencias de datos financieros o autenticación.
- Registro automático del Service Worker en `main.tsx`.

### ¿Qué NO entra en esta feature?
- Lógica de interfaz reactiva para prompts de instalación en pantalla (corresponde a F-36).
- Sincronización offline en segundo plano (Background Sync) para mutaciones de backend (fuera de alcance de la épica E-05).
- Empaquetado nativo APK con Capacitor (corresponde a F-37).

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Web App Manifest** | Archivo estandarizado por el W3C en formato JSON que instruye al sistema operativo sobre cómo registrar, nombrar y renderizar la aplicación instalada. |
| **Service Worker** | Hilo de ejecución en segundo plano (*Web Worker*) instalado en el navegador del cliente que intercepta peticiones de red y administra la caché de assets. |
| **Standalone Display Mode** | Modo de visualización en el que el navegador suprime todos sus controles propios (barra de direcciones, flechas de historial, botones de recarga), brindando la apariencia idéntica a una app nativa descargada de tienda. |
| **Maskable Icon** | Icono adaptativo con una zona de seguridad (*safe-zone circular central del 80%*) que permite a Android aplicar máscaras circulares, cuadradas o redondeadas según el fabricante sin recortar el isotipo. |
| **Precaching (Workbox)** | Proceso mediante el cual el Service Worker descarga y almacena en caché local todos los ficheros JS/CSS del bundle durante la instalación inicial, garantizando arranque a velocidad nativa. |

---

## 3. Especificación Visual de Iconografía y Splash (Atelier Editorial)

### 3.1 Anatomía del Icono y Pantalla de Carga

```
┌──────────────────────────────────────────────┐
│ PWA Icon (512x512 / Maskable)               │
│                                              │
│       ┌──────────────────────────────┐       │
│       │                              │       │
│       │      █████  █████            │       │
│       │     ██   ██ ██   ██          │       │  Fondo: #f9f7f5 (Warm Chalk Paper)
│       │     ███████ ███████          │       │  Monograma: #6b0008 (Arrendis Garnet)
│       │     ██   ██ ██  ██           │       │  Borde / Relieve: Hairline sutil
│       │                              │       │
│       └──────────────────────────────┘       │
│                                              │
└──────────────────────────────────────────────┘
```

- **Paleta corporativa:**
  - Fondo de arranque (*Background Color*): `#f9f7f5` (evita el temido destello blanco cegador de las apps web convencionales).
  - Barra de estado (*Theme Color*): `#6b0008` (en Android) o `#f9f7f5` (en iOS con contraste alto).

---

## 4. Diseño Técnico y Arquitectura de Código

### 4.1 Configuración de `vite-plugin-pwa` en `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'Arrendis — Gestión Patrimonial',
        short_name: 'Arrendis',
        description: 'Plataforma de gestión patrimonial y fiscal de inmuebles en alquiler.',
        theme_color: '#6b0008',
        background_color: '#f9f7f5',
        display: 'standalone',
        orientation: 'portrait-primary',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'maskable-icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        navigateFallback: '/index.html',
        // REGLA ARQUITECTÓNICA CRÍTICA:
        // Jamás interceptar ni cachear llamadas al backend REST de FastAPI
        navigateFallbackDenylist: [/^\/api/],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api'),
            handler: 'NetworkOnly', // Siempre petición directa al servidor
          }
        ]
      }
    })
  ]
})
```

### 4.2 Registro en `frontend/src/main.tsx`
```typescript
import { registerSW } from 'virtual:pwa-register'

// Registrar auto-actualización del Service Worker en segundo plano
registerSW({
  immediate: true,
  onNeedRefresh() {
    console.log('[PWA] Nueva versión disponible.')
  },
  onOfflineReady() {
    console.log('[PWA] Aplicación lista para operar con caché local.')
  }
})
```

### 4.3 Generación de Assets en `frontend/public/`
- `pwa-192x192.png`
- `pwa-512x512.png`
- `maskable-icon-512x512.png`
- `apple-touch-icon.png` (180x180)

---

## 5. Plan de Pruebas y Validación

| ID de Test | Tipo | Descripción de la Prueba | Criterio de Éxito |
|---|---|---|---|
| `TEST-F35-01` | Build / Compilación | Ejecución de `npm run build` en el frontend. | Generación correcta de `sw.js` y `manifest.webmanifest` en la carpeta `dist/`. |
| `TEST-F35-02` | Integración PWA | Inspección del contenido de `dist/manifest.webmanifest`. | `display: standalone`, colores `#6b0008` / `#f9f7f5` e iconos declarados. |
| `TEST-F35-03` | Arquitectura de Red | Validación de regla `navigateFallbackDenylist` y `NetworkOnly` para `/api/*`. | Peticiones a endpoints no son interceptadas por caché obsoleta. |
| `TEST-F35-04` | Integridad de Iconos | Validación de formato, resolución y existencia de los ficheros de imagen en `public/`. | Todos los assets referenciados en el manifiesto existen y son legibles. |

---

## 6. 📚 El Rincón del Estudiante

### 🎓 Concepto 1: ¿Qué es un Service Worker y por qué vive "fuera" de React?

**La analogía del mundo real:**  
Piensa en una oficina bancaria. La aplicación React es el empleado sentado en la ventanilla atendiendo tus gestiones. El **Service Worker** es un conserje inteligente apostado en la puerta de la calle. Cuando el empleado necesita un archivador o un formulario oficial (un archivo JavaScript o CSS), el conserje comprueba si ya lo tiene guardado en su casillero local. Si lo tiene, se lo entrega al instante sin que el empleado tenga que esperar al camión de mensajería (la red de Internet).

Lo fascinante del Service Worker es que es un hilo (*thread*) totalmente independiente:
- No tiene acceso al DOM (`window` o `document`).
- Puede seguir vivo incluso si el usuario cierra la pestaña o navega entre pantallas.
- Puede actualizarse en segundo plano sin interrumpir lo que el usuario está escribiendo.

### 🎓 Concepto 2: ¿Por qué NUNCA debemos cachear `/api/*` con un Service Worker en una aplicación financiera?

**La analogía del mundo real:**  
Imagina que consultas el saldo de tu cuenta bancaria. Si el conserje de la puerta decidiera por su cuenta entregarte la fotocopia del saldo de ayer porque *"así tardamos menos y ahorramos viajes"*, podrías creer que tienes 1.000 € cuando en realidad acabas de pagar una reparación urgente de 800 €. En aplicaciones financieras y de gestión patrimonial como Arrendis, la interfaz debe ser rápida, pero los datos contables deben ser siempre la verdad más reciente de la base de datos.

Por eso en nuestra configuración de Workbox definimos estrictamente:
```typescript
navigateFallbackDenylist: [/^\/api/],
runtimeCaching: [
  {
    urlPattern: ({ url }) => url.pathname.startsWith('/api'),
    handler: 'NetworkOnly' // ¡Obliga a ir siempre a la base de datos!
  }
]
```

### 🎓 Concepto 3: Comparativa de Modos de Visualización PWA

| Modo `display` | ¿Qué ve el usuario? | ¿Cuándo se utiliza? |
|---|---|---|
| `browser` | Pestaña ordinaria con barra de URL, marcadores y pestañas. | Webs informativas estándar. |
| `minimal-ui` | Ventana propia pero mantiene botones mínimos de "Atrás" y "Recargar". | Aplicaciones web que requieren navegación tradicional. |
| `standalone` *(Elegido para Arrendis)* | 100% pantalla completa, sin URL ni controles del navegador; se comporta idéntica a una app de App Store o Play Store. | SPAs modernas que tienen su propia barra de navegación integrada. |
