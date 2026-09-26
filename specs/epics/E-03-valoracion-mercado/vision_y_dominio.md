# 🏢 Épica E-03: Estimación de Mercado y Orientación de Renta por IA

> **Versión:** 1.0  
> **Estado:** En Descubrimiento (Discovery)  
> **Fecha:** 2026-09-24  
> **Dependencias previas:** F-08 (Multi-tenancy), F-09 (Datos Físicos/Fiscales de Propiedad), F-10 (Contratos de Arrendamiento), F-17 (Puerto LLM)

---

## 1. Objetivo de Negocio y Justificación

Proporcionar a los propietarios de inmuebles de **Arrendis** una herramienta objetiva, transparente y bajo demanda que calcule la **estimación de precio de mercado para venta** y la **renta mensual de alquiler recomendada**, apoyándose en modelos de lenguaje con búsqueda en tiempo real (**Gemini Flash + Google Search Grounding**).

### ¿Qué problema resuelve?

1. **Incertidumbre en la fijación de rentas:** Los caseros particulares suelen fijar el precio del alquiler basándose en corazonadas o en conversaciones informales, cobrando con frecuencia rentas inferiores al mercado real de su barrio o desajustadas tras reformas.
2. **Inviabilidad y coste de APIs inmobiliarias tradicionales:** Portales comerciales como Idealista o Fotocasa no disponen de APIs abiertas ni gratuitas para proyectos independientes, y los scrapers sufren bloqueos anti-bot constantes y fragilidad técnica.
3. **Falta de contexto patrimonial:** El propietario gestiona ingresos y gastos fiscales en Arrendis, pero desconoce la plusvalía latente (valor actual de venta estimado vs. coste de adquisición original) y la rentabilidad bruta teórica de su activo.
4. **Opacidad de las IAs genéricas:** Las estimaciones de IA convencionales sufren de datos estáticos ("alucinaciones") si no están ancladas en búsquedas web reales. Arrendis debe resolver esto con **transparencia radical**: aportando las fuentes reales indexadas y desglosando los factores del cálculo.

---

## 2. Límites del Subdominio (Bounded Context)

### ✅ Lo que ENTRA en esta épica

- **Extensión del modelo de `Property`:** Incorporación de atributos físicos esenciales para la valoración ($m^2$ de superficie, número de dormitorios, planta, presencia de ascensor y estado de conservación).
- **Puerto de Dominio `MarketValuationPort`:** Interfaz agnóstica para solicitar análisis de mercado a partir de dirección y características físicas.
- **Adaptador de Infraestructura con Gemini Flash + Grounding:** Integración con el SDK `google.genai` activando búsqueda web en vivo (`types.GoogleSearch()`) y forzando salida determinista mediante esquema JSON estructurado (`response_schema`).
- **Política de Cooldown / Throttling Configurable:** Limitación temporal de solicitudes por inmueble (ej. configurable vía `VALUATION_COOLDOWN_DAYS`, valor por defecto 30 días) para proteger cuotas de API y evitar solicitudes compulsivas.
- **Persistencia de Valoraciones y Fuentes de Contraste:** Registro en base de datos del informe de valoración (`PropertyValuation`), guardando la fecha, horquilla de precios (mínimo, mediano, máximo), factores correctores y enlaces/títulos de los anuncios reales utilizados como testigos.
- **Experiencia de Usuario Transparente (Explainable AI):** Interfaz en React (diseño *Atelier Editorial*) que muestra claramente el rango estimado, los factores ponderados (ej. ajuste por ascensor o reforma), las fuentes detectadas y el indicador de confianza.

### ❌ Lo que NO ENTRA (fuera de alcance en esta fase)

- **Integración con APIs comerciales de pago o scrapers (Idealista, Fotocasa):** Descartado por límites de cuota abusivos, costes elevados y fragilidad técnica.
- **Tasación Oficial Homologada:** No se emiten certificados con validez legal hipotecaria (norma ECO/Banco de España). La estimación es informativa y orientativa para el inversor.
- **Visualización Georreferenciada en Mapa Interactivo:** Pospuesto como funcionalidad opcional futura (ver `F-33`) para evitar complejidad cosmética innecesaria en el MVP.
- **Actualización automática periódica en segundo plano sin acción del usuario:** Las estimaciones se solicitan siempre bajo demanda explícita del propietario para garantizar control de costes y cuotas.

---

## 3. Lenguaje Ubicuo del Subdominio

| Término | Definición |
|---|---|
| **PropertyCondition** | Enumeración del estado de conservación de la vivienda: `A_REFORMAR`, `BUEN_ESTADO`, `REFORMADO`, `A_ESTRENAR`. |
| **PhysicalAttributes** | Conjunto de datos físicos de la vivienda: superficie construida ($m^2$), número de habitaciones, baños, planta y presencia de ascensor. |
| **MarketValuationReport** | Value Object / Entidad que encapsula el resultado completo del análisis: rangos de venta, rangos de alquiler, factores de cálculo, nivel de confianza y fuentes. |
| **ValuationConfidence** | Indicador de solidez del análisis según la muestra encontrada: `HIGH` (muchas ofertas similares en la zona inmediata), `MEDIUM` (ofertas a nivel de distrito/barrio ampliado), `LOW` (zona con escasos testigos). |
| **ValuationSource** | Registro de un anuncio o testigo real localizado en la búsqueda web: título, URL de referencia, precio publicado y características resumidas. |
| **ReasoningFactor** | Explicación cualitativa y cuantitativa de un factor que sube o baja el valor (ej. *"Bonificación del +10% por vivienda reformada"* o *"Penalización del -15% por ser 4ª planta sin ascensor"*). |
| **ValuationCooldown** | Regla de negocio que impide recalcular la valoración de un inmueble antes de que transcurran $N$ días desde la última estimación guardada. |

---

## 4. Modelo de Dominio y Arquitectura Hexagonal

```
┌────────────────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER (Pure Python, Zero Frameworks)                            │
│                                                                        │
│   Entities & Enums:                                                    │
│     - Property (con surface_m2, bedrooms, floor, has_elevator, cond)   │
│     - PropertyCondition, ValuationConfidence                          │
│     - PropertyValuation                                                │
│                                                                        │
│   Value Objects:                                                       │
│     - ValuationRange (min, median, max)                                │
│     - ValuationSource (title, url, price, m2)                          │
│     - ReasoningFactor (factor_name, impact_percent, description)       │
│                                                                        │
│   Ports:                                                               │
│     - MarketValuationPort (ABC)                                        │
│     - PropertyValuationRepository (ABC)                                │
└────────────────────────────────────────────────────────────────────────┘
                                ▲
                                │ Implements / Uses
┌───────────────────────────────┴────────────────────────────────────────┐
│ APPLICATION LAYER (Use Cases)                                          │
│                                                                        │
│   - RequestPropertyValuationUseCase                                    │
│       * Verifica si existe una valoración dentro del Cooldown          │
│       * Si existe y está en cooldown, devuelve la guardada             │
│       * Si ha expirado o se fuerza, invoca MarketValuationPort         │
│       * Persiste el nuevo PropertyValuation en base de datos           │
│   - GetPropertyValuationHistoryUseCase                                 │
└────────────────────────────────────────────────────────────────────────┘
                                ▲
                                │ Ports & Adapters
┌───────────────────────────────┴────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER                                                   │
│                                                                        │
│   - GeminiMarketValuationAdapter (google.genai + Search Grounding)     │
│   - SQLitePropertyValuationRepository                                  │
│   - MockMarketValuationAdapter (para tests unitarios rápidos y offline)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Estrategia de Determinismo, Transparencia y Control de Cuota

### A. Reducción de la Aleatoriedad del LLM (Determinismo)
1. **Temperature fija:** `temperature = 0.2` para minimizar la variabilidad en los números calculados.
2. **JSON Schema Estricto (`response_schema`):** Se exige a Gemini un formato estructurado con tipos precisos (campos monetarios numéricos enteros, arrays de fuentes con URL válida y lista de factores).
3. **Instrucción de Anclaje de Búsqueda:** El prompt del sistema fuerza al modelo a realizar queries de búsqueda acotadas a la zona (ej: `"alquiler piso [barrio/calle] [ciudad] idealista fotocasa"`) y a basar su cálculo exclusivamente en los datos devueltos por el motor de búsqueda de Google.

### B. Transparencia Radical (Anti-Slop)
En la interfaz de usuario:
* **No usar el término "Tasación Oficial":** Se presenta como *"Estimación de Mercado Arrendis AI"*.
* **Bloque de Evidencias:** Mostrar los enlaces a las ofertas activas encontradas para que el usuario pueda verificar los anuncios con un clic.
* **Desglose de Factores:** Explicar cómo influye tener ascensor, los metros cuadrados y la reforma.

### C. Cooldown Configurable (Protección de Cuotas)
* Variable en entorno: `VALUATION_COOLDOWN_DAYS=30` (por defecto 30 días, configurable por despliegue).
* Si el usuario accede a la ficha del inmueble, visualiza los datos de la última estimación guardada sin hacer llamadas externas.
* El botón *"Actualizar estimación"* muestra el tiempo restante si el cooldown está activo (ej: *"Disponible para actualizar en 12 días"*), evitando el gasto compulsivo de búsquedas.

---

## 6. Desglose de Features Propuestas

| Feature ID | Título | Estado | Descripción |
|---|---|---|---|
| **F-29** | Atributos Físicos de Propiedad y Entidades de Valoración | Pendiente | Extensión de `Property` en dominio, BD y API con $m^2$, habitaciones, planta, ascensor y estado de reforma. Creación de entidades `PropertyValuation` y VOs de fuentes. |
| **F-30** | Puerto de Valoración y Adaptador Gemini con Search Grounding | Pendiente | Creación de `MarketValuationPort` e implementación de `GeminiMarketValuationAdapter` con `google.genai`, herramientas de búsqueda web en tiempo real y validación de esquema JSON. |
| **F-31** | Caso de Uso de Estimación con Política de Cooldown y Persistencia | Pendiente | Orquestación del caso de uso, verificación de periodo de enfriamiento (`VALUATION_COOLDOWN_DAYS`), guardado en SQLite y endpoints FastAPI (`POST /properties/{id}/valuation`, `GET /properties/{id}/valuation`). |
| **F-32** | Interfaz UI de Estimación de Mercado y Explicabilidad (Atelier) | Pendiente | Pantalla/Panel en frontend con solicitud bajo demanda, horquillas visuales de alquiler/venta, desglose de factores de ajuste, enlaces a testigos y estado de cooldown. |
| **F-33** | *(Opcional / Futuro)* Mapa Interactivo de Testigos Georreferenciados | Deferred | Visualización espacial con Leaflet / OpenStreetMap de los comparables detectados en el radio de la propiedad. |
