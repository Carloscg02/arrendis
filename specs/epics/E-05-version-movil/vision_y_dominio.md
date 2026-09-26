# 📱 Épica E-05: Experiencia Móvil y Distribución Multiplataforma (PWA y Capacitor)

> **Versión:** 1.0  
> **Estado:** En Descubrimiento (Discovery) / Roadmap Definido  
> **Fecha:** 2026-09-26  
> **Dependencias previas:** F-03 (Frontend React+TS), F-04 (Diseño Atelier Editorial)  

---

## 1. Objetivo de Negocio y Justificación

Garantizar que **Arrendis** ofrezca una experiencia móvil impecable, fluida y de pantalla completa en teléfonos inteligentes (iOS y Android), permitiendo a los primeros usuarios y familiares instalar y utilizar la aplicación sin fricciones de tiendas de aplicaciones, sin costes de publicación iniciales y con control total del ciclo de actualizaciones.

### ¿Qué problema resuelve?

1. **La incomodidad de la web convencional en móvil:** La navegación web móvil típica suele adolecer de zooms accidentales, retardos en toques (300ms delay), barras de direcciones que saltan al scrollear y botones con áreas táctiles reducidas. Arrendis debe comportarse con la solidez táctil y visual de una aplicación nativa.
2. **Barreras de coste y burocracia de las tiendas de apps:** Las cuentas de desarrollador de Apple (99 $/año) y Google Play (25 $ tasa única con requisitos estrictos de 14 días de testing cerrado con 20 usuarios) suponen una fricción excesiva para fases tempranas de validación y pruebas familiares.
3. **Distribución controlada y actualizaciones continuas:** El propietario de la plataforma debe poder compartir la app de forma inmediata y desplegar mejoras o correcciones sin obligar a los usuarios a reinstalar ficheros binarios manualmente.

---

## 2. Estrategia de Evolución y Roadmap en 3 Fases

```
   ┌──────────────────────────────────────────────────────────────┐
   │ FASE 1: PWA Mobile-First (Inmediata / Beta Familiar)        │
   │ - Coste: 0 €. Tiempo de desarrollo mínimo.                   │
   │ - Instalación en 1 clic en Android y Safari iOS.             │
   │ - Pantalla completa (standalone), splash screen e icono.    │
   │ - Actualizaciones instantáneas vía despliegue en VPS.        │
   └──────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │ FASE 2: Capacitor Runtime (Distribución Local APK)           │
   │ - Envoltorio nativo sobre el mismo código React.             │
   │ - Generación de instalador .apk para Android sin tiendas.    │
   │ - Preparación para APIs nativas futuras (Cámara, FaceID).    │
   └──────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │ FASE 3: Publicación Oficial en Tiendas (Google Play / Apple) │
   │ - Registro de cuentas de desarrollador cuando el producto    │
   │   esté validado con usuarios reales.                         │
   │ - Envío del mismo binario Capacitor depurado a auditoría.    │
   └──────────────────────────────────────────────────────────────┘
```

---

## 3. Límites del Subdominio (Bounded Context)

### ✅ Lo que ENTRA en esta épica

- **Optimización Mobile-First de UI:**
  - Supresión de zoom accidental y delay táctil (`touch-action: manipulation`).
  - Desactivación de selección accidental de texto en elementos interactivos (`user-select: none`).
  - Respeto del área segura de pantallas con notch o barra inferior (`safe-area-inset`).
  - Ajuste de tamaños mínimos de controles táctiles a $\ge 48\times 48\text{ px}$.
- **Infraestructura PWA (Progressive Web App):**
  - Manifiesto web estandarizado (`manifest.webmanifest`) con nombre, colores de marca, iconos adaptativos y modo `display: standalone`.
  - Integración de Service Worker ligero con `vite-plugin-pwa` para precaching de assets estáticos y arranque instantáneo.
  - Pantalla de carga nativa (*Splash Screen*) con logotipo y paleta corporativa Atelier Editorial.
- **Componentes de Adopción e Instalación:**
  - Banner inteligente en la UI para sugerir la instalación al detectar navegadores móviles.
  - Modal didáctico paso a paso para usuarios de iOS (Safari: botón compartir ➔ Añadir a inicio).
- **Envoltorio Nativo con Capacitor:**
  - Configuración del runtime de Capacitor (`@capacitor/core`, `@capacitor/cli`, `@capacitor/android`).
  - Script para generar y compilar el binario instalador `.apk` de Android para pruebas directas (sideloading).

### ❌ Lo que NO ENTRA (fuera de alcance en esta fase)

- **Pago y publicación en Apple App Store ni Google Play Store:** Se aplaza hasta la Fase 3, una vez recogido el feedback de los primeros usuarios.
- **Reescritura en lenguajes nativos (Swift / Kotlin):** La base de código se mantiene 100% unificada en React + TypeScript.
- **Modo offline con sincronización bidireccional compleja:** La app requiere conexión con el backend de FastAPI en el VPS; el Service Worker se limita al almacenamiento en caché de la interfaz y recursos estáticos.

---

## 4. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **PWA (Progressive Web App)** | Aplicación web construida con estándares modernos que se comporta visual y funcionalmente como una app nativa en el dispositivo móvil. |
| **Web App Manifest** | Archivo JSON (`manifest.webmanifest`) que define metadatos de la aplicación: nombre, iconos, color de tema y modo de visualización. |
| **Standalone Mode** | Modo de visualización donde el navegador oculta por completo su barra de direcciones, botones de pestañas y controles de navegación, ocupando el 100% de la pantalla. |
| **Service Worker** | Script en segundo plano en el navegador cliente que gestiona el almacenamiento en caché de ficheros estáticos (HTML/CSS/JS) para carga ultrarrápida. |
| **Safe Area Insets** | Variables del sistema operativo (`env(safe-area-inset-top)`, etc.) que evitan que el contenido quede tapado por la cámara frontal (notch/isla dinámica) o la barra de inicio inferior. |
| **Capacitor** | Plataforma de código abierto que empaqueta una web SPA dentro de un contenedor nativo (WebView) para generar ejecutables de Android e iOS. |
| **Sideloading / APK Directo** | Instalación de un paquete `.apk` en un dispositivo Android sin descargarlo desde Google Play Store. |

---

## 5. Arquitectura Técnica de la Solución Móvil

```
┌────────────────────────────────────────────────────────────────────────┐
│ CLIENTE MÓVIL (Dispositivo Usuario)                                   │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ PWA Standalone (Navegador WebView o Chrome/Safari Autónomo)   │    │
│   │                                                              │    │
│   │   [ Service Worker (Vite PWA) ] ── (Caché Assets Estáticos)   │    │
│   │   [ React UI (Atelier Editorial + Mobile Tokens CSS) ]       │    │
│   │   [ PWA Install Prompt & iOS Share Modal ]                   │    │
│   └──────────────────────────────┬───────────────────────────────┘    │
└──────────────────────────────────┼─────────────────────────────────────┘
                                   │ HTTPS / REST API (JWT)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ SERVIDOR (VPS Oracle / Docker / Caddy)                                 │
│                                                                        │
│   FastAPI Backend (Hexagonal) ── SQLite DB                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Desglose de Features Propuestas

1. **F-34: Optimización Táctil Mobile-First y Viewport Seguro**
   - Configuración de meta-viewport sin escalado accidental.
   - Utilidades CSS para `touch-action`, `user-select: none`, `overscroll-behavior-y: none`.
   - Ajuste de safe-areas en cabeceras y barras de acción inferiores.
   - Auditoría de tamaño táctil mínimo ($\ge 48\text{ px}$) en botones y formularios.

2. **F-35: Manifiesto PWA, Service Worker y Pantalla de Carga (Splash Screen)**
   - Configuración de `vite-plugin-pwa` en `vite.config.ts`.
   - Generación de iconos en múltiples resoluciones (192x192, 512x512, maskable).
   - Configuración de `display: "standalone"`, `theme_color` y `background_color`.
   - Generación de assets de Splash Screen para iOS y Android.

3. **F-36: Guía y Asistente de Instalación PWA en Frontend**
   - Detección del evento `beforeinstallprompt` en Android con botón de instalación de 1 clic.
   - Modal explicativo ilustrado para Safari en iOS (*"Compartir ➔ Añadir a pantalla de inicio"*).
   - Persistencia en almacenamiento local para no molestar a usuarios que ya la instalaron o declinaron.

4. **F-37: Empaquetado Nativo con Capacitor y Pipeline de APK Local (Android Sideloading)**
   - Inicialización del proyecto Capacitor en la raíz del frontend.
   - Configuración de `capacitor.config.json` apuntando al dominio de producción.
   - Scripts de compilación para generar el `.apk` de prueba sin intermediarios de tienda.

---

## 7. Criterios de Aceptación Globales de la Épica

- [ ] La aplicación se instala en la pantalla de inicio tanto en Android como en iOS sin mostrar advertencias ni fallos de renderizado.
- [ ] Al abrirse desde el icono de la pantalla de inicio, la interfaz corre en modo `standalone` a pantalla completa (sin barras de navegador visibles).
- [ ] No existe retardo táctil ni zoom indeseado al tocar rápidamente botones o campos de formulario.
- [ ] Las barras superiores e inferiores respetan las áreas seguras en dispositivos con notch / isla dinámica.
- [ ] Se genera un archivo `.apk` funcional que puede instalarse directamente en dispositivos Android de prueba.
