# Modulo: Motor Fiscal y Liquidacion IRPF (`tax-and-fiscal-engine`)

> Subsistema funcional vertical encargado de la contabilizacion de ingresos/gastos, clasificacion fiscal segun normativa AEAT y liquidacion del Modelo 100 de IRPF.

---

## 1. Responsabilidad y Alcance de Negocio
- Registro y clasificacion de ingresos computables y gastos deducibles por inmueble.
- Motor de amortizacion de inmuebles segun reglas oficiales de la AEAT (3% sobre mayor de valor catastral o coste adquisicion, excluyendo suelo).
- Control de limites de deducibilidad para gastos de reparacion/conservacion e intereses de financiacion, con acumulacion de saldos a compensar en 4 ejercicios posteriores (`FiscalCarryforward`).
- Calculo del rendimiento neto del capital inmobiliario y reduccion por arrendamiento de vivienda habitual.
- Generacion de informes fiscales descargables en formato PDF oficial listos para presentar en la declaracion de la renta.

---

## 2. Artefactos del Corte Vertical
- **Dominio**:
  - Entidades: `Income`, `Expense`, `FiscalCarryforward`, `FiscalExpenseCategory`, `FiscalIncomeCategory` (`backend/domain/entities.py`)
  - Servicios de Dominio: `FiscalCalculator`, `FiscalCategoryMapper`, `FiscalSimulatorService`, `ProfitCalculator` (`backend/domain/services.py`)
  - Puertos: `IncomeRepository`, `ExpenseRepository`, `FiscalCarryforwardRepository`, `FiscalReportRendererPort` (`backend/domain/ports.py`)
- **Aplicacion (Casos de Uso)**:
  - `RecordIncomeUseCase`, `RecordExpenseUseCase`, `UpdatePropertyFiscalDataUseCase`, `GetPropertyFiscalDataUseCase`, `UpdateFiscalCategoryUseCase`, `SuggestFiscalCategoriesUseCase`, `GenerateFiscalReportUseCase`, `DownloadFiscalReportPdfUseCase`, `QuickFiscalEstimateUseCase`, `GetPropertyProfitReportUseCase` (`backend/application/use_cases.py`)
- **Adaptadores de Infraestructura**:
  - `SQLiteIncomeRepository`, `SQLiteExpenseRepository`, `SQLiteFiscalCarryforwardRepository` (`backend/adapters/sqlite_adapter.py`)
  - `AEATReportLabRendererAdapter` (`backend/adapters/aeat_pdf_renderer_adapter.py`)
- **API & Endpoints**:
  - `backend/api/routes/expenses.py` (`GET/POST /api/expenses`, `PATCH /api/expenses/{id}/fiscal-category`, `POST /api/expenses/suggest-categories`)
  - `backend/api/routes/incomes.py` (`GET/POST /api/incomes`)
  - `backend/api/routes/properties.py` (`GET/PUT /api/properties/{id}/fiscal`, `GET /api/properties/{id}/fiscal-report`, `GET /api/properties/{id}/fiscal-report/pdf`)
- **Frontend**:
  - Vistas: Secciones fiscales en `PropertyDetail.tsx`
  - Componentes: `FiscalDataForm.tsx`, `FiscalReportView.tsx`, `ExpenseForm.tsx`, `IncomeForm.tsx`, `KPICard.tsx`
