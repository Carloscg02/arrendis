# 📋 Requisitos de Negocio y Sistema: F-42
# Descubrimiento Web, SEO, Social Graph y Crawling (robots.txt, sitemap.xml, Open Graph, Twitter Cards)

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Especificado  
> **Fecha:** 2026-10-03  
> **Formato:** Notación EARS (Easy Approach to Requirements Syntax)  

---

## 1. Requisitos del Sistema (EARS)

### R-42.1: Desindexación Estricta de Áreas Privadas en robots.txt (Ubiquitous)
El sistema **DEBERÁ** servir un archivo estático `robots.txt` en la raíz del dominio público (`/robots.txt`) que:
- Permita el rastreo de páginas públicas (`/`, `/landing`, `/login`, `/register`, `/privacy`, `/terms`).
- **PROHÍBA TAXATIVAMENTE** a todos los motores de búsqueda e indexadores (`User-agent: *`) el rastreo de rutas privadas y protegidas:
  - `Disallow: /portfolio`
  - `Disallow: /properties`
  - `Disallow: /properties/`
  - `Disallow: /onboarding`
  - `Disallow: /api/`
- Enlace la ubicación del mapa del sitio mediante `Sitemap: https://arrendis.com/sitemap.xml`.

### R-42.2: Mapa del Sitio Estructurado (sitemap.xml) (Ubiquitous)
El sistema **DEBERÁ** servir un archivo estático `sitemap.xml` en la raíz pública (`/sitemap.xml`) conteniendo las URLs públicas canónicas con sus metadatos de frecuencia y prioridad:
- `https://arrendis.com/` (prioridad 1.0, `weekly`)
- `https://arrendis.com/landing` (prioridad 0.9, `monthly`)
- `https://arrendis.com/login` (prioridad 0.8, `monthly`)
- `https://arrendis.com/register` (prioridad 0.8, `monthly`)
- `https://arrendis.com/privacy` (prioridad 0.5, `yearly`)
- `https://arrendis.com/terms` (prioridad 0.5, `yearly`)

### R-42.3: Metadatos Open Graph y Twitter Cards en index.html (Ubiquitous)
El archivo `frontend/index.html` **DEBERÁ** incorporar:
- Corrección del atributo de idioma a español: `<html lang="es">`.
- Etiqueta meta descripción exhaustiva (`<meta name="description" ...>`).
- Protocolo Open Graph:
  - `og:type`: `"website"`
  - `og:site_name`: `"Arrendis"`
  - `og:title`: `"Arrendis — Gestión de Alquileres y Cálculo Fiscal"`
  - `og:description`: Descripción editorial sobre gestión de inmuebles y borrador IRPF Modelo 100.
  - `og:url`: `"https://arrendis.com"`
  - `og:image`: `"https://arrendis.com/og-image.png"`
  - `og:locale`: `"es_ES"`
- Tarjetas de Twitter (Twitter Cards):
  - `twitter:card`: `"summary_large_image"`
  - `twitter:title`, `twitter:description` y `twitter:image`.

### R-42.4: Seguridad en Hipervínculos Salientes (Ubiquitous)
Todos los hipervínculos externos en componentes de interfaz que utilicen `target="_blank"` **DEBERÁN** incluir de forma obligatoria el atributo de seguridad `rel="noopener noreferrer"` para prevenir vulnerabilidades de secuestro de pestaña (*reverse tabnabbing*).

---

## 2. Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Rastreo de robots.txt por bots de búsqueda
  Dado que un bot de indexación consulta "https://arrendis.com/robots.txt"
  Cuando lee las directivas de exclusión
  Entonces encuentra bloqueadas las rutas "/portfolio", "/properties/", "/onboarding" y "/api/"
  Y encuentra referenciado el "Sitemap: https://arrendis.com/sitemap.xml"

Escenario: Consulta del sitemap.xml
  Dado que un motor de búsqueda solicita "https://arrendis.com/sitemap.xml"
  Cuando analiza el documento XML
  Entonces todas las URLs públicas activas están listadas con protocolo HTTPS
  Y no contiene ninguna URL privada (/portfolio o /properties/1)

Escenario: Compartir enlace en redes sociales y mensajería
  Dado que un usuario comparte "https://arrendis.com" en WhatsApp, Telegram o LinkedIn
  Cuando la aplicación genera la tarjeta de vista previa
  Entonces muestra la imagen corporativa og:image
  Y muestra el título editorial y la descripción en español
```
