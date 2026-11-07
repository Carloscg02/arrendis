# Modulo: Extraccion Inteligente de Facturas (`invoice-ai-extraction`)

> Subsistema funcional vertical para la ingesta multimodal de facturas de suministros (luz, agua, gas), lectura OCR/LLM y conciliacion automatica.

---

## 1. Responsabilidad y Alcance de Negocio
- Ingesta de recibos y facturas en formato PDF/imagen mediante subida manual por lote o webhook de reenvio de correo entrante.
- Extraccion automatizada con IA/LLM: deteccion de emisor, CUPS/referencia de contador, fechas de consumo, importe base, IVA y total.
- Resolucion del inmueble receptor emparejando el codigo CUPS registrado con el catalogo de inmuebles.
- Creacion automatica del registro de gasto deducible (`Expense`) clasificado fiscalmente con enlace a la factura original.

---

## 2. Artefactos del Corte Vertical
- **Dominio**:
  - Enums y Modelos: `UtilityType`, `ExpenseSource`, `ExtractionConfidence`, `InboundInvoiceItemResult`, `InboundEmailProcessResult` (`backend/domain/entities.py`)
  - Excepciones: `UtilityExtractionError`, `EmptyPDFTextError`, `PDFExtractionError`, `PropertyNotFoundForCUPSError`, `DuplicateInvoiceError`
  - Puertos: `LLMProviderPort`, `InvoiceExtractorPort`, `PDFTextExtractorPort` (`backend/domain/ports.py`)
- **Aplicacion (Casos de Uso)**:
  - `CheckLLMHealthUseCase`, `ProcessUtilityInvoiceUseCase`, `ProcessBatchUtilityInvoicesUseCase`, `ProcessInboundEmailUseCase` (`backend/application/use_cases.py`)
- **Adaptadores de Infraestructura**:
  - LLM & Extraccion: `backend/adapters/extraction/` (Gemini, regex heuristico)
  - Parser de documentos: `PyMuPDFTextExtractorAdapter` (`backend/adapters/pdf_extractor_adapter.py`)
- **API & Endpoints**:
  - `backend/api/routes/llm.py` (`GET /api/llm/health`, `POST /api/llm/extract-invoice`, `POST /api/llm/batch-upload`)
  - `backend/api/routes/webhooks.py` (`POST /api/webhooks/inbound-email`)
- **Frontend**:
  - Componentes: `InvoiceUploadModal.tsx`, `CupsModal.tsx`, `GmailForwardingGuide.tsx`, `SuppliesAutomationPanel.tsx`
