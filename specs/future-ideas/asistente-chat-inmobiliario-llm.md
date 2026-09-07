# Asistente Conversacional IA para Propietarios (Chat Inmobiliario con Gemini Flash)

Este documento describe la propuesta técnica y de producto para incorporar un **asistente de chat inteligente** dentro de la plataforma **Rental Handler / Arrendis**. 

El asistente permitirá a los propietarios consultar en lenguaje natural el estado de sus finanzas, vencimientos de contratos, rentabilidad y suministros, reutilizando la infraestructura de IA ya construida y manteniéndose **100% gratuito (0 €/mes)**.

---

## 1. Visión y Casos de Uso

Los propietarios a menudo necesitan respuestas rápidas sin tener que navegar por múltiples pantallas, tablas y filtros. El chat actuará como un **asesor financiero y gestor patrimonial personal**:

* **Consultas de Rentabilidad y Finanzas:**
  * *"¿Cuánto beneficio neto llevo acumulado este año en el Piso Gran Vía?"*
  * *"¿Cuál de mis propiedades ha tenido más gastos este trimestre y por qué?"*
  * *"¿Cuánto he pagado en total de suministros (luz y gas) en los últimos 6 meses?"*
* **Gestión de Contratos e Inquilinos:**
  * *"¿Cuándo vence el contrato de arrendamiento de Gran Vía?"*
  * *"¿Qué contratos tengo que renovar antes de final de año?"*
  * *"¿A cuánto asciende la renta mensual total de todos mis inmuebles alquilados?"*
* **Alertas y Pendientes:**
  * *"¿Tengo alguna factura de suministro sin verificar o pendiente de asignar?"*
  * *"¿Hay algún inmueble actualmente en estado desocupado?"*

---

## 2. Aprovechamiento de la Infraestructura Existente (Cero Coste Adicional)

La implementación se apoya directamente en las piezas ya creadas en la **Epic E-02**:

1. **Reutilización del Puerto y Adaptador (`LLMProviderPort` / `GeminiFlashAdapter` - F-17):**
   - El adaptador no está atado a facturas; es un cliente genérico de **Google Gemini 2.0 Flash**.
   - Se conecta usando la misma variable `GEMINI_API_KEY`.
2. **Capa Gratuita de Google AI Studio:**
   - **1.500 peticiones gratuitas al día** (se renuevan cada 24 horas).
   - Para un propietario o un grupo reducido de usuarios, 1.500 consultas diarias es una capacidad enorme (equivalente a 45.000 mensajes al mes a coste 0,00 €).
3. **Privacidad Garantizada (`PrivacyScrubber` - F-18):**
   - Antes de enviar el resumen financiero a la IA, el texto se pasa por el anonimizador para redactar IBANs, DNIs o cuentas bancarias, asegurando el cumplimiento estricto del RGPD.

---

## 3. Arquitectura Técnica: RAG Ligero (In-Context Prompting)

A diferencia de sistemas que requieren bases de datos vectoriales pesadas (Pinecone, Chroma, Qdrant), en una aplicación de gestión de alquileres **los datos de un propietario caben en unos pocos kilobytes**. 

Por tanto, el patrón más eficiente, rápido y barato es el **RAG en memoria (In-Context Prompting)**:

```
[Usuario en el Chat] ───> "¿Cuánto llevo ganado en Gran Vía este año?"
                               │
                               ▼
           [Backend: ChatWithPropertyAssistantUseCase]
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
[SQLite: Repositorios]                       [Verificación Multi-Tenant]
- Filtra por user_id                         Solo accede a inmuebles
- Carga Propiedades, Contratos,              del usuario autenticado
  Ingresos y Gastos del año
        │
        ▼
[PrivacyScrubber] (Elimina IBANs / DNIs residuales)
        │
        ▼
[Prompt Estructurado a Gemini 2.0 Flash]
  System: "Eres el asesor financiero personal de Arrendis. 
           Responde al propietario basándote EXCLUSIVAMENTE en sus datos reales..."
  Contexto JSON/Texto: Resumen de inmuebles, balances y contratos
  Pregunta: "¿Cuánto llevo ganado en Gran Vía este año?"
        │
        ▼
[Respuesta en Lenguaje Natural] ───> "En 2026 llevas 7.150 € de beneficio neto..."
```

---

## 4. Política de Cuotas y Protección de Límites (Rate Limiting)

Para garantizar que la cuota diaria gratuita de Google (1.500 RPD) nunca se agote por abusos accidentales o ataques:

1. **Límite Diario por Usuario:**  
   - Máximo **25 - 30 mensajes al día por usuario**.
   - Un contador en base de datos o en memoria que se resetea a las 00:00 UTC.
   - Si el usuario supera el límite, la UI muestra un aviso amigable: *"Has alcanzado tu límite de 25 consultas diarias del asistente. Se renovará mañana a las 00:00."*
2. **Protección de Ráfagas (Burst Control):**  
   - Google impone un límite de **15 peticiones por minuto (RPM)**.
   - Implementar un rate-limiter en el endpoint del chat (ej. máximo 3 mensajes por minuto por usuario) para evitar saturar la ventana de ráfaga.

---

## 5. Diseño de Interfaz de Usuario (UI / UX)

* **Ubicación:** Un botón flotante o acceso directo en la barra superior/lateral (*"Asistente IA"* con icono de chispa/robot).
* **Modo Drawer / Modal lateral:** Un panel deslizable que no interrumpe la navegación del usuario.
* **Sugerencias rápidas (Pills):** Botones preconfigurados al abrir el chat para incentivar el uso:
  - *📊 "Resumen financiero de este año"*
  - *📅 "¿Qué contratos vencen pronto?"*
  - *⚡ "¿Cuánto gasté en luz el mes pasado?"*
* **Renderizado:** Formato Markdown con cifras destacadas en negrita y tablas limpias si la respuesta compara propiedades.

---

## 6. Estimación de Esfuerzo

| Componente | Tarea | Complejidad |
| :--- | :--- | :--- |
| **Backend** | Crear `ChatWithPropertyAssistantUseCase` + context builder de propiedades | Baja (2-3 horas) |
| **Seguridad** | Rate limiting por usuario (contador diario + ráfaga) | Baja (1 hora) |
| **API** | Endpoint `POST /api/chat/message` | Muy baja (30 min) |
| **Frontend** | Componente flotante de chat en React + selector de sugerencias | Media (3-4 horas) |
| **Coste recurrente** | Facturación API | **0 €/mes** (Capa gratuita de Gemini Flash) |
