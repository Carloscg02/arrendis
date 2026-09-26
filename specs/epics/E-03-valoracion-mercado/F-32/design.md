# F-32: Interfaz UI de Estimación de Mercado, Explicabilidad de Factores y Fuentes (Atelier)

## 1. Visión y Objetivos

La Feature **F-32** dota al frontend de Arrendis de un panel analítico y editorial (*Atelier Editorial*) integrado en la vista de detalle de propiedad (`PropertyDetail.tsx`).

Objetivos principales:
1. **Transparencia Radical (Explainable AI):** Presentar con nitidez las horquillas de venta y alquiler mensual, rentabilidad bruta estimada (*Gross Rental Yield*), nivel de confianza, factores correctores ponderados y testigos de búsqueda web reales con enlaces externos verificables.
2. **Control de Cooldown y Acción Bajo Demanda:** Informar al usuario del estado de enfriamiento de la estimación ("Próxima actualización en X días"), permitiendo forzar el recálculo mediante confirmación explícita cuando haya habido reformas o cambios en el mercado.
3. **Desbloqueo de Inmuebles sin Metros Cuadrados:** Proveer un modal integrado de edición de atributos físicos (`PhysicalAttributesModal`) para que el usuario pueda registrar o corregir la superficie y características de su vivienda directamente desde el panel sin abandonar el flujo.
4. **Manejo Elegante de Latencia:** Proporcionar estados de carga animados con mensajes contextuales durante los 10-15 segundos que toma la síntesis en tiempo real con Google Search Grounding.

---

## 2. Componentes y Arquitectura Frontend

### 2.1 Actualización de Tipos (`frontend/src/types/index.ts`)
```typescript
export interface PropertyValuation {
  id: string;
  property_id: string;
  valuation_date: string;
  sale_range: ValuationRange;
  rent_range: ValuationRange;
  confidence: ValuationConfidence;
  reasoning_factors: ReasoningFactor[];
  sources: ValuationSource[];
  raw_notes?: string | null;
  cooldown_days_remaining?: number;
  is_cached?: boolean;
}
```

### 2.2 Servicio API (`frontend/src/services/api.ts`)
```typescript
export async function requestValuation(propertyId: string, force: boolean = false): Promise<PropertyValuation> {
  const query = force ? "?force=true" : "";
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/valuation${query}`, {
    method: "POST",
  });
  return handleResponse<PropertyValuation>(res);
}
```

### 2.3 Helper de Formateo de Factores
Ubicación: `frontend/src/utils/formatters.ts` o inline en el componente:
```typescript
export function formatFactorPercent(impact: number): string {
  const val = Math.abs(impact) <= 1.0 ? impact * 100 : impact;
  const sign = val > 0 ? "+" : "";
  return `${sign}${val.toFixed(1)}%`;
}
```

### 2.4 Modal de Atributos Físicos: `PhysicalAttributesModal.tsx`
Ubicación: `frontend/src/components/PhysicalAttributesModal.tsx`.
- Formulario modal con campos para:
  - `surface_m2` (número entero > 0, obligatorio)
  - `bedrooms` (número >= 0)
  - `bathrooms` (número >= 0)
  - `floor` (número)
  - `has_elevator` (selector Sí / No)
  - `condition` (selector: `A reformar`, `Buen estado`, `Reformado`, `A estrenar`)
- Al guardar: invoca `updatePropertyPhysicalAttributes` de `api.ts`, notifica mediante toast, cierra el modal y dispara `onSaved(updatedProperty)`.

### 2.5 Componente Principal: `MarketValuationPanel.tsx`
Ubicación: `frontend/src/components/MarketValuationPanel.tsx`.

#### Ciclo de Vida y Máquina de Estados:
1. **Montaje (`useEffect`):**
   - Ejecuta `getLatestValuation(property.id)`.
   - Si existe valoración: pobla el estado `valuation` y muestra el informe con badge de cooldown.
   - Si no existe: mantiene `valuation = null` y muestra el estado inicial *hero*.
2. **Estado Faltan Atributos (`!property.surface_m2`):**
   - Muestra un banner destacado indicando que la valoración requiere conocer la superficie construida del inmueble.
   - Botón primario: *"Completar características físicas"* que abre `PhysicalAttributesModal`.
3. **Estado Hero Vacío (con superficie pero sin valoración previa):**
   - Bloque explicativo Atelier: *"Descubre el valor de mercado y la renta potencial de tu propiedad analizando testigos comparables en tiempo real."*
   - Botón de acción: *"Solicitar primera estimación"*.
4. **Estado Calculando (`isCalculating === true`):**
   - Botón en estado de carga (spinner `Loader2`).
   - Caja de estado animada con mensaje de progreso: *"Consultando portales inmobiliarios y testigos en tiempo real... (suele tardar 10-15s)"*.
5. **Estado de Valoración Cargada:**
   - **Hero Cards:**
     - **Venta estimada:** Horquilla Mínimo - Mediano - Máximo en euros.
     - **Renta orientativa mensual:** Horquilla Mínimo - Mediano - Máximo en euros/mes.
     - **Rentabilidad Bruta Teórica (Yield):**
       $$\text{Yield} = \frac{\text{renta\_mediana} \times 12}{\text{venta\_mediana}} \times 100$$
   - **Badge de Confianza:**
     - `Alta`: Verde esmeralda (`#059669`)
     - `Media`: Ámbar (`#d97706`)
     - `Baja`: Pizarra (`#64748b`)
   - **Barra de Cooldown:**
     - Si `cooldown_days_remaining > 0`: *"Actualizado el DD/MM/YYYY • Próxima revisión estándar en X días"*.
     - Botón *"Forzar recálculo"* que despliega `ConfirmDialog` avisando del consumo de cuota antes de ejecutar `requestValuation(id, true)`.
     - Si `cooldown_days_remaining === 0`: Botón *"Actualizar estimación"*.
   - **Desglose de Factores Explicativos:**
     - Píldoras verdes para bonificaciones (ej. `+7.5% Ascensor`) y rojas/ámbar para penalizaciones.
     - Descripción cualitativa redactada por el motor de tasación.
   - **Testigos y Anuncios Reales (Grounding Sources):**
     - Enlaces con `ExternalLink`, validando que la URL sea segura (`http://` o `https://`).
     - Título del anuncio, precio publicado y $m^2$.
   - **Aviso Legal:**
     - Explicación de que es una estimación estadística y orientativa Arrendis AI basada en testigos web, sin validez hipotecaria oficial.

---

## 3. Integración en `PropertyDetail.tsx`

1. **Ampliación del tipo `activeTab`:**
   ```typescript
   const [activeTab, setActiveTab] = useState<"dashboard" | "fiscal" | "contracts" | "valuation">("dashboard");
   ```
2. **Pestaña en la barra de navegación:**
   ```tsx
   <button 
     className={`tab-btn ${activeTab === "valuation" ? "active" : ""}`}
     onClick={() => setActiveTab("valuation")}
   >
     <TrendingUp size={16} /> Valoración IA
   </button>
   ```
3. **Renderizado en el cuerpo:**
   ```tsx
   {activeTab === "valuation" && (
     <MarketValuationPanel 
       property={property} 
       onPropertyUpdated={(updated) => setProperty(updated)} 
     />
   )}
   ```

---

## 4. Estilos Visuales Atelier (`frontend/src/index.css`)
Estilos dedicados para la paleta cálida, tarjetas flotantes, badges semánticos y fuentes web con enlaces sutiles.

---

## 5. Estrategia de Testing y Verificación
1. **Verificación TypeScript y Vite:**
   - Ejecutar `npm run build` en `frontend/` asegurando 0 errores de tipado o compilación.
2. **Verificación de Regresión Backend:**
   - Ejecutar `./venv/bin/pytest` para asegurar que los 393 tests siguen en verde.

---

## 6. Criterios de Aceptación
1. `PhysicalAttributesModal` permite editar características físicas desbloqueando la valoración.
2. `MarketValuationPanel` implementa el ciclo de vida completo: carga inicial, estado vacío, cálculo animado, cooldown, confirmación para forzar y desglose explicativo con yield y fuentes.
3. Tipado estricto en `activeTab` de `PropertyDetail.tsx`.
4. `npm run build` y `./venv/bin/pytest` 100% limpios.
