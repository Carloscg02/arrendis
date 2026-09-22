# 📋 F-28: Onboarding Guiado & Estimador Fiscal Interactivo — Requirements

> **Feature ID:** F-28  
> **Título:** Onboarding Guiado & Estimador Fiscal Interactivo Multiplataforma (First-Time User Experience)  
> **Estado:** Borrador — Pendiente de Aprobación  
> **Fecha:** 2026-09-22  
> **Dependencias:** F-06 (Auth/JWT), F-08 (Multi-tenancy), F-09 (Datos Fiscales), F-12 (Motor Fiscal)  

---

## 1. Visión y Justificación de Negocio

### 1.1 El Problema (The Drop-off Gap)
Cuando un nuevo propietario se registra en Arrendis, actualmente aterriza en un panel vacío (*"No tienes propiedades registradas"*). 
El valor diferencial más potente de Arrendis frente a un Excel o cualquier software genérico de alquileres es su **motor fiscal oficial homologado con la normativa del IRPF de la AEAT** (amortización del 3% del valor de construcción, deducción de suministros, Modelo 100).

Sin embargo:
1. Si dejamos al usuario solo ante un formulario en blanco, la tasa de activación cae en picado.
2. Si le exigimos los 10 campos fiscales exactos (desglose catastral suelo/construcción del recibo del IBI, gastos de notaría y registro con céntimos) durante el registro, el 90% abandonará porque nadie tiene la escritura a mano al probar una app.
3. El usuario necesita experimentar un **"Aha! moment"** en sus primeros 90 segundos: ver con números reales cuánto dinero va a deducir en su declaración de la Renta.

### 1.2 La Restricción Estratégica: Arquitectura Multiplataforma (Web hoy, Móvil mañana)
El usuario ha definido como requisito que **esta experiencia debe ser reutilizable en la futura aplicación móvil**.
Por tanto:
- **Cero lógica fiscal o de validación aislada en el frontend:** El cálculo del simulador fiscal rápido, los porcentajes estándar de construcción, los tipos de amortización y las reglas de negocio deben residir en el **Backend (Capa de Dominio y Aplicación)**.
- **API REST Agnóstica:** Los mismos endpoints que utiliza el cliente web React deben poder ser consumidos por una futura app en React Native, Flutter, Kotlin o Swift sin cambiar una sola línea de código en el servidor.
- **Persistencia del Estado de Onboarding por Usuario:** El backend debe saber si el usuario ha completado o saltado el onboarding (`onboarding_completed`), garantizando coherencia si el usuario alterna entre web y móvil.

---

## 2. Requerimientos de Usuario (Notación EARS)

### US-F28-01: Detección de Primer Acceso
- **Ubiquitous:** El sistema debe identificar si un usuario autenticado ha completado o no su onboarding inicial.
- **EARS (Event-Driven):** *Cuando* un usuario inicia sesión o se registra y su campo `onboarding_completed` sea `false` (o no tenga ninguna propiedad en su catálogo), *el sistema deberá* ofrecerle la experiencia de onboarding guiado.

### US-F28-02: Registro Ágil de la Primera Propiedad (Paso 1)
- **EARS (State-Driven):** *Mientras* el usuario esté en el Paso 1 del onboarding, *el sistema deberá* solicitar únicamente los datos esenciales del inmueble (Alias/Nombre, Dirección básica y Tipología) con valores por defecto inteligentes.

### US-F28-03: Simulación Fiscal en Tiempo Real y Momento 'Aha!' (Paso 2)
- **EARS (Event-Driven):** *Cuando* el usuario introduzca el precio de compra y el año de adquisición en el Paso 2, *el sistema deberá* calcular en tiempo real (vía API backend) la deducción anual estimada por amortización (3% s/ valor de construcción estimado según ratio medio legal del 70%) y el ahorro orientativo en el IRPF.
- **EARS (Ubiquitous):** *El sistema deberá* mostrar un mensaje pedagógico que explique claramente que cada euro amortizado y cada factura registrada reduce la base imponible del alquiler en el Modelo 100 de la AEAT.

### US-F28-04: Automatización de Alquiler y Suministros (Paso 3)
- **EARS (Optional):** *Donde* el usuario desee configurar la automatización desde el inicio, *el sistema deberá* permitir registrar la renta mensual y el código CUPS de electricidad/gas, explicando que los suministros pagados por el propietario son 100% deducibles.

### US-F28-05: Mecanismo de Salto / Abandono Voluntario (Fricción Cero)
- **EARS (Event-Driven):** *Cuando* el usuario decida no completar el asistente y pulse "Explorar panel por mi cuenta", *el sistema deberá* marcar el onboarding como omitido/completado y redirigirlo inmediatamente al catálogo general sin bloquearlo.

### US-F28-06: Bootstrapping Atómico de Datos
- **EARS (Event-Driven):** *Cuando* el usuario confirme el asistente en el último paso, *el sistema deberá* crear la propiedad, los datos fiscales iniciales derivados y el contrato/suministros asociados en una única operación atómica para evitar estados inconsistentes (especialmente crítico en conexiones móviles inestables).

---

## 3. Requerimientos Funcionales (RF)

| ID | Requerimiento | Prioridad |
|---|---|---|
| **RF-F28-01** | **Endpoint de Simulación Fiscal Rápida:** `POST /api/fiscal/quick-estimate` accesible para calcular deducción sin persistir datos. | Must Have |
| **RF-F28-02** | **Persistencia de Estado de Onboarding:** Añadir bandera `onboarding_completed: bool` en la entidad `User` y en la tabla SQLite de usuarios. | Must Have |
| **RF-F28-03** | **Endpoint de Bootstrapping Atómico:** `POST /api/onboarding/bootstrap` que cree propiedad + datos fiscales iniciales + contrato opcional en un Caso de Uso atómico. | Must Have |
| **RF-F28-04** | **Endpoint de Omisión (Skip):** `POST /api/users/me/onboarding/skip` para marcar el onboarding como completado sin crear inmueble. | Must Have |
| **RF-F28-05** | **Interfaz Web Editorial:** Wizard interactivo de 3 pasos montado sobre el sistema de diseño Montamont (Newsreader serif, unbleached canvas, acento granate Arrendis). | Must Have |
| **RF-F28-06** | **Disclaimer Legal:** Mensaje explícito informando de que la amortización rápida es una estimación orientativa (Art. 23.1.b LIRPF) y que los decimales exactos se calibran con el recibo del IBI. | Must Have |

---

## 4. Requerimientos No Funcionales (RNF)

| Dimensión | Criterio |
|---|---|
| **Multiplataforma** | El 100% de las fórmulas matemáticas, porcentajes de amortización (3%) y ratios de estimación deben ejecutarse en el dominio Python. Cero duplicación de lógica en clientes. |
| **Rendimiento** | El endpoint de simulación rápida debe responder en menos de 50 ms para permitir actualización reactiva mientras el usuario escribe en el input. |
| **Retrocompatibilidad** | Los usuarios registrados antes de esta feature deben inicializarse con `onboarding_completed = 1` mediante migración segura en SQLite para no forzar onboarding a usuarios veteranos. |
| **Experiencia Móvil (Touch & Layout)** | La interfaz debe ser completamente utilizable con una sola mano en pantallas de 360px a 430px de ancho, con botones de acción generosos (mínimo 44px de altura táctil). |
| **Arquitectura Limpia** | Separación estricta en 4 capas (Domain -> Application -> Ports -> Adapters) según la constitución `agents.md`. |
