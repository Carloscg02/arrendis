# 📋 Requisitos de Negocio y Sistema: F-43
# Resiliencia de Navegación (Página 404 Personalizada Atelier Editorial) y Accesibilidad en Formularios

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Especificado  
> **Fecha:** 2026-10-03  
> **Formato:** Notación EARS (Easy Approach to Requirements Syntax)  

---

## 1. Requisitos del Sistema (EARS)

### R-43.1: Ruta Comodín de Respaldo 404 en React Router (Event-Driven)
**CUANDO** un usuario o cliente web navegue a una ruta no reconocida o inexistente en la aplicación (ej. `/xyz`, `/inmueble/999`), el enrutador de React (`frontend/src/App.tsx`) **DEBERÁ** interceptar la petición mediante la ruta comodín `<Route path="*" element={<NotFound />} />` y renderizar la página de error 404 personalizada con diseño Atelier Editorial, evitando pantallas en blanco o fallos no controlados.

### R-43.2: Página de Error 404 Atelier Editorial y Navegación de Rescate (Ubiquitous)
El componente `NotFound.tsx` **DEBERÁ** renderizarse con la identidad visual corporativa de Arrendis (Newsreader para titulares, Space Mono para códigos de error y coordenadas, Inter para texto explicativo y fondo `#f9f7f5`), ofreciendo enlaces de rescate accesibles hacia el inicio (`/`) y la cartera de inmuebles (`/portfolio`), sin contener emojis en la interfaz. Asimismo, se **DEBERÁ** proporcionar una plantilla de fallback estática `frontend/public/404.html` para servidores web.

### R-43.3: Accesibilidad Semántica en Controles de Formulario (Ubiquitous)
Todos los campos de entrada (`<input>`, `<select>`) en `ContractForm.tsx` y demás formularios del sistema **DEBERÁN** estar vinculados explícitamente a su etiqueta mediante el atributo `id` en el campo y `htmlFor` en el `<label>`, garantizando compatibilidad con lectores de pantalla (criterio WCAG 2.1 / 1.3.1 e ISO 40500).

### R-43.4: Corrección de Elementos Interactivos No Semánticos (Ubiquitous)
Los contenedores `<div>` o `<span>` que incorporen manejadores de eventos `onClick` en `Modal.tsx`, `FiscalDataForm.tsx`, `PWAInstallModalIOS.tsx` y `PropertyDetail.tsx` **DEBERÁN** sustituirse por botones semánticos `<button>` o dotarse de atributos de accesibilidad explícitos (`role="button"` o `role="group"`, `tabIndex={0}`, y escuchadores de teclado para `Enter`/`Space`/`Escape`).

### R-43.5: Prevención de Doble Envío en Operaciones Asíncronas (State-Driven)
**CUANDO** un usuario envíe un formulario de contrato en `ContractForm.tsx`, el botón de confirmación **DEBERÁ** deshabilitarse durante el procesamiento de la petición de red (`disabled={isSubmitting}`), previniendo la duplicación de registros por doble clic.

### R-43.6: Integridad de Rutas y Enlaces Internos (Ubiquitous)
La plataforma **DEBERÁ** garantizar que todos los enlaces internos detectados en el código resuelvan hacia rutas válidas o activos estáticos correspondientes, alcanzando un estado de cero alertas de severidad `HIGH` en el auditor de rutas y enlaces (`audit-links`).

---

## 2. Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Navegación a una URL inexistente
  Dado que un usuario ingresa la dirección "https://arrendis.com/ruta-invalida"
  Cuando la aplicación evalúa la ruta
  Entonces se muestra la página 404 personalizada de Arrendis con diseño Atelier Editorial
  Y el usuario dispone de botones funcionales para regresar al inicio o a su cartera
  Y no se muestran emojis en la interfaz

Escenario: Lectura accesible en el formulario de contratos
  Dado que un usuario con lector de pantalla accede al modal de "Nuevo Contrato"
  Cuando navega por los campos de nombre, NIF, fecha y renta
  Entonces cada campo de entrada tiene su identificador "id" emparejado con el "htmlFor" de su etiqueta
  Y el lector anuncia con claridad el propósito de cada campo

Escenario: Cierre accesible de modales y cabeceras desplegables
  Dado que un usuario navega utilizando el teclado
  Cuando interactúa con el fondo del modal o las cabeceras de sección fiscal
  Entonces los elementos interactivos responden a la tecla Escape o Enter
  Y no existen avisos de elementos interactivos no semánticos en la auditoría
```
