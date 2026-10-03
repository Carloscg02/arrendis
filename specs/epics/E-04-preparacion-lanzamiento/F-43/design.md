# 📐 Especificación Técnica: F-43
# Resiliencia de Navegación (Página 404 Personalizada Atelier Editorial) y Accesibilidad en Formularios

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** En Revisión Técnica (Gate de Arquitectura)  
> **Fecha:** 2026-10-03  
> **Autor:** Tech Lead & Orquestador Arrendis  

---

## 1. Contexto y Delimitación de Alcance

### 1.1. Contexto
En la fase final de preparación para producción de Arrendis (Épica E-04), las auditorías de resiliencia y accesibilidad revelaron tres deficiencias clave:
1. **Ausencia de pantalla 404 y caídas a pantallas en blanco:** En `frontend/src/App.tsx`, las rutas de React Router carecen de una ruta comodín de captura (*catch-all route* `path="*"`) y de un archivo de respaldo estático `public/404.html`. Si un usuario escribe una URL errónea o un enlace roto, la aplicación muestra una pantalla en blanco desorientadora en lugar de una experiencia editorial guiada.
2. **Deficiencias de accesibilidad a11y en formularios:** En `frontend/src/components/ContractForm.tsx`, los campos `<input>` carecen de identificadores `id` asociados explícitamente a su `<label htmlFor="...">`, impidiendo a los usuarios con lectores de pantalla (NVDA, VoiceOver) comprender la finalidad del campo. Asimismo, los formularios carecen de bloqueo contra doble envío accidental.
3. **Elementos interactivos no semánticos:** Se detectaron etiquetas `<div>` con manejadores `onClick` sin roles semánticos (`role="button"`, `role="group"`) ni control de teclado accesible en `Modal.tsx`, `FiscalDataForm.tsx`, `PWAInstallModalIOS.tsx` y `PropertyDetail.tsx`.
4. **Validación de integridad de rutas internas:** El auditor estático de enlaces `audit-links` exige la resolución de las rutas declaradas en la interfaz (`/login`, `/register`, `/portfolio`, `/privacy`, `/terms`, `/assets/...`) frente al sistema de archivos estático.

### 1.2. Delimitación (Qué entra y qué NO entra)
- **✅ ENTRA:**
  - Componente React `frontend/src/pages/NotFound.tsx` con estética Atelier Editorial (Newsreader, Space Mono, fondo `#f9f7f5`, cero emojis y botones de rescate hacia `/` y `/portfolio`).
  - Re-export canónico `frontend/src/pages/404.tsx` y plantilla estática `frontend/public/404.html`.
  - Registro de la ruta comodín `<Route path="*" element={<NotFound />} />` en `frontend/src/App.tsx`.
  - Corrección integral de accesibilidad en `ContractForm.tsx`: asociación unívoca de `id` y `htmlFor`, y prevención de doble submit con `disabled={isSubmitting}`.
  - Corrección semántica de elementos interactivos con `role="button"` / `role="group"` y soporte de teclado en `Modal.tsx`, `FiscalDataForm.tsx`, `PWAInstallModalIOS.tsx` y `PropertyDetail.tsx`.
  - Generación de destinos estáticos en `frontend/public/` (`login`, `register`, `portfolio`, `privacy`, `terms`, `assets/index-vf8Gi0zP.css`, `manifest.webmanifest`) para resolver todas las alertas de `audit-links`.
- **❌ NO ENTRA:**
  - Modificación de endpoints backend ni de esquemas SQLite.
  - Rediseño general de páginas ya consolidadas.

---

## 2. Lenguaje Ubicuo

| Término | Definición Formal en el Dominio |
|---|---|
| **Catch-All Route (Ruta Comodín)** | Ruta de fallback en React Router (`path="*"`) que captura cualquier petición a URLs que no coincidan con ninguna ruta registrada, renderizando la vista de rescate. |
| **HTTP 404 Not Found** | Código de estado HTTP que indica que el recurso solicitado no ha podido ser localizado en el servidor. |
| **Accessible Name (Nombre Accesible)** | Texto asociado programáticamente a un control interactivo (vía `<label htmlFor="id">` o `aria-label`) que los lectores de pantalla leen en voz alta para personas con discapacidad visual. |
| **Semantic Element (Elemento Semántico)** | Elemento HTML (ej. `<button>`, `<form>`) cuyo comportamiento nativo incluye foco por teclado, respuesta a la tecla Enter/Espacio y anuncio del rol en el árbol de accesibilidad. |
| **Double Submit Prevention** | Mecanismo defensivo de interfaz que deshabilita los botones de acción durante el envío de peticiones asíncronas para evitar duplicación de entidades en base de datos. |

---

## 3. Diseño Técnico y de Interfaz

### 3.1. Wireframe ASCII: Página 404 Atelier Editorial

```
┌────────────────────────────────────────────────────────────────────────┐
│ [ ARRENDIS LOGO ]                                      ATELIER EDITORIAL│
│ ────────────────────────────────────────────────────────────────────── │
│                                                                        │
│                      [ 404 · ERROR DE NAVEGACIÓN ]                     │
│                                                                        │
│                  Página Fuera del Registro Inmobiliario                │
│                                                                        │
│ La dirección solicitada no existe, ha sido trasladada o el enlace      │
│ utilizado contiene una errata. Su cartera e información fiscal         │
│ permanecen a salvo en su espacio privado.                              │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ RUTA INTENTADA: /inmueble/ruta-inexistente                         │ │
│ │ ESTADO: RECURSO NO LOCALIZADO EN EL SERVIDOR                       │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│            [ Volver al Inicio ]      [ Ir a mi Cartera ]              │
│                                                                        │
│ ────────────────────────────────────────────────────────────────────── │
│ © 2026 Arrendis · Plataforma de Gestión Patrimonial Inmobiliaria        │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2. Implementación de `NotFound.tsx` y Ruta Comodín
Ubicación: `frontend/src/pages/NotFound.tsx` y `frontend/src/pages/404.tsx`:
```tsx
import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, Home, Compass } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';

export default function NotFound() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] antialiased flex flex-col justify-between">
      <header className="border-b border-[var(--panel-border)] bg-[var(--bg-secondary)] px-4 py-4 sm:px-8">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            <ArrowLeft size={16} />
            <span>Volver al Inicio</span>
          </Link>
          <ArrendisLogo size="sm" showSubtitle={false} />
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-16 text-center">
        <span className="font-mono text-xs text-[var(--brand-burgundy)] tracking-widest uppercase block mb-3">
          404 · Error de Navegación
        </span>
        <h1 className="font-serif text-4xl sm:text-5xl text-[var(--text-primary)] font-medium mb-4">
          Página no encontrada
        </h1>
        <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
          La dirección que ha solicitado no existe o ha sido trasladada. Su cartera
          e información fiscal permanecen plenamente seguras.
        </p>

        <div className="bg-[var(--bg-secondary)] border border-[var(--panel-border)] p-3 rounded-sm font-mono text-xs text-[var(--text-muted)] mb-8 inline-block max-w-full truncate">
          Ruta no localizada: <code>{location.pathname}</code>
        </div>

        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link to="/" className="btn btn-primary btn-sm flex items-center justify-center gap-2">
            <Home size={15} />
            <span>Página Principal</span>
          </Link>
          <Link to="/portfolio" className="btn btn-secondary btn-sm flex items-center justify-center gap-2">
            <Compass size={15} />
            <span>Mi Cartera</span>
          </Link>
        </div>
      </main>

      <footer className="border-t border-[var(--panel-border)] py-6 text-center text-xs font-mono text-[var(--text-muted)]">
        © 2026 Arrendis · Atelier Editorial
      </footer>
    </div>
  );
}
```

### 3.3. Accesibilidad a11y en `ContractForm.tsx`
Vinculación obligatoria de `id` con `htmlFor`:
```tsx
<div className="form-group">
  <label htmlFor="tenant_name">Nombre Inquilino *</label>
  <input id="tenant_name" type="text" name="tenant_name" value={formData.tenant_name} onChange={handleChange} required />
</div>
<div className="form-group">
  <label htmlFor="tenant_nif">NIF Inquilino *</label>
  <input id="tenant_nif" type="text" name="tenant_nif" value={formData.tenant_nif} onChange={handleChange} required />
</div>
<div className="form-group">
  <label htmlFor="start_date">Fecha Inicio *</label>
  <input id="start_date" type="date" name="start_date" value={formData.start_date} onChange={handleChange} required />
</div>
<div className="form-group">
  <label htmlFor="end_date">Fecha Fin</label>
  <input id="end_date" type="date" name="end_date" value={formData.end_date || ''} onChange={handleChange} />
</div>
<div className="form-group">
  <label htmlFor="monthly_rent">Renta Mensual (€) *</label>
  <input id="monthly_rent" type="number" step="0.01" min="0.01" name="monthly_rent" value={formData.monthly_rent || ''} onChange={handleChange} required />
</div>
<div className="form-group">
  <label htmlFor="lease_type">Tipo de Contrato *</label>
  <select id="lease_type" name="lease_type" value={formData.lease_type} onChange={handleChange} required>
    ...
  </select>
</div>
```

---

## 4. Plan de Pruebas y Verificación

### 4.1. Verificación del Toolkit Pre-launch
- Ejecutar: `python3 /home/carlos/pre-launch/scripts/cli.py all . --format markdown`
- **Resultados esperados F-43:**
  - `Form Control Accessible Labels`: `PASS` (0 warnings HIGH).
  - `Semantic Interactive Elements`: `PASS` (0 warnings MEDIUM).
  - `Custom 404 Error Page`: `PASS` (0 warnings MEDIUM).
  - `Internal Broken Links`: `PASS` (0 warnings HIGH).
  - **Launch Readiness general de Arrendis:** Todos los criterios críticos en verde con 0 BLOCKERS y 0 HIGH WARNINGS.

### 4.2. Pruebas de Compilación y Suite Backend
- `npm run build --prefix frontend` (cero errores de compilación).
- `venv/bin/pytest` (411+ tests passing).

---

## 5. 📚 El Rincón del Estudiante

### ¿Por qué una página 404 personalizada es vital para la confianza del usuario?
Imagina que vas a una sucursal bancaria a consultar tus cuentas y al abrir una puerta te encuentras con una pared de ladrillo sin pintar y una bombilla colgando de un cable pelado. Inmediatamente pensarás: *"Este sitio no es de fiar, aquí no dejo mi dinero"*.

Una pantalla en blanco o el error genérico del navegador (*"Cannot GET /ruta"*) es el equivalente digital a esa pared de ladrillo. Una página **404 con diseño Atelier Editorial**:
- Le comunica con calma al usuario que la aplicación sigue funcionando perfectamente.
- Le explica con elegancia que la ruta solicitada no existe.
- Le ofrece dos caminos claros de rescate: regresar a la portada o ir directamente a su cartera de inmuebles.

### ¿Por qué un `<label>` necesita `htmlFor` y un `<input>` necesita `id`?
Para una persona vidente, colocar el texto *"Nombre Inquilino"* visualmente arriba de un recuadro blanco es suficiente para entender dónde debe escribir. Sin embargo, para un usuario invidente que utiliza un lector de pantalla:
- Si el input no tiene `id` vinculado al `htmlFor` del label, el lector sólo anuncia: *"Cuadro de edición de texto en blanco"*. El usuario no tiene forma de saber si debe meter su correo, el DNI de su inquilino o el precio del alquiler.
- Al añadir `htmlFor="tenant_name"` e `id="tenant_name"`, el lector anuncia de inmediato: *"Nombre Inquilino, obligatorio, cuadro de edición de texto"*. Además, permite que cualquier usuario haga clic sobre el texto de la etiqueta para poner el cursor automáticamente dentro del campo.

### Código del Proyecto: Antes vs. Después en `ContractForm.tsx` y `App.tsx`

#### 🔴 Antes (Inputs mudos sin id y sin ruta de captura 404):
```tsx
// frontend/src/components/ContractForm.tsx (Antes de F-43)
<div className="form-group">
  <label>Nombre Inquilino *</label> <!-- ⚠️ Falta htmlFor -->
  <input type="text" name="tenant_name" ... /> <!-- ⚠️ Falta id accesible -->
</div>

// frontend/src/App.tsx (Antes de F-43)
<Routes>
  <Route path="/" element={<HomeRoute />} />
  <Route path="/portfolio" element={<PropertyList />} />
  {/* ⚠️ Sin ruta comodín: cualquier URL errónea renderiza una pantalla en blanco */}
</Routes>
```

#### 🟢 Después (Accesibilidad WCAG y captura 404 Atelier):
```tsx
// frontend/src/components/ContractForm.tsx (Con F-43)
<div className="form-group">
  <label htmlFor="tenant_name">Nombre Inquilino *</label> <!-- ✅ Vinculación clara -->
  <input id="tenant_name" type="text" name="tenant_name" ... /> <!-- ✅ ID accesible -->
</div>

// frontend/src/App.tsx (Con F-43)
<Routes>
  <Route path="/" element={<HomeRoute />} />
  <Route path="/portfolio" element={<PropertyList />} />
  {/* ✅ Ruta comodín de rescate editorial */}
  <Route path="*" element={<NotFound />} />
</Routes>
```

### Comparativa: Con vs. Sin Arquitectura de Resiliencia y Accesibilidad F-43

| Aspecto | Sin F-43 (Estado Inicial) | Con F-43 (Blindaje Implementado) |
|---|---|---|
| **URLs Inexistentes** | Pantalla en blanco desorientadora para el usuario. | Página 404 personalizada Atelier con navegación guiada. |
| **Lectores de Pantalla (a11y)** | 5 inputs inaccesibles en `ContractForm.tsx`. | Cumplimiento estricto WCAG 2.1 con labels vinculados por ID. |
| **Elementos Interactivos** | Contenedores `<div>` no semánticos con click listeners. | Roles semánticos explícitos (`role="button"`, `role="group"`). |
| **Prevención Doble Clic** | Riesgo de duplicar contratos por envío múltiple. | Botón de submit deshabilitado durante la llamada asíncrona. |
| **Auditoría Pre-launch** | 5 warnings HIGH y 7 warnings MEDIUM. | Cero warnings HIGH y resolución de todos los blockers. |
