# 🏛️ Módulo Fiscal: Resumen Funcional y Guía de Uso para el Cliente

Este documento sirve como guía y presentación del **Módulo Fiscal** de la plataforma. Su objetivo es explicar de forma clara y funcional qué hace este módulo, qué información necesita por parte del propietario, qué resultados entrega y cómo probarlo paso a paso en la aplicación web.

> **Estado del Módulo:** ✅ **100% Completado (Épica E-01 / Features F-09 a F-13)**  
> _Todas las funcionalidades están activas: recopilación de datos catastrales y de adquisición, gestión de contratos de arrendamiento, clasificación fiscal de gastos e ingresos, motor de cálculo de amortización y reducciones (IRPF modelo D-100), y generación/descarga del Borrador Fiscal en PDF._

---

## 🎯 1. El Objetivo: Tu Borrador Fiscal Automático

La Declaración de la Renta para propietarios de inmuebles alquilados suele ser un proceso complejo (cálculo de amortizaciones, clasificación de gastos deducibles, prorrateo de días alquilados, tope de reparaciones, etc.). 

El Módulo Fiscal **convierte la gestión diaria de tu alquiler en un Informe y Borrador Fiscal en PDF listo para trasladar a Renta Web**. 

El sistema funciona como un "asesor virtual" que procesa todos tus datos y genera el **Rendimiento Neto del Capital Inmobiliario**, aplicando automáticamente todas las reducciones y beneficios fiscales a los que tengas derecho (como la reducción del 60% por vivienda habitual, sujeta a la normativa vigente).

---

## 📥 2. ¿Qué información necesita el sistema? (Entradas)

Para que el motor fiscal haga su trabajo, introduces la información en tres sencillos bloques dentro de la ficha de cada propiedad:

### A. Datos Fiscales del Inmueble (✅ Disponible)
Información base que solo necesitas introducir una vez por cada propiedad:
* **Referencia Catastral:** El identificador oficial (20 caracteres).
* **Valor Catastral:** Extraído del recibo del IBI, desglosado en *Suelo* y *Construcción*. _Clave para el cálculo de amortización._
* **Coste de Adquisición:** Precio de compra + Impuestos de transmisión (ITP) + Notaría + Registro.

### B. Contratos de Arrendamiento (✅ Disponible)
Información sobre los periodos de alquiler:
* Fechas de inicio y fin del contrato.
* Renta mensual y fianza.
* Tipo de arrendamiento: **Vivienda Habitual** (aplica reducción del 60%), **Temporal**, **Turístico** o **Comercial**.

### C. Ingresos y Gastos Clasificados (✅ Disponible)
Tu contabilidad diaria categorizada para Hacienda:
* **Ingresos:** Clasificados como *Rendimiento Íntegro* o *Fianza/Otros*.
* **Gastos:** Categorizados en las casillas oficiales del IRPF (*Intereses de capital*, *Reparación y conservación*, *Tributos (IBI)*, *Seguros*, *Suministros*, *Amortización*, etc.).

---

## ⚙️ 3. ¿Qué hace el Motor Fiscal? (Cálculos Automáticos)

El motor de cálculo (`FiscalCalculator`) procesa los datos en segundo plano aplicando la normativa del IRPF (art. 23 LIRPF):

1. **Cálculo de la Amortización (Regla del 3%):** Calcula automáticamente el 3% del mayor valor entre el coste de adquisición de la construcción (incluyendo gastos de compra proporcionales) y el valor catastral de la construcción, excluyendo siempre el suelo.
2. **Prorrateo por Ocupación:** Determina los días exactos que la vivienda estuvo alquilada en el año (fusionando intervalos de contratos para evitar duplicados) y prorratea los gastos fijos y la amortización.
3. **Tope de Reparación e Intereses:** Suma los gastos de conservación, reparación e intereses de préstamos y garantiza que no superen los ingresos íntegros del ejercicio, guardando el exceso para deducir en los 4 años siguientes.
4. **Reducción por Vivienda Habitual (60%):** Aplica la reducción del 60% sobre el rendimiento neto positivo atribuible a los días bajo contratos de vivienda habitual.

---

## 📄 4. El Resultado Final: Informe en Pantalla y PDF Descargable

En la pestaña **"Datos Fiscales"** de tu propiedad puedes:

1. Seleccionar el ejercicio fiscal (ej. 2026, 2025).
2. Pulsar **"Generar Informe"** para ver en pantalla el desglose paso a paso:
   * Rendimientos Íntegros Totales.
   * Porcentaje de ocupación y días alquilados.
   * Gastos Deducibles categorizados por casillas AEAT.
   * Desglose de Amortización.
   * Reducción por Vivienda Habitual aplicada.
   * **Rendimiento Neto Reducido Final** (la cifra a declarar).
3. Pulsar el botón **"📄 Descargar Borrador Fiscal (PDF)"** para obtener un documento oficial listo para imprimir o enviar a tu gestor, mapeado exactamente a las casillas del **Modelo D-100 de la AEAT** (Casillas 0075 a 0088).

---

## 🧪 5. Plan de Pruebas Paso a Paso en la Aplicación Web

Sigue este itinerario de prueba para comprobar el funcionamiento completo del módulo fiscal desde tu navegador.

### Paso 1: Arrancar los servidores

Abre una terminal en el directorio del proyecto (`/home/carlos/rental-handler`):

```bash
# 1. Arrancar el Backend en una terminal
source venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000

# 2. Arrancar el Frontend en otra terminal
cd frontend
npm run dev
```

Abre tu navegador en **`http://localhost:5173`**.

---

### Paso 2: Crear cuenta e iniciar sesión
1. Si no tienes cuenta, haz clic en **"Registrarse"**.
2. Introduce tus datos (ej: `usuario@prueba.com` / `Password123!`).
3. Inicia sesión para acceder al panel principal.

---

### Paso 3: Crear una propiedad de prueba
1. Haz clic en **"+ Nueva Propiedad"**.
2. Rellena los datos básicos:
   * **Nombre:** *Piso Gran Vía*
   * **Dirección:** *Calle Gran Vía 42, Madrid, 28013, España*
   * **Tipo:** *Apartamento*
3. Guarda la propiedad y entra en su vista de detalle haciendo clic sobre ella.

---

### Paso 4: Configurar los Datos Fiscales de la Propiedad
1. Haz clic en la pestaña **"⚖️ Datos Fiscales"**.
2. Rellena el formulario de Datos Fiscales:
   * **Referencia Catastral:** `1234567VK3813N0001XF`
   * **Valor Catastral Suelo:** `40.000 €`
   * **Valor Catastral Construcción:** `60.000 €`
   * **Precio de Compra (Construcción):** `120.000 €`
   * **Precio de Compra (Suelo):** `80.000 €`
   * **Impuesto ITP:** `16.000 €`
   * **Gastos Notaría:** `1.000 €`
   * **Gastos Registro:** `500 €`
   * **Fecha de Adquisición:** `01/01/2020`
3. Haz clic en **"Guardar Datos Fiscales"**. Verás que el indicador cambia a **"🟢 Datos Fiscales Completos"**.

---

### Paso 5: Registrar un Contrato de Arrendamiento
1. Ve a la pestaña **"📋 Contratos"**.
2. Haz clic en **"+ Nuevo Contrato"**.
3. Rellena:
   * **Inquilino:** *Juan Pérez*
   * **NIF Inquilino:** *12345678A*
   * **Fecha Inicio:** `01/01/2026`
   * **Fecha Fin:** `31/12/2026`
   * **Renta Mensual:** `1.000 €`
   * **Fianza:** `1.000 €`
   * **Tipo de Contrato:** *Vivienda Habitual (Aplica reducción)*
4. Guarda el contrato.

---

### Paso 6: Añadir Ingresos y Gastos Clasificados
1. Ve a la pestaña **"📊 Finanzas"**.
2. **Añadir un Ingreso:**
   * Haz clic en **"+ Registrar Ingreso"**.
   * Importe: `12.000 €` | Fecha: `01/06/2026` | Descripción: *Rentas de alquiler 2026*.
   * Categoría Fiscal: **Rendimiento Íntegro**.
3. **Añadir Gastos:**
   * **Gasto 1 (IBI):** Importe: `600 €` | Categoría Fiscal: **Tributos, Tasas y Recargos (IBI, basura)**.
   * **Gasto 2 (Seguro del Hogar):** Importe: `300 €` | Categoría Fiscal: **Primas de Seguro**.
   * **Gasto 3 (Fontanero):** Importe: `400 €` | Categoría Fiscal: **Reparación y Conservación**.

---

### Paso 7: Generar el Informe Fiscal en Pantalla
1. Regresa a la pestaña **"⚖️ Datos Fiscales"**.
2. En el panel inferior **"Motor de Cálculo Fiscal (IRPF)"**:
   * Selecciona el año **2026**.
   * Haz clic en **"Generar Informe"**.
3. **Comprobaciones en pantalla:**
   * **Rendimientos Íntegros:** `12.000,00 €`
   * **Ocupación:** `365/365 días (100%)`
   * **Gastos Deducibles:** `1.300,00 €` (600€ IBI + 300€ Seguros + 400€ Fontanero).
   * **Amortización:** ~`3.957,00 €` (3% sobre la base de adquisición de construcción).
   * **Rendimiento Neto Previo:** `12.000 - 1.300 - 3.957 = ~6.743,00 €`
   * **Reducción Vivienda Habitual (60%):** ~`-4.045,80 €`
   * **Rendimiento Neto Reducido Final:** ~`2.697,20 €` (Destacado en una tarjeta grande verde/azul).

---

### Paso 8: Descargar y Verificar el Borrador Fiscal en PDF
1. Al final del informe generado, localiza la sección **"Descargar Borrador Fiscal"**.
2. Haz clic en el botón **"📄 Descargar Borrador Fiscal (PDF)"**.
3. Verás que el botón muestra el spinner **"Generando PDF..."** durante un instante.
4. El navegador descargará un archivo llamado:  
   `borrador_fiscal_Piso_Gran_Via_2026.pdf`
5. Abre el PDF descargado y comprueba:
   * Encabezado con título azul corporativo, año fiscal `2026` y datos del inmueble.
   * Tablas estilizadas con casillas AEAT (**0075**, **0076**, **0077**, **0079**, **0081**, **0083**, **0085**, **0086**, **0087**, **0088**).
   * Coincidencia exacta de todos los importes calculados en la web.
   * Pie de página con aviso legal e indicación de borrador orientativo.

¡Enhorabuena! Has verificado la funcionalidad completa del módulo fiscal end-to-end.
