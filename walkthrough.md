# Walkthrough y Resumen - Feature F-07

## Resumen del Trabajo Realizado

En esta feature (F-07: Frontend Route Protection and Auth Header) se completó la infraestructura de seguridad iniciada en la característica F-06, implementando guardias de navegación y un encabezado de aplicación (AppHeader) en el frontend. El backend se ha mantenido intacto, de acuerdo a la filosofía de Arquitectura Hexagonal y a las restricciones de la arquitectura definida, y los tests verifican que no haya dependencias cruzadas y mantengan un 100% de efectividad.

### Componentes de React Creados
- **`ProtectedRoute`**: Un componente envoltorio (wrapper) que requiere que el usuario esté autenticado (`isAuthenticated`). Si no lo está, intercepta el acceso a rutas privadas y lo redirige automáticamente a `/login` mediante `<Navigate>`. Se añadió un `Loading Screen` temporal que resuelve los tiempos de espera al restaurar sesiones.
- **`PublicOnlyRoute`**: Similar al componente anterior, intercepta rutas públicas como el registro y el inicio de sesión. Si el usuario ya está autenticado y posee tokens activos, se le redirige al inicio (`/`).
- **`AppHeader`**: Un menú y panel de navegación premium adherido a las rutas privadas. Aprovechando una estética **Glassmorphism**, permite la visualización del usuario actual y da una vía segura, visual y elegante para el cierre de sesión interactuando directamente con `useAuth()`.

### Servicios y Red de Aplicación
- Se introdujo un bloqueador silencioso que detecta errores en `frontend/src/services/api.ts` (específicamente, un interceptor que examina si una petición responde con el estado `401 Unauthorized`).
- Ante la ocurrencia de la intercepción, el servicio gestiona el uso del `Refresh Token` para recuperar sesión (`authService.refresh()`), reenviando la petición nativa y solucionando los cortes abruptos de sesión para el usuario final.
- Se añadió un control de `clearSession()` en `frontend/src/services/auth.ts` que permite vaciar manualmente las credenciales y desviar al inicio si la re-verificación falla del todo.

### Estilos y Mejoras Visuales
- Se creó en `index.css` el componente de Glassmorphism para `.app-header` y su equivalente para el botón `.app-header__logout-btn`.
- Se corrigieron detalles en los espaciadores de la aplicación como `.page-container` y en los `Loaders`.

## Verificación Final
La pipeline de compilación para producción del Frontend se ha completado sin ningún problema usando TypeScript en 473ms. Adicionalmente, el entorno del Backend (gestionado por FastAPI) pasó los 94 casos del suite de pruebas automatizadas (`pytest`) en 3.46 segundos. El entorno carece de importaciones externas en `backend/domain/`.

---

# Walkthrough y Resumen - Feature F-08

## Resumen del Trabajo Realizado (Multi-tenancy)

En la feature F-08 hemos sentado las bases para la Épica de Fiscalidad aislando los datos por usuario (Multi-tenancy por filas). Ahora, cada propiedad pertenece exclusivamente al usuario que la creó.

### Cambios en Dominio y Casos de Uso
- **`Property`**: Se añadió el campo obligatorio `user_id`.
- **Casos de Uso**: Se actualizaron `ListPropertiesUseCase`, `GetPropertyUseCase`, `RecordIncomeUseCase` y `RecordExpenseUseCase` para exigir el `user_id` del solicitante y bloquear cualquier acceso a propiedades ajenas, previniendo así filtraciones de información.

### Persistencia y API
- **SQLite**: Se migró la tabla `properties` para incluir la columna `user_id` de forma nativa.
- **FastAPI**: Todos los endpoints del catálogo y contabilidad se protegieron con inyección de dependencias JWT (`get_current_user`).

## Verificación Final
La suite de integración asegura que si el Usuario A intenta registrar un gasto en la propiedad del Usuario B, la API responde con un seguro `404 Not Found`, garantizando privacidad total. Los 98 tests backend pasan exitosamente.

---

# Walkthrough y Resumen - Feature F-09

## Resumen del Trabajo Realizado (Datos Fiscales de Propiedad)

En la feature F-09 hemos implementado la primera base de la Épica de Fiscalidad (E-01) introduciendo los datos catastrales y de adquisición de las propiedades.

### Cambios en Dominio y Casos de Uso
- **Value Objects**: Se crearon `CadastralBreakdown` y `AcquisitionCost` siguiendo el patrón inmutable (`frozen=True`) para encapsular las reglas de los valores catastrales (suelo y construcción) y los costes de adquisición con sus gastos asociados.
- **`Property`**: Extendida con campos opcionales (`cadastral_ref`, `cadastral_breakdown`, `acquisition_cost`, `acquisition_date`) y un helper `has_fiscal_data`.
- **Casos de Uso**: `UpdatePropertyFiscalDataUseCase` para transformar datos primitivos a Value Objects, y `GetPropertyFiscalDataUseCase`.

### Persistencia y API
- **SQLite**: Migración idempotente (`ALTER TABLE`) para agregar las 9 columnas nuevas relacionadas a la fiscalidad a la tabla `properties` y actualización de los adaptadores de repositorios.
- **FastAPI**: Nuevos endpoints `GET /api/properties/{id}/fiscal-data` y `PUT /api/properties/{id}/fiscal-data` con sus respectivos esquemas Pydantic para separar limpiamente la información fiscal de los datos genéricos de la propiedad.

### Frontend
- **Tipos y Servicios**: Agregadas las interfaces de TypeScript `CadastralBreakdown`, `AcquisitionCost` y `FiscalData`. Se crearon los métodos API para conectarse a los nuevos endpoints.
- **Componentes**: 
  - `FiscalDataForm`: Un componente unificado para llenar en detalle los valores del catastro y de adquisición, usando íconos de `lucide-react` para mantener la experiencia premium.
  - `PropertyDetail`: Modificado para incluir un sistema de pestañas (Tabs) que permite al usuario alternar entre el "Dashboard" tradicional (Ingresos/Gastos) y los "Datos Fiscales", mostrando un indicador (🟢/⚪) de si los datos están completos.

## Verificación Final
- La compilación en TypeScript finaliza con éxito (`npm run build`).
- Se escribieron y agregaron exhaustivas pruebas al proyecto para cubrir los nuevos Value Objects, los Casos de Uso, la persistencia en el Adaptador SQLite y los endpoints de API REST. La suite Backend ahora cuenta con 126 pruebas que pasan exitosamente en ~2.5 segundos, validando una cobertura completa y sin alterar funcionalidades pasadas (regresión nula).

---

# Walkthrough y Resumen - Feature F-10

## Resumen del Trabajo Realizado (Contratos de Arrendamiento)

En la feature F-10 hemos implementado la gestión completa de Contratos de Arrendamiento (*Lease Contracts*), elemento imprescindible para el motor de cálculo fiscal (F-12) que requerirá calcular los días de ocupación efectiva y aplicar reducciones fiscales según el tipo de contrato.

### Cambios en Dominio y Casos de Uso
- **Enum `LeaseType`**: Clasificación fiscal del contrato (`VIVIENDA_HABITUAL`, `TEMPORAL`, `TURISTICO`, `COMERCIAL`).
- **Entidad `LeaseContract`**: Encapsula la relación entre propiedad e inquilino (`tenant_name`, `tenant_nif`, `start_date`, `end_date`, `monthly_rent`, `lease_type`). Incluye métodos puros de dominio:
  - `is_active`: Determina si el contrato sigue vigente calculando dinámicamente sobre la fecha actual (sin redundancia de datos).
  - `rented_days_in_year(fiscal_year)`: Calcula los días exactos de alquiler efectivo dentro de un año fiscal para el prorrateo de gastos.
- **Puerto `LeaseContractRepository`**: Interfaz abstracta para la persistencia.
- **Casos de Uso**: `CreateLeaseContractUseCase`, `ListLeaseContractsUseCase`, `UpdateLeaseContractUseCase` y `DeleteLeaseContractUseCase`, todos con validación estricta de propiedad de usuario.

### Persistencia y API
- **SQLite**: Nueva tabla `lease_contracts` y repositorio `SQLiteLeaseContractRepository`. Se actualizó la eliminación de propiedades para incluir borrado en cascada de contratos.
- **FastAPI**: Nuevo router `backend/api/routes/contracts.py` registrado en `main.py` con endpoints para crear, listar, actualizar y eliminar contratos.

### Frontend
- **Tipos y Servicios**: Interfaces `LeaseContract` y `LeaseContractInput` en TypeScript y funciones API cliente en `services/api.ts`.
- **Componentes**: 
  - `ContractForm`: Formulario modal para alta y edición de contratos con validaciones en cliente.
  - `ContractSection`: Vista de tarjetas y lista de contratos con badges visuales de estado (🟢 Activo / 🔴 Finalizado) y etiquetas por tipo de arrendamiento.
  - `PropertyDetail`: Integración de la tercera pestaña "📋 Contratos".

## Verificación Final
- La compilación en TypeScript pasa limpiamente (`npm run build`).
- Se añadieron 29 tests nuevos entre unitarios e integración. Toda la suite de Backend ejecutó **155 pruebas pasando en verde** en 2.53s.

---

# Walkthrough y Resumen - Feature F-11

## Resumen del Trabajo Realizado (Clasificación Fiscal de Gastos e Ingresos)

En la feature F-11 hemos introducido la clasificación fiscal paralela para ingresos y gastos conforme al modelo D-100 de la Agencia Tributaria española (Rendimientos del Capital Inmobiliario).

### Cambios en Dominio y Casos de Uso
- **Enums de Clasificación Fiscal**:
  - `FiscalExpenseCategory` (9 categorías AEAT: `intereses_capital`, `reparacion_conservacion`, `tributos`, `primas_seguros`, `servicios_suministros`, `formalizacion`, `dudoso_cobro`, `otros_deducibles`, `no_deducible`).
  - `FiscalIncomeCategory` (2 categorías AEAT: `rendimiento_integro`, `otros_ingresos`).
- **Extensión de Entidades**: `Income` y `Expense` incorporan el campo opcional `fiscal_category`.
- **Servicio de Dominio `FiscalCategoryMapper`**: Lógica pura de sugerencia que mapea automáticamente categorías contables generales a su correspondiente partida fiscal AEAT.
- **Casos de Uso**:
  - `UpdateFiscalCategoryUseCase`: Actualización puntual de la categoría fiscal de un gasto o ingreso.
  - `SuggestFiscalCategoriesUseCase`: Generación de sugerencias de clasificación fiscal en lote para registros sin clasificar.

### Persistencia y API
- **SQLite**: Migraciones `ALTER TABLE` para añadir `fiscal_category` a las tablas `incomes` y `expenses`, y actualización de `SQLiteIncomeRepository` y `SQLiteExpenseRepository`.
- **FastAPI**:
  - Endpoints `PATCH /api/incomes/{id}/fiscal-category` y `PATCH /api/expenses/{id}/fiscal-category`.
  - Endpoint `GET /api/properties/{id}/fiscal-suggestions` para obtener sugerencias en lote.
  - Soporte de `fiscal_category` opcional en la creación de ingresos y gastos.

### Frontend
- **Tipos y Servicios**: Nuevos tipos TypeScript y métodos API cliente (`updateIncomeFiscalCategory`, `updateExpenseFiscalCategory`, `getFiscalSuggestions`).
- **Componentes**:
  - `IncomeForm` y `ExpenseForm`: Selectores opcionales para la categoría fiscal.
  - `FiscalClassificationPanel`: Panel interactivo integrado en la pestaña "Datos Fiscales" que permite la clasificación masiva de gastos e ingresos con ayuda del motor de sugerencias.

## Verificación Final
- Compilación de TypeScript limpia mediante `npm run build`.
- Se escribieron 28 pruebas adicionales. Toda la suite Backend cuenta ahora con **183 tests en verde** ejecutados en 3.90s.

---

# Walkthrough y Resumen - Feature F-12

## Resumen del Trabajo Realizado (Motor de Cálculo Fiscal)

En la feature F-12 hemos construido la pieza central de toda la Épica Fiscal (E-01): el motor de cálculo del **Rendimiento Neto del Capital Inmobiliario** según la normativa IRPF / modelo D-100 de la AEAT.

### Cambios en Dominio y Casos de Uso
- **Value Object `FiscalReport`**: Representación inmutable y detallada con ~30 campos que desglozan el cálculo paso a paso (ingresos, días ocupación, gastos por categoría, tope art. 23.1.a, amortización, reducción vivienda habitual y rendimiento neto final).
- **Servicio de Dominio `FiscalCalculator`**: Motor puro (sin dependencias de I/O o base de datos) que implementa el algoritmo de 11 pasos:
  1. Filtrado por año fiscal.
  2. Separación de registros clasificados vs no clasificados.
  3. Cálculo de Rendimientos Íntegros.
  4. Cálculo del Ratio de Ocupación mediante fusión de intervalos de contratos solapados (`_merge_rented_intervals`).
  5. Prorrateo de gastos fijos según ratio de ocupación.
  6. Aplicación del Tope del Art. 23.1.a LIRPF (gastos de reparación/conservación e intereses no pueden superar rendimientos íntegros).
  7. Cálculo de la Amortización (3% sobre el mayor entre coste de adquisición de la construcción y valor catastral de la construcción, prorrateado por ocupación).
  8. Suma de gastos deducibles totales.
  9. Rendimiento Neto Previo.
  10. Reducción del 60% por Vivienda Habitual (solo sobre rendimiento positivo y días bajo ese tipo de contrato).
  11. Rendimiento Neto Final.
- **Caso de Uso `GenerateFiscalReportUseCase`**: Orquesta la carga de propiedades, contratos, ingresos y gastos de los repositorios y ejecuta `FiscalCalculator.calculate`.

### API REST
- **Schema `FiscalReportResponse`**: Schema Pydantic para exponer el informe fiscal.
- **Endpoint `GET /api/properties/{property_id}/fiscal-report?year={year}`**: Genera y retorna el informe fiscal completo del año solicitado.

### Frontend
- **Tipos y Servicios**: Interface `FiscalReport` en TypeScript y método `getFiscalReport` en `services/api.ts`.
- **Componentes**:
  - `FiscalReportView`: Componente completo que incluye selector de año fiscal (2020-2026), tarjetas resumidas de ingresos y resultado final, barra visual de ocupación, tablas de gastos deducibles, desglose de amortización y avisos si existen datos sin clasificar.
  - `PropertyDetail`: Renderizado del `FiscalReportView` dentro de la pestaña "Datos Fiscales".

## Verificación Final
- Compilación en TypeScript perfecta (`npm run build` en 490ms).
- Se crearon 27 tests nuevos (17 unitarios del motor fiscal, 2 del VO `FiscalReport`, 3 del use case y 5 de integración de la API).
- Toda la suite del Backend pasa **210 tests en verde** en 4.06s.

---

# Walkthrough y Resumen - Feature F-16

## Resumen del Trabajo Realizado (Modelo de Dominio de Suministros)

En la feature F-16 hemos sentado las bases del dominio para la Épica E-02 (Automatización de Gastos de Suministros), extendiendo las entidades de `Property` y `Expense` y creando los Value Objects y estructuras necesarias para soportar la ingesta y verificación de facturas de suministros.

### Cambios en Dominio y Casos de Uso
- **Enums**: Creados `UtilityType` (`ELECTRICITY`, `GAS`, `WATER`), `ExpenseSource` (`MANUAL`, `AUTO_IMPORT`) y `ExtractionConfidence` (`HIGH`, `MEDIUM`, `LOW`).
- **Value Object `UtilityInvoiceData`**: VO inmutable que encapsula los datos extraídos de facturas (`cups`, `amount`, `issue_date`, `provider_name`, `utility_type`, `invoice_number`, `extraction_confidence`) con validación estricta de formato CUPS español (20-22 alfanuméricos), importe positivo y fecha no futura (>60 días).
- **Entidad `Property`**: Extendida con campos opcionales `cups_electricity`, `cups_gas`, `cups_water` con validación de formato CUPS en `__post_init__`.
- **Entidad `Expense`**: Extendida con campos retrocompatibles `is_verified` (default `True`), `source` (default `MANUAL`), `receipt_path` y `utility_data`.
- **Regla Fiscal de Dominio**: Modificado `FiscalCalculatorService` para garantizar que los gastos no verificados (`is_verified = False`) se excluyan del cálculo fiscal.
- **Puerto `PropertyRepository`**: Añadidos métodos `find_by_cups(cups, user_id)` y `update_cups(...)`.

### Adaptadores y API
- **SQLite**: Migraciones idempotentes (`ALTER TABLE`) para añadir columnas CUPS a `properties` y columnas de verificación/datos de suministro a `expenses`. Implementado `find_by_cups()` y `update_cups()`.
- **FastAPI**:
  - `PUT /api/properties/{property_id}/cups`: Endpoint para actualizar los CUPS de un inmueble.
  - Actualizados `ExpenseResponse` y `PropertyResponse` para exponer los nuevos campos.

## Verificación Final
- Cero violaciones de arquitectura (0 imports externos en `backend/domain/`).
- 259 tests pasados exitosamente en verde en 6.66s.

---

# Walkthrough y Resumen - Feature F-17

## Resumen del Trabajo Realizado (Puerto y Adaptador Genérico de LLM)

En la feature F-17 hemos implementado el puerto de servicio genérico e infraestructura transversal para interactuar con modelos de lenguaje (LLM), utilizando Google Gemini Flash como primer adaptador concreto, preparado para actuar como motor de fallback en la extracción de facturas (F-18) y en futuras capacidades de IA.

### Cambios en Dominio y Casos de Uso
- **Value Objects**:
  - `LLMRequest`: Encapsula de forma inmutable la petición al LLM (`user_prompt`, `system_prompt`, `response_schema`, `temperature`, `max_output_tokens`) con validación estricta de invariantes (prompt no vacío, temperatura entre 0.0 y 2.0, tokens positivos).
  - `LLMResponse`: Encapsula la respuesta del modelo (`text`, `parsed_data`, `model_name`, `input_tokens`, `output_tokens`) y propiedad derivada `total_tokens`.
- **Excepciones de Dominio**:
  - `LLMProviderError`: Excepción base para fallos no recuperables del proveedor.
  - `RateLimitError`: Subclase para exceso de cuota / error 429 con soporte para `retry_after_seconds`.
- **Puerto `LLMProviderPort`**: Interfaz abstracta con método único `generate(request: LLMRequest) -> LLMResponse` capaz de manejar tanto texto libre como extracción estructurada (`response_schema`).
- **Caso de Uso**: `CheckLLMHealthUseCase` para verificar conectividad y disponibilidad del proveedor sin acoplar la API a implementaciones concretas.

### Adaptadores y API
- **Adaptador `GeminiFlashAdapter`**: Implementación de `LLMProviderPort` utilizando el SDK `google-genai` y el modelo `gemini-2.0-flash`.
  - Soporte de Structured Outputs mediante `response_mime_type="application/json"` y `response_schema`.
  - Resiliencia y tolerancia a fallos con política de reintentos (`exponential backoff` con `jitter` aleatorio) para mitigar transitorios 429 y 5xx sin añadir librerías externas.
  - Inicialización limpia y segura mediante API Key desde variable de entorno `GEMINI_API_KEY`.
- **FastAPI**:
  - Endpoint `GET /api/llm/health` protegido por autenticación JWT (`get_current_user`) que reporta el estado del servicio (`ok`, `not_configured` o `error`).
  - Inyección de dependencias `get_llm_provider` en `backend/api/dependencies.py`.

### Tests y Verificación
- **Tests Unitarios**:
  - `test_llm_value_objects.py`: Cobertura de validaciones, inmutabilidad y cálculo de tokens en `LLMRequest`, `LLMResponse`, `LLMProviderError` y `RateLimitError` (T-17-01 a T-17-12).
  - `test_llm_health_use_case.py`: Cobertura del caso de uso con dobles de prueba (T-17-13 a T-17-15).
  - `FakeLLMProviderAdapter`: Test double en memoria en `conftest.py` para testing aislado.
- **Tests de Integración**:
  - `test_llm_api.py`: Validación de endpoint `GET /api/llm/health` con estados 200 (configurado y no configurado) y rechazo 401 sin autenticación (T-17-16 a T-17-18).

## Verificación Final
- Cero violaciones de arquitectura (0 imports externos en `backend/domain/`).
- Suite Backend ejecutada con **277 tests en verde** (0 fallos, 0 regresiones).
- Compilación de Frontend exitosa con TypeScript y Vite en 447ms.

---

# Walkthrough y Resumen - Feature F-26

## Retirada de 'Clasificación Fiscal Inteligente' de la UI y Limpieza de Deuda Técnica

### Diagnóstico y Justificación
- La herramienta de "Clasificación Fiscal Inteligente" (`FiscalClassificationPanel`) consistía en un envoltorio sobre un diccionario estático en backend (`FiscalCategoryMapper`) originalmente concebido en F-11 como migrador temporal de datos.
- En el flujo actual de la aplicación, los formularios de ingresos y gastos (`IncomeForm` y `ExpenseForm`) y el procesador de facturas PDF ya asignan las categorías fiscales directamente en el momento del registro.
- En consecuencia, el panel resultaba redundante, no permitía edición granular y generaba ruido visual ("IA slop") en la pestaña "Datos Fiscales".

### Cambios Realizados
- **Frontend**:
  - Eliminado el componente [`FiscalClassificationPanel.tsx`](file:///home/carlos/rental-handler/frontend/src/components/FiscalClassificationPanel.tsx).
  - Retirada la inclusión de dicho panel en [`PropertyDetail.tsx`](file:///home/carlos/rental-handler/frontend/src/pages/PropertyDetail.tsx), dejando la pestaña Fiscal estructurada limpiamente en:
    1. Datos Catastrales y Adquisición (`FiscalDataForm`).
    2. Motor de Cálculo Fiscal IRPF y descarga de Borrador AEAT en PDF (`FiscalReportView`).
  - Limpieza de estilos CSS obsoletos en `frontend/src/index.css`.
- **Backlog**:
  - Registrada la tarea `F-26` en `feature_list.json`.



