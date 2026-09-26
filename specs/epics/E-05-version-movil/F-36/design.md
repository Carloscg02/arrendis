# 📐 Especificación Técnica — F-36: Guía y Prompt Inteligente de Instalación PWA (Banner y Modal Safari/Android)

> **Feature:** F-36  
> **Título:** Guía y Prompt Inteligente de Instalación PWA (Banner y Modal Safari/Android)  
> **Épica:** E-05 — Experiencia Móvil y Distribución Multiplataforma (PWA y Capacitor)  
> **Estado:** En Especificación Técnica  
> **Fecha:** 2026-09-26  
> **Dependencias:** F-34 (Optimización Táctil) ✅, F-35 (Manifiesto PWA y Service Worker) ⏳  
> **Normativa de diseño:** Directrices Atelier Editorial y leyes anti-slop en [`DESIGN.md`](file:///home/carlos/rental-launch-prep/DESIGN.md)

---

## 1. Contexto y Justificación

Tener un manifiesto PWA (F-35) es necesario pero insuficiente por sí solo: la gran mayoría de usuarios familiares o clientes desconocen cómo instalar una aplicación web desde el navegador móvil. Además, la experiencia entre plataformas está fragmentada:
1. **En Android / Chromium:** El navegador emite el evento nativo `beforeinstallprompt`, que permite a la aplicación mostrar un botón de instalación en 1 clic gestionado por la propia SPA.
2. **En iOS / Safari:** Apple **no** soporta `beforeinstallprompt`. La instalación en iPhone/iPad requiere que el usuario toque manualmente el icono de "Compartir" de Safari y seleccione la opción "Añadir a pantalla de inicio". Sin una guía visual clara, casi ningún usuario de iOS logra instalar la app.
3. **Control de intrusividad:** La app no debe mostrar banners molestos ni repetitivos. Si el usuario ya está usando la app instalada en modo `standalone`, o si pulsa "Ahora no", el banner debe ocultarse y respetar un período de cortesía (*cooldown* en `localStorage`).

### ¿Qué ENTRA en esta feature?
- Hook reactivo `usePWAInstall` que gestiona:
  - Detección de modo `standalone` (`window.matchMedia('(display-mode: standalone)').matches` o `(navigator as any).standalone`).
  - Detección de dispositivo/navegador (iOS Safari vs Android Chrome vs Desktop).
  - Captura y retención del evento `BeforeInstallPromptEvent` en navegadores compatibles.
  - Persistencia de rechazo en `localStorage` (cooldown de 14 días).
- Componente de interfaz `PWAInstallBanner` (Atelier Editorial):
  - Banner sobrio y flotante en la parte inferior de la pantalla o barra integrada.
  - Botón de instalación directa en 1 clic para Android.
  - Botón "Cómo instalar" que despliega la guía paso a paso para usuarios de iOS.
  - Botón de cierre discreto con icono `X` de `lucide-react`.
- Modal didáctico `PWAInstallModalIOS`:
  - Instrucciones concisas en 3 pasos con iconos vectoriales SVG (`Share2`, `PlusSquare`, `CheckCircle2`).
  - Diseñado conforme a las 6 leyes anti-slop (cero emojis, tipografía Newsreader/Inter, lienzo tiza `#f9f7f5`).

### ¿Qué NO entra en esta feature?
- Notificaciones push en segundo plano (Web Push).
- Empaquetado APK nativo de Capacitor (corresponde a F-37).

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **BeforeInstallPromptEvent** | Evento emitido por motores Chromium cuando una PWA cumple los requisitos de instalabilidad, permitiendo aplazar o disparar el diálogo nativo del sistema. |
| **Standalone Detection** | Comprobación programática en JavaScript que determina si la página se está ejecutando dentro del contenedor de app instalada o en una pestaña de navegador web. |
| **Install Cooldown** | Marca temporal almacenada en `localStorage` (`arrendis_pwa_dismissed_until`) que silencia las invitaciones de instalación durante 14 días si el usuario las descarta. |
| **PWAInstallBanner** | Componente visual no intrusivo que invita al usuario móvil a incorporar Arrendis a su pantalla de inicio. |
| **PWAInstallModalIOS** | Modal ilustrado con las indicaciones exactas requeridas por Safari en dispositivos Apple para completar la instalación. |

---

## 3. Especificación Visual y Wireframes (Atelier Editorial)

### 3.1 Banner de Instalación Móvil (Flotante o Anclado Inferior)

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [Smartphone] Instalar Arrendis en tu móvil       │  │
│  │ Acceso directo y pantalla completa sin tiendas.  │  │
│  │                                                  │  │
│  │ [ Ahora no ]           [ Instalar App (1 clic) ] │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.2 Modal Didáctico para iOS Safari

```
┌────────────────────────────────────────────────────────┐
│  Añadir Arrendis a la pantalla de inicio         [✕]   │
│  ────────────────────────────────────────────────────  │
│  Para instalar Arrendis en tu iPhone o iPad:           │
│                                                        │
│  1. [Share2]  Toca el botón 'Compartir' en la barra    │
│               inferior de Safari.                      │
│                                                        │
│  2. [Plus]    Desplaza el menú hacia abajo y pulsa     │
│               'Añadir a pantalla de inicio'.           │
│                                                        │
│  3. [Check]   Confirma pulsando 'Añadir' arriba a      │
│               la derecha. ¡Listo!                      │
│                                                        │
│  ────────────────────────────────────────────────────  │
│                                            [ Entendido ]│
└────────────────────────────────────────────────────────┘
```

**Reglas de Anti-Slop estrictas:**
- **Zero Emojis:** Prohibido usar `📲`, `👇`, `✨`, `🍎`. Todos los pasos utilizan iconos vectoriales limpios de `lucide-react`.
- **Canvas Atelier:** Fondo `#ffffff` sobre overlay `#1c1917` con opacidad suave (40%), bordes `#e5e2dd`.
- **Tipografía:** Título en `Newsreader`, instrucciones en `Inter` a 14px con alto contraste (`#1c1917`).

---

## 4. Diseño Técnico y Arquitectura de Código

### 4.1 Hook `usePWAInstall.ts` en `frontend/src/utils/usePWAInstall.ts`

```typescript
import { useState, useEffect } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function usePWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isStandalone, setIsStandalone] = useState<boolean>(false)
  const [isIOS, setIsIOS] = useState<boolean>(false)
  const [isDismissed, setIsDismissed] = useState<boolean>(true)

  useEffect(() => {
    // 1. Detectar si ya corre en standalone
    const inStandalone = window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as unknown as { standalone?: boolean }).standalone === true
    setIsStandalone(inStandalone)

    // 2. Detectar si es dispositivo iOS
    const userAgent = window.navigator.userAgent.toLowerCase()
    const isAppleDevice = /iphone|ipad|ipod/.test(userAgent)
    setIsIOS(isAppleDevice)

    // 3. Comprobar cooldown en localStorage
    const dismissedUntil = localStorage.getItem('arrendis_pwa_dismissed_until')
    const now = Date.now()
    if (dismissedUntil && now < parseInt(dismissedUntil, 10)) {
      setIsDismissed(true)
    } else {
      setIsDismissed(false)
    }

    // 4. Capturar beforeinstallprompt en Android/Chrome
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
  }, [])

  const triggerInstall = async () => {
    if (deferredPrompt) {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      if (outcome === 'accepted') {
        setDeferredPrompt(null)
      }
    }
  }

  const dismissPrompt = (days = 14) => {
    const expireTime = Date.now() + days * 24 * 60 * 60 * 1000
    localStorage.setItem('arrendis_pwa_dismissed_until', expireTime.toString())
    setIsDismissed(true)
  }

  const canInstall = !isStandalone && !isDismissed && (Boolean(deferredPrompt) || isIOS)

  return {
    canInstall,
    isStandalone,
    isIOS,
    canPromptDirectly: Boolean(deferredPrompt),
    triggerInstall,
    dismissPrompt
  }
}
```

### 4.2 Componentes React
- `frontend/src/components/PWAInstallBanner.tsx`: Renderiza el banner condicionalmente si `canInstall` es `true`. Si es iOS, al hacer clic en instalar abre el modal didáctico `PWAInstallModalIOS`. Si es Chromium, ejecuta `triggerInstall()`.
- `frontend/src/components/PWAInstallModalIOS.tsx`: Modal accesible con overlay, cierre con `ESC` y botón "Entendido".

---

## 5. Plan de Pruebas y Validación

| ID de Test | Tipo | Descripción de la Prueba | Criterio de Éxito |
|---|---|---|---|
| `TEST-F36-01` | Unit / Hook | Inicialización de `usePWAInstall` en modo standalone. | Si `display-mode: standalone` es true, `canInstall` permanece false. |
| `TEST-F36-02` | Unit / Hook | Captura del evento `beforeinstallprompt`. | El evento se intercepta (`preventDefault()`) y activa `canPromptDirectly`. |
| `TEST-F36-03` | Unit / LocalStorage | Cooldown tras descarte. | `dismissPrompt()` guarda timestamp futuro y oculta el banner inmediatamente. |
| `TEST-F36-04` | UI / Accesibilidad | Renderizado del Modal iOS. | El modal contiene instrucciones limpias sin emojis, iconos `lucide-react` y cierre funcional. |

---

## 6. 📚 El Rincón del Estudiante

### 🎓 Concepto 1: ¿Por qué Android y Apple tratan la instalación de PWAs de manera tan opuesta?

**La analogía del mundo real:**  
Imagina dos hoteles:
- **Hotel Android (Google):** En la recepción tienen un botón luminoso que dice: *"¿Quieres una llave directa para entrar desde el parking sin pasar por el mostrador?"*. Si le das, te entregan la llave en mano (`beforeinstallprompt`).
- **Hotel iOS (Apple):** En la recepción no hay ningún botón. Las tiendas de apps oficiales (la App Store) son el negocio principal de Apple (con un 30% de comisión). Por ello, Apple no permite que una web dispare un diálogo que diga *"Instálame con 1 clic"*. Para tener el acceso directo, el huésped tiene que abrir conscientemente el cajón del menú de compartir y seleccionar *"Añadir a pantalla de inicio"*.

Como ingenieros de software, no podemos cambiar las políticas de los sistemas operativos, pero sí podemos crear una capa de abstracción limpia en TypeScript que detecte en qué hotel está el usuario y le ofrezca la mejor experiencia posible.

### 🎓 Concepto 2: ¿Cómo evitamos la "fatiga de banners" con un Cooldown en LocalStorage?

**La analogía del mundo real:**  
Piensa en los camareros pesados de zonas turísticas que te asaltan cada 10 metros ofreciéndote la carta. Si un usuario entra a Arrendis a consultar una factura rápida y le sale un cartel gigante para instalar la app, y a los 5 minutos vuelve a salirle, el usuario se sentirá acosado.

Guardar un *timestamp* de caducidad en el navegador nos permite ser respetuosos:
```typescript
// Si el usuario pulsa "Ahora no":
const catorceDias = 14 * 24 * 60 * 60 * 1000;
localStorage.setItem('arrendis_pwa_dismissed_until', (Date.now() + catorceDias).toString());
```
Durante dos semanas enteras, la app guarda absoluto silencio. Pasado ese tiempo, si sigue usando la web móvil, volverá a sugerírselo suavemente.
