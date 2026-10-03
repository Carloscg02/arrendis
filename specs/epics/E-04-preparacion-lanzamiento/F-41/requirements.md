# 📋 Requisitos de Negocio y Sistema: F-41
# Marco Legal y Cumplimiento Normativo RGPD (Páginas /privacy, /terms y Aviso Early Access)

> **Épica:** E-04 (Launch Readiness & Hardening)  
> **Estado:** Especificado  
> **Fecha:** 2026-10-03  
> **Formato:** Notación EARS (Easy Approach to Requirements Syntax)  

---

## 1. Requisitos del Sistema (EARS)

### R-41.1: Disponibilidad Pública de Páginas Legales (Ubiquitous)
El sistema **DEBERÁ** disponer de rutas públicas accesibles sin requerir autenticación para la Política de Privacidad (`/privacy`) y los Términos y Condiciones de Uso (`/terms`).

### R-41.2: Conformidad RGPD y Categorización de Datos (Ubiquitous)
La Política de Privacidad **DEBERÁ** detallar con precisión las categorías de datos personales y patrimoniales tratados en Arrendis:
- Datos de cuenta: email, nombre de usuario y contraseña cifrada (bcrypt).
- Datos de inmuebles: referencias catastrales, direcciones, superficies, costes de adquisición y desgloses de amortización.
- Datos de inquilinos y contratos: nombres, NIF/NIE, fechas de vigencia y rentas pactadas.
- Datos económicos y de suministros: ingresos de arrendamiento, facturas deducibles y códigos CUPS de suministros.
- Datos técnicos: dirección IP con fines de seguridad y prevención de abusos.

### R-41.3: Derechos ARCO+ y Plazo de Conservación Fiscal (Ubiquitous)
La Política de Privacidad **DEBERÁ** especificar el plazo legal de retención de datos vinculado a las obligaciones tributarias españolas (5 años según Ley General Tributaria) y el cauce de ejercicio de derechos ARCO+ (Acceso, Rectificación, Cancelación/Supresión, Oposición, Limitación y Portabilidad) mediante correo electrónico dedicado `privacidad@arrendis.com`.

### R-41.4: Cláusula Estricta de Exención de Responsabilidad Fiscal (Ubiquitous)
Los Términos de Servicio **DEBERÁN** estipular taxativamente que los cálculos de amortización, rendimientos netos y borradores de IRPF generados por Arrendis constituyen simulaciones algorítmicas de carácter orientativo e informativo, declarando expresamente que Arrendis no presta servicios de gestoría ni asesoramiento fiscal vinculante y que la responsabilidad última de presentación ante la Agencia Tributaria (AEAT) recae en el usuario.

### R-41.5: Disciplina Estricta de Marcadores (Placeholder Discipline) (Ubiquitous)
Los textos legales **DEBERÁN** abstenerse rigurosamente de inventar o ficcionar entidades jurídicas, números CIF, direcciones postales o registros mercantiles, empleando marcadores explícitos estandarizados (`[Razón Social / Titular de la Plataforma]`, `[NIF/CIF del Responsable]`, `[Dirección Postal de Notificaciones]`).

### R-41.6: Aviso Discreto de Versión Preliminar (Early Access) (Ubiquitous)
El sistema **DEBERÁ** mostrar en el pie de página de la aplicación y en las páginas públicas un distintivo discreto informando del estado de versión preliminar: *"Versión Preliminar (Early Access) · Cálculos fiscales orientativos no vinculantes"*.

### R-41.7: Estética Atelier Editorial y Navegabilidad Responsiva (State-Driven)
**CUANDO** un usuario visualice `/privacy` o `/terms` en cualquier dispositivo (móvil o escritorio), el sistema **DEBERÁ** renderizar las páginas aplicando los tokens de `DESIGN.md` (tipografía Newsreader para títulos, Space Mono para metadatos/fechas, Inter para cuerpo de texto y lienzo cálido `#f9f7f5`), con controles de navegación para regresar al inicio o a la cartera sin elementos interactivos mudos ni emojis.

---

## 2. Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Acceso directo a la Política de Privacidad
  Dado que un usuario no autenticado navega a "/privacy"
  Cuando carga la página
  Entonces visualiza el documento de Política de Privacidad de Arrendis
  Y el texto detalla los datos de inmuebles, contratos y suministros tratados
  Y contiene la dirección de contacto "privacidad@arrendis.com" para derechos ARCO
  Y no contiene datos mercantiles ficticios (utiliza marcadores explícitos)

Escenario: Acceso a Términos y Condiciones con limitación fiscal
  Dado que cualquier usuario navega a "/terms"
  Cuando examina la cláusula de responsabilidad de cálculos fiscales
  Entonces el texto aclara que Arrendis no es una asesoría fiscal ni gestoría colegiada
  Y establece que las simulaciones del borrador IRPF son orientativas y no vinculantes

Escenario: Enlaces en el pie de página
  Dado que un usuario visita la página de inicio o landing
  Cuando desciende hasta el pie de página
  Entonces encuentra enlaces funcionales hacia "/privacy" y "/terms"
  Y visualiza el distintivo "Versión Preliminar (Early Access)"
```
