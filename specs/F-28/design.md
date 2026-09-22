# 📐 F-28: Onboarding Guiado & Estimador Fiscal Interactivo Multiplataforma — Design

> **Feature ID:** F-28  
> **Título:** Onboarding Guiado & Estimador Fiscal Interactivo Multiplataforma (First-Time User Experience)  
> **Estado:** Borrador — Pendiente de Aprobación Humana  
> **Fecha:** 2026-09-22  
> **Dependencias:** F-06 (Auth/JWT) ✅, F-08 (Multi-tenancy) ✅, F-09 (Datos Fiscales) ✅, F-12 (Motor Fiscal) ✅  

---

## 1. Lenguaje Ubicuo (Términos nuevos)

| Término | Definición | Ejemplo en el proyecto |
|---|---|---|
| **FiscalQuickEstimate** | Value Object inmutable que modela la proyección preliminar de amortización y desgravación en IRPF a partir de datos esenciales de adquisición, sin requerir recibos catastrales detallados. | `FiscalQuickEstimate(purchase_price=Decimal("210000"), ...)` |
| **ConstructionRatio** | Porcentaje legal/orientativo del coste de adquisición atribuible a la construcción (por defecto 0.70 o 70%, estándar urbanístico en España). | `Decimal("0.70")` |
| **OnboardingBootstrapPayload** | Contrato de entrada que agrupa en una única llamada atómica la creación del inmueble, sus datos fiscales estimados y el contrato/suministro inicial. | Payload de `POST /api/onboarding/bootstrap` |
| **OnboardingStatus** | Estado de compleción del proceso de bienvenida del usuario en la plataforma (`completed=True/False`). | `user.onboarding_completed` |
| **Aha! Moment** | Momento psicológico en el que el usuario descubre el beneficio financiero directo de Arrendis: el cálculo instantáneo de los miles de euros anuales que puede amortizar ante Hacienda. | *"~4.410 € / año deducibles en tu Renta"* |

---

## 2. Modelo de Dominio (Python Puro — Cero Dependencias)

### 2.1 Value Object: `FiscalQuickEstimate`

```python
# backend/domain/value_objects.py (NUEVO)

@dataclass(frozen=True)
class FiscalQuickEstimate:
    """Estimación fiscal rápida de amortización según normativa de la AEAT.
    
    Aplica el Art. 23.1.b de la Ley 35/2006 del IRPF:
    Amortización anual = 3% sobre el mayor entre el coste de adquisición 
    satisfecho o el valor catastral (atribuible a la construcción).
    
    En ausencia de desglose catastral exacto, aplica un ratio de construcción
    estándar (default 70% construcción / 30% suelo).
    """
    purchase_price: Decimal
    acquisition_year: int
    construction_ratio: Decimal = Decimal("0.70")
    amortization_rate: Decimal = Decimal("0.03")

    def __post_init__(self) -> None:
        if self.purchase_price <= Decimal("0"):
            raise ValueError("El precio de adquisición debe ser un importe positivo.")
        if self.acquisition_year < 1900 or self.acquisition_year > 2100:
            raise ValueError(f"Año de adquisición fuera de rango válido: {self.acquisition_year}")
        if not (Decimal("0.10") <= self.construction_ratio <= Decimal("0.95")):
            raise ValueError("El ratio de construcción debe situarse entre el 10% y el 95%.")

    @property
    def estimated_construction_value(self) -> Decimal:
        """Valor estimado de la construcción sujeto a amortización."""
        return (self.purchase_price * self.construction_ratio).quantize(Decimal("0.01"))

    @property
    def estimated_land_value(self) -> Decimal:
        """Valor estimado del suelo (no amortizable por ley)."""
        return (self.purchase_price * (Decimal("1.00") - self.construction_ratio)).quantize(Decimal("0.01"))

    @property
    def annual_amortization(self) -> Decimal:
        """Deducción anual por amortización aplicable en el Modelo 100 de IRPF (3%)."""
        return (self.estimated_construction_value * self.amortization_rate).quantize(Decimal("0.01"))

    @property
    def estimated_tax_savings_typical(self) -> Decimal:
        """Ahorro fiscal anual estimado al tipo marginal medio habitual (~30%)."""
        return (self.annual_amortization * Decimal("0.30")).quantize(Decimal("0.01"))
```

### 2.2 Entidad `User` (Modificación de Dominio)

```python
# backend/domain/entities.py (MODIFICAR)

@dataclass
class User:
    """Representa un usuario registrado en la plataforma."""
    email: Email
    password_hash: PasswordHash
    username: str
    forwarding_email: str | None = None
    onboarding_completed: bool = False  # NUEVO CAMPO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

### 2.3 Servicio de Dominio: `FiscalSimulatorService`

```python
# backend/domain/services.py (NUEVO o EXPANDIR)

class FiscalSimulatorService:
    """Servicio de cálculo preliminar y simulación fiscal."""

    @staticmethod
    def simulate_quick_estimate(
        purchase_price: Decimal, 
        acquisition_year: int,
        construction_ratio: Decimal = Decimal("0.70")
    ) -> FiscalQuickEstimate:
        return FiscalQuickEstimate(
            purchase_price=purchase_price,
            acquisition_year=acquisition_year,
            construction_ratio=construction_ratio,
        )
```

---

## 3. Casos de Uso (Capa de Aplicación)

### 3.1 `QuickFiscalEstimateUseCase`
- **Propósito:** Permitir al cliente (web o móvil) simular en tiempo real la amortización y el ahorro antes de comprometerse a crear ningún dato.
- **Entrada:** `purchase_price: Decimal`, `acquisition_year: int`, `construction_ratio: Decimal | None`.
- **Salida:** DTO con `purchase_price`, `estimated_construction_value`, `annual_amortization`, `estimated_tax_savings`, `legal_reference`, `disclaimer`.

### 3.2 `BootstrapOnboardingUseCase`
- **Propósito:** Registrar de forma atómica y consistente el primer inmueble con su configuración fiscal inicial y contrato/suministros opcionales, marcando al usuario con `onboarding_completed = True`.
- **Flujo:**
  1. Validar propiedad y persistir mediante `PropertyRepositoryPort.save(property)`.
  2. Construir `AcquisitionCost` y `CadastralBreakdown` derivados del precio de compra y ratio de construcción (guardando la fecha aproximada `YYYY-01-01`).
  3. Persistir datos fiscales mediante `PropertyRepositoryPort.update_fiscal_data(fiscal_data)`.
  4. Si se especificó renta mensual, crear `LeaseContract` inicial.
  5. Si se especificaron CUPS, actualizar puntos de suministro en la propiedad.
  6. Actualizar `user.onboarding_completed = True` en `UserRepositoryPort`.
  7. Devolver DTO consolidado con la propiedad creada y el resultado fiscal.

### 3.3 `SkipOnboardingUseCase`
- **Propósito:** Permitir al usuario saltar el asistente en cualquier momento.
- **Flujo:**
  1. Invocar `user_repository.update_onboarding_status(user_id=current_user.id, completed=True)`.
  2. Devolver confirmación.

---

## 4. Puertos y Adaptadores (Hexagonal)

### 4.1 Puertos de Persistencia (`backend/domain/ports.py`)

```python
class UserRepositoryPort(ABC):
    # Métodos existentes...
    @abstractmethod
    def update_onboarding_status(self, user_id: str, completed: bool) -> None:
        """Actualiza la bandera de onboarding completado de un usuario."""
        pass
```

### 4.2 Adaptador SQLite (`backend/adapters/sqlite_adapter.py`)

1. **Migración Retrocompatible de Base de Datos:**
   ```sql
   ALTER TABLE users ADD COLUMN onboarding_completed INTEGER NOT NULL DEFAULT 1;
   ```
   *Nota de diseño:* Los usuarios ya existentes en la BD quedan con `1` (completado), para no interrumpir su flujo habitual. Los nuevos registros creados a partir de ahora nacen explícitamente con `0` (pendiente).

2. **Implementación de `update_onboarding_status`:**
   ```python
   def update_onboarding_status(self, user_id: str, completed: bool) -> None:
       cursor = self._conn.cursor()
       cursor.execute(
           "UPDATE users SET onboarding_completed = ? WHERE id = ?",
           (1 if completed else 0, user_id)
       )
       self._conn.commit()
   ```

---

## 5. Contratos de API REST (FastAPI Adapters)

### 5.1 Schemas Pydantic (`backend/api/schemas.py`)

```python
class QuickEstimateRequest(BaseModel):
    purchase_price: Decimal = Field(..., gt=0, description="Precio de compra en euros")
    acquisition_year: int = Field(..., ge=1900, le=2100, description="Año de adquisición")
    construction_ratio: Optional[Decimal] = Field(Decimal("0.70"), ge=Decimal("0.10"), le=Decimal("0.95"))

class QuickEstimateResponse(BaseModel):
    purchase_price: str
    estimated_construction_value: str
    estimated_land_value: str
    annual_amortization: str
    estimated_tax_savings_typical: str
    legal_reference: str
    disclaimer: str

class OnboardingBootstrapRequest(BaseModel):
    property_name: str = Field(..., min_length=1)
    property_type: str = Field(default="apartment")
    street: str = Field(default="Dirección pendiente")
    city: str = Field(default="Ciudad")
    postal_code: str = Field(default="00000")
    country: str = Field(default="España")
    
    # Fiscal simulation inputs (opcionales para el paso 2)
    purchase_price: Optional[Decimal] = Field(None, gt=0)
    acquisition_year: Optional[int] = Field(None, ge=1900, le=2100)
    
    # Rental & supplies inputs (opcionales para el paso 3)
    monthly_rent: Optional[Decimal] = Field(None, gt=0)
    cups_electricity: Optional[str] = None
    cups_gas: Optional[str] = None
    cups_water: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    forwarding_email: Optional[str] = None
    onboarding_completed: bool  # EXPANDIDO
```

### 5.2 Endpoints

| Método | Ruta | Autenticación | Descripción |
|---|---|---|---|
| `POST` | `/api/fiscal/quick-estimate` | Opcional / Requerida | Calcula en vivo la deducción del 3% y ahorro orientativo. |
| `POST` | `/api/onboarding/bootstrap` | Requerida (Bearer) | Crea la propiedad, fiscalidad y contrato en un solo comando atómico. |
| `POST` | `/api/users/me/onboarding/skip` | Requerida (Bearer) | Marca el onboarding como finalizado sin crear inmueble. |
| `GET` | `/api/auth/me` | Requerida (Bearer) | Devuelve el perfil actual incluyendo `onboarding_completed`. |

---

## 6. Diseño de la Experiencia de Usuario (Web & Preparación Móvil)

### 6.1 Estructura del Wizard en Web (`/onboarding`) y Visualización de Valor Real

El wizard vive en una ruta protegida limpia (`/onboarding`) sin la cabecera completa del dashboard, para garantizar enfoque absoluto y cero distracciones:

```
┌────────────────────────────────────────────────────────────────────────┐
│  ARRENDIS                                             Paso [1 | 2 | 3] │
│  REGISTRO PATRIMONIAL                                 [ Omitir guía ]  │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                        │
│   PASO 1: Tu Primer Inmueble                                           │
│   - ¿Cómo llamas a este inmueble? (ej. "Ático en Malasaña")           │
│   - Tipo: [ Piso / Casa / Local / Garaje ]                             │
│   - Ciudad / Ubicación                                                 │
│                                                   [ Siguiente: Fiscal] │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                        │
│   PASO 2: Fiscalidad Oficial · Modelo 100 AEAT                         │
│   ┌── Columna Izq: Parámetros & Cálculo ───┐ ┌── Columna Der: Borrador Oficial ──┐
│   │ Precio adquisición: [ 210.000 € ]      │ │ [Icon: FileText] Modelo 100 AEAT   │
│   │ Año de compra:      [ 2021 ]           │ │                                    │
│   │                                        │ │ [Miniatura 200 DPI Borrador Real]  │
│   │ Amortización anual (3%): ~ 4.410 €/año │ │ - Casilla 0102: Rendimientos       │
│   │ Ahorro estimado IRPF:    ~ 1.323 €/año │ │ - Casilla 0115: Amortización (3%)  │
│   │ Asignado en IRPF:        [Casilla 0131]│ │ - Casilla 0154: Rendimiento Neto   │
│   │                                        │ │ [ Ver Borrador a Pantalla Completa]│
│   └────────────────────────────────────────┘ └────────────────────────────────────┘
│                                                  [ Siguiente: Suministros ]  │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                        │
│   PASO 3: Automatización de Suministros y Facturas                     │
│   ┌── Pilar 1: Buzón Inteligente ──────────┐ ┌── Pilar 2: Drag & Drop PDFs ───────┐
│   │ [Icon: Mail] Reenvío Automático        │ │ [Icon: UploadCloud] Carga Inmediata│
│   │ facturas-carlos@inbound.arrendis.com   │ │ OCR + IA lee fechas, importes y    │
│   │ Se leen y asignan solas con IA.        │ │ CUPS en < 2 segundos.              │
│   └────────────────────────────────────────┘ └────────────────────────────────────┘
│   - Renta mensual que percibes: [ 1.250 € / mes ] (Contrato y Casilla 0102)│
│   - Código CUPS (Opcional): [ ES0031... ]                                  │
│     Pedagogía: "Es el DNI de tu contador para vincular facturas solas."    │
│     [ Botón: "Omitir CUPS por ahora · Se detectará en mi primera factura" ]│
│                                                                            │
│                          [ Atrás ]   [ Finalizar y ver mi Patrimonio ]     │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Estrategia de Reutilización en la Futura App Móvil

Para que el salto al desarrollo móvil sea inmediato y sin refactorizaciones:
1. **Lógica de Estado Headless:** El hook o gestor de estado (`useOnboardingFlow`) maneja únicamente el estado de los pasos y las llamadas a la API REST. No manipula elementos del DOM.
2. **Contratos API idempotentes:** El endpoint `POST /api/onboarding/bootstrap` acepta todos los datos en un único JSON. En redes móviles (donde 3 peticiones HTTP consecutivas pueden fallar a mitad), una sola llamada atómica garantiza consistencia transaccional.
3. **Componentes visuales puros:** Las tarjetas de presentación fiscal (`FiscalEstimateDisplay`) son componentes presentacionales desacoplados de la navegación, lo que facilitará su recreación equivalente en React Native o Flutter.

---

## 7. Especificación de Tests

### 7.1 Tests Unitarios de Dominio (`tests/unit/backend/domain/`)

| Test ID | Archivo | Qué verifica |
|---|---|---|
| **UT-F28-01** | `test_fiscal_quick_estimate.py` | `FiscalQuickEstimate` calcula el 70% de construcción y 3% de amortización correctamente. |
| **UT-F28-02** | `test_fiscal_quick_estimate.py` | Rechaza precios negativos o cero con `ValueError`. |
| **UT-F28-03** | `test_fiscal_quick_estimate.py` | Rechaza años de adquisición fuera de rango (ej. < 1900 o > 2100). |
| **UT-F28-04** | `test_fiscal_quick_estimate.py` | Ratio de construcción configurable (ej. 80%) recalcula adecuadamente suelo y construcción. |
| **UT-F28-05** | `test_entities.py` | Entidad `User` inicializa `onboarding_completed = False` por defecto. |
| **UT-F28-06** | `test_fiscal_simulator_service.py` | `FiscalSimulatorService.simulate_quick_estimate()` produce el VO esperado. |

### 7.2 Tests de Integración (`tests/integration/`)

| Test ID | Archivo | Qué verifica |
|---|---|---|
| **IT-F28-01** | `test_sqlite_user_onboarding.py` | `update_onboarding_status` actualiza el valor en SQLite y se recupera correctamente en `get_by_id`. |
| **IT-F28-02** | `test_sqlite_user_onboarding.py` | La migración automática añade la columna `onboarding_completed` con default 1 a tablas preexistentes. |
| **IT-F28-03** | `test_bootstrap_onboarding_use_case.py` | El caso de uso crea la propiedad, sus datos fiscales derivados, su contrato opcional y actualiza al usuario a `onboarding_completed=True`. |
| **IT-F28-04** | `test_skip_onboarding_use_case.py` | El caso de uso de omisión actualiza al usuario a `onboarding_completed=True` sin crear inmuebles. |

### 7.3 Tests de API / Endpoints (`tests/unit/backend/api/`)

| Test ID | Archivo | Qué verifica |
|---|---|---|
| **API-F28-01** | `test_fiscal_quick_estimate_api.py` | `POST /api/fiscal/quick-estimate` devuelve 200 y JSON con cálculos formateados. |
| **API-F28-02** | `test_fiscal_quick_estimate_api.py` | `POST /api/fiscal/quick-estimate` devuelve 422 si el precio es <= 0. |
| **API-F28-03** | `test_onboarding_bootstrap_api.py` | `POST /api/onboarding/bootstrap` con token JWT válido crea los recursos y devuelve 201. |
| **API-F28-04** | `test_onboarding_bootstrap_api.py` | `POST /api/onboarding/bootstrap` sin token devuelve 401 Unauthorized. |
| **API-F28-05** | `test_onboarding_skip_api.py` | `POST /api/users/me/onboarding/skip` marca completado y devuelve 200. |

---

## 8. Resumen de Archivos a Crear / Modificar

| Archivo | Acción | Propósito |
|---|---|---|
| `backend/domain/value_objects.py` | **Modificar** | Añadir `FiscalQuickEstimate` Value Object. |
| `backend/domain/entities.py` | **Modificar** | Añadir campo `onboarding_completed` a la entidad `User`. |
| `backend/domain/services.py` | **Modificar** | Añadir `FiscalSimulatorService`. |
| `backend/domain/ports.py` | **Modificar** | Añadir `update_onboarding_status()` a `UserRepositoryPort`. |
| `backend/application/use_cases.py` | **Modificar** | Añadir `QuickFiscalEstimateUseCase`, `BootstrapOnboardingUseCase`, `SkipOnboardingUseCase`. |
| `backend/adapters/sqlite_adapter.py` | **Modificar** | Migración SQLite (`onboarding_completed`) e implementación de métodos de persistencia. |
| `backend/api/schemas.py` | **Modificar** | Añadir DTOs de estimación rápida y bootstrap de onboarding. Extender `UserResponse`. |
| `backend/api/routes/fiscal.py` | **Modificar** | Añadir endpoint `POST /api/fiscal/quick-estimate`. |
| `backend/api/routes/onboarding.py` | **Crear** | Añadir endpoints `POST /api/onboarding/bootstrap` y `POST /api/users/me/onboarding/skip`. |
| `frontend/src/types/index.ts` | **Modificar** | Interfaces TypeScript para estimación rápida, bootstrap y estado de usuario. |
| `frontend/src/services/api.ts` | **Modificar** | Funciones clientes para consumir los nuevos endpoints. |
| `frontend/src/pages/Onboarding.tsx` | **Crear** | Página editorial interactiva de 3 pasos con estimador en vivo. |
| `frontend/src/App.tsx` | **Modificar** | Enrutamiento protegido para `/onboarding` y redirección automática si `!user.onboarding_completed`. |

---

## 📚 El Rincón del Estudiante

### ¿Por qué calcular la simulación fiscal en el Backend en vez de calcularla en React?

Cuando programamos para la web, es muy tentador hacer esto en el frontend:
```typescript
// ❌ Mala práctica: duplicar la lógica fiscal en el componente React
const amortizacion = precio * 0.70 * 0.03;
```
Parece inocuo porque es una sola multiplicación, pero viola los principios fundamentales de la arquitectura:
1. **La app móvil tendría que repetir el código:** Cuando creemos la app en Flutter o React Native, tendríamos que volver a escribir esa misma fórmula en Dart o TypeScript móvil. Si la AEAT cambia el criterio, o si queremos afinar los tramos del IRPF, tendríamos que actualizar la web y lanzar una actualización a la App Store y Google Play.
2. **Single Source of Truth (Fuente Única de Verdad):** La ley fiscal y las reglas de negocio pertenecen al **Dominio** del backend. El cliente (ya sea un navegador, un iPhone o una llamada de test) es un simple terminal de presentación.
3. **Consistencia numérica y tipos monetarios:** En JavaScript, `0.1 + 0.2 = 0.30000000000000004` (problemas de punto flotante IEEE 754). En Python usamos `Decimal` con redondeo bancario estricto (`quantize`), garantizando que tanto en la simulación como en el informe oficial el céntimo cuadre al 100%.

### Analogía del Mundo Real: La Cocina Central y las Ventanillas

Imagina una prestigiosa pastelería. Tienen dos puntos de atención al cliente:
- Un **salón elegante de té** (nuestra Web en escritorio).
- Una **ventanilla rápida para ciclistas y peatones** (nuestra futura App móvil).

```
 ┌──────────────────────┐         ┌──────────────────────┐
 │   Salón de Té (Web)  │         │  Ventanilla (Móvil)  │
 └──────────┬───────────┘         └──────────┬───────────┘
            │                                │
            │   Piden la misma tarta        │
            └───────────────┬────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   COCINA CENTRAL (API)    │
              │  Receta canónica del chef │
              └───────────────────────────┘
```

Si cada camarero del salón intentara hornear su propia tarta con su propia receta improvisada, la tarta sabría distinta según dónde te sientes. 
Al centralizar la receta en la cocina central (el backend de dominio), garantizamos que la tarta sabe exactamente igual tanto si la tomas en la mesa como si te la llevas en la bicicleta.

### Comparativa: Enfoque "Frontend-Heavy" vs Enfoque "API-First Hexagonal"

| Criterio | Frontend-Heavy (Lógica en React) ❌ | API-First Hexagonal (Lógica en Backend) ✅ |
|---|---|---|
| **Lanzamiento de App Móvil** | Obliga a reescribir y testear toda la matemática fiscal en el código móvil. | La app móvil solo dibuja los datos devueltos por `/api/fiscal/quick-estimate`. |
| **Mantenimiento legal (AEAT)** | Cambios en dos sitios distintos con riesgo de discrepancias. | Se actualiza una sola vez en `backend/domain/value_objects.py`. |
| **Resiliencia en redes inestables** | 3-4 peticiones consecutivas desde el móvil que pueden fallar a mitad. | Un solo endpoint `bootstrap` atómico transaccional. |
| **Testabilidad** | Requiere tests pesados de componentes UI para validar números. | Se valida con tests unitarios instantáneos en `pytest` (< 5ms). |

### ¿Qué es el "Bootstrapping Atómico" y por qué es crítico en Móvil?

En la web, con fibra óptica o Wi-Fi estable, podemos permitirnos hacer:
`POST /api/properties` ➡️ `POST /api/fiscal-data` ➡️ `POST /api/contracts` ➡️ `PUT /api/cups`.

Pero en un teléfono móvil con cobertura 4G/5G intermitente (por ejemplo, en un ascensor o un tren):
- Si la llamada 1 funciona pero la 2 falla por corte de red, el usuario queda en un **estado zombi**: tiene un inmueble creado pero sin datos fiscales ni contrato, y el wizard se cuelga.
- Con el endpoint atómico `POST /api/onboarding/bootstrap`, el cliente envía todo el paquete en una sola petición. La base de datos SQLite procesa todo dentro de una misma transacción. Si la conexión se corta, no se queda nada corrupto ni a medias.
