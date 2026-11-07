# Modulo: Valoracion Inmobiliaria de Mercado (`market-valuation`)

> Subsistema funcional vertical para la estimacion automatica de precio de venta y renta esperada basada en comparables de mercado.

---

## 1. Responsabilidad y Alcance de Negocio
- Solicitud asincrona de valoracion inmobiliaria a partir de atributos fisicos (metros cuadrados, codigo postal, estado de conservacion, dormitorios, ascensor).
- Calculo de horquillas de valoracion (minima, estimada, maxima), precio por metro cuadrado y nivel de confianza estadistica (`HIGH`, `MEDIUM`, `LOW`).
- Persistencia historica de valoraciones (`PropertyValuation`) para seguir la evolucion patrimonial de los inmuebles.

---

## 2. Artefactos del Corte Vertical
- **Dominio**:
  - Entidad: `PropertyValuation`, `ValuationConfidence` (`backend/domain/entities.py`)
  - Excepciones: `MarketValuationError`, `ValuationRateLimitError`, `MissingPhysicalAttributesError`
  - Puertos: `PropertyValuationRepository`, `MarketValuationPort` (`backend/domain/ports.py`)
- **Aplicacion (Casos de Uso)**:
  - `GetPropertyValuationUseCase`, `RequestPropertyValuationUseCase` (`backend/application/valuation_use_cases.py`, `backend/application/use_cases.py`)
- **Adaptadores de Infraestructura**:
  - `backend/adapters/valuation/` (Scraping etico/API Idealista y agregacion heuristica)
  - `SQLitePropertyValuationRepository` (`backend/adapters/sqlite_adapter.py`)
- **API & Endpoints**:
  - `backend/api/routes/properties.py` (`GET /api/properties/{id}/valuation`, `POST /api/properties/{id}/valuation`)
- **Frontend**:
  - Componentes: `MarketValuationPanel.tsx`, `PhysicalAttributesModal.tsx`
