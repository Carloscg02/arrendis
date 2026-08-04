# 📗 Manual de Cálculo Fiscal y Mapeo AEAT (IRPF Modelo D-100)

Este documento constituye el **manual de referencia contable, financiero y fiscal** del sistema de gestión de alquileres. Describe detalladamente todas las entradas de datos, el algoritmo matemático de cálculo del Rendimiento del Capital Inmobiliario según la Ley del Impuesto sobre la Renta de las Personas Físicas (LIRPF), y la correspondencia exacta con las **casillas oficiales de la Agencia Tributaria (AEAT - Modelo D-100)**.

---

## 📋 1. Estructura de Datos de Entrada (Inputs)

Para llevar a cabo el cálculo fiscal de una propiedad en un ejercicio determinado ($Y$), el sistema requiere los siguientes tres bloques de información:

### 1.1. Datos Fiscales de la Propiedad

* **Referencia Catastral (`cadastral_ref`)**: Código alfa-numérico oficial de 20 caracteres asignado por la Dirección General del Catastro.
* **Desglose de Valor Catastral (`cadastral_breakdown`)** *(extraído del recibo del IBI)*:
  * **Valor Catastral del Suelo ($V_{suelo\_cat}$)**: Valor asignado al terreno.
  * **Valor Catastral de la Construcción ($V_{const\_cat}$)**: Valor asignado a la edificación.
  * **Valor Catastral Total ($V_{cat\_total}$)**: $V_{suelo\_cat} + V_{const\_cat}$.
* **Coste de Adquisición ($acquisition\_cost$)** *(extraído de la escritura de compraventa)*:
  * **Precio de Compraventa ($P_{compra}$)**: Precio íntegro pactado.
  * **Porción Construcción ($P_{const}$)**: Importe del precio de compra correspondiente a la edificación.
  * **Porción Suelo ($P_{suelo}$)**: Importe del precio de compra correspondiente al terreno ($P_{compra} = P_{const} + P_{suelo}$).
  * **Gastos de Adquisición ($G_{adq}$)**: Impuestos de Transmisiones (ITP/IVA) + Honorarios de Notaría + Honorarios de Registro de la Propiedad.
* **Fecha de Adquisición (`acquisition_date`)**: Fecha en la que se formalizó la compraventa.

---

### 1.2. Contratos de Arrendamiento

Cada contrato de alquiler registrado incluye:
* **Fecha de Inicio (`start_date`)** y **Fecha de Fin (`end_date`)** *(si es indeterminado, se asume activo)*.
* **Tipo de Arrendamiento (`lease_type`)**:
  * **Vivienda Habitual (`vivienda_habitual`)**: Destinado a satisfacer la necesidad permanente de vivienda del inquilino. Otorga derecho a la **reducción del 60%** sobre el rendimiento neto (art. 23.2 LIRPF).
  * **Otros Usos (`temporal`, `turistico`, `comercial`)**: Alquileres de temporada, vacacionales o locales comerciales. No aplican reducción del 60%.

---

### 1.3. Movimientos Financieros y Categorización Fiscal AEAT

Cada ingreso y gasto registrado por el propietario cuenta con un importe en euros (€), una fecha de cobro/pago y una **Categoría Fiscal AEAT**:

#### A. Categorías Fiscales de Ingreso (`FiscalIncomeCategory`)
1. **Rendimiento Íntegro (`rendimiento_integro`)**: Rentas cobradas por el alquiler de la vivienda.
2. **Otros Ingresos Computables (`otros_ingresos`)**: Indemnizaciones recibidas, cobros por servicios accesorios o suministros reexpedidos al inquilino.

#### B. Categorías Fiscales de Gasto (`FiscalExpenseCategory`)
1. **Intereses de Capital / Financiación (`intereses_capital`)**: Intereses de préstamos o hipotecas solicitados para la compra o mejora del inmueble.
2. **Reparación y Conservación (`reparacion_conservacion`)**: Gastos orientados a mantener el uso normal del inmueble (pintura, reparación de averías, sustitución de elementos deteriorados).
3. **Tributos, Tasas y Recargos (`tributos`)**: Impuesto sobre Bienes Inmuebles (IBI), tasa de basuras, vados y recargos no estatales.
4. **Primas de Seguros (`primas_seguros`)**: Seguros de hogar, responsabilidad civil o impago de alquiler.
5. **Suministros y Gastos de Comunidad (`servicios_suministros`)**: Cuotas de la comunidad de propietarios, agua, luz, gas, internet (si los paga el propietario).
6. **Gastos de Formalización (`formalizacion`)**: Honorarios de gestoría, abogados, notaría o intermediación para la formalización del contrato.
7. **Saldos de Dudoso Cobro (`dudoso_cobro`)**: Impagos de rentas debidamente justificados conforme a los plazos exigidos por la LIRPF.
8. **Otros Gastos Deducibles (`otros_gastos_deducibles`)**: Cualquier otro gasto necesario para la obtención de los rendimientos.
9. **No Deducible (`no_deducible`)**: Gastos personales o no deducibles que quedan excluidos del cálculo fiscal.

---

## 🧮 2. Algoritmo Paso a Paso de Cálculo Fiscal (LIRPF)

El cálculo del Rendimiento del Capital Inmobiliario para un año fiscal $Y$ se ejecuta mediante el siguiente algoritmo matemático estricto:

```
PASO 1: Suma de Rendimientos Íntegros (Ingresos)
PASO 2: Cálculo del Intervalo de Ocupación y Ratios
PASO 3: Prorrateo de Gastos Fijos
PASO 4: Aplicación del Tope de Reparación e Intereses (Art. 23.1.a LIRPF)
PASO 5: Cálculo de la Amortización de la Edificación (Art. 23.1.b LIRPF)
PASO 6: Rendimiento Neto Previo
PASO 7: Aplicación de la Reducción por Vivienda Habitual (Art. 23.2 LIRPF)
PASO 8: Rendimiento Neto Reducido Final
```

---

### PASO 1: Suma de Rendimientos Íntegros (Ingresos)

Se computan todos los ingresos cobrados en el año $Y$:

$$\text{Rendimiento Íntegro Total } (I_{total}) = \sum \text{Ingresos}_{\text{rendimiento\_integro}} + \sum \text{Ingresos}_{\text{otros\_ingresos}}$$

---

### PASO 2: Cálculo del Ratio de Ocupación

Para evitar duplicidad en caso de contratos que se solapen o renovaciones dentro del mismo año, el sistema realiza la **fusión de intervalos temporales** (algoritmo de *range merging*):

1. Se toman todas las fechas de inicio y fin de contratos vigentes en el año $Y$.
2. Se recortan las fechas al límite del año (del $01/01/Y$ al $31/12/Y$).
3. Se unen los intervalos solapados para obtener el número de días únicos efectivamente alquilados ($D_{alquilados}$).
4. Se calcula el **Ratio de Ocupación ($R_{ocupacion}$)**:

$$R_{ocupacion} = \frac{D_{alquilados}}{D_{total\_año}}$$

*(donde $D_{total\_año}$ es 366 en años bisiestos o 365 en años ordinarios).*

---

### PASO 3: Prorrateo de Gastos Fijos

Los gastos fijos anuales que cubren la totalidad del año se prorratean en función de los días en que el inmueble produjo rendimientos:

$$\text{Gasto Prorrateado} = \text{Gasto Anual Bruto} \times R_{ocupacion}$$

* **Gastos que se Prorratean**: Tributos ($G_{trib}$), Seguros ($G_{seg}$), Suministros/Comunidad ($G_{sum}$), Formalización ($G_{form}$), Dudoso Cobro ($G_{dud}$) y Otros ($G_{otros}$).
* **Gastos que NO se Prorratean**: Los gastos de **Intereses de Hipoteca ($G_{int}$)** y **Reparación y Conservación ($G_{rep}$)** no se prorratean; se imputan al 100% siempre que el inmueble haya estado alquilado en el año.

---

### PASO 4: Aplicación del Tope de Reparación e Intereses (Art. 23.1.a LIRPF)

La normativa del IRPF establece que la suma de los gastos por intereses y reparación/conservación **no puede generar un rendimiento neto negativo por sí sola**.

$$\text{Suma Reparación e Intereses } (S_{rep\_int}) = G_{int} + G_{rep}$$

$$\text{Tope Máximo Deducible } (T) = I_{total}$$

$$\text{Importe Deducible Aplicado} = \min(S_{rep\_int}, T)$$

$$\text{Exceso Pendiente de Deducir (Remanente 4 años)} = \max(0, S_{rep\_int} - T)$$

> **Efecto práctico**: El exceso no deducido en el ejercicio $Y$ no se pierde; el propietario lo guarda para deducirlo en las declaraciones de los 4 años siguientes.

#### Aplicación de Excesos de Ejercicios Anteriores

Si existen excesos de ejercicios anteriores (máximo 4 años de antigüedad) y hay margen bajo el tope:

$$\text{Margen disponible} = T - \text{Importe Deducible Aplicado}$$

$$\text{Exceso anterior aplicado} = \min(\sum \text{Excesos anteriores disponibles},\, \text{Margen disponible})$$

Los excesos se aplican por orden FIFO (primero los más antiguos).

---

### PASO 5: Cálculo de la Amortización de la Edificación (Art. 23.1.b LIRPF)

La amortización anual es el **3% sobre el mayor de los dos valores siguientes**, excluyendo siempre el valor del suelo:

1. **Valor Catastral de la Construcción ($V_{const\_cat}$)**.
2. **Coste de Adquisición de la Construcción ($Coste_{const\_adq}$)**, que incluye el precio pactado por la edificación más la parte proporcional de los gastos e impuestos de compra:

$$\text{Gastos Compra Construcción} = G_{adq} \times \left(\frac{P_{const}}{P_{compra}}\right)$$

$$Coste_{const\_adq} = P_{const} + \text{Gastos Compra Construcción}$$

$$\text{Base de Amortización } (B_{amort}) = \max(Coste_{const\_adq}, V_{const\_cat})$$

$$\text{Amortización Anual Completa} = B_{amort} \times 3\%$$

$$\text{Amortización Deducible Prorrateada } (G_{amort}) = (B_{amort} \times 3\%) \times R_{ocupacion}$$

---

### PASO 6: Rendimiento Neto Previo

Se calcula sumando todos los gastos deducibles admitidos y restándolos de los ingresos íntegros:

$$\text{Total Gastos Deducibles } (G_{totales}) = \text{Importe Deducible Aplicado } (S_{rep\_int}) + G_{trib} + G_{seg} + G_{sum} + G_{amort} + G_{form} + G_{dud} + G_{otros}$$

$$\text{Rendimiento Neto Previo } (RN_{previo}) = I_{total} - G_{totales}$$

---

### PASO 7: Aplicación de la Reducción por Vivienda Habitual (Art. 23.2 LIRPF)

Si el $RN_{previo} > 0$ y la propiedad estuvo alquilada bajo contrato de **Vivienda Habitual**:

1. Se determina la proporción de días alquilados bajo contrato de vivienda habitual ($R_{vh}$):

$$R_{vh} = \frac{D_{\text{vivienda\_habitual}}}{D_{alquilados}}$$

2. Se calcula la **Base de Reducción**:

$$\text{Base Reducción} = RN_{previo} \times R_{vh}$$

3. Se aplica el porcentaje de **Reducción por Vivienda Habitual (Ley 12/2023 de Vivienda)** según la fecha de inicio del contrato:
   * **Contratos firmados ANTES de 01/01/2024:** Reducción del **60%**.
   * **Contratos firmados A PARTIR de 01/01/2024:** Reducción general del **50%**.

$$\text{Importe Reducción} = \text{Base Reducción} \times \text{Porcentaje (50\% o 60\%)}$$

---

### PASO 8: Rendimiento Neto Reducido Final

$$\text{Rendimiento Neto Reducido Final } (RN_{final}) = RN_{previo} - \text{Importe Reducción}$$

Este es el resultado final que se integra en la Base Imponible General del IRPF del contribuyente.

---

## 🏛️ 3. Mapeo Oficial de Casillas AEAT (Modelo D-100)

A continuación se detalla la correspondencia exacta entre los conceptos calculados por el sistema y las **casillas oficiales de la Declaración de la Renta de la Agencia Tributaria (Modelo D-100)**:

| Casilla AEAT | Denominación Oficial en Renta Web | Concepto Interno / Fórmula del Sistema |
|:---:|:---|:---|
| **0102** | Ingresos íntegros computables | Total Ingresos de Alquiler ($I_{total}$) |
| **0105** | Intereses de capitales ajenos y gastos de financiación | Gastos de Hipoteca/Financiación aplicados ($G_{int}$) |
| **0106** | Gastos de conservación y reparación | Gastos de Reparación y Mantenimiento aplicados ($G_{rep}$) |
| **0109** | Gastos de comunidad | Gastos de comunidad prorrateados ($G_{com}$) |
| **0110** | Gastos de formalización del contrato | Gestoría, notaría, contrato prorrateados ($G_{form}$) |
| **0113** | Servicios y suministros | Agua, luz, gas, internet prorrateados ($G_{sum}$) |
| **0114** | Primas de contratos de seguro | Seguros prorrateados ($G_{seg}$) |
| **0115** | Tributos, recargos y tasas | IBI, basuras y tasas prorrateados ($G_{trib}$) |
| **0116** | Saldos de dudoso cobro | Impagos justificados prorrateados ($G_{dud}$) |
| **0117** | Amortización de bienes muebles | 10% anual de enseres/muebles prorrateado ($G_{muebles}$) |
| **0131** | Amortización del inmueble y la mejora | Amortización anual del 3% de la construcción prorrateada ($G_{amort}$) |
| **0148** | Otros gastos deducibles | Otros gastos deducibles prorrateados ($G_{otros}$) |
| **0149** | Rendimiento neto | Rendimiento Neto Previo ($I_{total} - \text{Total Gastos}$) |
| **0150** | Reducción por arrendamiento de vivienda habitual | Reducción del 50% o 60% sobre el rendimiento positivo de vivienda habitual |
| **0154** | Rendimiento neto reducido | **Resultado Final a integrar en el IRPF** ($\text{Casilla } 0149 - \text{Casilla } 0150$) |

---

## 📊 4. Ejemplo Numérico Completo Resuelto

### Ejemplo de Caso Práctico:
- **Inmueble**: Piso en Madrid alquilado **365 días del año (100% ocupación)** como **Vivienda Habitual**.
- **Valor Catastral**: Suelo = 40.000 € (40%), Construcción = 60.000 € (60%).
- **Adquisición**: Precio = 200.000 € (Construcción = 120.000 €, Suelo = 80.000 €). Gastos (ITP/Notaría/Registro) = 20.000 €.
- **Ingresos de Alquiler**: 12.000 €/año.
- **Gastos**: IBI = 600 €, Seguro = 400 €, Comunidad/Suministros = 1.000 €, Pintura/Averías = 800 €, Intereses Hipoteca = 1.200 €.

---

### Resución Paso a Paso:

1. **Rendimiento Íntegro (Casilla [0102])**: **12.000,00 €**
2. **Gastos Intereses (Casilla [0105])**: **1.200,00 €**
3. **Gastos Reparación (Casilla [0106])**: **800,00 €**
   * *Verificación de Tope*: $1.200 + 800 = 2.000 \text{ €} \le 12.000 \text{ €}$ $\rightarrow$ **Se deducen 2.000,00 € íntegros (0 € exceso).**
4. **Tributos / IBI (Casilla [0115])**: **600,00 €**
5. **Seguros (Casilla [0114])**: **400,00 €**
6. **Gastos de Comunidad (Casilla [0109]) y Suministros (Casilla [0113])**: **1.000,00 €**
7. **Cálculo de Amortización (Casilla [0131])**:
   * Gastos de compra proporcionales a la construcción: $20.000 \times \frac{120.000}{200.000} = 12.000 \text{ €}$
   * Base de adquisición de construcción: $120.000 + 12.000 = 132.000 \text{ €}$
   * Base catastral de construcción: $60.000 \text{ €}$
   * Mayor de los dos: $\max(132.000, 60.000) = \mathbf{132.000 \text{ €}}$
   * Amortización del 3%: $132.000 \times 3\% = \mathbf{3.960,00 \text{ €}}$
8. **Total Gastos Deducibles**:
   $$1.200 + 800 + 600 + 400 + 1.000 + 3.960 = \mathbf{7.960,00 \text{ €}}$$
9. **Rendimiento Neto (Casilla [0149])**:
   $$12.000 - 7.960 = \mathbf{4.040,00 \text{ €}}$$
10. **Reducción Vivienda Habitual (Casilla [0150])**:
   * *Si el contrato se firmó antes de 01/01/2024 (60%)*: $4.040 \times 60\% = \mathbf{2.424,00 \text{ €}}$ $\rightarrow$ Rendimiento Neto Reducido: **1.616,00 €**
   * *Si el contrato se firmó a partir de 01/01/2024 (50%)*: $4.040 \times 50\% = \mathbf{2.020,00 \text{ €}}$ $\rightarrow$ Rendimiento Neto Reducido: **2.020,00 €**
11. **Rendimiento Neto Reducido Final (Casilla [0154])**: **1.616,00 €** *(con contrato pre-2024)* o **2.020,00 €** *(con contrato post-2024)*.

> 💡 **Conclusión**: De los 12.000 € cobrados de alquiler, gracias al desglose de gastos, la amortización de la edificación y la reducción del 50-60% de vivienda habitual, el propietario solo tributará en su IRPF por **1.616,00 €** (o **2.020,00 €** en contratos post-2024).
