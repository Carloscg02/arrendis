# 📐 Especificación Técnica: F-41
# Marco Legal y Cumplimiento Normativo RGPD (Páginas /privacy, /terms y Aviso Early Access)

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Revisado con Enmiendas Arquitectónicas  
> **Fecha:** 2026-10-03  
> **Autor:** Tech Lead & Orquestador Arrendis  

---

## 1. Contexto y Delimitación de Alcance

### 1.1. Contexto
Arrendis es una plataforma web para la gestión de carteras de inmuebles en alquiler y cálculo fiscal automatizado para la declaración de la renta en España (AEAT Modelo 100). La aplicación recopila y procesa datos patrimoniales y personales de alta sensibilidad:
- Identidad de propietarios e inquilinos (nombres, documentos de identidad NIF/NIE).
- Ubicación catastral e importes de adquisición de inmuebles.
- Contratos de arrendamiento, rentas mensuales y cuentas bancarias asociadas.
- Facturas y recibos de suministros (luz, agua, gas) con identificadores únicos CUPS.

De acuerdo con el Reglamento General de Protección de Datos (RGPD UE 2016/679) y la Ley de Servicios de la Sociedad de la Información (LSSI-CE Ley 34/2002), es imperativo que la plataforma cuente con una **Política de Privacidad** exhaustiva (`/privacy`) y unos **Términos de Servicio** vinculantes (`/terms`), incluyendo una cláusula expresa de exención de responsabilidad sobre los cálculos fiscales y un aviso transparente del estado de versión preliminar (*Early Access*).

### 1.2. Delimitación (Qué entra y qué NO entra)
- **✅ ENTRA:**
  - Componente React `PrivacyPolicy.tsx` en `frontend/src/pages/` (y re-export `privacy.tsx` para compatibilidad heurística con escáneres estáticos).
  - Componente React `TermsOfService.tsx` en `frontend/src/pages/` (y re-export `terms.tsx`).
  - Redacción rigurosa de cláusulas adaptadas al dominio de Arrendis: categorías de datos recopilados, base legal, retención de 5 años por prescripción tributaria y ejercicio de derechos ARCO+ mediante `privacidad@arrendis.com`.
  - Cláusula de limitación de responsabilidad fiscal estipulando que los cálculos del Modelo 100 son simulaciones orientativas y que Arrendis no actúa como asesoría fiscal ni gestoría colegiada.
  - Aplicación estricta de la *Placeholder Discipline* (cero invención de datos mercantiles o CIF falsos).
  - Distintivo sutil de *Early Access* en el pie de página de la plataforma y en las páginas públicas.
  - Registro de las rutas públicas `/privacy` y `/terms` en `frontend/src/App.tsx` y enlaces en `Landing.tsx`.
  - Configuración de enlaces simbólicos raíz `src -> frontend/src` y `public -> frontend/public` para que el toolkit `pre-launch` y los motores de descubrimiento detecten los activos sin distorsionar la estructura monorepo.
- **❌ NO ENTRA:**
  - Banner de consentimiento de cookies complejo (el proyecto no utiliza cookies de seguimiento ni analytics de terceros).
  - Pasarelas de contratación mercantil o firmas notariales electrónicas.

---

## 2. Lenguaje Ubicuo

| Término | Definición Formal en el Dominio |
|---|---|
| **RGPD / GDPR** | Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo relativo a la protección de las personas físicas en lo que respecta al tratamiento de sus datos personales. |
| **LSSI-CE** | Ley 34/2002 de servicios de la sociedad de la información y de comercio electrónico de España, aplicable a prestadores de servicios web. |
| **Placeholder Discipline** | Norma de ingeniería que prohíbe taxativamente inventar o suponer datos mercantiles (razón social, NIF, tomo/folio del registro mercantil o direcciones ficticias) en plantillas legales, utilizando marcadores explícitos (`[Razón Social]`, `[NIF/CIF]`). |
| **Cláusula de Exención Fiscal** | Estipulación contractual que establece que los algoritmos de cálculo tributario (amortizaciones, casillas AEAT) son herramientas orientativas de apoyo y no asesoramiento fiscal vinculante. |
| **Derechos ARCO+** | Derechos de Acceso, Rectificación, Cancelación/Supresión, Oposición, Limitación del Tratamiento y Portabilidad de los datos personales. |
| **Early Access / Versión Preliminar** | Estado de despliegue donde las funcionalidades están disponibles para validación temprana de usuarios bajo premisas de software en evolución. |

---

## 3. Diseño Técnico y de Interfaz

### 3.1. Rutas, Componentes y Enlaces Simbólicos Canónicos
Ubicación de archivos:
- `frontend/src/pages/PrivacyPolicy.tsx` y `frontend/src/pages/privacy.tsx` (re-export).
- `frontend/src/pages/TermsOfService.tsx` y `frontend/src/pages/terms.tsx` (re-export).
- `frontend/src/App.tsx`: Incorporación de las rutas públicas:
  ```tsx
  <Route path="/privacy" element={<PrivacyPolicy />} />
  <Route path="/terms" element={<TermsOfService />} />
  ```
- `frontend/src/pages/Landing.tsx`: Inclusión en el footer de los enlaces `<Link to="/privacy">Privacidad</Link>` y `<Link to="/terms">Términos</Link>`, junto al badge *"Versión Preliminar (Early Access)"*.
- **Estructura de Enlaces Simbólicos Raíz:**
  El toolkit de auditoría de pre-lanzamiento inspecciona patrones relativos a la raíz del repositorio (`src/pages/*`, `public/*`). Para garantizar su detección sin modificar el código de la herramienta de auditoría, se mantienen en la raíz del repositorio los enlaces simbólicos:
  - `src -> frontend/src`
  - `public -> frontend/public`

### 3.2. Wireframe ASCII de Páginas Legales (Atelier Editorial)

```
┌────────────────────────────────────────────────────────────────────────┐
│ [← Volver al Inicio]                                    ARRENDIS       │
│ ────────────────────────────────────────────────────────────────────── │
│                                                                        │
│                      POLÍTICA DE PRIVACIDAD                            │
│           Última actualización: 03 de octubre de 2026                  │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ AVISO PRELIMINAR (EARLY ACCESS)                                    │ │
│ │ Arrendis opera en fase de acceso preliminar. Los datos tratados se │ │
│ │ custodian con cifrado de grado bancario y estricto respeto al RGPD.│ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ 1. RESPONSABLE DEL TRATAMIENTO                                         │
│ El responsable del tratamiento de los datos recabados en esta          │
│ plataforma web es [Razón Social / Titular de la Plataforma], con       │
│ NIF/CIF [NIF/CIF del Responsable] y domicilio a efectos de             │
│ notificaciones en [Dirección Postal de Contacto]. Correo de contacto: │
│ privacidad@arrendis.com.                                               │
│                                                                        │
│ 2. DATOS OBJETO DE TRATAMIENTO                                         │
│ En el marco de la gestión patrimonial y fiscal inmobiliaria, Arrendis  │
│ recopila las siguientes categorías de datos:                           │
│   • Identificativos de cuenta: Correo electrónico, usuario y clave.    │
│   • Inmuebles y Catastro: Referencia catastral, dirección física,      │
│     valor catastral del suelo y construcción, fecha de adquisición.    │
│   • Arrendamientos e Inquilinos: Nombres, NIF/NIE, renta mensual.      │
│   • Fiscalidad y Suministros: Gastos deducibles, códigos CUPS y       │
│     recibos de suministros energéticos e hídricos.                     │
│                                                                        │
│ 3. FINALIDAD Y BASE JURÍDICA                                           │
│ La base jurídica del tratamiento es la ejecución del contrato de uso   │
│ (Art. 6.1.b RGPD) para la consolidación de carteras inmobiliarias y el │
│ cálculo automatizado de borradores fiscales orientativos.              │
│                                                                        │
│ 4. PLAZO DE CONSERVACIÓN                                               │
│ Los datos fiscales y de facturación se conservarán durante la vigencia │
│ de la cuenta de usuario y por un periodo adicional de 5 años tras su   │
│ cancelación, en cumplimiento de los plazos de prescripción de la Ley   │
│ General Tributaria (Ley 58/2003).                                      │
│                                                                        │
│ 5. DERECHOS DEL USUARIO (ARCO+)                                        │
│ Puede ejercer sus derechos de acceso, rectificación, supresión y       │
│ portabilidad escribiendo a privacidad@arrendis.com.                    │
│                                                                        │
│ ────────────────────────────────────────────────────────────────────── │
│ © 2026 Arrendis · Atelier Editorial · Versión Preliminar (Early Access)│
└────────────────────────────────────────────────────────────────────────┘
```

### 3.3. Cláusula Contractual de Exención de Responsabilidad Fiscal (Términos)
En `frontend/src/pages/TermsOfService.tsx`:

> **"6. EXENCIÓN DE RESPONSABILIDAD SOBRE CÁLCULOS FISCALES Y BORRADORES AEAT"**  
> "Arrendis es una solución de software orientada a la organización documental y simulación analítica de carteras inmobiliarias. Todos los cálculos, porcentajes de amortización (Ley IRPF Art. 23), rendimientos netos y casillas estimadas del Modelo 100 de IRPF generados por el sistema constituyen simulaciones algorítmicas de carácter estrictamente informativo y orientativo."  
> "Arrendis y sus desarrolladores NO prestan servicios de gestoría tributaria, asesoría jurídica ni asesoramiento fiscal vinculante. La exactitud de los resultados depende de la integridad de los datos ingresados por el usuario. Es responsabilidad exclusiva e indelegable del usuario cotejar sus declaraciones con un profesional tributario colegiado y con la normativa vigente antes de su presentación oficial ante la Agencia Estatal de Administración Tributaria (AEAT)."

---

## 4. Plan de Pruebas y Verificación

### 4.1. Verificación en Frontend
1. Compilación de TypeScript y Vite: `npm run build --prefix frontend` (cero errores de tipos y empaquetado exitoso).
2. Verificación de renderizado de rutas `/privacy` y `/terms` en React Router.
3. Comprobación de que la interfaz consume los tokens CSS de `index.css` (`var(--bg-primary)`, `var(--text-primary)`, `var(--font-serif)`).
4. Comprobación de que no existen emojis en las vistas legales.

### 4.2. Verificación SAST y Toolkit Pre-launch
- Ejecutar: `python3 /home/carlos/pre-launch/scripts/cli.py all . --format markdown`
- **Criterio de éxito F-41:**
  - `Privacy Policy Page`: `PASS` (antes `WARNING: HIGH`).
  - `Terms & Conditions Page`: `PASS` (antes `WARNING: HIGH`).
  - Cero blockers SAST.

---

## 5. 📚 El Rincón del Estudiante

### ¿Por qué una startup necesita términos legales antes de lanzar, incluso en fase beta?
Imagina que construyes un coche de carreras artesanal en tu garaje y le dices a tu vecino: *"Pruébalo un fin de semana"*. Si tu vecino va a 200 km/h y se sale de la carretera, sin un contrato firmado te dirá que la culpa fue de tus frenos y te demandará por los daños.

En software financiero e inmobiliario ocurre exactamente lo mismo:
1. **La Política de Privacidad:** Es como el inventario de una aduana. La Unión Europea (mediante el RGPD) exige que expliques con transparencia meridiana qué datos metes en tu "maleta" (DNI del inquilino, facturas de Repsol, referencia catastral), con qué derecho los tocas y durante cuántos años los vas a guardar. Si no lo pones, la sanción mínima puede arruinar un proyecto antes de nacer.
2. **Los Términos de Servicio y la Cláusula Fiscal:** Arrendis calcula amortizaciones del 3% sobre el valor catastral de la construcción. Si Hacienda inspecciona a un usuario y le reclama 500€ porque el usuario metió un valor catastral erróneo, los Términos de Servicio son el escudo legal que demuestra que Arrendis es una **calculadora orientativa**, no su asesor fiscal personal.

### ¿Qué es la "Placeholder Discipline"?
Cuando un ingeniero genera plantillas legales mediante Inteligencia Artificial, el modelo suele alucinar nombres como *"Inversiones Ficticias S.L., CIF B-12345678, Calle Gran Vía 123"*. Si esto llega a producción:
- Podrías estar suplantando la identidad de una empresa real existente.
- Estás cometiendo una infracción mercantil en España por publicidad engañosa (LSSI).
La **disciplina de marcadores** exige utilizar etiquetas explícitas como `[Razón Social / Titular de la Plataforma]` para que cualquier auditor o usuario comprenda que se trata de una plantilla en espera de los datos constitutivos definitivos.

### Código del Proyecto: Antes vs. Después en `frontend/src/App.tsx` y `Landing.tsx`

#### 🔴 Antes (Sin rutas legales ni exención en pie de página):
```tsx
// frontend/src/App.tsx - Antes de F-41
<Routes>
  <Route path="/" element={<HomeRoute />} />
  <Route path="/landing" element={<Landing />} />
  <Route path="/portfolio" element={<ProtectedRoute><PropertyList /></ProtectedRoute>} />
  <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
  {/* ⚠️ Faltan rutas /privacy y /terms -> URLs legales devuelven pantalla en blanco */}
</Routes>

// frontend/src/pages/Landing.tsx (Footer) - Antes de F-41
<footer className="landing-footer">
  <p>© 2026 Arrendis. Todos los derechos reservados.</p>
</footer>
```

#### 🟢 Después (Rutas registradas, enlaces funcionales y badge Early Access):
```tsx
// frontend/src/App.tsx - Con F-41
<Routes>
  <Route path="/" element={<HomeRoute />} />
  <Route path="/landing" element={<Landing />} />
  <Route path="/privacy" element={<PrivacyPolicy />} />
  <Route path="/terms" element={<TermsOfService />} />
  <Route path="/portfolio" element={<ProtectedRoute><PropertyList /></ProtectedRoute>} />
</Routes>

// frontend/src/pages/Landing.tsx (Footer) - Con F-41
<footer className="landing-footer flex flex-col md:flex-row justify-between items-center py-8 border-t border-[var(--panel-border)] text-xs text-[var(--text-secondary)]">
  <div className="flex items-center gap-3">
    <span>© 2026 Arrendis</span>
    <span className="px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] border border-[var(--panel-border)] font-mono text-[10px]">
      Versión Preliminar (Early Access)
    </span>
  </div>
  <div className="flex items-center gap-6 mt-4 md:mt-0">
    <Link to="/privacy" className="hover:text-[var(--text-primary)] transition-colors">Privacidad</Link>
    <Link to="/terms" className="hover:text-[var(--text-primary)] transition-colors">Términos de Servicio</Link>
  </div>
</footer>
```

### Comparativa: Con vs. Sin Marco Legal F-41

| Aspecto | Sin F-41 (Estado Inicial) | Con F-41 (Blindaje Implementado) |
|---|---|---|
| **Auditoría Pre-launch** | 2 Warnings de severidad `HIGH` por páginas legales ausentes. | `Privacy Policy` y `Terms` en estado `PASS` (`LOW`). |
| **Responsabilidad Fiscal** | Riesgo de reclamación civil por discrepancias con la AEAT. | Blindaje mediante cláusula explícita de cálculo no vinculante. |
| **Tratamiento de Datos Sensibles** | Opacidad en la recogida de contratos, CUPS y DNIs. | Cumplimiento estricto del deber de información RGPD (Art. 13). |
| **Transparencia con el Usuario** | El usuario desconoce si el producto es final o experimental. | Badge discreto de *Versión Preliminar (Early Access)*. |
