# 🔬 Informe de Análisis de Disyuntivas — Épica E-02: Automatización de Suministros

> **Versión:** 1.0  
> **Fecha:** 2026-08-04  
> **Método:** Análisis técnico a partir de inspección real de factura de muestra + investigación de servicios  
> **Factura analizada:** [`factura_ejemplo_1.pdf`](file:///home/carlos/rental-handler/specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf) (Repsol Electricidad, julio 2026)

---

## 📄 Resultado de la Inspección del PDF de Muestra

### Texto extraído con PyMuPDF — Hallazgos clave

PyMuPDF extrae **texto limpio, con estructura lineal y bien delimitada** de esta factura de Repsol. La factura tiene **4 páginas** y el texto es vectorial (no escaneado), lo cual es óptimo.

#### Campos críticos detectados y su posición

| Campo | Valor encontrado | Página | Método de localización |
|---|---|---|---|
| **CUPS** | `ES0031103721971011PR0F` | Pág. 1 | Línea siguiente a la etiqueta literal `"CUPS"` |
| **Total factura** | `75,46 €` | Pág. 1 y 2 | Línea siguiente a `"Total factura"` |
| **Fecha de emisión** | `01/08/2026` | Pág. 1 | Línea siguiente a `"Fecha de emisión"` |
| **Periodo de facturación** | `28/06/2026 - 28/07/2026` | Pág. 1 | Línea siguiente a `"Periodo de facturación"` |
| **Nº de factura** | `61088387754` | Pág. 1 y 3 | Línea siguiente a `"Nº de factura"` |
| **Comercializadora** | `Repsol Comercializadora de Electricidad y Gas, S.L.U.` | Pág. 3 | Línea siguiente a `"Comercializadora"` |
| **Nº de contrato** | `4305565356` | Pág. 1 y 3 | Línea siguiente a `"Nº de contrato"` |
| **Titular** | `Alvaro Heredia Casado` | Pág. 1 y 3 | Línea siguiente a encabezado |
| **DNI** | `53918290B` | Pág. 3 | Línea siguiente a `"DNI"` |
| **Cuenta bancaria** | `*3940` (parcialmente enmascarada) | Pág. 3 | Línea siguiente a `"Cuenta bancaria"` |
| **Tipo de suministro** | Electricidad | Pág. 1 | Título del documento: `"Factura de luz"` |
| **Consumo** | `354,50 kWh` | Pág. 1 | Línea siguiente a `"Consumo en este periodo"` |

### Estructura del texto extraído (patrón etiqueta-valor)

El texto de PyMuPDF sigue un patrón **etiqueta en línea N → valor en línea N+1**, que es extremadamente favorable para Regex:

```
CUPS
ES0031103721971011PR0F
Nº de contrato
4305565356
Nº de factura
61088387754
Fecha de emisión
01/08/2026
...
Total factura
75,46 €
```

> [!IMPORTANT]
> Este patrón `etiqueta\nvalor` es la clave. No es un formato tabular confuso ni texto libre — es una secuencia lineal predecible que hace que la Vía A (Regex) sea **altamente viable** para esta comercializadora.

### Datos personales detectados (relevante para GDPR)

| Dato personal | Presente | Ejemplo |
|---|---|---|
| Nombre completo | ✅ | `Alvaro Heredia Casado` |
| DNI/NIF | ✅ | `53918290B` |
| Dirección postal | ✅ | `CL FRANK CAPRA 4 3 6 A 29010 MÁLAGA` |
| IBAN / Cuenta bancaria | ⚠️ Parcial | `*3940` (ya enmascarado por Repsol) |

---

## 🔬 Disyuntiva 1: Regex (Vía A) vs. IA Generativa (Vía B)

### Veredicto: **Estrategia Híbrida con Fallback — Vía A primaria, Vía B de respaldo**

### Análisis detallado

#### ✅ Viabilidad de la Vía A (Regex) — ALTA para esta factura

La estructura de texto de Repsol es **altamente predecible**:

```python
# Ejemplo de extracción por Regex para Repsol
import re

def extract_repsol(text: str) -> dict:
    """Extrae datos de factura Repsol con patrón etiqueta\\nvalor."""
    def after_label(label: str) -> str | None:
        match = re.search(rf'{re.escape(label)}\n(.+)', text)
        return match.group(1).strip() if match else None

    cups = after_label("CUPS")
    total_match = re.search(r'Total factura\n([\d.,]+)\s*€', text)
    fecha = after_label("Fecha de emisión")
    nfactura = after_label("Nº de factura")
    
    return {
        "cups": cups,
        "amount": total_match.group(1) if total_match else None,
        "issue_date": fecha,
        "invoice_number": nfactura,
    }
```

**Resultado del Regex sobre la muestra:**
- 🟢 CUPS: `ES0031103721971011PR0F` ✓
- 🟢 Total: `75,46` ✓  
- 🟢 Fecha emisión: `01/08/2026` ✓
- 🟢 Nº factura: `61088387754` ✓
- 🟢 Comercializadora: `Repsol` (detectable por presencia de la palabra en el texto) ✓

**Tasa de éxito en la muestra: 100%**

#### ⚠️ Riesgos conocidos de la Vía A

1. **Cada comercializadora tiene un formato diferente.** Endesa, Iberdrola, Naturgy y Aqualia pueden usar layouts y etiquetas distintos. No podemos generalizar de 1 muestra.
2. **Cambios de diseño.** Si Repsol rediseña su PDF, las reglas se rompen silenciosamente.
3. **Mantenimiento acumulativo.** Con N comercializadoras, se mantienen N conjuntos de reglas.

#### 🤖 Cuándo se activaría la Vía B (IA / Gemini Flash)

Solo como **fallback** cuando:
- El CUPS extraído por Regex no tiene formato válido (`ES` + 16-18 dígitos + 0-2 letras).
- No se encuentra la etiqueta `"Total factura"` o el importe es negativo/absurdo.
- La comercializadora no está en el registro de parsers Regex conocidos.

#### Límites del Free Tier de Gemini Flash (suficientes para este caso de uso)

| Límite | Free Tier | Necesidad estimada* |
|---|---|---|
| Requests/día | ~1.500 RPD | ~3-10 facturas/día/propietario |
| Requests/minuto | ~10-15 RPM | No es batch masivo |
| Coste | $0 | $0 |

*\*Para un propietario con 5 pisos × 3 suministros (luz, agua, gas) = 15 facturas/mes = 0,5/día. Incluso con 50 propietarios: 750/mes ≈ 25/día. Holgadísimo.*

> [!WARNING]
> **Nota GDPR:** El free tier de Gemini permite a Google usar el contenido para mejorar sus productos. Si se envía texto con datos personales, esto podría constituir una transferencia no consentida bajo GDPR. → Refuerza la necesidad del **Scrubbing de Privacidad** (ver Disyuntiva 3).

### Decisión Arquitectónica Recomendada

```
┌──────────────────────────────────────────────────────────┐
│                  ProcessUtilityInvoice                    │
│                                                          │
│  1. PyMuPDF → texto plano                                │
│  2. Detectar comercializadora (keyword matching)         │
│  3. ¿Parser Regex disponible en ExtractorRegistry?       │
│     ├─ SÍ → RegexExtractionStrategy(provider)           │
│     │    └─ ¿Resultado válido? (CUPS ok, importe > 0)   │
│     │       ├─ SÍ → Usar resultado (Confianza: ALTA)    │
│     │       └─ NO → Fallback a AIExtractionStrategy      │
│     └─ NO → AIExtractionStrategy (LLMProviderPort)       │
│            └─ (Confianza: MEDIA / IA Mode)               │
│  4. Matching CUPS → Property                             │
│  5. Crear PendingReviewExpense (is_verified = False)     │
└──────────────────────────────────────────────────────────┘
```

### 🧪 Estrategia de Corpus Multi-Comercializadora y Test Suite Empírica (F-18)

Para garantizar la robustez del sistema frente a la diversidad de comercializadoras en España (Endesa, Iberdrola, Naturgy, Repsol, Aqualia, TotalEnergies, Holaluz, etc.), la implementación de **F-18** debe contemplar explícitamente:

1. **Directorio de Fixtures Extensible:**  
   La carpeta `specs/epics/E-02-suministros/samples/` (y su réplica en `tests/fixtures/receipts/`) servirá como corpus vivo de pruebas. Cada nueva factura aportada por los usuarios se integrará como un caso de prueba anonimizado.

2. **Registro de Estrategias Desacoplado (`UtilityExtractorRegistry`):**  
   Basado en el principio de Abierto/Cerrado (SOLID Open-Closed Principle). Añadir soporte optimizado por Regex para una nueva comercializadora consiste en implementar una nueva clase (ej. `EndesaExtractorStrategy`) y agregarla al registro con su palabra clave de detección.

3. **Garantía de Fallback Universal vía LLM:**  
   Cualquier factura perteneciente a una compañía sin regla Regex específica o cuyo PDF haya sufrido un rediseño de maquetación pasará automáticamente a la `AIExtractionStrategy` (consumiendo `LLMProviderPort` de **F-17**). De este modo, la aplicación no falla ni rechaza facturas desconocidas.

4. **Suite de Test de Regresión Empírica:**  
   El plan de pruebas de F-18 incluirá `tests/integration/test_utility_extraction_corpus.py`, un test parametrizado que recorrerá **todos los archivos PDF presentes en la carpeta de muestras**, validando la correcta extracción de `CUPS`, `amount`, `date` e `invoice_number`, y reportando el porcentaje de resolución por Regex local vs. Fallback de IA.

---

## 💾 Disyuntiva 2: Almacenamiento Documental (Object Storage)

### Veredicto: **Disco Local del VPS (fase 1) con migración preparada a Cloudflare R2 (fase 2)**

### Análisis comparativo

| Criterio | Disco Local VPS | Cloudflare R2 | S3 Free Tier | SQLite BLOB |
|---|---|---|---|---|
| **Coste** | $0 (usa disco existente) | $0 (10 GB gratis permanente) | $0 solo 12 meses | $0 |
| **Egreso (descargas)** | $0 (se sirve desde el backend) | $0 (sin costes de egreso) | $0.09/GB (caro) | $0 |
| **Persistencia** | Depende del VPS | Permanente, distribuido | Permanente | BD se puede corromper |
| **Backups** | Manual | Incluido | Configurable | Incluido en backup de BD |
| **Complejidad de integración** | Mínima (`Path.write_bytes()`) | Media (SDK S3-compatible) | Media (boto3) | Baja |
| **Escalabilidad** | Limitada al disco | 10 GB gratis → luego $0.015/GB | 5 GB gratis → luego $0.023/GB | ⛔ No recomendado |
| **URLs firmadas para descarga** | Requiere endpoint propio | Sí, nativo | Sí, nativo | No aplica |

### Cálculo de espacio necesario

Factura de muestra: **~556 KB**. Estimación conservadora con varias comercializadoras: **~200-500 KB por factura.**

| Escenario | Facturas/año | Espacio/año | En 5 años (retención AEAT) |
|---|---|---|---|
| 1 propietario, 3 suministros | 36 | ~14 MB | ~72 MB |
| 10 propietarios, 3 suministros | 360 | ~144 MB | ~720 MB |
| 50 propietarios, 3 suministros | 1.800 | ~720 MB | ~3.6 GB |

> [!NOTE]
> Incluso en el escenario más exigente (50 propietarios), 5 años de retención consumen **3.6 GB** — dentro de la capa gratuita de Cloudflare R2 (10 GB) y perfectamente manejable en disco local.

### Decisión Recomendada (en dos fases)

**Fase 1 (MVP):** Almacenamiento en disco local del servidor.
- Ruta: `data/receipts/{property_id}/{year}/{filename}.pdf`
- Servido desde un endpoint FastAPI protegido: `GET /api/receipts/{expense_id}/download`
- Backup incluido en el backup general del VPS.
- Zero dependencias externas.

**Fase 2 (escala):** Migración a Cloudflare R2 cuando el disco local supere ~5 GB o se necesiten URLs firmadas con CDN.
- La migración es transparente gracias a la Arquitectura Hexagonal: solo se cambia el adaptador (`LocalFileStorageAdapter` → `CloudflareR2StorageAdapter`). El puerto `ReceiptStoragePort` no cambia.

### Política de Retención Documental

```python
# Regla de purgado automático
RETENTION_YEARS = 5  # Plazo de prescripción AEAT

# Cron job mensual:
# DELETE receipts WHERE date < now() - 5 years
# + eliminar archivo físico del disco/R2
```

---

## 🔒 Disyuntiva 3: Privacidad y Cumplimiento GDPR

### Veredicto: **Capa de Scrubbing obligatoria antes de enviar texto a la Vía B (IA)**

### Datos personales encontrados en la factura de muestra

| Dato | Presente | Necesario para la extracción | Acción |
|---|---|---|---|
| Nombre (`Alvaro Heredia Casado`) | ✅ | ❌ No | **Eliminar** |
| DNI (`53918290B`) | ✅ | ❌ No | **Eliminar** |
| Dirección postal | ✅ | ❌ No | **Eliminar** |
| IBAN / Cuenta (`*3940`) | ⚠️ Parcial | ❌ No | **Eliminar** |
| CUPS | ✅ | ✅ SÍ | **Conservar** |
| Importes y fechas | ✅ | ✅ SÍ | **Conservar** |
| Consumo kWh | ✅ | ⚠️ Útil | **Conservar** |

### Estrategia de Scrubbing recomendada

**No enviar el texto completo al LLM.** Aplicar un filtro previo que:

1. **Elimine líneas por patrón** (nombres, NIF, direcciones, IBANs).
2. **Conserve solo las secciones relevantes:** `CUPS`, `Total factura`, `Fecha de emisión`, `Periodo de facturación`, `Nº de factura`, `Comercializadora`, desglose de conceptos.

```python
# Pseudocódigo del Privacy Scrubber
REDACT_PATTERNS = [
    r'\d{8}[A-Z]',                           # NIF persona física
    r'[A-Z]\d{8}',                           # CIF persona jurídica  
    r'ES\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{10}',  # IBAN completo
    r'\*\d{4}',                              # Cuenta enmascarada
]

REDACT_LABELS = [
    "Nombre y Apellidos",
    "DNI", 
    "Dirección postal",
    "Cuenta bancaria",
    "Localizador de pago",
]

def scrub_text(raw_text: str) -> str:
    """Elimina datos personales del texto antes de enviarlo al LLM."""
    lines = raw_text.split('\n')
    cleaned = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if any(label.lower() in line.lower() for label in REDACT_LABELS):
            skip_next = True  # saltar la línea de valor siguiente
            continue
        # Redactar patrones inline
        for pattern in REDACT_PATTERNS:
            line = re.sub(pattern, '[REDACTED]', line)
        cleaned.append(line)
    return '\n'.join(cleaned)
```

> [!TIP]
> Como la Vía B (IA) es solo un **fallback**, en la práctica se invocará raramente. La mayoría de facturas de comercializadoras conocidas se resolverán con Regex local (Vía A), sin enviar nada al exterior.

---

## 📩 Disyuntiva 4: Mecanismo de Ingesta de Correo

### Veredicto: **Subida manual de PDF (fase 1) → Inbound Parse Webhook con buzón virtual por usuario/inmueble (fase 2)**

### Análisis de opciones

| Criterio | IMAP Polling (Lectura directa buzón usuario) | Inbound Parse Webhook (SendGrid, Mailgun, Postmark, Cloudflare) |
|---|---|---|
| **Compliance & Seguridad** | ⛔ Crítico: Exige permisos intrusivos (`gmail.readonly` requiere auditoría CASA de 15k-75k$) | 🟢 Cero fricción: El usuario no cede acceso a su cuenta personal |
| **Confianza del Usuario** | ❌ Baja (nadie quiere dar acceso a su bandeja personal) | 🟢 Alta (el usuario solo reenvía a una dirección dedicada) |
| **Complejidad de setup** | Media (gestión de contraseñas de aplicación/OAuth) | Baja/Media (configurar MX y endpoint webhook) |
| **Coste** | $0 inicial, pero caro en consumo de polling a escala | $0 (tiers gratuitos en Cloudflare Email Routing / SendGrid / Mailgun) |
| **Latencia / Eficiencia** | Polling periódico (inmeficiente a escala) | Tiempo real (Event-Driven, push inmediato) |
| **Multi-tenancy** | Muy complejo y propenso a bloqueos por rate-limit | 🟢 Nativo: Subdirecciones o subdominios únicos por usuario (`facturas+{user_id}@...`) |

### Arquitectura de Multi-tenancy en la Ingesta (Fase 2)

**Buzón virtual con identificador único (Inbound Parse Webhook):**
- A cada usuario o propiedad se le asigna un alias/correo de ingesta (ej. `facturas+{user_id}@rental-handler.com` o `inmueble-123@inbound.rental-handler.com`).
- El usuario configura en su comercializadora (o regla de reenvío en su correo) el envío a esa dirección.
- El proveedor transaccional (SendGrid / Mailgun / Cloudflare Email Routing) recibe el correo y dispara un `POST` al endpoint webhook `/api/v1/webhooks/incoming-email` con el payload y el PDF adjunto.
- El webhook valida la firma, guarda el PDF y delega la ejecución al caso de uso `ProcessUtilityInvoiceUseCase` (síncrono o vía cola/worker asíncrono).

### Decisión Recomendada

**Fase 1 (MVP actual):** Subida manual del PDF desde la interfaz web.
- El propietario sube el archivo PDF directamente desde su área de propiedades.
- El backend aplica el pipeline completo de extracción (PyMuPDF → Regex/IA → matching CUPS → PendingReviewExpense).
- Esto permite validar el 100% de la lógica de dominio y motor de parsing con **cero complejidad de infraestructura de correos**.

**Fase 2 (ingesta desatendida):** Inbound Parse Webhook con buzón dedicado por usuario. Se descarta definitivamente el polling IMAP directo a cuentas de usuario.

> [!IMPORTANT]
> Esta decisión de **empezar con subida manual de PDF** en lugar de ingesta IMAP reduce drásticamente el alcance de la primera iteración. El valor diferencial de la épica (automatizar el parseo del PDF y extraer datos estructurados) se mantiene intacto. La ingesta por correo se convierte en una mejora incremental posterior.

---

## 👤 Disyuntiva 5: Flujo UX de Validación Humana (Human-in-the-Loop)

### Veredicto: **Estado `PENDING_REVIEW` con panel de revisión y confirmación 1-click**

### Cambios necesarios en el modelo de dominio actual

La entidad `Expense` actual ([entities.py](file:///home/carlos/rental-handler/backend/domain/entities.py#L207-L236)) no tiene concepto de verificación ni de recibo adjunto. Se necesitan dos ampliaciones:

#### 1. Nuevos campos en la entidad `Expense`

```python
@dataclass
class Expense:
    property_id: str
    amount: Money
    date: date
    category: ExpenseCategory
    description: str = ""
    fiscal_category: FiscalExpenseCategory | None = None
    # --- NUEVOS CAMPOS E-02 ---
    is_verified: bool = True            # True para gastos manuales, False para gastos auto-importados
    receipt_path: str | None = None      # Ruta relativa al PDF del recibo almacenado
    source: ExpenseSource = ExpenseSource.MANUAL  # Origen del gasto
    utility_data: UtilityInvoiceData | None = None  # Datos extraídos del suministro (solo si source=AUTO_IMPORT)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

#### 2. Nuevo enum `ExpenseSource`

```python
class ExpenseSource(Enum):
    MANUAL = "manual"            # Introducido a mano por el usuario
    AUTO_IMPORT = "auto_import"  # Importado automáticamente desde un PDF
```

#### 3. Nuevo campo `cups` en la entidad `Property`

```python
@dataclass
class Property:
    # ... campos existentes ...
    cups_electricity: str | None = None   # CUPS de electricidad
    cups_gas: str | None = None           # CUPS de gas  
    cups_water: str | None = None         # Código contrato de agua (no siempre CUPS)
```

### Flujo UX propuesto

```
┌─────────────────────────────────────────────────────────┐
│  PANEL DE GASTOS PENDIENTES DE REVISIÓN                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ⚡ Factura de luz — Repsol       28/07/2026     │    │
│  │                                                  │    │
│  │  Propiedad:  Piso Calle Frank Capra 4 [auto]    │    │
│  │  Importe:    75,46 €    [editable]              │    │
│  │  Categoría:  Suministro [auto]                  │    │
│  │  CUPS:       ES0031103721971011PR0F             │    │
│  │  Nº Factura: 61088387754                        │    │
│  │                                                  │    │
│  │  [📄 Ver PDF]  [✅ Confirmar]  [✏️ Editar]  [🗑️] │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Confianza de extracción: ██████████░ 95% (Regex)       │
└─────────────────────────────────────────────────────────┘
```

**Reglas de negocio:**
1. Un gasto con `is_verified = False` **NO** computa en el cálculo fiscal (`FiscalReport`) ni en el rendimiento neto de la propiedad.
2. Al confirmar (`is_verified = True`), el gasto pasa al flujo normal y queda incluido en futuros borradores fiscales.
3. Se muestra un indicador de **confianza de extracción** (basado en si se usó Regex vs. IA, y si todos los campos se extrajeron con éxito).

---

## 📋 Resumen Ejecutivo de Decisiones

| # | Disyuntiva | Decisión |
|---|---|---|
| **1** | Regex vs. IA | **Híbrido con Fallback:** Regex local primero (por comercializadora conocida), IA (Gemini Flash free tier) como respaldo. Patrón Strategy + Fallback. |
| **2** | Almacenamiento de PDFs | **Fase 1: Disco local** (`data/receipts/`), servido por endpoint FastAPI. **Fase 2: Cloudflare R2** (10 GB gratis, $0 egreso). Puerto `ReceiptStoragePort` con adaptadores intercambiables. Política de purgado: 5 años. |
| **3** | GDPR / Privacidad | **Scrubbing obligatorio** antes de enviar a Vía B. Eliminar NIFs, nombres, direcciones, IBANs. Conservar solo CUPS, importes, fechas y conceptos. |
| **4** | Ingesta de correo | **Fase 1: Subida manual de PDF** desde la interfaz web (zero infraestructura). **Fase 2: Inbound Parse Webhook** con buzón dedicado por usuario (`facturas+{user_id}@...`). Se descarta IMAP directo por compliance y escalabilidad. |
| **5** | Validación humana | **Estado `is_verified = False`** para gastos auto-importados. Panel de revisión con vista previa del PDF, campos editables y confirmación 1-click. Los gastos no verificados no computan en borradores fiscales. |

---

## 🔄 Backlog Revisado de Features (Post-Análisis)

Tras el análisis, se recomienda **reenfocar las features** para reflejar la decisión de empezar con subida manual de PDF (no IMAP):

| ID | Título Revisado | Estado | Notas |
|---|---|---|---|
| **F-16** | Modelo de Dominio de Suministros: CUPS en Property, `is_verified` y `receipt_path` en Expense, `UtilityInvoiceData` VO | `backlog` | Base para todo lo demás |
| **F-17** | Puerto y Adaptador Genérico de LLM (`LLMProviderPort` + `GeminiFlashAdapter`) | `backlog` | Infraestructura transversal reutilizable |
| **F-18** | Motor de Extracción de Datos: PyMuPDF + Strategy Pattern (Regex Repsol + Gemini Flash Fallback) + Privacy Scrubber | `backlog` | Núcleo del pipeline |
| **F-19** | Almacenamiento Documental de Recibos PDF y Política de Retención 5 años | `deferred` | Disco local fase 1, Cloudflare R2 fase 2 |
| **F-20** | Interfaz UI: Subida Manual de PDF, Panel de Gastos Pendientes y Confirmación | `backlog` | La ingesta manual valida el pipeline en fase 1 |
| **F-21** | Ingesta Automática por Email: Inbound Parse Webhook (SendGrid/Mailgun/Cloudflare) | `deferred` | Fase 2, buzón dedicado por usuario sin acceso a buzones personales |
