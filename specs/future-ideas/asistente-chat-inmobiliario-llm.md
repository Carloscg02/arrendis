# 🤖 Co-piloto Operativo del Propietario (Asistente IA Inmobiliario con LLM)

> **Estado:** 📦 **Archivado en Future Ideas (Descartado temporalmente por falta de valor real / ROI insuficiente)**  
> **Fecha de dictamen estratégico:** 2026-09-08  
> **Conclusión de producto:** Actualmente **no se le ve valor suficiente frente a una buena interfaz de usuario tradicional (tooltips, microcopy, tablas visuales)**. Se descarta su implementación inmediata para evitar caer en *"IA por tener IA"* (AI slop / postureo técnico).  
> **Apertura a futuro:** Si en el futuro se identifica una necesidad de negocio real comprobada o un caso de uso con retorno tangible indiscutible (ej. canal móvil de WhatsApp para operaciones en movilidad), este documento contiene toda la arquitectura técnica, modelo de dominio y desglose de tareas listo para ser rescatado y transformado en una **Épica real (`E-03`)**.

---

## 1. Reflexión Crítica y Lecciones de Producto (¿Por qué se descarta por ahora?)

Durante las sesiones de evaluación de producto del 2026-09-08 se debatió exhaustivamente si este asistente aportaba una ventaja real al propietario o si era una distracción técnica superflua. Se llegó a las siguientes conclusiones determinantes:

### 1.1 La trampa de la "IA Visible" (Chatbots) vs. la "IA Invisible" (Automatización Real)
* **IA Visible (Chatbots):** Casi siempre generan una experiencia inferior a una buena UI. Obligan al usuario a pensar un prompt, teclearlo y esperar 3 segundos para obtener datos que estarían mejor representados en un gráfico o tarjeta fija del dashboard.
* **IA Invisible (Headless):** Es donde la IA realmente aporta magia y ahorro de tiempo. Un ejemplo perfecto ya implementado en la plataforma es la **Épica E-02 (Suministros)**: el usuario sube un PDF de Endesa o Repsol y el LLM (`GeminiFlashAdapter` + `PrivacyScrubber`) extrae el CUPS, fechas e importes en segundo plano, ahorrando tiempo real de mecanografiado sin obligar a nadie a "charlar" con la máquina.

### 1.2 Por qué otros casos de uso del chat no justifican su desarrollo:
* **¿Explicar conceptos como qué es el CUPS o cómo funciona la amortización?**  
  Un usuario que rellena un formulario no quiere abrir un chat lateral para preguntar. Necesita un **tooltip in-situ** o un texto de ayuda claro junto al campo (`❓ ¿Dónde encuentro el CUPS en mi factura?`). Una buena UX tradicional es 100 veces más rápida, precisa y cómoda.
* **¿Explicar las funcionalidades de la aplicación (Onboarding / FAQ)?**  
  Arrendis no es un ERP inabarcable. Es una herramienta enfocada (Propiedades, Contratos, Ingresos/Gastos, Suministros, Fiscalidad). La propia navegación explica la app sin necesidad de un bot que nadie lee.
* **¿Asesoramiento fiscal?**  
  Totalmente descartado: la fiscalidad en España es delicada y genera responsabilidad. Ya contamos con la **Épica E-01**, cuyo motor determinista en Python puro calcula amortizaciones y borradores de Renta Web con precisión matemática y sin riesgo de alucinaciones.

### 1.3 La fricción de la detección de cobros bancarios:
* Se valoró la posibilidad de que el asistente avisara de qué inquilinos no han pagado la renta del mes.
* **Conclusión:** Si el usuario tiene que meter el ingreso a mano en la app, el chat no aporta nada. Y automatizarlo mediante reglas de correo (reenviar alertas de transferencias del banco por inquilino/cuenta) impone una **fricción de configuración inasumible** para la mayoría de los usuarios.

---

## 2. Condiciones para su Reactivación Futura como Épica E-03

Esta iniciativa solo debería ser rescatada del archivo si se cumple alguna de estas dos condiciones:

1. **Se implementa previamente un sistema natural y sin fricción de control de cobros:**
   * Por ejemplo, un modelo nativo de *"Rentas esperadas a 1-clic"* en la app (el día 1 se listan los cobros esperados y con un botón se marca `Cobrado` o se abre WhatsApp) o subida mensual de extracto bancario en 15 segundos.
2. **Se prioriza el canal de movilidad directa (WhatsApp):**
   * Si el propietario necesita interactuar con su cartera de inmuebles desde la calle sin abrir el navegador web (ej. consultar datos de un contrato o reclamar un recibo mientras habla por teléfono).

---

## 3. Casos de Uso de Alto Valor (si se decide reactivar en el futuro)

Si se reactiva, el asistente debe concebirse exclusivamente como un **Co-piloto Operativo (Actionable Landlord Co-Pilot)**, enfocado en:

### 3.1 Control de Morosidad y Avisos de WhatsApp (Días 1 al 10 de mes)
* **Consulta:** *"¿Quién falta por pagar este mes?"*
* **Respuesta:**
  > *"De tus 3 contratos vigentes, 2 han pagado: Elena (Piso Centro, 750 €) y Marta (Estudio B, 600 €).  
  > ⚠️ **Falta Carlos (Piso Mayor, 850 €)**. Su fecha límite era el día 5 (lleva 3 días de retraso)."*
* **Acción 1-Click:**  
  Generación automática de borrador cordial listo para enviar por WhatsApp:  
  `[📱 Abrir en WhatsApp]` (`https://wa.me/?text=...`) o `[📋 Copiar texto]`:
  > *"Hola Carlos, espero que todo vaya bien. Te escribo brevemente porque revisando las cuentas no veo aún reflejada la transferencia de la renta de septiembre (850 €). ¿Podrías confirmarme cuando puedas si está emitida? ¡Muchas gracias!"*

### 3.2 Analítica Ad-Hoc Compleja (Preguntas que ningún dashboard responde)
Consultas agregadas que requerirían múltiples filtros o cálculos manuales en Excel:
* *"¿Cuánto he pagado de media de luz al mes en el piso de Gran Vía en lo que va de 2026?"*
  > *"En Gran Vía has pagado un total de 420 € de luz en 2026 (media de **52,50 €/mes**). El mes más caro fue enero (84 €) y el más bajo mayo (31 €)."*
* *"¿Cuál ha sido el mes con más gastos este año y qué conceptos lo dispararon?"*
* *"¿Qué porcentaje de los ingresos brutos se han llevado los suministros en el piso de Salamanca?"*

### 3.3 Auditoría de Integridad de la Cartera y Datos Incompletos
* *"¿Tengo alguna propiedad a la que le falten datos para el informe fiscal?"*
  > *"Sí: **Piso Gran Vía** no tiene registrado el desglose catastral de la construcción ni los gastos de compra, por lo que el motor fiscal de la Épica E-01 no puede calcular su amortización del 3%."*
* *"¿Hay facturas de suministros pendientes de confirmar?"*
  > *"Tienes 2 facturas de luz auto-importadas en estado pendiente de revisión (`is_verified = False`) en Piso Centro por un total de 115,40 €."*

### 3.4 Vencimientos y Redacción de Notificaciones Formales (LAU)
* *"¿Qué contratos vencen en los próximos 90 días?"*
* *"Redáctame el preaviso formal de no renovación según la LAU para el inquilino del Piso Mayor respetando los meses legales de antelación."*
* *"Calcula la actualización de renta de Elena según el último índice y redacta la notificación."*

---

## 4. Arquitectura Técnica Diseñada (Lista para ser implementada)

El diseño técnico ya está concebido con **Arquitectura Hexagonal desacoplada**, de modo que el núcleo de negocio sea agnóstico del canal de entrada:

```
                           CANALES DE ENTRADA (Inbound Adapters)
                           ┌───────────────────────────────────┐
                           │ A) Drawer Web en React (Frontend) │
                           └─────────────────┬─────────────────┘
                                             │
                                             ▼
                           ┌───────────────────────────────────┐
                           │ B) Webhook Inbound de WhatsApp    │
                           │    (Twilio / Evolution API)       │
                           └─────────────────┬─────────────────┘
                                             │
                                             ▼
                                  NÚCLEO DE DOMINIO / CASO DE USO
                           ┌───────────────────────────────────┐
                           │ OwnerOperationsAgentUseCase       │
                           │                                   │
                           │ 1. Consulta Repositorios          │
                           │    (Inmuebles, Contratos, Pagos,  │
                           │     Suministros, Fiscalidad)      │
                           │ 2. Construye Snapshot en memoria  │
                           │ 3. Aplica PrivacyScrubber (GDPR)  │
                           │ 4. Prompting a Gemini 2.0 Flash   │
                           │ 5. Controla Cuota Diaria / Ráfaga │
                           └─────────────────┬─────────────────┘
                                             │
                                             ▼
                                     MOTOR LLM GRATUITO
                           ┌───────────────────────────────────┐
                           │ LLMProviderPort                   │
                           │ └── GeminiFlashAdapter            │
                           │     (0 €/mes, 1.500 RPD)          │
                           └───────────────────────────────────┘
```

---

## 5. Política de Cuotas y Cero Coste (Free Tier)

* **Proveedor:** Google Gemini 2.0 Flash a través del `GeminiFlashAdapter` existente (F-17).
* **Capacidad de Google:** 1.500 peticiones al día (RPD) y 15 peticiones por minuto (RPM) gratuitas.
* **Cuota por Usuario en SQLite:**
  * Máximo **25 - 30 consultas diarias por propietario** (se resetea a las 00:00 UTC).
  * Límite de ráfaga: máximo **3 peticiones por minuto** para blindar la ventana de 15 RPM.
* **Privacidad (RGPD):** Paso obligatorio por `PrivacyScrubber` (F-18) para eliminar IBANs y DNIs antes de enviar el snapshot de contexto al LLM.

---

## 6. Desglose en Features Atómicas para la futura Épica E-03

En caso de activarse, la épica se desarrollará mediante el flujo SDD estricto en estas 3 tareas:

1. **F-XX (Backend Core & Quota Engine):**
   * `OwnerFinancialSnapshot` + `AssistantContextBuilder` (agregación de métricas y auditoría en memoria).
   * Persistencia en SQLite de cuota diaria y control de ráfagas.
   * Filtro de privacidad RGPD con `PrivacyScrubber`.
2. **F-XX (API & Casos de Uso):**
   * `OwnerOperationsAgentUseCase` integrando Gemini Flash con system prompt estricto (cero alucinaciones, respuestas ceñidas a datos reales).
   * Endpoints REST `POST /api/assistant/chat` y `GET /api/assistant/quota`.
3. **F-XX (Frontend o Integración de Canal):**
   * *Opción Web:* Drawer deslizante en React con renderizado Markdown, quick pills y botón de acción directa a WhatsApp.
   * *Opción WhatsApp:* Webhook para recibir y contestar mensajes directamente desde la app de WhatsApp del propietario.
