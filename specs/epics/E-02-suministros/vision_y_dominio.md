# ⚡ Épica E-02: Automatización de Gastos de Suministros vía Email

> **Versión:** 1.0  
> **Estado:** En Descubrimiento (Discovery)  
> **Fecha:** 2026-08-04  
> **Dependencias previas:** F-08 (Multi-tenancy), F-11 (Clasificación Fiscal de Gastos)

---

## 1. Objetivo de Negocio y Justificación

Implementar una funcionalidad **zero-cost** (o de coste extremadamente bajo) y de **bajo mantenimiento** que permita a los propietarios registrar automáticamente los gastos mensuales de suministros (luz, agua, gas) de sus inmuebles a partir de los correos electrónicos de facturación recibidos de las comercializadoras, almacenando los recibos PDF originales para su consulta y justificación fiscal.

### ¿Qué problema resuelve?

1. **Trabajo manual recurrente:** El propietario debe revisar sus correos o portales de suministradoras (Endesa, Iberdrola, Naturgy, Aqualia, etc.), descargar el PDF del recibo, extraer el importe, la fecha y la propiedad correspondiente, e introducirlo a mano en la aplicación.
2. **Inviabilidad de integraciones bancarias o APIs directas:** Conectar con APIs bancarias o de comercializadoras implica costes de licencias elevados o integraciones altamente frágiles/complejas que chocan con la premisa de mantener la plataforma como un software gratuito/low-cost.
3. **Pérdida de comprobantes fiscales:** En caso de inspección de la AEAT, el propietario necesita disponer del PDF del recibo original vinculado al gasto deducible.

---

## 2. Límites del Subdominio (Bounded Context)

### ✅ Lo que ENTRA en esta épica
- Lectura/ingesta de correos electrónicos con facturas adjuntas en formato PDF.
- Extracción del texto en bruto del PDF usando herramientas locales de Python (`PyMuPDF`).
- Motor de parsing con arquitectura basada en el **Patrón Estrategia (Strategy Pattern)** para alternar entre:
  - **Vía A:** Reglas de Expresiones Regulares (Regex) locales por comercializadora.
  - **Vía B:** Extracción Semántica mediante IA Generativa (Free Tier de Gemini / LLM) estructurada con JSON Mode (`response_schema`).
- Identificación automática de la propiedad correspondiente a través del código **CUPS** (Código Unificado de Punto de Suministro) o número de contrato.
- Almacenamiento eficiente de los archivos PDF originales (Object Storage o disco local) con vinculación directa al gasto.
- Flujo de **Validación Humana (Human-in-the-loop)**: creación del gasto en estado `PENDING_REVIEW` para confirmación del usuario antes de computar en la rentabilidad neta o borrador fiscal.
- Política de conservación y retención documental (ej. 5 años para cumplimiento fiscal AEAT).

### ❌ Lo que NO ENTRA (fuera de alcance)
- Conexión directa a banca online o APIs de agregación financiera de pago (Salt Edge, Plaid, Tink, etc.).
- Scraping de portales web de comercializadoras que requieran resolver Captchas o doble factor de autenticación (MFA).
- Procesamiento de recibos escaneados en formato imagen sin texto vectorial (OCR complejo fuera del alcance inicial; PyMuPDF asume PDFs con capa de texto digital).
- Pago automático de facturas desde la plataforma.

---

## 3. Lenguaje Ubicuo del Subdominio

| Término | Definición |
|---|---|
| **CUPS** | *Código Unificado de Punto de Suministro*. Identificador único de 20 a 22 caracteres alfanuméricos que identifica un punto de suministro de energía o agua en España. Es la clave clave para emparejar la factura con el inmueble. |
| **IngestionEmail** | Mensaje de correo electrónico entrante recibido en el buzón de la aplicación que contiene uno o más archivos adjuntos de tipo PDF de facturación. |
| **RawPDFDocument** | Documento PDF del recibo de suministro en estado binario u original descargado del correo. |
| **TextExtraction** | Resultado del procesamiento de un `RawPDFDocument` mediante `PyMuPDF` que devuelve el texto plano del documento manteniendo el orden de flujo. |
| **UtilityInvoiceData** | Value Object que contiene los datos estructurados extraídos de la factura: `cups`, `amount`, `issue_date`, `provider_name`, `invoice_number`, `utility_type` (ELECTRICITY, WATER, GAS). |
| **ExtractionStrategy** | Interfaz del puerto de dominio para el motor de parsing de facturas. |
| **RegexExtractionStrategy** | Implementación de `ExtractionStrategy` basada en reglas y expresiones regulares locales por comercializadora. |
| **AIExtractionStrategy** | Implementación de `ExtractionStrategy` basada en el envío del texto plano a un modelo LLM gratuito (ej. Gemini Flash con `response_schema`). |
| **ReceiptStorageAdapter** | Adaptador de infraestructura para guardar los PDFs (ej. Cloudflare R2, S3 o almacenamiento local). |
| **PendingReviewExpense** | Registro de gasto generado automáticamente por la ingesta que requiere confirmación explícita del usuario (`is_verified = False`) antes de computar en balances y borradores fiscales. |

---

## 4. Modelo de Dominio y Arquitectura Hexagonal

### 4.1 Diagrama de Arquitectura y Puertos/Adaptadores

```mermaid
graph TD
    subgraph Adaptadores de Entrada (Inbound)
        A1[IMAP Email Poller] -->|IngestionEmail| P1[EmailIngestionPort]
        A2[Inbound Webhook Receiver] -->|IngestionEmail| P1
    end

    subgraph Núcleo de Dominio (Domain Core)
        P1 --> UC1[ProcessUtilityInvoiceUseCase]
        UC1 --> P2[PDFTextExtractorPort]
        UC1 --> P3[UtilityDataExtractorPort Strategy]
        UC1 --> P4[ReceiptStoragePort]
        UC1 --> P5[PropertyRepositoryPort]
        UC1 --> P6[ExpenseRepositoryPort]
    end

    subgraph Adaptadores de Salida (Outbound)
        P2 --> A3[PyMuPDFAdapter]
        P3 --> A4[RegexUtilityExtractorAdapter Vía A]
        P3 --> A5[GeminiFlashExtractorAdapter Vía B]
        P4 --> A6[CloudflareR2StorageAdapter / LocalFileAdapter]
        P5 --> A7[SQLitePropertyRepository]
        P6 --> A8[SQLiteExpenseRepository]
    end
```

---

## 5. Matriz de Análisis y Puntos de Decisión para el Modelo de Razonamiento

Para cerrar la especificación técnica detallada de las features, el modelo de razonamiento avanzado debe evaluar y resolver las siguientes 5 disyuntivas clave:

### 🔬 Disyuntiva 1: Extracción Regex (Vía A) vs. IA Generativa Gratuita (Vía B)

- **Vía A (Regex Local con PyMuPDF):**
  - *Ventajas:* Cero latencia externa, coste cero absoluto, 100% privado, ejecutable offline.
  - *Inconvenientes:* Fragilidad ante cambios de formato del PDF por parte de Endesa, Iberdrola, etc. Requiere mantenimiento de reglas por proveedor.
- **Vía B (IA Generativa - Gemini Flash Free Tier con `response_schema`):**
  - *Ventajas:* Alta resiliencia a variaciones de formato y maquetación. No requiere mantener reglas Regex por comercializadora.
  - *Inconvenientes:* Dependencia de API externa, latencia de red, límites de cuota (rate limits del free tier), posibles problemas GDPR si se envían datos personales.
- **Enfoque Propuesto a Evaluar:** Implementar el patrón **Fallback Strategy**: Intentar primero Vía A (Regex de proveedor conocido); si no coincide o falla el parseo/validación del CUPS, recurrir a Vía B (IA).

### 💾 Disyuntiva 2: Almacenamiento Documental y Capa Gratuita (Object Storage)

- **Opciones a evaluar:**
  1. **Cloudflare R2:** Capa gratuita permanente de 10 GB de almacenamiento, 1 millón de operaciones de escritura/mes, 10 millones de lecturas/mes, sin costes de egreso de ancho de banda.
  2. **Amazon S3:** Capa gratuita limitada a 12 meses (5 GB).
  3. **Disco Local del VPS / Servidor:** Guardar PDFs en `/var/app/data/receipts/`. Simple, pero requiere backups y gestión de espacio.
  4. **Base de Datos SQLite (BLOB):** Guardar los PDFs comprimidos en la propia BD.
- **Política de Retención Fiscal:** Definir reglas de purgado/auto-borrado tras 5 años (plazo de prescripción legal en España según AEAT).

### 🔒 Disyuntiva 3: Privacidad y Cumplimiento GDPR

- En caso de utilizar la Vía B (IA / LLM en la nube), el PDF contiene datos personales (Nombre del titular, NIF, Dirección, IBAN parcialmente enmascarado).
- **Punto de Análisis:** Diseñar un middleware/filtro local de **Scrubbing de Privacidad** que limpie nombres, NIFs e IBANs del texto en bruto antes de enviar el prompt al LLM, conservando únicamente las líneas relevantes (CUPS, fecha, conceptos, importes).

### 📩 Disyuntiva 4: Mecanismo de Ingesta de Correo (IMAP Polling vs Inbound Webhook)

- **IMAP Polling:** Un worker en Python se conecta periódicamente vía `imaplib` / `aioimaplib` a un buzón (ej. `facturas@midominio.com`) y procesa correos unread.
  - *Pros:* No requiere IP pública expuesta ni servidor web abierto para recibir webhooks.
  - *Contras:* Polling periódico (cron / background task).
- **Inbound Email Webhook (ej. SendGrid, Mailgun, Postmark, Cloudflare Email Routing + Worker):**
  - *Pros:* Procesamiento en tiempo real (Event-Driven).
  - *Contras:* Requiere configurar dominio, DNS y endpoint público HTTPS con token de autenticación.

### 👤 Disyuntiva 5: Flujo UX de Validación Humana (Human-in-the-Loop)

- Ningún sistema de extracción es 100% infalible.
- **Punto de Análisis:** Todo gasto importado automáticamente debe nacer en estado `is_verified = False` (Gasto Pendiente). En la interfaz de usuario, se mostrará una tarjeta de alerta con el PDF incrustado o vista previa y los campos extraídos pre-cumplimentados para confirmación con 1-click.

---

## 6. Decisiones Consolidadas del Análisis de Disyuntivas

> Documento de análisis completo con todas las opciones evaluadas, comparativas y alternativas: [`analisis_disyuntivas.md`](file:///home/carlos/rental-handler/specs/epics/E-02-suministros/analisis_disyuntivas.md)

| # | Disyuntiva | Decisión |
|---|---|---|
| **1** | Regex vs. IA | **Híbrido con Fallback:** Regex local primero (por comercializadora conocida), IA (Gemini Flash free tier con `response_schema`) como motor universal de respaldo. Patrón Strategy + Fallback. |
| **2** | Almacenamiento de PDFs | **Diferido (`deferred`).** El pipeline extrae datos en memoria. El usuario conserva el PDF original en su correo/disco. Se implementará en el futuro (disco local fase 1, Cloudflare R2 fase 2). Política de retención: 5 años (prescripción AEAT). |
| **3** | GDPR / Privacidad | **Scrubbing obligatorio** antes de enviar texto a la Vía B (IA). Eliminar NIFs, nombres, direcciones, IBANs. Conservar solo CUPS, importes, fechas y conceptos. |
| **4** | Ingesta de correo | **Fase 1: Subida manual de PDF** desde la interfaz web (zero infraestructura). **Fase 2 (deferred):** IMAP polling a **carpeta dedicada** del correo del usuario. El usuario crea una regla en Gmail/Outlook para mover facturas de comercializadoras a una carpeta específica; el sistema solo escanea esa carpeta. Menor fricción que acceso al inbox completo y máxima privacidad. |
| **5** | Validación humana | **Estado `is_verified = False`** para gastos auto-importados. Panel de revisión con campos editables y confirmación 1-click. Los gastos no verificados no computan en borradores fiscales. |

---

## 7. Desglose de Features (Backlog de la Épica E-02)

### Features a implementar (primera iteración)

| ID | Título | Estado | Descripción |
|---|---|---|---|
| **F-16** | Modelo de Dominio de Suministros (CUPS en Property, `is_verified` y `receipt_path` en Expense, `UtilityInvoiceData` VO) | `backlog` | Extensiones al modelo de dominio existente: campos CUPS en Property, estado de verificación en Expense, y nuevo Value Object para datos extraídos de facturas. |
| **F-17** | Puerto y Adaptador Genérico de LLM (`LLMProviderPort` + `GeminiFlashAdapter`) | `backlog` | **Feature transversal (sin épica).** Puerto de dominio genérico para interacciones con LLMs, con adaptador de Gemini Flash (free tier, `response_schema`). Incluye rate limiting, retry logic y gestión de API key. Diseñado para ser reutilizable por cualquier feature futura (chat con límites, resúmenes, etc.). |
| **F-18** | Motor de Extracción de Datos: PyMuPDF + Strategy Pattern (Regex + LLM Fallback) + Privacy Scrubber | `backlog` | Núcleo del pipeline: extracción de texto con PyMuPDF, registro extensible de parsers por comercializadora (`UtilityExtractorRegistry` con soporte para Repsol, Endesa, Iberdrola, Naturgy, Aqualia, etc.), fallback automático a LLM (`LLMProviderPort` de F-17) para facturas de formato desconocido o fallos de Regex, scrubbing de datos personales, matching CUPS → Property, y suite de pruebas empíricas sobre el corpus de muestras PDF en `samples/`. |
/us| **F-20** | Interfaz UI: Subida Manual de PDF, Panel de Gastos Pendientes y Confirmación 1-click | `backlog` | Componente de subida de archivo PDF, vista de gastos pendientes de revisión con campos pre-cumplimentados editables, y acción de confirmar/rechazar. |

### Features diferidas (futuro)

| ID | Título | Estado | Notas |
|---|---|---|---|
| **F-19** | Almacenamiento Documental de Recibos PDF y Política de Retención 5 años | `deferred` | Disco local (fase 1) o Cloudflare R2 (fase 2). Se implementará cuando se valide la necesidad de conservar los PDFs en la plataforma. |
| **F-21** | Ingesta Automática por Email: IMAP Polling a Carpeta Dedicada | `deferred` | Conexión IMAP al correo del usuario, escaneando solo una carpeta específica donde el usuario redirige facturas de comercializadoras mediante reglas de correo. |

### Orden de implementación y dependencias

```
F-16 (Dominio) → F-17 (LLM Port genérico) → F-18 (Motor Extracción) → F-20 (UI)
                       │                              │
                       │                        usa LLMProviderPort
                       │                        como fallback
                       │
                  Reutilizable por
                  features futuras
                  (chat, resúmenes...)
                                                       │
                                                 ┌─────┴──────┐
                                                 │  DIFERIDOS  │
                                                 │  F-19 (PDFs)│
                                                 │  F-21 (IMAP)│
                                                 └─────────────┘
```

> [!NOTE]
> **F-17 no pertenece a la Épica E-02** — es una pieza de infraestructura transversal. Se implementa como parte de esta épica porque es su primer consumidor, pero el puerto `LLMProviderPort` y el adaptador `GeminiFlashAdapter` son genéricos y reutilizables por cualquier feature futura sin dependencia de E-02.

---

## 8. Próximos Pasos

1. ✅ Análisis de disyuntivas completado y decisiones consolidadas.
2. **→ Siguiente:** Redactar `specs/epics/E-02-suministros/F-16/design.md` — Especificación técnica del modelo de dominio.
3. Continuar con `specs/F-17/design.md` — Puerto genérico de LLM y adaptador de Gemini Flash (fuera de la épica, al ser transversal).
4. Continuar con `specs/epics/E-02-suministros/F-18/design.md` — Motor de extracción y sus estrategias.
5. Cerrar con `specs/epics/E-02-suministros/F-20/design.md` — UI de subida y panel de revisión.

