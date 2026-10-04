# 🧪 Épica E-07: Estrategia de Testing Agéntico y Pirámide Invertida (E2E Playwright, Integración Real y Golden Tests)

> **Versión:** 1.0  
> **Estado:** Backlog / Planificada para recogida futura  
> **Fecha:** 2026-10-04  
> **Dependencias previas:** F-23/F-24 (Infraestructura y CI/CD GitHub Actions) ✅, E-01 (Fiscalidad), E-02 (Suministros), E-03 (Tasación), E-05 (Mobile/PWA)  

---

## 1. Contexto, Diagnóstico y Justificación

### 1.1 La Paradoja del Refactor Hexagonal
Durante el refactor de arquitectura hexagonal en `rental-handler`, se evidenció una disonancia crítica entre las métricas tradicionales de desarrollo y la realidad operativa con agentes de IA (SDD - Spec-Driven Development):
* **401 tests pasaban al 100% en verde**, pero la **confianza percibida del desarrollador era cero**, requiriendo un despliegue y validación manual paso a paso en local.
* El **80% del esfuerzo y consumo de tokens** durante el refactor no se dedicó a diseñar la arquitectura ni a verificar lógica de negocio, sino a **reparar tests unitarios acoplados a detalles de implementación**: decoradores `@patch` frágiles, rutas de importación mockeadas, y firmas de constructores artificialmente mantenidas (shimming de retrocompatibilidad) solo para no romper tests unitarios desfasados.

### 1.2 Auditoría del Repositorio Actual
* **Código de producción backend:** 8.356 LOC.
* **Código de tests:** 8.459 LOC (50,3% del código total).
* **Distribución de tests (401 totales):**
  * **Unitarios:** 382 tests (95,2%).
  * **Integración / E2E:** 19 tests (4,8%).

### 1.3 El Problema: El "Teatro del Mock" (Mock Theater)
Los tests unitarios tradicionales fueron concebidos hace más de dos décadas cuando compilar un monolito tardaba decenas de minutos y arrancar un navegador headless era inviable. En el desarrollo moderno con agentes y LLMs avanzados:
1. **Falsa sensación de seguridad:** Un test unitario con 4 mocks (`mock_pdf_extractor`, `mock_property_repo`, `mock_expense_repo`, `mock_invoice_extractor`) solo comprueba que una función llama a otra en el orden esperado. Si SQLite rechaza un tipo de dato, si FastAPI falla al deserializar un payload multipart, o si la librería externa cambia su API, el test sigue dando verde.
2. **Resistencia al cambio (Fragilidad estructural):** El test se convierte en una armadura rígida. Si el agente refactoriza una clase para aplicar DDD o separar responsabilidades, 15 tests fallan no por un bug, sino porque cambió el `__init__` interno.
3. **Inutilidad en modelos de vanguardia:** Los LLMs actuales casi nunca cometen errores de lógica sintáctica elemental o asignación de campos en dataclasses (como los 395 tests de `test_entities.py`). Donde los agentes cometen errores es en los **límites del sistema** (desincronización de esquemas Pydantic/TypeScript, concurrencia en BD, flujos de sesión, manipulación del DOM).

---

## 2. Paradigma: La Pirámide Invertida de la Era Agéntica

Esta épica redefine la jerarquía de pruebas de **Arrendis**, sustituyendo la pirámide de testing clásica por un modelo adaptado a la asistencia por IA:

```text
               ▲
              / \         1. E2E COMPLETOS (Playwright / Sin Mocks)
             /   \        Navegador real + API real + BD temporal.
            / E2E \       Certeza existencial: "¿El usuario puede completar el flujo?"
           /-------\
          /         \     2. INTEGRACIÓN DE LÍMITES (HTTP + SQLite)
         / Integra-  \    Peticiones HTTP reales contra FastAPI con SQLite en memoria.
        /    ción     \   Valida esquemas, Pydantic, HTTP status y transacciones SQL.
       /---------------\
      /     Golden      \ 3. GOLDEN TESTS (Artefactos Empíricos Reales)
     /     & Domain      \ Muestras reales fijadas (PDFs de facturas Repsol/Iberdrola,
    /                     \ JSONs de tasación) y Algoritmos Puros (FiscalCalculator SIN MOCKS).
   -------------------------
             ❌ [ZONA DEPRECIADA / ELIMINACIÓN]
             - "Teatro del Mock" (MagicMock / @patch generalizado)
             - Tests de getters, setters y asignación en dataclasses
             - Tests de puertos abstractos comprobando que lanzan NotImplementedError
```

### Principio de Oro del Testing Agéntico:
> *"Si un test unitario requiere simular (`mock`) dependencias internas de tu propio código para poder ejecutarse, no aporta valor real y debe convertirse en un test de integración real. Los únicos tests unitarios permitidos son aquellos sobre funciones algorítmicas puras de cálculo matemático o negocio sin un solo mock."*

---

## 3. Análisis de Complejidad Técnica e Integración en CI/CD

### 3.1 Retos de Incorporar Playwright (E2E)
1. **Coste temporal y recursos en CI/CD (GitHub Actions):**
   * Descargar navegadores completos (Chromium, Firefox, WebKit) puede añadir 2-3 minutos al pipeline.
   * *Mitigación:* Limitar la ejecución en CI a **Chromium Headless únicamente** (`--project=chromium`), utilizando la acción oficial de GitHub `microsoft/playwright-github-action` con caché de binarios.
2. **Orquestación concurrente de Backend y Frontend:**
   * Los tests E2E necesitan que tanto FastAPI (`:8000`) como Vite (`:5173`) estén corriendo con una base de datos limpia.
   * *Mitigación:* Usar la directiva nativa `webServer` de Playwright en `playwright.config.ts`, que arranca automáticamente ambos servicios antes de lanzar los tests y los destruye al terminar, o un contenedor Docker ephemeral en el runner.
3. **Flakiness (Inestabilidad en UI):**
   * *Mitigación:* Utilizar exclusivamente localizadores semánticos recomendados por Playwright (`getByRole`, `getByText`, `getByLabel`), evitando selectores CSS frágiles, y configurar `trace: 'on-first-retry'` para guardar trazas interactivas, capturas de pantalla y vídeo únicamente cuando un test falle.

### 3.2 Estrategia de Datos de Prueba (Seed y Aislamiento)
* Cada suite E2E creará un usuario nuevo mediante `/api/auth/register` (e.g. `test_user_<timestamp>@e2e.arrendis.com`), garantizando aislamiento multi-tenant estricto sin colisión de datos entre ejecuciones concurrentes.

---

## 4. Desglose de Features

```
┌────────────────────────────────────────────────────────────────────────┐
│ ÉPICA E-07: TESTING AGÉNTICO Y PIRÁMIDE INVERTIDA                      │
│                                                                        │
│   [ F-47: Setup Playwright E2E y Matriz de Flujos Críticos de Usuario ]│
│   [ F-48: Integración de Playwright en CI/CD (GitHub Actions) ]        │
│   [ F-49: Repositorio Central de Golden Tests ]                        │
│   [ F-50: Poda y Saneamiento de la Suite: Erradicación de Mocks ]      │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Feature F-47: Setup Playwright E2E y Matriz de Flujos Críticos de Usuario
* **Objetivo:** Instalar y configurar Playwright en el proyecto para validar de extremo a extremo la experiencia real de usuario en navegador web y simulación móvil (PWA).
* **Alcance:**
  1. Configuración de `@playwright/test` en el directorio `frontend/` o `tests/e2e/`.
  2. Implementación de **3 flujos críticos ("Happy Paths") indispensables**:
     * **E2E-01: Onboarding y Gestión Inmobiliaria:** Registro -> Creación de primera propiedad -> Asignación de datos catastrales e imagen -> Comprobación de renderizado en panel.
     * **E2E-02: Pipeline de Facturas de Suministros:** Subida de factura PDF real desde la UI de Gastos -> Procesamiento -> Aparición del gasto verificado con desglose de importe y CUPS.
     * **E2E-03: Ciclo Fiscal y Descarga AEAT:** Inmueble con ingresos y gastos -> Navegación a pestaña Fiscal -> Visualización de rendimientos y amortización -> Clic en descarga del PDF oficial y comprobación de respuesta HTTP 200 con cabecera `application/pdf`.
* **Criterios de Aceptación:**
  * Comando `npm run test:e2e` ejecuta la suite completa en local en menos de 30 segundos.
  * Trazas interactivas (`playwright show-trace`) disponibles para depuración visual.

---

### Feature F-48: Integración de Playwright en CI/CD (GitHub Actions)
* **Objetivo:** Integrar la batería E2E de Playwright en `.github/workflows/deploy.yml` para bloquear automáticamente cualquier Pull Request o commit a `develop`/`main` que rompa la experiencia de usuario.
* **Alcance:**
  1. Nuevo job `test-e2e` en GitHub Actions que se ejecuta tras pasar el build de frontend y backend.
  2. Instalación en caché de Chromium (`npx playwright install --with-deps chromium`).
  3. Ejecución contra servidores locales temporales (FastAPI con SQLite en memoria y Vite build/preview).
  4. Subida automática del reporte HTML y trazas (`playwright-report/`) como artefactos descargables de GitHub Actions en caso de fallo.
* **Criterios de Aceptación:**
  * El job de CI añade un tiempo total inferior a 90 segundos al pipeline.
  * Ante una regresión visual o de flujo, el artefacto de traza permite ver el vídeo exacto del fallo.

---

### Feature F-49: Repositorio Central de Golden Tests
* **Objetivo:** Centralizar y formalizar el conjunto de "Pruebas Doradas" (Golden Fixtures) como el ancla de invariabilidad técnica del sistema.
* **Alcance:**
  1. Creación del directorio unificado `tests/golden/`:
     * `tests/golden/invoices/`: PDFs reales de comercializadoras (Repsol, Iberdrola, Endesa, TotalEnergies) anonimizados para validar extracción empírica sin mocks.
     * `tests/golden/tax/`: Declaraciones fiscales complejas con resultados calculados a mano conforme a los manuales oficiales de la AEAT (casos límite de Ley 12/2023, reducción de zona tensionada, excesos plurianuales).
     * `tests/golden/valuation/`: Respuestas de grounding congeladas para probar sanitizadores de Idealista/Fotocasa contra respuestas reales de Google Gemini sin consumir cuota de API en tests diarios.
  2. Pruebas de regresión automatizadas que contrastan el comportamiento del sistema contra los archivos dorados.
* **Criterios de Aceptación:**
  * Cualquier cambio en motores de cálculo o extracción debe superar el 100% de los Golden Tests sin discrepancias decimales.

---

### Feature F-50: Poda y Saneamiento de la Suite: Erradicación del "Teatro del Mock"
* **Objetivo:** Purgar de forma segura y planificada los tests unitarios superfluos y sobre-mockeados que ralentizan el desarrollo agéntico y añaden fricción a los refactors.
* **Alcance:**
  1. Auditoría y eliminación de tests sin valor de negocio:
     * Eliminación de `test_entities.py` y tests triviales de asignación de atributos.
     * Eliminación de tests de use cases sobre-mockeados que duplican la cobertura que ya ofrecen los tests de endpoints API e integración de SQLite.
  2. Eliminación de decoradores `@patch` en adaptadores técnicos, sustituyéndolos por Golden Fixtures o adaptadores Mock desacoplados de alto nivel (como `MockMarketValuationAdapter`).
  3. Blindaje exclusivo de tests unitarios algorítmicos puros (ej. `test_fiscal_calculator.py`, `test_privacy_scrubber.py`).
* **Criterios de Aceptación:**
  * Reducción de la suite de tests de ~8.400 líneas a ~4.000 líneas de altísimo valor.
  * Tiempos de ejecución de `pytest` inferiores a 3 segundos.
  * Cero decoradores `@patch` dependientes de rutas internas de archivos en adaptadores.

---

## 5. Plan de Adopción y Fases de Ejecución Futura

La implementación de esta épica se planifica de forma progresiva para no interrumpir el flujo de entregas de negocio:

1. **Fase 1 (Cimientos E2E):** Ejecutar **F-47** instalando Playwright con los 3 flujos básicos en local.
2. **Fase 2 (Automatización CI/CD):** Ejecutar **F-48** integrando el job en GitHub Actions con reportes.
3. **Fase 3 (Anclaje Empírico):** Ejecutar **F-49** unificando Golden Fixtures para facturas y fiscalidad.
4. **Fase 4 (Poda y Eficiencia):** Ejecutar **F-50** retirando tests redundantes con mocks, dejando una suite ultrarrápida, resiliente a refactorizaciones agénticas y de máxima confianza.
