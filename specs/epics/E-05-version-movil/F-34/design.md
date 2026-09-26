# 📐 Especificación Técnica — F-34: Optimización Táctil Mobile-First y Viewport Seguro

> **Feature:** F-34  
> **Título:** Optimización Táctil Mobile-First y Viewport Seguro (CSS anti-clunkiness, safe areas y touch targets)  
> **Épica:** E-05 — Experiencia Móvil y Distribución Multiplataforma (PWA y Capacitor)  
> **Estado:** En Especificación Técnica  
> **Fecha:** 2026-09-26  
> **Dependencias:** F-03 (Frontend React+TS) ✅, F-04 (Diseño Atelier Editorial) ✅  
> **Normativa de diseño:** Directrices Atelier Editorial y leyes anti-slop en [`DESIGN.md`](file:///home/carlos/rental-launch-prep/DESIGN.md)

---

## 1. Contexto y Justificación

Actualmente el frontend de Arrendis carece de una metaetiqueta viewport optimizada en `frontend/index.html` y de utilidades ergonómicas CSS específicas para dispositivos táctiles. Esto genera:
1. **Escalado y viewport inconsistente:** En navegadores móviles, la página puede renderizarse asumiendo resoluciones de escritorio o sufrir re-escalados accidentales ante doble toque.
2. **Colisión con áreas seguras del hardware:** En terminales modernos (iOS con Dynamic Island / notch o Android con barra de gestos), los elementos pegados al borde superior o inferior quedan solapados por la barra del sistema.
3. **Retardo táctil y selección involuntaria:** Al pulsar botones rápidamente, los navegadores móviles pueden aplicar un retraso de 300ms para comprobar doble-tap o seleccionar texto accidentalmente.
4. **Zonas táctiles reducidas:** Ciertos botones, selectores y enlaces tienen áreas interactivas por debajo del umbral recomendado ($\ge 44-48\text{px}$), provocando toques erróneos.

### ¿Qué ENTRA en esta feature?
- Inserción y configuración del `<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />` en `frontend/index.html`.
- Incorporación de tokens y reglas CSS de ergonomía táctil en `frontend/src/index.css`:
  - Variables de entorno para áreas seguras: `env(safe-area-inset-top)`, `env(safe-area-inset-bottom)`, `env(safe-area-inset-left)`, `env(safe-area-inset-right)`.
  - Supresión de retardo táctil: `touch-action: manipulation`.
  - Supresión de rebote elástico indeseado en la raíz: `overscroll-behavior-y: none`.
  - Eliminación de resaltados grises por defecto en WebKit: `-webkit-tap-highlight-color: transparent`.
  - Protección de controles interactivos contra selección de texto accidental: `user-select: none`.
- Clases de utilidad mobile-first y soporte para padding seguro en cabeceras y pie de pantalla (`safe-top`, `safe-bottom`, `touch-target-min`).
- Optimización de barra de navegación superior/inferior para navegación natural con una sola mano (ergonomía de pulgar).
- Verificación de layout responsivo sin desbordamiento horizontal en anchos estándar de móvil (360px a 430px).

### ¿Qué NO entra en esta feature?
- El archivo de manifiesto PWA y Service Worker (corresponde a F-35).
- El banner y modal inteligente de instalación PWA (corresponde a F-36).
- El envoltorio nativo de Capacitor (corresponde a F-37).

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Viewport Fit Cover** | Parámetro `viewport-fit=cover` que indica al motor del navegador que el documento web debe extenderse hasta los bordes físicos del panel, ocupando el área bajo el notch o barra de inicio. |
| **Safe Area Insets** | Variables nativas CSS (`env(safe-area-inset-*)`) que reportan en píxeles el grosor reservado por la interfaz del sistema operativo móvil para evitar solapamientos. |
| **Touch Action Manipulation** | Regla CSS que desactiva el gesto de doble toque para zoom, eliminando el retardo perceptivo de 300 milisegundos en cada interacción táctil. |
| **Touch Target Minimum** | Estándar de accesibilidad ergonómica (W3C WCAG 2.5.5 / Apple HIG / Google Material) que establece un área interactiva mínima de $44\times 44\text{px}$ a $48\times 48\text{px}$ por control. |
| **Overscroll Behavior** | Propiedad CSS que impide el rebote o refresco accidental por arrastre elástico (*pull-to-refresh*) cuando no está explícitamente programado. |

---

## 3. Especificación Visual y de Ergonomía UI (Atelier Editorial)

### 3.1 Anatomía del Viewport Seguro

```
┌────────────────────────────────────────────────────────┐
│ [ Notch / Dynamic Island / Barra Estado ] (env(safe-top))
├────────────────────────────────────────────────────────┤
│  ARRENDIS          [Propiedades | Gastos | Fiscal]     │ <- safe-top padding
│  ────────────────────────────────────────────────────  │
│                                                        │
│  Contenido Principal Desplazable                       │
│  - Tarjetas de Inmuebles                               │
│  - Botones táctiles de min 48px                        │
│  - Sin desbordamiento horizontal (max-w 100vw)         │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Barra de Acciones / Resumen / Nav                     │ <- safe-bottom padding
│ [ Home ]       [ Inmuebles ]       [ Fiscal ]  [ Perfil ]
├────────────────────────────────────────────────────────┤
│ [ Indicador de Inicio / Home Indicator ] (env(safe-bottom))
└────────────────────────────────────────────────────────┘
```

### 3.2 Directrices Estilísticas (Anti-Slop)
- Cero emojis: todo icono o indicador procede de `lucide-react`.
- Paleta: Warm chalk paper (`#f9f7f5`), bordes sutiles de lino (`#e5e2dd`), acento granate Arrendis (`#6b0008`).
- Tipografía: `Newsreader` para títulos de pantalla, `Space Mono` para importes y casillas numéricas, `Inter` para texto de botones y etiquetas.
- Áreas táctiles: Para botones pequeños (icon buttons), se utiliza `min-height: 44px; min-width: 44px; display: inline-flex; align-items: center; justify-content: center;`.

---

## 4. Diseño Técnico y Arquitectura de Código

### 4.1 Modificación en `frontend/index.html`
Se actualiza la sección `<head>` para incluir:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="format-detection" content="telephone=no" />
```

### 4.2 Nuevas Variables y Reglas en `frontend/src/index.css`
```css
/* Ergonomía Mobile-First y Safe Area Insets */
:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --safe-left: env(safe-area-inset-left, 0px);
  --safe-right: env(safe-area-inset-right, 0px);
  --touch-target-min: 44px;
}

html, body {
  /* Eliminar rebote de página global no deseado */
  overscroll-behavior-y: none;
  /* Eliminar retardo de 300ms en toques */
  touch-action: manipulation;
  /* Resaltado táctil transparente en móviles */
  -webkit-tap-highlight-color: transparent;
}

/* Evitar selección accidental en elementos interactivos */
button, a, input[type="button"], input[type="submit"], [role="button"] {
  user-select: none;
  -webkit-user-select: none;
}

/* Utilidades de área segura */
.safe-area-top {
  padding-top: max(12px, var(--safe-top));
}

.safe-area-bottom {
  padding-bottom: max(16px, var(--safe-bottom));
}

.safe-area-container {
  padding-left: max(16px, var(--safe-left));
  padding-right: max(16px, var(--safe-right));
}

/* Botones y controles táctiles mínimos */
.touch-target {
  min-height: var(--touch-target-min);
  min-width: var(--touch-target-min);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

### 4.3 Ajustes Responsivos en Layout Principal
- Verificación y ajuste de `App.tsx` y contenedores principales para garantizar que el `Header` aplique `padding-top: var(--safe-top)` y que los pies de página o barras de navegación apliquen `padding-bottom: var(--safe-bottom)`.
- Asegurar que tablas anchas o paneles con datos financieros incorporen contenedor con scroll horizontal suave (`overflow-x: auto; -webkit-overflow-scrolling: touch;`) sin romper el ancho de pantalla de 100vw.

---

## 5. Plan de Pruebas y Validación

| ID de Test | Tipo | Descripción de la Prueba | Criterio de Éxito |
|---|---|---|---|
| `TEST-F34-01` | Estático / Build | Verificación de meta tags en `index.html`. | `viewport-fit=cover` y `width=device-width` presentes en `<head>`. |
| `TEST-F34-02` | CSS / Build | Verificación de variables CSS y utilidades táctiles en `index.css`. | `touch-action: manipulation`, `-webkit-tap-highlight-color`, y `env(safe-area-inset-*)` compilados sin errores en Vite. |
| `TEST-F34-03` | UI / Responsivo | Inspección en emulación móvil (iPhone 14/15 390px, Pixel 7 412px, SE 375px). | Cero desbordamiento horizontal (`window.innerWidth === document.documentElement.clientWidth`). |
| `TEST-F34-04` | Ergonomía Táctil | Medición de targets de interacción en controles clave. | Botones de navegación, acciones principales y cierres de modal cumplen $\ge 44\text{px}$. |

---

## 6. 📚 El Rincón del Estudiante

### 🎓 Concepto 1: ¿Por qué existe un retraso de 300ms en los navegadores móviles y cómo lo elimina `touch-action: manipulation`?

**La analogía del mundo real:**  
Imagina un semáforo inteligente que, cada vez que un peatón presiona el botón para cruzar, espera medio segundo con el cronómetro en pausa antes de responder, porque se pregunta: *"¿El peatón va a pulsar dos veces para correr o solo una?"*. En los primeros días de la web móvil (en el iPhone original de 2007), los navegadores introdujeron el gesto de doble toque para hacer zoom en páginas pensadas para monitores grandes. Para detectar si una pulsación era un clic simple o el inicio de un doble toque, el navegador esperaba exactamente 300 milisegundos tras levantar el dedo antes de disparar el evento `click`.

En una aplicación moderna diseñada específicamente para móviles (*mobile-first*), ese retardo de 300ms hace que la app se sienta torpe, lenta y "de juguete".

**En el código de Arrendis:**
```css
/* frontend/src/index.css */
html, body {
  /* Le dice al navegador: "Permite scroll y zoom con dos dedos (pinch),
     pero NO esperes un segundo toque para zoom rápido".
     El evento click se dispara inmediatamente al soltar el dedo (0ms delay). */
  touch-action: manipulation;
}
```

### 🎓 Concepto 2: ¿Qué son los *Safe Area Insets* y el `viewport-fit=cover`?

**La analogía del mundo real:**  
Imagina enmarcar un lienzo de pintura en un marco de madera noble con bordes biselados. Si el lienzo se corta exactamente al tamaño exterior del marco, parte del dibujo quedará oculta detrás de la madera. Si se corta más pequeño, quedarán huecos blancos feos. Las pantallas de los smartphones modernos tienen muescas (*notches*), agujeros para cámaras (*isla dinámica*) y esquinas redondeadas.

Si no especificas `viewport-fit=cover`, el navegador iOS añade automáticamente franjas blancas en los laterales y encierra la web en una "caja segura" artificial. Al indicar `viewport-fit=cover`, la web ocupa el 100% de la pantalla hasta el último cristal, pero entonces debemos usar `env(safe-area-inset-top)` y `env(safe-area-inset-bottom)` como margen interior (*padding*) para que nuestro texto o botones no queden tapados por la cámara frontal ni por la barra de gestos de inicio.

**Comparativa Con vs. Sin:**

| Sin Viewport Cover ni Safe Areas | Con `viewport-fit=cover` y `env(safe-area-inset-*)` |
|---|---|
| Franjas blancas antiestéticas arriba y abajo en Safari. | Experiencia inmersiva que ocupa toda la pantalla del teléfono. |
| Si se fuerza a pantalla completa sin insets, los botones del header quedan debajo de la cámara. | El header tiene el padding exacto para situarse justo debajo de la muesca de forma elegante. |
| El pie de página o botón flotante choca con la barra de gestos de deslizar para ir al inicio. | Margen ergonómico que separa las acciones de la barra del sistema. |
