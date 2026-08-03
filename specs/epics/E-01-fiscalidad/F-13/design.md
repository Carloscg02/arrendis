# F-13 — Informe Fiscal y Generación de PDF (Borrador AEAT)

> **Épica:** E-01 Fiscalidad  
> **Dependencias:** F-12 (Motor de Cálculo Fiscal)  
> **Estado:** Pendiente de aprobación

---

## 1. Objetivo

F-13 es la **feature de cierre** de la épica de fiscalidad. Toma el `FiscalReport` generado
por el motor de cálculo de F-12 y lo transforma en un **documento PDF descargable** con formato
de borrador fiscal, mapeando cada concepto de dominio a las casillas correspondientes del
modelo D-100 de la AEAT.

### Lo que entrega:

1. **Puerto de salida `FiscalReportRendererPort`** — Interfaz abstracta que define cómo se
   renderiza un `FiscalReport` a bytes (PDF u otro formato futuro).
2. **Adaptador `AEATPdfRendererAdapter`** — Implementación concreta con `reportlab` que genera
   un PDF profesional con el mapeo a casillas AEAT del ejercicio vigente.
3. **Diccionario de mapeo semántico ↔ casillas AEAT** — Desacoplado del dominio, vive en el
   adaptador. Si la AEAT cambia casillas, solo se actualiza este diccionario.
4. **Nuevo Use Case `DownloadFiscalReportPdfUseCase`** — Orquesta la obtención del
   `FiscalReport` y su renderizado a PDF.
5. **Endpoint `GET /api/properties/{id}/fiscal-report/pdf?year=YYYY`** — Retorna el PDF como
   `application/pdf` para descarga directa.
6. **Botón "Descargar Borrador Fiscal (PDF)"** en el frontend — Integrado en la vista de
   informe fiscal existente (`FiscalReportView`).

---

## 2. Lenguaje Ubicuo (Nuevos Términos)

| Término | Definición |
|---|---|
| **FiscalReportRendererPort** | Puerto de salida que define el contrato para transformar un `FiscalReport` (Value Object de dominio) en una representación binaria (bytes). Es la interfaz abstracta. |
| **AEATPdfRendererAdapter** | Adaptador concreto que implementa `FiscalReportRendererPort`. Genera un PDF con el layout del borrador fiscal de la AEAT, usando `reportlab`. |
| **Mapeo de Casillas AEAT** | Diccionario que traduce categorías semánticas estables del dominio (`TaxCategory`, campos del `FiscalReport`) a los números de casilla del modelo D-100 del ejercicio fiscal vigente. Vive exclusivamente en el adaptador. |
| **Borrador Fiscal** | Documento PDF generado por el sistema que resume el Rendimiento del Capital Inmobiliario de una propiedad para un ejercicio. Pensado para trasladar los datos a Renta Web manualmente. NO es una presentación telemática. |

---

## 3. Modelo de Dominio

### 3.1 Nuevo Puerto de Salida — `FiscalReportRendererPort`

Se añade en `backend/domain/ports.py`:

```python
class FiscalReportRendererPort(ABC):
    """Puerto de salida para renderizar un FiscalReport a un formato descargable.

    El dominio define QUÉ se renderiza (FiscalReport), pero no CÓMO.
    Cada adaptador concreto decide el formato (PDF, Excel, HTML, etc.).
    """

    @abstractmethod
    def render(self, report: FiscalReport, property_name: str, property_address: str) -> bytes:
        """Renderiza un FiscalReport a bytes.

        Args:
            report: El Value Object con todos los datos fiscales calculados.
            property_name: Nombre de la propiedad (para el encabezado del documento).
            property_address: Dirección de la propiedad.

        Returns:
            Los bytes del documento generado (PDF, etc.).
        """
        ...

    @abstractmethod
    def content_type(self) -> str:
        """Retorna el MIME type del formato de salida (e.g., 'application/pdf')."""
        ...

    @abstractmethod
    def file_extension(self) -> str:
        """Retorna la extensión del archivo (e.g., 'pdf')."""
        ...
```

### 3.2 Diccionario de Mapeo — Casillas AEAT 2024

El mapeo vive en el adaptador, **nunca en el dominio**. Es un diccionario de configuración
del adaptador `AEATPdfRendererAdapter`:

```python
# Mapeo para el Modelo D-100, Ejercicio 2024
# Página 8: Rendimientos del Capital Inmobiliario (inmuebles arrendados)
AEAT_CASILLA_MAP_2024 = {
    # ── Datos del Inmueble ──
    "referencia_catastral": "Casilla 0063",
    "situacion_inmueble": "Casilla 0064",  # 1=España
    "uso_inmueble": "Casilla 0065",  # 1=Arrendamiento

    # ── Rendimientos Íntegros ──
    "rendimiento_integro": "Casilla 0075",  # total_income

    # ── Gastos Deducibles ──
    "intereses_capital": "Casilla 0076",  # expenses_intereses
    "reparacion_conservacion": "Casilla 0077",  # expenses_reparacion
    "tributos": "Casilla 0079",  # expenses_tributos (IBI, tasas)
    "seguros": "Casilla 0081",  # expenses_seguros
    "suministros": "Casilla 0082",  # expenses_suministros
    "amortizacion": "Casilla 0083",  # amortization_prorated
    "otros_gastos": "Casilla 0084",  # expenses_otros + formalizacion + dudoso_cobro

    # ── Resultados ──
    "total_gastos_deducibles": "Casilla 0085",  # total_deductible_expenses
    "rendimiento_neto": "Casilla 0086",  # net_income_before_reduction
    "reduccion_vivienda": "Casilla 0087",  # reduction_amount
    "rendimiento_neto_reducido": "Casilla 0088",  # net_income_final
}
```

> **Nota:** Los números de casilla son ilustrativos del modelo D-100 2024.
> Si la AEAT los modifica en 2025, solo se actualiza este diccionario.
> El dominio, los tests y los cálculos permanecen intactos.

### 3.3 Ningún cambio en el dominio existente

F-13 **no modifica** ninguna entidad, value object, ni servicio de dominio existente.
Solo añade un nuevo puerto de salida y su adaptador.

---

## 4. Adaptador — `AEATPdfRendererAdapter`

Se crea como archivo nuevo: `backend/adapters/aeat_pdf_renderer_adapter.py`.

### 4.1 Layout del PDF

El PDF generado tiene el siguiente layout profesional:

```
┌──────────────────────────────────────────────────────────────┐
│  BORRADOR FISCAL — Rendimientos del Capital Inmobiliario     │
│  Ejercicio Fiscal: 2026                                      │
│──────────────────────────────────────────────────────────────│
│  Propiedad: Piso Calle Gran Vía 42, 3ºB                     │
│  Dirección: Calle Gran Vía 42, 3ºB, Madrid                  │
│  Fecha de generación: 02/08/2026                             │
│──────────────────────────────────────────────────────────────│
│                                                              │
│  SECCIÓN 1: RENDIMIENTOS ÍNTEGROS                            │
│  ┌──────────────────────────┬──────────┬────────────┐       │
│  │ Concepto                 │ Casilla  │ Importe    │       │
│  ├──────────────────────────┼──────────┼────────────┤       │
│  │ Rendimiento íntegro      │ 0075     │ 12.000,00€ │       │
│  └──────────────────────────┴──────────┴────────────┘       │
│                                                              │
│  SECCIÓN 2: GASTOS DEDUCIBLES                                │
│  ┌──────────────────────────┬──────────┬────────────┐       │
│  │ Intereses de capital     │ 0076     │  1.200,00€ │       │
│  │ Reparación/Conservación  │ 0077     │    800,00€ │       │
│  │ Tributos (IBI, tasas)    │ 0079     │    450,00€ │       │
│  │ Seguros                  │ 0081     │    300,00€ │       │
│  │ Suministros              │ 0082     │    150,00€ │       │
│  │ Amortización             │ 0083     │  3.816,00€ │       │
│  │ Otros gastos             │ 0084     │    200,00€ │       │
│  ├──────────────────────────┼──────────┼────────────┤       │
│  │ TOTAL GASTOS DEDUCIBLES  │ 0085     │  6.916,00€ │       │
│  └──────────────────────────┴──────────┴────────────┘       │
│                                                              │
│  SECCIÓN 3: RENDIMIENTO NETO                                 │
│  ┌──────────────────────────┬──────────┬────────────┐       │
│  │ Rendimiento neto         │ 0086     │  5.084,00€ │       │
│  │ Reducción vivienda hab.  │ 0087     │ -3.050,40€ │       │
│  │ RENDIMIENTO NETO REDUCIDO│ 0088     │  2.033,60€ │       │
│  └──────────────────────────┴──────────┴────────────┘       │
│                                                              │
│  SECCIÓN 4: DETALLE DEL CÁLCULO                              │
│  • Días alquilados: 365/365 (100%)                           │
│  • Base amortización: 127.200,00€ (coste adquisición)        │
│  • Amortización anual completa: 3.816,00€                    │
│  • Amortización prorrateada: 3.816,00€                       │
│  • Tope reparación + intereses: No aplicado                  │
│  • Días vivienda habitual: 365                               │
│  • Reducción VH: 60% sobre 5.084,00€ = 3.050,40€            │
│                                                              │
│  SECCIÓN 5: AVISOS                                           │
│  ⚠ Este documento es un borrador orientativo.                │
│    Los datos deben trasladarse manualmente a Renta Web.       │
│    No constituye presentación telemática ante la AEAT.        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Exceso reparación+intereses pendiente: 0,00€         │    │
│  │ (deducible en los 4 ejercicios siguientes)            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│──────────────────────────────────────────────────────────────│
│  Generado por Gestión de Alquileres — No válido para AEAT   │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Implementación del adaptador

```python
class AEATPdfRendererAdapter(FiscalReportRendererPort):
    """Genera un PDF con formato de borrador fiscal AEAT.

    Usa reportlab para generar el PDF en memoria (BytesIO).
    El diccionario de casillas se configura por ejercicio fiscal.
    """

    def __init__(self, casilla_map: dict[str, str] | None = None):
        self._casilla_map = casilla_map or AEAT_CASILLA_MAP_2024

    def render(self, report: FiscalReport, property_name: str, property_address: str) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, ...)
        # ... construye el PDF con reportlab
        return buffer.getvalue()

    def content_type(self) -> str:
        return "application/pdf"

    def file_extension(self) -> str:
        return "pdf"
```

### 4.3 Estructura interna del PDF (Reportlab)

El adaptador usa `reportlab.platypus` para construir el documento:
- **Header**: Logo/título + datos del ejercicio y propiedad
- **Tablas**: `Table` de reportlab con `TableStyle` para bordes y colores
- **Secciones**: Separadas con `Spacer` y títulos en negrita
- **Footer**: Disclaimer legal + fecha de generación
- **Colores**: Azul corporativo para encabezados (`HexColor("#1a56db")`), gris claro
  para filas alternas, rojo para avisos

---

## 5. Caso de Uso — `DownloadFiscalReportPdfUseCase`

Se añade en `backend/application/use_cases.py`:

```python
class DownloadFiscalReportPdfUseCase:
    """Genera y descarga el informe fiscal en PDF para una propiedad y año fiscal.

    Orquesta dos pasos:
    1. Delega el cálculo fiscal a GenerateFiscalReportUseCase.
    2. Pasa el FiscalReport al FiscalReportRendererPort para generar el PDF.
    """

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
        expense_repo: ExpenseRepository,
        lease_contract_repo: LeaseContractRepository,
        renderer: FiscalReportRendererPort,
    ):
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo
        self._lease_contract_repo = lease_contract_repo
        self._renderer = renderer

    def execute(self, user_id: str, property_id: str, fiscal_year: int) -> tuple[bytes, str, str]:
        """Ejecuta el caso de uso.

        Returns:
            Tupla (pdf_bytes, content_type, filename).
        """
        # 1. Obtener property y validar pertenencia
        property = self._property_repo.find_by_id(property_id)
        if property is None or property.user_id != user_id:
            raise ValueError("Propiedad no encontrada")
        if not property.has_fiscal_data:
            raise ValueError("La propiedad no tiene datos fiscales completos")

        # 2. Recopilar datos
        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)
        contracts = self._lease_contract_repo.find_by_property_id(property_id)

        # 3. Calcular el FiscalReport
        report = FiscalCalculator.calculate(
            fiscal_year, property, incomes, expenses, contracts
        )

        # 4. Renderizar a PDF
        pdf_bytes = self._renderer.render(
            report,
            property_name=property.name,
            property_address=str(property.address) if property.address else "",
        )

        # 5. Construir filename
        filename = f"borrador_fiscal_{property.name.replace(' ', '_')}_{fiscal_year}.{self._renderer.file_extension()}"

        return pdf_bytes, self._renderer.content_type(), filename
```

---

## 6. API REST

### 6.1 Nuevo Endpoint

| Método | Ruta | Descripción | Response |
|---|---|---|---|
| `GET` | `/api/properties/{property_id}/fiscal-report/pdf?year={year}` | Genera y descarga el PDF del borrador fiscal | `application/pdf` (descarga directa) |

### 6.2 Implementación en `properties.py`

```python
@router.get("/{property_id}/fiscal-report/pdf")
async def download_fiscal_report_pdf(
    property_id: str,
    year: int = Query(..., description="Año fiscal"),
    current_user: User = Depends(get_current_user),
    property_repo: PropertyRepository = Depends(get_property_repo),
    income_repo: IncomeRepository = Depends(get_income_repo),
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    lease_contract_repo: LeaseContractRepository = Depends(get_lease_contract_repo),
    renderer: FiscalReportRendererPort = Depends(get_fiscal_report_renderer),
):
    """Genera y descarga el borrador fiscal en PDF."""
    use_case = DownloadFiscalReportPdfUseCase(
        property_repo, income_repo, expense_repo, lease_contract_repo, renderer
    )
    try:
        pdf_bytes, content_type, filename = use_case.execute(
            current_user.id, property_id, year
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
```

### 6.3 Nueva Dependencia en `dependencies.py`

```python
def get_fiscal_report_renderer() -> FiscalReportRendererPort:
    """Inyecta el renderizador de informes fiscales (PDF AEAT por defecto)."""
    return AEATPdfRendererAdapter()
```

---

## 7. Frontend

### 7.1 Nuevo método API — `downloadFiscalReportPdf`

Se añade en `frontend/src/services/api.ts`:

```typescript
export async function downloadFiscalReportPdf(propertyId: string, year: number): Promise<void> {
  const res = await apiFetch(
    `${API_BASE}/properties/${propertyId}/fiscal-report/pdf?year=${year}`
  );

  if (!res.ok) {
    const text = await res.text();
    try {
      const json = JSON.parse(text);
      throw new Error(json.detail || text);
    } catch {
      throw new Error(text || 'Error al descargar el PDF');
    }
  }

  // Extraer filename del header Content-Disposition
  const contentDisposition = res.headers.get('content-disposition');
  const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
  const filename = filenameMatch ? filenameMatch[1] : `borrador_fiscal_${year}.pdf`;

  // Trigger descarga del navegador
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
```

### 7.2 Botón de descarga en `FiscalReportView.tsx`

Se añade un botón "📄 Descargar Borrador Fiscal (PDF)" al componente existente.
Se muestra **al final del informe**, después de la sección "Resultado Final",
para que el usuario primero revise los datos y luego descargue:

```tsx
// Nuevo estado
const [downloading, setDownloading] = useState(false);
const [downloadError, setDownloadError] = useState<string | null>(null);

// Handler
const handleDownloadPdf = async () => {
  setDownloading(true);
  setDownloadError(null);
  try {
    await downloadFiscalReportPdf(propertyId, year);
  } catch (err: any) {
    setDownloadError(err.response?.data?.detail || 'Error al descargar el PDF');
  } finally {
    setDownloading(false);
  }
};

// JSX — después de la sección de resultado final
<div className="fiscal-report-download-section">
  <button
    className="fiscal-report-download-btn"
    onClick={handleDownloadPdf}
    disabled={downloading}
  >
    {downloading ? (
      <>
        <span className="fiscal-report-download-spinner" />
        Generando PDF...
      </>
    ) : (
      <>📄 Descargar Borrador Fiscal (PDF)</>
    )}
  </button>
  {downloadError && (
    <p className="fiscal-report-download-error">{downloadError}</p>
  )}
  <p className="fiscal-report-download-disclaimer">
    Este documento es un borrador orientativo. Los datos deben trasladarse
    manualmente a Renta Web (AEAT).
  </p>
</div>
```

### 7.3 Estilos CSS

Se añaden en `frontend/src/index.css`, siguiendo el patrón `.fiscal-report-*`:

```css
/* ── F-13: Botón de descarga de PDF ── */
.fiscal-report-download-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: hsl(var(--color-surface-glass));
  backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid hsl(var(--color-border) / 0.15);
  text-align: center;
}

.fiscal-report-download-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg,
    hsl(var(--color-primary)),
    hsl(var(--color-primary) / 0.8));
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 15px hsl(var(--color-primary) / 0.3);
}

.fiscal-report-download-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px hsl(var(--color-primary) / 0.4);
}

.fiscal-report-download-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.fiscal-report-download-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fiscal-report-download-error {
  margin-top: 0.75rem;
  color: hsl(0 80% 60%);
  font-size: 0.875rem;
}

.fiscal-report-download-disclaimer {
  margin-top: 1rem;
  font-size: 0.8rem;
  color: hsl(var(--color-text-muted));
  font-style: italic;
}
```

---

## 8. Dependencia externa — `reportlab`

Se instala `reportlab` en el entorno virtual del proyecto:

```bash
source venv/bin/activate
pip install reportlab
```

> **Nota:** El proyecto no usa `requirements.txt` ni `pyproject.toml`.
> Las dependencias se gestionan directamente en el `venv/`.

### ¿Por qué `reportlab` y no `weasyprint`?

| Criterio | reportlab | weasyprint |
|---|---|---|
| **Instalación** | `pip install reportlab` (puro Python) | Requiere `cairo`, `pango`, `gdk-pixbuf` (dependencias de sistema) |
| **Peso** | Ligero (~5MB) | Pesado (~50MB+ con dependencias) |
| **Control de layout** | Programático, pixel-perfect | HTML/CSS → PDF (más flexible para diseños complejos) |
| **Complejidad** | Más código pero más predecible | Menos código pero debugging difícil |
| **Para este caso** | ✅ Ideal — tablas simples, layout fijo | Overkill para un informe tabular |

`reportlab` es la opción más ligera y predecible para nuestro caso de uso: un informe
tabular con secciones fijas. No necesitamos la flexibilidad de HTML/CSS de `weasyprint`.

---

## 9. Tests

### 9.1 Tests Unitarios del Adaptador PDF

| ID | Archivo | Descripción |
|---|---|---|
| T-U-13-01 | `test_aeat_pdf_renderer.py` | `render()` retorna bytes no vacíos para un FiscalReport válido |
| T-U-13-02 | `test_aeat_pdf_renderer.py` | `content_type()` retorna `"application/pdf"` |
| T-U-13-03 | `test_aeat_pdf_renderer.py` | `file_extension()` retorna `"pdf"` |
| T-U-13-04 | `test_aeat_pdf_renderer.py` | Los bytes generados empiezan con `%PDF` (magic bytes del formato PDF) |
| T-U-13-05 | `test_aeat_pdf_renderer.py` | El PDF se puede abrir como documento válido (parseable con reportlab) |
| T-U-13-06 | `test_aeat_pdf_renderer.py` | El PDF contiene el nombre de la propiedad en su texto |
| T-U-13-07 | `test_aeat_pdf_renderer.py` | El PDF contiene el año fiscal en su texto |
| T-U-13-08 | `test_aeat_pdf_renderer.py` | Se puede inyectar un mapa de casillas personalizado |

### 9.2 Tests Unitarios del Use Case

| ID | Archivo | Descripción |
|---|---|---|
| T-U-13-09 | `test_download_fiscal_pdf_use_case.py` | Genera PDF con datos completos (retorna bytes, content_type, filename) |
| T-U-13-10 | `test_download_fiscal_pdf_use_case.py` | Error si propiedad no pertenece al usuario |
| T-U-13-11 | `test_download_fiscal_pdf_use_case.py` | Error si propiedad sin datos fiscales |
| T-U-13-12 | `test_download_fiscal_pdf_use_case.py` | Filename contiene nombre de propiedad y año fiscal |

### 9.3 Tests Unitarios del Puerto

| ID | Archivo | Descripción |
|---|---|---|
| T-U-13-13 | `test_fiscal_report_renderer_port.py` | `FiscalReportRendererPort` no se puede instanciar directamente (es abstracta) |

### 9.4 Tests de Integración API

| ID | Archivo | Descripción |
|---|---|---|
| T-I-13-01 | `test_fiscal_report_pdf_api.py` | `GET .../fiscal-report/pdf?year=2026` con datos completos retorna 200 y `application/pdf` |
| T-I-13-02 | `test_fiscal_report_pdf_api.py` | El body del response empieza con `%PDF` |
| T-I-13-03 | `test_fiscal_report_pdf_api.py` | Header `Content-Disposition` contiene `attachment` y filename |
| T-I-13-04 | `test_fiscal_report_pdf_api.py` | Propiedad sin datos fiscales retorna 400 |
| T-I-13-05 | `test_fiscal_report_pdf_api.py` | Propiedad de otro usuario retorna 404 |
| T-I-13-06 | `test_fiscal_report_pdf_api.py` | Sin token de autenticación retorna 401 |

---

## 10. Archivos Afectados (Resumen)

| Acción | Archivo |
|---|---|
| ✏️ Modificar | `backend/domain/ports.py` — nuevo puerto `FiscalReportRendererPort` |
| 🆕 Crear | `backend/adapters/aeat_pdf_renderer_adapter.py` — adaptador PDF con reportlab |
| ✏️ Modificar | `backend/application/use_cases.py` — nuevo `DownloadFiscalReportPdfUseCase` |
| ✏️ Modificar | `backend/api/routes/properties.py` — nuevo endpoint GET `.../fiscal-report/pdf` |
| ✏️ Modificar | `backend/api/dependencies.py` — nueva dependencia `get_fiscal_report_renderer` |
| ✏️ Modificar | `frontend/src/services/api.ts` — nuevo método `downloadFiscalReportPdf` |
| ✏️ Modificar | `frontend/src/components/FiscalReportView.tsx` — botón de descarga PDF |
| ✏️ Modificar | `frontend/src/index.css` — estilos del botón de descarga |
| 🆕 Crear | `tests/unit/backend/adapters/test_aeat_pdf_renderer.py` — 8 tests adaptador |
| 🆕 Crear | `tests/unit/backend/application/test_download_fiscal_pdf_use_case.py` — 4 tests UC |
| 🆕 Crear | `tests/unit/backend/domain/test_fiscal_report_renderer_port.py` — 1 test puerto |
| 🆕 Crear | `tests/integration/backend/api/test_fiscal_report_pdf_api.py` — 6 tests API |

---

## 11. 📚 El Rincón del Estudiante

### ¿Qué es un Puerto de Salida "no repositorio"?

Hasta F-12, todos nuestros puertos de salida eran **repositorios**: interfaces para guardar
y recuperar entidades de la base de datos (`PropertyRepository`, `IncomeRepository`, etc.).
Pero la Arquitectura Hexagonal no limita los puertos a persistencia.

Un **puerto de salida** es cualquier contrato que el dominio necesita para interactuar con
el mundo exterior. Algunos ejemplos:

| Puerto | ¿Qué hace? | Adaptador actual |
|---|---|---|
| `PropertyRepository` | Persiste propiedades | `SQLitePropertyRepository` |
| `PasswordHasherPort` | Hashea contraseñas | `BcryptPasswordHasherAdapter` |
| `TokenServicePort` | Genera/valida tokens JWT | `JWTTokenServiceAdapter` |
| **`FiscalReportRendererPort`** (nuevo) | **Renderiza un informe a PDF** | **`AEATPdfRendererAdapter`** |

La convención de nombres del proyecto ayuda a distinguirlos:
- **`*Repository`** → persistencia de entidades DDD
- **`*Port`** → servicios de infraestructura que no son persistencia
- **`*Adapter`** → implementación concreta de cualquier puerto

### ¿Por qué el diccionario de casillas NO vive en el dominio?

Imagina que eres un contable. Tú sabes que un propietario pagó 300€ de seguro del hogar.
Eso es un hecho **estable** — siempre será un seguro, da igual el formulario que uses para
declararlo.

Ahora, la AEAT te dice: "En 2024, los seguros van en la casilla 0081. En 2025, van en la
0090". El **hecho** no ha cambiado (300€ de seguro), solo ha cambiado **dónde lo apuntas**
en el formulario.

```
DOMINIO (estable):     TaxCategory.INSURANCE → "Es un seguro. Siempre."
ADAPTADOR (variable):  casilla_map["seguros"] → "0081" (2024) / "0090" (2025)
```

Si el mapeo viviera en el dominio, cada cambio de la AEAT obligaría a modificar la lógica
de negocio, re-ejecutar tests del dominio y potencialmente romper cosas. Con el mapeo en
el adaptador, el dominio permanece intacto y solo se actualiza un diccionario de configuración.

### ¿Cómo funciona la descarga de archivos desde el navegador?

Cuando haces `fetch` o `axios.get` desde JavaScript, normalmente recibes JSON. Pero para
descargar un PDF, necesitas recibir **bytes crudos** (un "blob"):

```
PASO 1: El frontend pide el PDF al backend
         axios.get("/api/.../pdf", { responseType: 'blob' })
                                      ^^^^^^^^^^^^^^^^
                                      "Quiero bytes, no JSON"

PASO 2: El backend genera el PDF en memoria y lo envuelve en un Response
         Response(content=pdf_bytes, media_type="application/pdf",
                  headers={"Content-Disposition": "attachment; filename=..."})

PASO 3: El frontend recibe los bytes y crea una URL temporal
         const url = URL.createObjectURL(blob)

PASO 4: Se crea un <a> invisible que apunta a esa URL y se "clica" programáticamente
         link.href = url; link.download = "borrador_fiscal_2026.pdf"; link.click()

PASO 5: El navegador abre el diálogo de descarga y guarda el archivo
```

Es como si el frontend creara un "enlace fantasma" que solo existe una fracción de segundo,
el tiempo justo para que el navegador inicie la descarga.

### `reportlab` en 2 minutos

`reportlab` es una librería de Python para generar PDFs programáticamente. En vez de
diseñar el PDF visualmente (como en Word), lo construyes con código:

```python
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.pagesizes import A4

# 1. Creas un "documento" que escribe en un buffer de memoria
doc = SimpleDocTemplate(buffer, pagesize=A4)

# 2. Construyes una lista de "elementos" (párrafos, tablas, espacios)
elements = [
    Paragraph("Título del Informe", style_titulo),
    Table([
        ["Concepto", "Casilla", "Importe"],
        ["Seguros", "0081", "300,00€"],
    ]),
]

# 3. El documento "ensambla" los elementos en páginas PDF
doc.build(elements)
```

Es como construir un documento con piezas de Lego: cada pieza (párrafo, tabla, imagen)
se apila en orden y `reportlab` se encarga de paginar automáticamente.
