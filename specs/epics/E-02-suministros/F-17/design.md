# 📐 Especificación Técnica — F-17: Puerto y Adaptador Genérico de LLM

> **Feature:** F-17  
> **Título:** Puerto y Adaptador Genérico de LLM (`LLMProviderPort` + `GeminiFlashAdapter`)  
> **Épica:** Transversal (sin épica; primer consumidor: E-02)  
> **Estado:** Paso 1 — Especificación Técnica  
> **Fecha:** 2026-08-16  
> **Dependencias:** Ninguna (feature de infraestructura transversal)

---

## 1. Contexto y Objetivo

Esta feature introduce la **pieza de infraestructura genérica** que permite a cualquier caso de uso del sistema interactuar con un modelo de lenguaje grande (LLM) sin acoplarse a un proveedor específico.

### ¿Por qué ahora?

- **F-18** (Motor de Extracción de Datos) necesita un LLM como estrategia de fallback para extraer datos de facturas PDF cuando las reglas Regex fallan.
- El diseño debe ser **reutilizable**: futuras features (chat asistido, resúmenes, clasificación inteligente) podrán consumir el mismo puerto sin modificar el dominio.
- Siguiendo la Arquitectura Hexagonal, el dominio define **QUÉ** necesita (un puerto abstracto), y el adaptador concreto implementa **CÓMO** se comunica con Gemini Flash.

### ¿Qué NO es esta feature?

- No implementa la extracción de facturas (eso es F-18).
- No implementa la UI de suministros (eso es F-20).
- No almacena prompts ni historial de conversaciones.

---

## 2. Lenguaje Ubicuo (Términos Nuevos)

| Término | Definición |
|---|---|
| **LLMProviderPort** | Puerto de salida del dominio que define el contrato genérico para interactuar con cualquier LLM. Define operaciones de generación de texto y extracción estructurada. |
| **GeminiFlashAdapter** | Adaptador concreto que implementa `LLMProviderPort` usando el SDK `google-genai` con el modelo `gemini-2.0-flash`. |
| **Structured Extraction** | Capacidad de solicitar al LLM una respuesta en formato JSON que se ajuste a un esquema predefinido (`response_schema`), garantizando datos parseables automáticamente. |
| **LLMResponse** | Value Object inmutable que encapsula la respuesta del LLM: contenido textual, datos estructurados parseados (si los hubo), tokens consumidos y metadatos del modelo. |
| **LLMRequest** | Value Object inmutable que encapsula una petición al LLM: prompt del sistema, prompt del usuario, esquema de respuesta esperado (opcional) y parámetros de generación. |
| **RateLimitError** | Excepción de dominio que se lanza cuando el proveedor de LLM rechaza la petición por exceso de cuota (HTTP 429). |
| **LLMProviderError** | Excepción de dominio genérica para errores no recuperables del proveedor (API key inválida, modelo no disponible, errores 5xx tras reintentos). |

---

## 3. Modelo de Dominio

### 3.1 Value Objects Nuevos

#### `LLMRequest` (Inmutable)

```python
@dataclass(frozen=True)
class LLMRequest:
    """Petición genérica al LLM — independiente de proveedor."""
    user_prompt: str                          # Prompt principal del usuario
    system_prompt: str | None = None          # Instrucciones de sistema (opcional)
    response_schema: dict | None = None       # JSON Schema esperado (para extracción estructurada)
    temperature: float = 0.0                  # 0.0 = determinista (ideal para extracción)
    max_output_tokens: int = 2048             # Límite de tokens de salida

    def __post_init__(self):
        if not self.user_prompt or not self.user_prompt.strip():
            raise ValueError("user_prompt cannot be empty")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_output_tokens < 1:
            raise ValueError(f"max_output_tokens must be positive, got {self.max_output_tokens}")
```

#### `LLMResponse` (Inmutable)

```python
@dataclass(frozen=True)
class LLMResponse:
    """Respuesta genérica del LLM — independiente de proveedor."""
    text: str                                 # Texto crudo de la respuesta
    parsed_data: dict | None = None           # Datos estructurados parseados (si se pidió schema)
    model_name: str = ""                      # Nombre del modelo que respondió
    input_tokens: int = 0                     # Tokens de entrada consumidos
    output_tokens: int = 0                    # Tokens de salida consumidos

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
```

### 3.2 Excepciones de Dominio Nuevas

```python
class LLMProviderError(Exception):
    """Error genérico no recuperable del proveedor de LLM."""
    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")

class RateLimitError(LLMProviderError):
    """El proveedor rechazó la petición por exceso de cuota (429)."""
    def __init__(self, provider: str = "unknown", retry_after_seconds: int | None = None):
        self.retry_after_seconds = retry_after_seconds
        msg = "Rate limit exceeded"
        if retry_after_seconds:
            msg += f" (retry after {retry_after_seconds}s)"
        super().__init__(msg, provider)
```

> **Decisión de diseño**: Las excepciones viven en `domain/` porque el puerto las declara como parte de su contrato. El dominio necesita saber *qué* puede fallar, aunque no sepa *cómo* se conecta al proveedor.

### 3.3 Puerto Nuevo: `LLMProviderPort`

```python
class LLMProviderPort(ABC):
    """Puerto de salida genérico para interacciones con LLMs.
    
    Contrato que cualquier adaptador de LLM debe cumplir.
    El dominio usa este puerto sin saber si detrás hay Gemini, OpenAI, Anthropic, o un mock.
    """

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Genera una respuesta a partir de un LLMRequest.
        
        - Si request.response_schema está definido, el adaptador debe solicitar
          salida estructurada (JSON) y poblar LLMResponse.parsed_data.
        - Debe implementar retry con exponential backoff para errores transitorios (429, 5xx).
        
        Raises:
            RateLimitError: Si el proveedor rechaza por cuota tras agotar reintentos.
            LLMProviderError: Para errores no recuperables.
        """
        ...
```

> **Decisión de diseño**: Un solo método `generate()` cubre tanto texto libre como extracción estructurada, diferenciándose por la presencia o ausencia de `response_schema` en el `LLMRequest`. Esto mantiene el puerto mínimo y cohesivo, evitando la proliferación de métodos que sería necesaria si separáramos `generate_text()` y `extract_structured()`.

---

## 4. Adaptador: `GeminiFlashAdapter`

### 4.1 Ubicación

```
backend/adapters/gemini_adapter.py
```

### 4.2 Dependencia Externa

```
google-genai >= 1.0.0
```

Se añade al entorno virtual del proyecto (`venv/`). **No es una dependencia del dominio** — solo del adaptador.

### 4.3 Diseño del Adaptador

```python
class GeminiFlashAdapter(LLMProviderPort):
    """Adaptador que implementa LLMProviderPort usando Google Gemini Flash."""

    MODEL_NAME = "gemini-2.0-flash"
    PROVIDER_NAME = "gemini"
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1.0
    MAX_BACKOFF_SECONDS = 30.0

    def __init__(self, api_key: str):
        """Inicializa el cliente de Gemini.
        
        Args:
            api_key: API key de Google AI Studio (no Vertex AI).
            
        Raises:
            LLMProviderError: Si la API key está vacía o el cliente no se puede crear.
        """
        ...

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Implementa la generación usando google-genai SDK.
        
        Comportamiento interno:
        1. Construye el config con temperature, max_output_tokens.
        2. Si request.response_schema está presente:
           - Configura response_mime_type='application/json'
           - Pasa el schema al config.
        3. Llama a client.models.generate_content() con retry.
        4. Extrae texto, parsed_data (si aplica), y métricas de uso.
        5. Retorna LLMResponse.
        """
        ...
```

### 4.4 Estrategia de Retry y Rate Limiting

El adaptador implementa **exponential backoff con jitter** internamente:

```
Intento 1: Llamada directa
Intento 2 (si 429/5xx): Espera 1s ± jitter → Reintento
Intento 3 (si 429/5xx): Espera 2s ± jitter → Reintento
Intento 4 (si 429/5xx): Espera 4s ± jitter → Reintento (máximo)
Si falla tras MAX_RETRIES: Lanza RateLimitError (429) o LLMProviderError (5xx)
```

Implementado con `time.sleep()` y `random.uniform()` de la stdlib de Python. **No** se introduce la dependencia `tenacity` para mantener el stack mínimo, consistente con la filosofía del proyecto.

### 4.5 Gestión de la API Key

- La API key se lee desde la variable de entorno `GEMINI_API_KEY`.
- El adaptador **no** la busca en archivos `.env` — eso es responsabilidad del script de arranque o del usuario.
- El API router de FastAPI inyecta la key al crear el adaptador en `main.py`.

### 4.6 Diagrama de Secuencia

```
 Caso de Uso           LLMProviderPort           GeminiFlashAdapter         Google API
     │                       │                          │                       │
     │  generate(request)    │                          │                       │
     │──────────────────────▶│                          │                       │
     │                       │   generate(request)      │                       │
     │                       │─────────────────────────▶│                       │
     │                       │                          │  generate_content()   │
     │                       │                          │──────────────────────▶│
     │                       │                          │                       │
     │                       │                          │◀──────────────────────│
     │                       │                          │  (retry si 429/5xx)   │
     │                       │   LLMResponse            │                       │
     │                       │◀─────────────────────────│                       │
     │  LLMResponse          │                          │                       │
     │◀──────────────────────│                          │                       │
```

---

## 5. Integración con la Capa de API (FastAPI)

### 5.1 Wiring en `main.py`

El adaptador se crea condicionalmente: si la variable de entorno `GEMINI_API_KEY` existe, se instancia el `GeminiFlashAdapter`; si no, se usa `None` y las features que dependan de LLM devuelven un error claro.

```python
# En main.py lifespan / startup
import os
gemini_api_key = os.environ.get("GEMINI_API_KEY")
llm_provider = GeminiFlashAdapter(api_key=gemini_api_key) if gemini_api_key else None
```

> **Decisión**: No se crea un endpoint REST para el LLM directamente. El `LLMProviderPort` es un servicio de infraestructura interno inyectado en los casos de uso que lo necesiten (F-18, y futuros). Esta feature **no expone endpoints nuevos**.

### 5.2 Endpoint de Health Check (Opcional)

Se añade un endpoint simple para verificar que la conexión con el LLM funciona:

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/llm/health` | Retorna `{"status": "ok", "model": "gemini-2.0-flash"}` si el adaptador está configurado, o `{"status": "not_configured"}` si no hay API key. Protegido por autenticación JWT. |

### 5.3 Schema de Respuesta

```python
class LLMHealthResponse(BaseModel):
    status: str           # "ok" | "not_configured" | "error"
    model: str | None     # Nombre del modelo si está configurado
    message: str | None   # Mensaje descriptivo si hay error
```

---

## 6. Casos de Uso

Esta feature **no introduce casos de uso propios**. El `LLMProviderPort` es un servicio de infraestructura que será inyectado como dependencia en los casos de uso de **F-18** (`ProcessUtilityInvoiceUseCase`) y futuras features.

Sin embargo, se creará un caso de uso minimal para el health check:

```python
class CheckLLMHealthUseCase:
    """Verifica la disponibilidad del proveedor de LLM."""
    
    def __init__(self, llm_provider: LLMProviderPort | None):
        self._llm = llm_provider
    
    def execute(self) -> dict:
        if self._llm is None:
            return {"status": "not_configured", "model": None}
        # Intenta una generación trivial para verificar conectividad
        try:
            response = self._llm.generate(LLMRequest(user_prompt="ping"))
            return {"status": "ok", "model": response.model_name}
        except LLMProviderError as e:
            return {"status": "error", "model": None, "message": str(e)}
```

---

## 7. Plan de Archivos

### Archivos a crear

| Archivo | Descripción |
|---|---|
| `backend/adapters/gemini_adapter.py` | Adaptador `GeminiFlashAdapter` que implementa `LLMProviderPort` |
| `backend/api/routes/llm.py` | Router FastAPI con endpoint de health check |
| `tests/unit/test_llm_value_objects.py` | Tests unitarios de `LLMRequest` y `LLMResponse` |
| `tests/unit/test_llm_health_use_case.py` | Tests unitarios del `CheckLLMHealthUseCase` con mock del puerto |
| `tests/integration/test_llm_api.py` | Tests de integración del endpoint `/api/llm/health` |

### Archivos a modificar

| Archivo | Cambio |
|---|---|
| `backend/domain/value_objects.py` | Añadir `LLMRequest` y `LLMResponse` |
| `backend/domain/ports.py` | Añadir `LLMProviderPort` |
| `backend/domain/entities.py` | Añadir excepciones `LLMProviderError` y `RateLimitError` (o nuevo archivo `domain/exceptions.py`) |
| `backend/application/use_cases.py` | Añadir `CheckLLMHealthUseCase` |
| `backend/api/main.py` | Instanciar `GeminiFlashAdapter`, registrar router de LLM |
| `backend/api/schemas.py` | Añadir `LLMHealthResponse` |

---

## 8. Especificación de Tests

### 8.1 Tests Unitarios

| ID | Test | Qué verifica |
|---|---|---|
| `T-17-01` | `test_llm_request_valid_creation` | `LLMRequest` se crea correctamente con todos los campos |
| `T-17-02` | `test_llm_request_empty_prompt_raises` | `LLMRequest` con `user_prompt` vacío lanza `ValueError` |
| `T-17-03` | `test_llm_request_invalid_temperature_raises` | `LLMRequest` con `temperature` fuera de rango [0.0, 2.0] lanza `ValueError` |
| `T-17-04` | `test_llm_request_invalid_max_tokens_raises` | `LLMRequest` con `max_output_tokens < 1` lanza `ValueError` |
| `T-17-05` | `test_llm_request_defaults` | `LLMRequest` con solo `user_prompt` tiene los defaults correctos |
| `T-17-06` | `test_llm_request_is_immutable` | `LLMRequest` es `frozen=True` (no se puede modificar tras crear) |
| `T-17-07` | `test_llm_response_valid_creation` | `LLMResponse` se crea con texto y datos parseados |
| `T-17-08` | `test_llm_response_total_tokens` | `LLMResponse.total_tokens` suma correctamente input + output |
| `T-17-09` | `test_llm_response_defaults` | `LLMResponse` con solo `text` tiene los defaults correctos |
| `T-17-10` | `test_llm_provider_error_format` | `LLMProviderError` incluye el nombre del proveedor en el mensaje |
| `T-17-11` | `test_rate_limit_error_with_retry_after` | `RateLimitError` almacena y formatea `retry_after_seconds` |
| `T-17-12` | `test_rate_limit_error_is_llm_provider_error` | `RateLimitError` hereda de `LLMProviderError` |
| `T-17-13` | `test_check_llm_health_not_configured` | Use case retorna `{"status": "not_configured"}` si `llm_provider is None` |
| `T-17-14` | `test_check_llm_health_ok` | Use case retorna `{"status": "ok"}` con mock que responde exitosamente |
| `T-17-15` | `test_check_llm_health_error` | Use case retorna `{"status": "error"}` si mock lanza `LLMProviderError` |

### 8.2 Tests de Integración

| ID | Test | Qué verifica |
|---|---|---|
| `T-17-16` | `test_llm_health_endpoint_not_configured` | `GET /api/llm/health` retorna 200 con `status: not_configured` cuando no hay API key |
| `T-17-17` | `test_llm_health_endpoint_ok_with_mock` | `GET /api/llm/health` retorna 200 con `status: ok` cuando se inyecta un mock funcional |
| `T-17-18` | `test_llm_health_endpoint_requires_auth` | `GET /api/llm/health` retorna 401 sin token JWT |

### 8.3 Tests del Adaptador (con mock de red)

| ID | Test | Qué verifica |
|---|---|---|
| `T-17-19` | `test_gemini_adapter_generate_text` | El adaptador construye correctamente la llamada y retorna `LLMResponse` con texto |
| `T-17-20` | `test_gemini_adapter_generate_structured` | Con `response_schema`, el adaptador configura `response_mime_type` y parsea JSON |
| `T-17-21` | `test_gemini_adapter_retry_on_429` | Ante error 429, el adaptador reintenta con backoff y eventualmente devuelve respuesta |
| `T-17-22` | `test_gemini_adapter_max_retries_exceeded` | Tras `MAX_RETRIES` de 429, lanza `RateLimitError` |
| `T-17-23` | `test_gemini_adapter_non_retryable_error` | Ante error 400/401, lanza `LLMProviderError` sin reintentar |
| `T-17-24` | `test_gemini_adapter_empty_api_key_raises` | Constructor con API key vacía lanza `LLMProviderError` |

---

## 9. Reglas de Arquitectura

- ✅ `LLMRequest`, `LLMResponse`, `LLMProviderPort`, `LLMProviderError`, `RateLimitError` → viven en `backend/domain/` (cero dependencias externas).
- ✅ `GeminiFlashAdapter` → vive en `backend/adapters/` (única pieza que importa `google-genai`).
- ✅ La dependencia `google-genai` **NUNCA** aparece en imports de `domain/` ni `application/`.
- ✅ Los tests unitarios del dominio no necesitan la librería `google-genai` instalada.
- ✅ El adaptador es **intercambiable**: para usar OpenAI, Anthropic, o un LLM local, basta con crear otro adaptador que implemente `LLMProviderPort`.

---

## 10. 📚 El Rincón del Estudiante

### 🔌 ¿Qué es un "Puerto Genérico de Infraestructura"?

Hasta ahora, todos nuestros puertos eran **repositorios** — contratos para guardar y recuperar entidades. `PropertyRepository`, `IncomeRepository`, etc. Todos siguen el patrón CRUD y están íntimamente ligados a una entidad de dominio.

`LLMProviderPort` es diferente: es un **puerto de servicio de infraestructura**. No persiste entidades, sino que expone una capacidad técnica (hablar con un modelo de IA) al dominio de una forma abstracta.

#### Analogía: El Enchufe Universal de Viaje

Imagina que viajas por el mundo con tu móvil. Cada país tiene enchufes distintos (UK, EU, US, Australia), pero tu cargador siempre necesita lo mismo: **corriente eléctrica**. Un adaptador universal de viaje te permite enchufar en cualquier toma de corriente del mundo sin cambiar tu cargador.

```
Tu App (dominio)          LLMProviderPort              Adaptadores
    │                    (enchufe universal)              │
    │── "Necesito que     ┌──────────────┐    ┌──────────┤
    │    analices este  ──▶│ generate()   │───▶│ Gemini   │ (hoy)
    │    texto"           │              │    │ Flash    │
    │                     └──────────────┘    ├──────────┤
    │                                         │ OpenAI   │ (futuro)
    │                                         │ GPT-4    │
    │                                         ├──────────┤
    │                                         │ Ollama   │ (futuro)
    │                                         │ Local    │ (privacidad total)
    │                                         └──────────┘
```

Tu dominio dice `generate(request)` y **no le importa** si detrás hay Gemini, GPT-4, o un modelo local en tu portátil. Eso es el poder de la Arquitectura Hexagonal aplicada a servicios de IA.

### 🧊 ¿Por qué Value Objects para Request/Response?

En features anteriores aprendimos que los Value Objects son **inmutables** y se definen por su contenido, no por una identidad. ¿Por qué usarlos para peticiones y respuestas del LLM?

| Sin VOs (datos sueltos) | Con VOs (`LLMRequest` / `LLMResponse`) |
|---|---|
| `generate(prompt, temp, max_tokens, schema)` — 4 parámetros sueltos que pueden pasarse en orden incorrecto | `generate(request)` — un solo objeto tipado que se valida al construirse |
| El caller puede pasar `temperature=-5` y el error aparece en la API de Gemini | El VO valida en `__post_init__` y falla inmediatamente con un mensaje claro |
| Cada adaptador interpreta los parámetros a su manera | El contrato está centralizado en el VO del dominio |

```python
# ❌ Sin Value Objects — propenso a errores silenciosos
def generate(prompt: str, system: str, temp: float, max_tokens: int, schema: dict):
    ...  # ¿Qué pasa si intercambias prompt y system? Python no se queja.

# ✅ Con Value Objects — seguro y auto-documentado
def generate(request: LLMRequest) -> LLMResponse:
    ...  # El VO valida todo al construirse. Imposible pasar datos inválidos.
```

### 🔄 Exponential Backoff: ¿Qué es y por qué es crucial?

Cuando llamas a una API externa (como Gemini), el servidor puede estar saturado y responderte con un error 429 ("Too Many Requests"). Si reintentaras inmediatamente, solo empeorarías la congestión.

**Exponential backoff** es una estrategia donde cada reintento espera **el doble** que el anterior:

```
Intento 1: Falla (429) → Espera 1 segundo
Intento 2: Falla (429) → Espera 2 segundos  
Intento 3: Falla (429) → Espera 4 segundos
Intento 4: Éxito ✅
```

**El jitter** (ruido aleatorio) añade variación para que si 100 usuarios reciben un 429 al mismo tiempo, no todos reintenten exactamente en el mismo segundo:

```
Usuario A: Espera 1.0 + 0.3 = 1.3 segundos
Usuario B: Espera 1.0 + 0.7 = 1.7 segundos
Usuario C: Espera 1.0 + 0.1 = 1.1 segundos
→ Los reintentos se distribuyen en el tiempo, dando respiro al servidor.
```

#### Analogía: La Cola del Supermercado

Si llegas al supermercado y todas las cajas están llenas, no te quedas pegado a la caja esperando tu turno cada nanosegundo. Te alejas, haces una vuelta por los pasillos (espera exponencial), y cada vez que vuelves a mirar, esperas un poco más antes de la siguiente ronda. Si todo el mundo hiciera la vuelta al mismo tiempo, seguirían chocando — por eso añades un "jitter": uno mira los cereales, otro va al baño, otro revisa su lista. Se descongestiona naturalmente.

### 📊 Tabla Resumen: Repository Port vs. Service Port

| Aspecto | Repository Port (ej. `PropertyRepository`) | Service Port (ej. `LLMProviderPort`) |
|---|---|---|
| **Propósito** | Persistir y recuperar entidades de dominio | Exponer una capacidad técnica al dominio |
| **Métodos típicos** | `save()`, `find_by_id()`, `list()`, `delete()` | `generate()`, `send()`, `validate()` |
| **Estado** | Gestiona estado (BD) | Sin estado (cada llamada es independiente) |
| **Naming convention** | `*Repository` | `*Port` |
| **Adaptador nombrado** | `SQLite*Repository` | `Gemini*Adapter`, `Bcrypt*Adapter` |
| **Ejemplo en proyecto** | `SQLitePropertyRepository` implementa `PropertyRepository` | `GeminiFlashAdapter` implementa `LLMProviderPort` |
