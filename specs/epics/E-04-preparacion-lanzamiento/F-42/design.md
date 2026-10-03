# 📐 Especificación Técnica: F-42
# Descubrimiento Web, SEO, Social Graph y Crawling (robots.txt, sitemap.xml, Open Graph, Twitter Cards)

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** En Revisión Técnica (Gate de Arquitectura)  
> **Fecha:** 2026-10-03  
> **Autor:** Tech Lead & Orquestador Arrendis  

---

## 1. Contexto y Delimitación de Alcance

### 1.1. Contexto
En la actualidad, Arrendis carece de directivas de indexación y exploración para motores de búsqueda y rastreadores web (*crawlers*):
1. **Riesgo de indexación de datos privados:** Sin un archivo `robots.txt`, motores de búsqueda como Google o Bing intentan rastrear rutas internas privadas como `/portfolio`, `/properties/:id` y los endpoints de la API (`/api/*`), lo que podría provocar la exposición accidental o almacenamiento en caché de información financiera o catastral confidencial.
2. **Deficiencia de indexación pública:** La ausencia de `sitemap.xml` dificulta el descubrimiento estructurado de las páginas públicas activas (`/`, `/landing`, `/login`, `/register`, `/privacy`, `/terms`).
3. **Ausencia de Social Graph:** Al compartir enlaces de Arrendis en canales de mensajería (WhatsApp, Telegram, LinkedIn, X/Twitter), la previsualización no muestra ninguna tarjeta gráfica enriquecida, título descriptivo ni logotipo corporativo debido a la falta de etiquetas Open Graph y Twitter Cards en `index.html`. Asimismo, el atributo de idioma permanece indebidamente en `<html lang="en">` en lugar de `es`.
4. **Vulnerabilidades en hipervínculos salientes:** Enlaces externos sin `rel="noopener noreferrer"` abren la puerta a ataques de suplantación de contexto de navegación (*reverse tabnabbing*).

### 1.2. Delimitación (Qué entra y qué NO entra)
- **✅ ENTRA:**
  - Creación de `frontend/public/robots.txt` permitiendo rutas públicas y bloqueando explícitamente `/portfolio`, `/properties`, `/properties/`, `/onboarding` y `/api/`.
  - Creación de `frontend/public/sitemap.xml` con protocolo HTTPS canónico y todas las URLs públicas activas.
  - Corrección de `frontend/index.html`: `lang="es"`, `<meta name="description">`, Open Graph (`og:*`) y Twitter Cards (`twitter:*`).
  - Creación del activo visual `frontend/public/og-image.png` para previsualización social.
  - Auditoría y verificación de `rel="noopener noreferrer"` en todos los enlaces salientes externos con `target="_blank"`.
- **❌ NO ENTRA:**
  - Renderizado del lado del servidor (SSR) o prerenderizado estático de rutas autenticadas (la app privada es una SPA detrás de autenticación JWT).
  - Campañas de posicionamiento SEM o analítica invasiva de terceros.

---

## 2. Lenguaje Ubicuo

| Término | Definición Formal en el Dominio |
|---|---|
| **Robots Exclusion Protocol (robots.txt)** | Estándar web que instruye a los rastreadores automatizados sobre qué rutas del sitio tienen permitido o prohibido indexar. |
| **Sitemap XML** | Archivo estático que enumera las URLs canónicas del sitio para informar a los motores de búsqueda sobre la estructura y frecuencia de actualización del contenido público. |
| **Open Graph Protocol** | Protocolo de metadatos estandarizado en el `<head>` que permite a las redes sociales y plataformas de mensajería generar vistas previas enriquecidas (*rich snippets*) con imagen, título y descripción. |
| **Twitter Cards** | Conjunto de etiquetas meta propietarias de X/Twitter para enriquecer la tarjeta de previsualización con formatos grandes (`summary_large_image`). |
| **Reverse Tabnabbing** | Vulnerabilidad de seguridad donde una página de destino abierta con `target="_blank"` obtiene acceso a `window.opener` para redirigir la pestaña original a un sitio de phishing. Mitigada por `rel="noopener noreferrer"`. |

---

## 3. Diseño Técnico Detallado

### 3.1. Archivo `robots.txt`
Ubicación: `frontend/public/robots.txt` (y accesible en raíz vía symlink `public`).

```txt
# robots.txt para Arrendis (Gestión de Alquileres y Cálculo Fiscal)
User-agent: *
Allow: /
Allow: /landing
Allow: /login
Allow: /register
Allow: /privacy
Allow: /terms

# Desindexación estricta de áreas privadas y sensibles
Disallow: /portfolio
Disallow: /properties
Disallow: /properties/
Disallow: /onboarding
Disallow: /api/

# Mapa del sitio
Sitemap: https://arrendis.com/sitemap.xml
```

### 3.2. Archivo `sitemap.xml`
Ubicación: `frontend/public/sitemap.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://arrendis.com/</loc>
    <lastmod>2026-10-03</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://arrendis.com/landing</loc>
    <lastmod>2026-10-03</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://arrendis.com/login</loc>
    <lastmod>2026-10-03</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://arrendis.com/register</loc>
    <lastmod>2026-10-03</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://arrendis.com/privacy</loc>
    <lastmod>2026-10-03</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://arrendis.com/terms</loc>
    <lastmod>2026-10-03</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
```

### 3.3. Metadatos en `frontend/index.html`
- Atributo `<html lang="es">`.
- Etiqueta meta descripción:
  ```html
  <meta name="description" content="Arrendis — Plataforma editorial para la gestión de carteras de inmuebles en alquiler, automatización de suministros por CUPS y cálculo fiscal orientativo para el Modelo 100 de IRPF." />
  ```
- Metadatos Open Graph:
  ```html
  <!-- Open Graph / Facebook / WhatsApp / Telegram -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Arrendis" />
  <meta property="og:url" content="https://arrendis.com" />
  <meta property="og:title" content="Arrendis — Gestión de Alquileres y Cálculo Fiscal" />
  <meta property="og:description" content="Gestión integral de carteras inmobiliarias en alquiler, centralización de facturas por CUPS y cálculo del rendimiento neto del IRPF (Modelo 100)." />
  <meta property="og:image" content="https://arrendis.com/og-image.png" />
  <meta property="og:locale" content="es_ES" />
  ```
- Metadatos Twitter Cards:
  ```html
  <!-- Twitter Cards -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Arrendis — Gestión de Alquileres y Cálculo Fiscal" />
  <meta name="twitter:description" content="Gestión integral de carteras inmobiliarias en alquiler, centralización de facturas por CUPS y cálculo del rendimiento neto del IRPF (Modelo 100)." />
  <meta name="twitter:image" content="https://arrendis.com/og-image.png" />
  ```

---

## 4. Plan de Pruebas y Verificación

### 4.1. Verificación Estática y Toolkit Pre-launch
- Ejecutar: `python3 /home/carlos/pre-launch/scripts/cli.py all . --format markdown`
- **Criterio de éxito F-42:**
  - `robots.txt Configuration`: `PASS` (antes `WARNING: MEDIUM`).
  - `sitemap.xml Discovery`: `PASS` (antes `WARNING: MEDIUM`).
  - `Document Title Tags`: `PASS`.
  - `Meta Description`: `PASS`.
  - Ningún hipervínculo externo `target="_blank"` sin `rel="noopener noreferrer"`.
- Compilación de frontend: `npm run build --prefix frontend`.

---

## 5. 📚 El Rincón del Estudiante

### ¿Por qué `robots.txt` es indispensable para una aplicación privada?
Imagina que eres el director de un hotel de lujo. En la entrada principal colocas un mapa para los turistas indicando dónde está la recepción y la cafetería pública (páginas de inicio, login y registro). Sin embargo, en los pasillos que conducen a las suites de los huéspedes o a la caja fuerte de contabilidad colocas un letrero claro de *"Solo Personal Autorizado"*.

En la web, el archivo **`robots.txt`** es ese letrero para los robots de búsqueda de Google o Bing:
- Si no pones `Disallow: /portfolio` o `Disallow: /api/`, un robot indexador que encuentre un enlace podría intentar rastrear los datos de inmuebles de tus usuarios o llamar endpoints de tu API, saturando tu base de datos o guardando en la caché pública de Google fragmentos de información confidencial.

### ¿Qué hace el protocolo Open Graph?
Cuando pegas un enlace de tu web en un chat de WhatsApp o en LinkedIn, la aplicación no sabe qué mostrar por defecto. Hace una petición HTTP silenciosa al `<head>` de tu página.
- **Sin Open Graph:** Muestra una caja gris vacía con la URL en azul, pareciendo un enlace sospechoso o inacabado.
- **Con Open Graph (`og:*`):** Lee la etiqueta `og:image`, el título y la descripción, renderizando una tarjeta editorial profesional con el logotipo, generando confianza inmediata en el usuario.

### Código del Proyecto: Antes vs. Después en `frontend/index.html`

#### 🔴 Antes (Sin metadatos sociales, idioma erróneo y sin descripción):
```html
<!-- frontend/index.html - Antes de F-42 -->
<!doctype html>
<html lang="en"> <!-- ⚠️ Idioma en inglés para una app española -->
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="..." />
    <!-- ⚠️ Sin meta description, sin Open Graph, sin Twitter Cards -->
    <title>Arrendis — Gestión Patrimonial</title>
  </head>
```

#### 🟢 Después (Metadatos completos, Open Graph y lang="es"):
```html
<!-- frontend/index.html - Con F-42 -->
<!doctype html>
<html lang="es"> <!-- ✅ Idioma oficial en español -->
  <head>
    <meta charset="UTF-8" />
    <meta name="description" content="Arrendis — Plataforma editorial para la gestión de carteras de inmuebles..." />
    
    <!-- Open Graph Protocol -->
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="Arrendis" />
    <meta property="og:title" content="Arrendis — Gestión de Alquileres y Cálculo Fiscal" />
    <meta property="og:image" content="https://arrendis.com/og-image.png" />
    <meta property="og:locale" content="es_ES" />
    
    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image" />
    <title>Arrendis — Gestión de Alquileres y Cálculo Fiscal</title>
  </head>
```

### Comparativa: Con vs. Sin Arquitectura SEO F-42

| Aspecto | Sin F-42 (Estado Inicial) | Con F-42 (Blindaje Implementado) |
|---|---|---|
| **Auditoría Pre-launch** | 2 Warnings `MEDIUM` por ausencia de `robots.txt` y `sitemap.xml`. | `robots.txt` y `sitemap.xml` en estado `PASS` (`LOW`). |
| **Indexación de Áreas Privadas** | Los motores de búsqueda intentan indexar `/portfolio` y `/api/`. | Bloqueo categórico con `Disallow: /portfolio`, `/api/`. |
| **Tarjetas en Redes Sociales** | Enlace gris en blanco al compartir en WhatsApp o Telegram. | Tarjeta corporativa editorial con imagen, título y sinopsis. |
| **Accesibilidad de Idioma** | Atributo `lang="en"` confunde a lectores de pantalla hispanohablantes. | Atributo `lang="es"` normalizado para lectores a11y. |
| **Seguridad de Enlaces Salientes** | Riesgo de reverse tabnabbing si faltase `rel="noopener noreferrer"`. | Todos los enlaces externos blindados con `rel="noopener noreferrer"`. |
