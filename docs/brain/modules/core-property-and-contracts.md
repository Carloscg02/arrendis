# Modulo: Gestion de Inmuebles y Contratos (`core-property-and-contracts`)

> Subsistema funcional vertical para la administracion del catalogo inmobiliario, contratos de arrendamiento, inquilinos y ciclo de vida de alquiler.

---

## 1. Responsabilidad y Alcance de Negocio
- Catalogo y alta de inmuebles con datos catastrales, direccion, estado y atributos fisicos (superficie, habitaciones, banos, conservacion).
- Administracion de contratos de arrendamiento (`LeaseContract`), vinculacion de inquilinos (`Tenant`), fechas de vigencia y renta pactada.
- Onboarding inicial guiado (`BootstrapOnboardingUseCase`) para incorporar rapidamente la primera propiedad y contrato.
- Calculo del estado de ocupacion y metricas basicas de rendimiento de la cartera.

---

## 2. Artefactos del Corte Vertical
- **Dominio**:
  - Entidades y Enums: `Property`, `Tenant`, `LeaseContract`, `PropertyType`, `PropertyCondition`, `PropertyStatus`, `LeaseType` (`backend/domain/entities.py`)
  - Puertos: `PropertyRepository`, `LeaseContractRepository` (`backend/domain/ports.py`)
- **Aplicacion (Casos de Uso)**:
  - Inmuebles: `CreatePropertyUseCase`, `ListPropertiesUseCase`, `GetPropertyUseCase`, `UpdatePropertyPhysicalAttributesUseCase`
  - Contratos: `CreateLeaseContractUseCase`, `ListLeaseContractsUseCase`, `UpdateLeaseContractUseCase`, `DeleteLeaseContractUseCase`
  - Onboarding: `BootstrapOnboardingUseCase`, `SkipOnboardingUseCase` (`backend/application/use_cases.py`)
- **Adaptadores de Infraestructura**:
  - `SQLitePropertyRepository`, `SQLiteLeaseContractRepository` (`backend/adapters/sqlite_adapter.py`)
- **API & Endpoints**:
  - Inmuebles: `backend/api/routes/properties.py` (`GET /api/properties`, `POST /api/properties`, `GET /api/properties/{id}`, `PATCH /api/properties/{id}/physical-attributes`)
  - Contratos: `backend/api/routes/contracts.py` (`GET /api/contracts`, `POST /api/contracts`, `PUT /api/contracts/{id}`, `DELETE /api/contracts/{id}`)
  - Onboarding: `backend/api/routes/onboarding.py` (`POST /api/onboarding/bootstrap`, `POST /api/onboarding/skip`)
- **Frontend**:
  - Vistas: `PropertyList.tsx`, `PropertyDetail.tsx`, `Onboarding.tsx`
  - Componentes: `PropertyCard.tsx`, `PropertyForm.tsx`, `ContractForm.tsx`, `ContractSection.tsx`, `PhysicalAttributesModal.tsx`, `WelcomeOnboardingBanner.tsx`
