# 📐 Refactor: Arquitectura Hexagonal Limpia y Desacoplamiento de IA — Design

> **Tipo de Tarea:** Refactor Estructural / Deuda Técnica  
> **Rama:** `feature/refactor-hexagonal-clean`  
> **Estado:** Listo para Aprobación (Revisión V2 tras Feedback del Arquitecto)  
> **Fecha:** 2026-10-04  
> **Objetivo:** Eliminar la contaminación tecnológica en el dominio (`backend/domain/extraction.py`), modularizar el adaptador de valoración (`backend/adapters/gemini_valuation_adapter.py`) en submódulos de responsabilidad única, y formalizar los puertos de negocio (`InvoiceExtractorPort` y `MarketValuationPort`) garantizando el 100% de compatibilidad hacia atrás en los 382 tests unitarios.

---

## 1. Motivación y Diagnóstico de Estado Actual

### 1.1 Síntomas detectados
1. **Contaminación del Dominio con Detalles Técnicos de Entrada:**
   `backend/domain/extraction.py` contiene expresiones regulares específicas de la maqueta de facturas en PDF de *Repsol Comercializadora de Electricidad y Gas, S.L.U.* (`RepsolExtractionStrategy`), esquemas JSON de Gemini y prompts de IA (`AIExtractionStrategy`). En Arquitectura Hexagonal y DDD, la estructura visual o el formato de un documento emitido por un tercero es un detalle de **infraestructura / adaptador de entrada**, nunca una regla intrínseca del dominio inmobiliario.
2. **Antipatrón *Fat Adapter* (Adaptador Monolítico):**
   `backend/adapters/gemini_valuation_adapter.py` ha crecido hasta **671 líneas**, acumulando responsabilidades dispares: llamadas al SDK de Gemini, resolución de redirecciones HTTP con `ThreadPoolExecutor`, reglas heurísticas de rutas y barrios de Idealista/Fotocasa, prompts de tasación extensos y mocks de test.
3. **Inconsistencia de Patrones para IA:**
   - La extracción de facturas utilizaba un puerto técnico genérico (`LLMProviderPort.generate(LLMRequest)`).
   - La valoración de mercado utilizaba un puerto de negocio semántico (`MarketValuationPort.estimate_valuation(...)`).
   Esta disparidad provoca confusión en el repositorio y dificulta el mantenimiento.

---

## 2. Principios de Arquitectura Hexagonal a Aplicar

1. **Pureza del Núcleo (Dominio):**
   - El dominio (`backend/domain/`) solo contiene Entidades, Value Objects, Servicios de Dominio puros (como `FiscalCalculator` y `ProfitCalculator`) y **Puertos** (interfaces abstractas que expresan necesidades de negocio).
   - El dominio desconoce por completo la existencia de Google Gemini, prompts, PyMuPDF, expresiones regulares de comerciales eléctricas o redirecciones web.
2. **Puertos Orientados al Negocio (Semantic Ports):**
   - Los puertos se definen en el lenguaje ubicuo del negocio inmobiliario:
     - `InvoiceExtractorPort`: *"Dada la información textual de un documento, extrae los datos estructurados del suministro y reporta la estrategia (`ExtractedInvoice`)"*.
     - `MarketValuationPort`: *"Dados los atributos físicos y ubicación de un inmueble, estima sus rangos de valor de venta y alquiler (`MarketValuationResult`)"*.
3. **Conservación de `LLMProviderPort` como Puerto Técnico Transversal:**
   - `LLMProviderPort` y `GeminiFlashAdapter` **permanecen** como la infraestructura transversal de IA para operaciones técnicas del sistema, como el chequeo de salud de conectividad (`CheckLLMHealthUseCase` y `/api/llm/health`).
4. **Casos de Uso Aislados y Limpios:**
   - Los casos de uso (`ProcessUtilityInvoiceUseCase`, `RequestPropertyValuationUseCase`) orquestan entidades y llaman a los puertos. No contienen prompts, ni parámetros de temperatura, ni lógica de reintentos de red.
   - `ProcessUtilityInvoiceUseCase` adopta un constructor estrictamente limpio (`pdf_extractor`, `invoice_extractor`, `property_repo`, `expense_repo`) sin arrastrar parámetros obsoletos (`registry`, `fallback_strategy`). Los ~12 tests existentes se actualizan de forma transparente.
   - `valuation_use_cases.py` se mantiene como un fichero independiente y cohesionado, evitando la masificación de `use_cases.py`.
5. **Adaptadores Especializados e Independientes (Infraestructura):**
   - Cada adaptador vive en su propio paquete modular (`backend/adapters/extraction/` y `backend/adapters/valuation/`).
   - Cero dependencias cruzadas entre la extracción de facturas y la valoración inmobiliaria.

---

## 3. Estructura de Ficheros Objetivo

```text
backend/
├── domain/
│   ├── entities.py                       # Entidades y Enums (Expense, Property, PropertyValuation, etc.)
│   ├── value_objects.py                  # Money, Address, UtilityInvoiceData, MarketValuationResult, etc.
│   ├── services.py                       # FiscalCalculator, ProfitCalculator (100% puro)
│   └── ports.py                          # CONTRATOS ABSTRACTOS:
│                                         #   - InvoiceExtractorPort (puerto semántico de extracción)
│                                         #   - MarketValuationPort (puerto semántico de valoración)
│                                         #   - LLMProviderPort (puerto técnico para salud/generación)
│
├── application/
│   ├── use_cases.py                      # ProcessUtilityInvoiceUseCase (usa InvoiceExtractorPort limpio)
│   └── valuation_use_cases.py            # RequestPropertyValuationUseCase (usa MarketValuationPort)
│
└── adapters/
    ├── extraction/                       # Subpaquete modular de extracción de facturas
    │   ├── __init__.py                   # Exporta CompositeInvoiceExtractor, RepsolInvoiceExtractor, GeminiInvoiceExtractor, GeminiFlashAdapter, etc.
    │   ├── base.py                       # Contrato base interno ExtractionStrategy y UtilityExtractorRegistry
    │   ├── repsol_regex_adapter.py       # Extractor Regex específico de Repsol
    │   ├── gemini_extractor_adapter.py   # Estrategia IA con prompt contable y sanitizado
    │   ├── gemini_adapter.py             # Implementación GeminiFlashAdapter(LLMProviderPort) con backoff exponencial
    │   ├── privacy_scrubber.py           # Sanitizador RGPD (DNI, IBAN, CIF)
    │   └── composite_registry.py         # Orquestador Composite que implementa InvoiceExtractorPort
    │
    └── valuation/                        # Subpaquete modular de estimación de mercado
        ├── __init__.py                   # Exporta GeminiMarketValuationAdapter, MockMarketValuationAdapter
        ├── adapter.py                    # Implementación limpia de MarketValuationPort (~140 líneas)
        ├── schemas.py                    # Schemas Pydantic internos (_RangePayload, _GeminiValuationPayload, etc.)
        ├── prompts.py                    # System instructions y plantillas de 2 fases
        ├── search_grounding.py           # Resolución concurrente de URLs de Google Search Grounding
        ├── url_sanitizer.py              # Normalización canónica de rutas Idealista / Fotocasa y ensamblado
        └── mock_adapter.py               # Mock desacoplado para tests unitarios
```

---

## 4. Diseño Técnico Detallado

### 4.1 Dominio: Definición de `InvoiceExtractorPort` y `ExtractedInvoice` en `backend/domain/ports.py`

Para preservar los metadatos de auditoría que requiere `ProcessUtilityInvoiceResult` (`strategy_used`) y garantizar un diagnóstico limpio de errores, definimos:

```python
@dataclass(frozen=True)
class ExtractedInvoice:
    """Resultado de la extracción de una factura conteniendo los datos y la estrategia empleada."""
    data: UtilityInvoiceData
    strategy_used: str  # Ej: "Repsol", "AI_Fallback"


class InvoiceExtractorPort(ABC):
    """Puerto de salida para la extracción de datos estructurados de facturas de suministros."""

    @abstractmethod
    def extract_invoice_data(self, document_text: str) -> ExtractedInvoice | None:
        """Extrae datos de la factura (CUPS, importe, fecha, comercializadora, tipo) y la estrategia utilizada.
        
        Args:
            document_text: Texto plano extraído del documento original.
            
        Returns:
            ExtractedInvoice con los datos identificados y el identificador de estrategia,
            o None si la extracción no pudo completarse.
            
        Raises:
            ExtractionFailedError: Si se desea comunicar diagnósticos específicos de fallo.
        """
        ...
```

### 4.2 Adaptadores de Extracción: `backend/adapters/extraction/`

1. **`privacy_scrubber.py`**:
   - Trasladado desde `domain/extraction.py`.
   - Contiene la lógica de anonimización RGPD (`PrivacyScrubber.scrub(raw_text)`).
2. **`base.py`**:
   - Define `ExtractionStrategy` y `UtilityExtractorRegistry` manteniendo la interfaz original para asegurar que los tests unitarios de estrategias específicas (`test_repsol_strategy.py`, `test_ai_extraction_strategy.py`, `test_utility_registry.py`) sigan funcionando idénticos.
3. **`repsol_regex_adapter.py`**:
   - `RepsolExtractionStrategy` (con alias `RepsolInvoiceExtractor`) que procesa maquetas de Repsol.
4. **`gemini_extractor_adapter.py`**:
   - `AIExtractionStrategy` (con alias `GeminiInvoiceExtractor`) que recibe opcionalmente `LLMProviderPort` o inicializa cliente, ejecutando `PrivacyScrubber.scrub` y llamada estructurada con el prompt contable.
5. **`composite_registry.py`**:
   - `CompositeInvoiceExtractor(InvoiceExtractorPort)`:
     - Mantiene `registry: UtilityExtractorRegistry` y `fallback_strategy: ExtractionStrategy | None`.
     - Implementa `extract_invoice_data(document_text) -> ExtractedInvoice | None`:
       - Intenta `registry.find_strategy(text)`. Si tiene éxito -> `ExtractedInvoice(data=..., strategy_used=strategy.provider_name)`.
       - Si no hay coincidencia o falla, comprueba si hay `fallback_strategy`. Si no hay fallback -> lanza `ExtractionFailedError("No se pudo extraer la factura con reglas Regex y no hay estrategia de IA configurada.")`.
       - Ejecuta `fallback_strategy.extract(text)`. Si tiene éxito -> `ExtractedInvoice(data=..., strategy_used=fallback_strategy.provider_name)`.
       - Si falla -> lanza `ExtractionFailedError("La extracción de la factura no pudo completarse ni por Regex ni por IA.")`.

### 4.3 Constructor Limpio en `ProcessUtilityInvoiceUseCase` y Actualización de Tests

En lugar de arrastrar parámetros obsoletos en código de producción, el constructor de `ProcessUtilityInvoiceUseCase` adopta su forma canónica y limpia:

```python
class ProcessUtilityInvoiceUseCase:
    def __init__(
        self,
        pdf_extractor: PDFTextExtractorPort,
        invoice_extractor: InvoiceExtractorPort,
        property_repo: PropertyRepository,
        expense_repo: ExpenseRepository,
    ) -> None:
        self._pdf_extractor = pdf_extractor
        self._invoice_extractor = invoice_extractor
        self._property_repo = property_repo
        self._expense_repo = expense_repo

    def execute(self, pdf_bytes: bytes, user_id: str) -> ProcessUtilityInvoiceResult:
        raw_text = self._pdf_extractor.extract_text(pdf_bytes)
        
        extracted = self._invoice_extractor.extract_invoice_data(raw_text)
        if extracted is None:
            raise ExtractionFailedError("La extracción de la factura no pudo completarse.")
            
        invoice_data = extracted.data
        strategy_used = extracted.strategy_used

        # Continuación de validación de duplicados y matching de propiedad...
```

Los ~12 puntos de instanciación en los tests (`test_process_utility_invoice_use_case.py`, `test_f21_inbound_email_use_case.py` y `test_process_utility_invoice_sqlite.py`) se actualizan directamente para inyectar `invoice_extractor = CompositeInvoiceExtractor(...)` o `mock_invoice_extractor`. De esta manera, el código de producción permanece 100% puro y libre de parches de retrocompatibilidad.

### 4.4 Inyección de Dependencias en `backend/api/dependencies.py`

Se define explícitamente el proveedor de FastAPI:

```python
def get_invoice_extractor(
    llm_provider: LLMProviderPort | None = Depends(get_llm_provider),
) -> InvoiceExtractorPort:
    from backend.adapters.extraction import (
        CompositeInvoiceExtractor,
        UtilityExtractorRegistry,
        RepsolExtractionStrategy,
        AIExtractionStrategy,
    )
    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    fallback = AIExtractionStrategy(llm_provider) if llm_provider else None
    return CompositeInvoiceExtractor(registry=registry, fallback_strategy=fallback)


def get_process_utility_invoice_use_case(
    pdf_extractor: PDFTextExtractorPort = Depends(get_pdf_extractor),
    invoice_extractor: InvoiceExtractorPort = Depends(get_invoice_extractor),
    property_repo: PropertyRepository = Depends(get_property_repo),
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
) -> ProcessUtilityInvoiceUseCase:
    return ProcessUtilityInvoiceUseCase(
        pdf_extractor=pdf_extractor,
        invoice_extractor=invoice_extractor,
        property_repo=property_repo,
        expense_repo=expense_repo,
    )
```

### 4.5 Adaptadores de Valoración: `backend/adapters/valuation/`

Descomposición limpia del fichero monolítico de 671 líneas en submódulos con SRP:

1. **`schemas.py`**:
   - `_RangePayload`, `_FactorPayload`, `_SourcePayload`, `_GeminiValuationPayload`.
2. **`prompts.py`**:
   - `VALUATION_SYSTEM_INSTRUCTION`: Instrucciones de sistema con criterios de micro-localización.
   - `build_search_prompt(...)`: Prompt de la Fase 1 para Google Search Grounding.
   - `build_direct_prompt(...)`: Prompt de contingencia directa.
   - `build_grounded_calculation_prompt(...)`: Prompt de la Fase 2 fundamentado en evidencia real.
3. **`search_grounding.py`**:
   - `resolve_real_url(url, timeout)`: Desenlace de URLs de redirección.
   - `resolve_grounding_urls(chunks)`: Concurrencia con `ThreadPoolExecutor`.
4. **`url_sanitizer.py`**:
   - `sanitize_property_url(url)`: Reglas regex para Idealista/Fotocasa (evita 404s en calles anidadas y ajusta micro-barrios).
   - `format_source_title(raw_title, url)`: Títulos legibles.
   - `assemble_sources(payload_sources, resolved_grounding)`: Deduplicación y emparejamiento.
5. **`adapter.py`**:
   - `GeminiMarketValuationAdapter(MarketValuationPort)`: Orquestación pura de ~120 líneas que conecta las fases y gestiona retries/backoff ante 429.
6. **`mock_adapter.py`**:
   - `MockMarketValuationAdapter(MarketValuationPort)` para entornos de test unitario.

### 4.6 Fachadas de Compatibilidad y Mocks en Tests

1. **Fachada `backend/adapters/gemini_valuation_adapter.py`**:
   Reexporta los símbolos para no romper tests ni código que importe desde la ruta antigua:
   ```python
   from google import genai  # Necesario para tests con @patch("backend.adapters.gemini_valuation_adapter.genai.Client")
   from backend.adapters.valuation import (
       GeminiMarketValuationAdapter,
       MockMarketValuationAdapter,
   )
   from backend.adapters.valuation.url_sanitizer import (
       sanitize_property_url as _sanitize_property_url,
       format_source_title as _format_source_title,
       assemble_sources as _assemble_sources,
   )
   from backend.adapters.valuation.schemas import (
       _SourcePayload,
       _GeminiValuationPayload,
   )
   ```
2. **Fachada `backend/domain/extraction.py`**:
   Reexporta `PrivacyScrubber`, `ExtractionStrategy`, `RepsolExtractionStrategy`, `AIExtractionStrategy`, `UtilityExtractorRegistry` desde `backend/adapters/extraction/`.
3. **Actualización de tests de valoración**:
   Se asegura que [`tests/unit/backend/adapters/test_gemini_valuation_adapter.py`](file:///home/carlos/rental-handler/tests/unit/backend/adapters/test_gemini_valuation_adapter.py) continúe pasando al 100%, tanto si apunta a la fachada como al nuevo submódulo.

---

## 5. Estrategia de Migración y Verificación

### 5.1 Fases de Implementación
1. **Fase 1: Creación de submódulos de valoración (`adapters/valuation/`)**:
   Extraer schemas, prompts, search_grounding, url_sanitizer, mock_adapter y adapter. Crear fachada de re-export en `gemini_valuation_adapter.py`. Ejecutar `pytest tests/unit/backend/adapters/test_gemini_valuation_adapter.py`.
2. **Fase 2: Creación de submódulos de extracción (`adapters/extraction/`)**:
   Mover `PrivacyScrubber`, `RepsolExtractionStrategy`, `AIExtractionStrategy`, `UtilityExtractorRegistry` y crear `CompositeInvoiceExtractor(InvoiceExtractorPort)`.
3. **Fase 3: Contratos en `domain/ports.py` y compatibilidad en `use_cases.py`**:
   Añadir `InvoiceExtractorPort` y `ExtractedInvoice`. Añadir soporte dual en `ProcessUtilityInvoiceUseCase`.
4. **Fase 4: Inyección en `dependencies.py` y verificación general**:
   Cablear `get_invoice_extractor` en FastAPI.
5. **Fase 5: Ejecución integral de la suite**:
   Ejecutar los **382 tests unitarios**. Ningún test debe fallar.

---

## 6. Rincón del Estudiante 🎓

### ¿Por qué mover `extraction.py` fuera de `domain/` no es solo cuestión de estética?
En la arquitectura hexagonal, el núcleo de dominio representa el conocimiento perpetuo del negocio. Si dentro de `domain/` tenemos una expresión regular que busca `r"Total factura\s*\n\s*([\d.,]+)\s*€"`, estamos acoplando el corazón de nuestra aplicación a la decisión de diseño de un diseñador gráfico de Repsol en 2024. Cuando Repsol cambie la tipografía o el orden de los campos en su factura, el dominio no debería cambiar, porque las reglas de alquiler de Arrendis siguen siendo exactamente las mismas. Mover el parser a un adaptador mantiene el dominio inmutable frente a cambios de maquetación externos.

### ¿Por qué `ExtractedInvoice` es un Value Object de Dominio y no un DTO de Infraestructura?
Porque el hecho de saber *qué mecanismo validó y extrajo los datos de un gasto* forma parte de la trazabilidad y auditoría contable de la plataforma. El dominio necesita registrar si el gasto fue inferido por una regla determinista de alta confianza (Regex) o por una estimación probabilística (IA), para gobernar las políticas de verificación y revisión humana.
