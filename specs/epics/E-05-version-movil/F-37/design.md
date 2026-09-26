# 📐 Especificación Técnica — F-37: Empaquetado Nativo con Capacitor y Pipeline de Generación de APK Local para Android

> **Feature:** F-37  
> **Título:** Empaquetado Nativo con Capacitor y Pipeline de Generación de APK Local para Android (Sideloading)  
> **Épica:** E-05 — Experiencia Móvil y Distribución Multiplataforma (PWA y Capacitor)  
> **Estado:** En Especificación Técnica  
> **Fecha:** 2026-09-26  
> **Dependencias:** F-34 (Optimización Táctil) ✅, F-35 (Manifiesto PWA) ✅  
> **Normativa de diseño:** Directrices Atelier Editorial y leyes anti-slop en [`DESIGN.md`](file:///home/carlos/rental-launch-prep/DESIGN.md)

---

## 1. Contexto y Justificación

Aunque la PWA (F-35 y F-36) resuelve la instalación web sin tiendas, existen escenarios de validación donde los usuarios o familiares prefieren o requieren un **instalador binario real (`.apk`)**:
1. Usuarios de Android que desean tener el archivo ejecutable para guardarlo o compartirlo por mensajería.
2. Acceso futuro sin limitaciones a hardware del dispositivo (ej. cámara nativa para escanear recibos físicos, biometría facial/huella con Keystore del sistema).
3. Preparación anticipada para el momento en que se decida publicar en Google Play Store sin reescribir una sola línea de código.

**Capacitor** (creado por el equipo de Ionic) es el puente nativo moderno estándar de la industria. Permite encapsular la SPA compilada de React en un contenedor WebView nativo optimizado con aceleración por hardware.

### ¿Qué ENTRA en esta feature?
- Incorporación de dependencias de Capacitor en `frontend/package.json`:
  - `@capacitor/core`
  - `@capacitor/cli`
  - `@capacitor/android`
- Archivo de configuración oficial `frontend/capacitor.config.ts`:
  - `appId: 'com.arrendis.app'`
  - `appName: 'Arrendis'`
  - `webDir: 'dist'`
  - Configuración de scheme seguro: `server: { androidScheme: 'https' }`.
- Inicialización del proyecto nativo de Android (`frontend/android/`) con manifiesto nativo, permisos de red para consultar la API de Arrendis y assets de icono/splash sincronizados.
- Scripts de automatización en `frontend/package.json`:
  - `cap:sync`: Compila el frontend con Vite y sincroniza los assets con el proyecto nativo Android.
  - `cap:build:apk`: Script auxiliar para invocar el compilador Gradle local y generar el paquete `app-debug.apk` listo para sideloading.
- Documentación concisa paso a paso para compilar y transferir el `.apk` al móvil mediante cable USB (`adb install`) o descarga directa.

### ¿Qué NO entra en esta feature?
- Proyecto de iOS / Xcode (`@capacitor/ios`): Requiere macOS y cuenta Apple Developer; se abordará en la Fase 3 del roadmap.
- Publicación formal en Google Play Store ni generación de claves de firma de producción (Keystore de release).

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Capacitor** | Capa de abstracción multiplataforma moderna que empaqueta aplicaciones web estándar (HTML/JS/CSS) dentro de un contenedor nativo nativo de Android e iOS. |
| **Android WebView** | Componente del sistema operativo Android basado en Chromium que renderiza código web dentro de una aplicación nativa a 60/120 fps. |
| **Sideloading** | Método de instalación directa de un paquete `.apk` en un terminal Android transfiriendo el fichero, sin requerir la Google Play Store. |
| **Gradle** | Sistema automatizado de compilación y empaquetado del ecosistema Android que toma el código Java/Kotlin y los assets web y produce el archivo binario `.apk`. |
| **Capacitor Sync (`npx cap sync`)** | Comando que copia los archivos estáticos de `frontend/dist/` dentro de la carpeta `frontend/android/app/src/main/assets/public/` y actualiza los plugins nativos. |

---

## 3. Arquitectura Técnica de Empaquetado

```
┌─────────────────────────────────────────────────────────────┐
│ CÓDIGO FUENTE ÚNICO (frontend/src/)                        │
│ React 19 + TypeScript + Atelier Editorial CSS               │
└──────────────────────────────┬──────────────────────────────┘
                               │ npm run build (Vite)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ BUNDLE ESTÁTICO (frontend/dist/)                            │
│ index.html + assets/ + manifest.webmanifest + sw.js         │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
        (Vía Web / VPS)                 (npx cap sync)
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ PWA NAVEGADOR MÓVIL         │ │ CAPACITOR ANDROID CONTAINER│
│ (Safari / Chrome Mobile)     │ │ (frontend/android/)        │
│ Standalone / Service Worker  │ │ WebView + AndroidManifest  │
└──────────────────────────────┘ └────────────┬───────────────┘
                                              │ ./gradlew assembleDebug
                                              ▼
                                 ┌────────────────────────────┐
                                 │ ARCHIVO .APK NATIVO        │
                                 │ (app-debug.apk)            │
                                 │ Distribución Sideloading   │
                                 └────────────────────────────┘
```

---

## 4. Diseño Técnico y Configuración de Archivos

### 4.1 Configuración de Capacitor en `frontend/capacitor.config.ts`

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.arrendis.app',
  appName: 'Arrendis',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    cleartext: false // Seguridad estricta: solo conexiones cifradas
  },
  android: {
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: false
  }
};

export default config;
```

### 4.2 Scripts en `frontend/package.json`

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "oxlint",
    "preview": "vite preview",
    "cap:sync": "npm run build && npx cap sync android",
    "cap:open:android": "npx cap open android"
  }
}
```

### 4.3 Permisos de Red en `AndroidManifest.xml`
Garantizar que el contenedor nativo tenga permiso explícito para consultar la API del servidor:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

---

## 5. Plan de Pruebas y Validación

| ID de Test | Tipo | Descripción de la Prueba | Criterio de Éxito |
|---|---|---|---|
| `TEST-F37-01` | Dependencias / Build | Instalación e integridad de `@capacitor/core`, `@capacitor/cli`, `@capacitor/android`. | `npm list @capacitor/core` reporta versión válida sin conflictos. |
| `TEST-F37-02` | Configuración | Validación sintáctica y de esquema de `capacitor.config.ts`. | `npx cap config` procesa el fichero y refleja `appId: com.arrendis.app`. |
| `TEST-F37-03` | Sincronización Assets | Ejecución de `npx cap sync android`. | Los ficheros estáticos de `dist/` se copian en el árbol de assets de Android sin errores. |
| `TEST-F37-04` | Seguridad de Contenedor | Inspección de permisos en `AndroidManifest.xml` y directiva `cleartext: false`. | Se impide tráfico HTTP no seguro; solo se permite conexión cifrada HTTPS. |

---

## 6. 📚 El Rincón del Estudiante

### 🎓 Concepto 1: ¿Por qué Capacitor en lugar de Cordova o React Native para este proyecto?

**La analogía del mundo real:**  
- **Apache Cordova (el viejo puente de madera):** Fue la primera solución en 2011. Sin embargo, su arquitectura antigua ralentizaba la comunicación entre la web y el teléfono, inyectaba librerías pesadas y generaba errores frecuentes de compatibilidad.
- **React Native (construir un coche nuevo):** Obliga a no usar HTML ni CSS normal. En lugar de un `<div>` o una etiqueta `<button>`, tienes que programar con componentes propietarios (`<View>`, `<Text>`) y rediseñar toda la interfaz desde cero.
- **Capacitor (un túnel de alta velocidad moderno):** Diseñado en 2018 para la web moderna. Respeta tu aplicación web de React tal cual está escrita, no toca tu CSS, y se limita a abrir un navegador nativo ultrarrápido y seguro dentro de la aplicación móvil. Con un único código fuente mantenemos la versión web de escritorio, la PWA móvil y la app nativa de Android.

### 🎓 Concepto 2: ¿Cómo funciona el *Sideloading* en Android?

**La analogía del mundo real:**  
Instalar una app desde Google Play Store es como comprar un libro en una librería oficial: ellos revisan que el libro no tenga páginas rotas ni contenido peligroso, le ponen su sello y te lo cobran o entregan.  
Hacer **Sideloading** con un archivo `.apk` es como si el autor del libro te entrega el manuscrito directamente en la mano en una memoria USB. En Android, basta con activar *"Permitir instalar aplicaciones de orígenes desconocidos"* para tu gestor de archivos o navegador, tocar el archivo `.apk` y el teléfono lo instalará con total normalidad. Es la herramienta definitiva para probar una app con amigos o familiares en menos de 5 minutos sin pagar un céntimo en licencias de Google.
