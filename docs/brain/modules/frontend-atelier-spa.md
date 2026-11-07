# Modulo: Frontend SPA Atelier Editorial (`frontend-atelier-spa`)

> Subsistema vertical de interfaz de usuario: Single Page Application responsive con sistema de diseno editorial, PWA y runtime hibrido Capacitor.

---

## 1. Responsabilidad y Alcance de Negocio
- Experiencia de usuario completa para propietarios de alquileres en España: navegacion fluida, formularios accesibles, respuesta tactil inmediata.
- Implementacion estricta del sistema de diseno Atelier Editorial: tipografia Newsreader/Space Mono/Inter, lienzo calido papel tiza (`#f9f7f5`), acento granate (`#6b0008`) y cero emojis/slop.
- Soporte Progressive Web App (PWA) instalable y sincronizacion nativa para Android mediante `@capacitor/android`.
- Cumplimiento normativo y transparencia legal (paginas RGPD `/privacy` y terminos de servicio `/terms`).

---

## 2. Artefactos del Corte Vertical
- **Arquitectura de Cliente**:
  - `React 19`, `TypeScript 5/6`, `Vite 6/8`, `react-router-dom 7`, `lucide-react`, `motion`
- **Tokens y Contrato de Diseno**:
  - `frontend/src/index.css` (variables CSS `:root`, utilidades tipograficas y layouts)
  - `docs/brain/design.md` (contrato activo con las 7 leyes anti-slop)
- **Vistas Principales (`frontend/src/pages/`)**:
  - `Landing.tsx`, `Login.tsx`, `Register.tsx`, `PropertyList.tsx`, `PropertyDetail.tsx`, `Onboarding.tsx`, `NotFound.tsx`, `PrivacyPolicy.tsx`, `TermsOfService.tsx`
- **Componentes Transversales (`frontend/src/components/`)**:
  - `AppHeader.tsx`, `Modal.tsx`, `ConfirmDialog.tsx`, `Toast.tsx`, `PWAInstallBanner.tsx`, `PWAInstallModalIOS.tsx`, `ErrorBoundary.tsx`
- **Servicios de Red (`frontend/src/services/`)**:
  - `api.ts`, clientes HTTP con manejo de tokens en cookies seguras y refresco automatico.
