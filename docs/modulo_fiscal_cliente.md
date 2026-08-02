# Módulo Fiscal: Resumen Funcional para el Cliente

Este documento sirve como guía y presentación del **Módulo Fiscal** de la plataforma. Su objetivo es explicar de forma clara y funcional (sin entrar en detalles técnicos) qué hace este módulo, qué información necesita por parte del propietario y qué resultados y automatizaciones le entregará.

> **Estado del Módulo:** 🚧 _En Construcción (Epic E-01)_  
> _Funcionalidades como la recopilación de datos fiscales de la propiedad (valor catastral y adquisición) y la gestión de contratos de arrendamiento ya están disponibles. Los cálculos automáticos y la generación del borrador final se irán activando en las próximas actualizaciones._

---

## 🎯 1. El Objetivo: Tu Borrador Fiscal Automático

La Declaración de la Renta para propietarios de inmuebles alquilados suele ser un proceso complejo (cálculo de amortizaciones, clasificación de gastos deducibles, prorrateo de días alquilados, etc.). 

El objetivo principal del Módulo Fiscal es **convertir la gestión diaria de tu alquiler en un Informe Fiscal listo para presentar a Hacienda**. 

El sistema funcionará como un "asesor virtual" que procesará todos tus datos y generará el **Rendimiento Neto del Capital Inmobiliario**, aplicando automáticamente todas las reducciones y beneficios fiscales a los que tengas derecho (como la reducción del 60% por vivienda habitual, sujeta a la normativa vigente).

---

## 📥 2. ¿Qué información necesita el sistema? (Entradas)

Para que el motor fiscal pueda hacer su trabajo, el sistema te pedirá que introduzcas cierta información a lo largo del tiempo. Esta información se divide en tres grandes bloques:

### A. Datos Fiscales del Inmueble (✅ Ya disponible)
Información base que solo necesitas introducir una vez por cada propiedad:
*   **Referencia Catastral:** El identificador oficial (20 caracteres).
*   **Valor Catastral:** Extraído del recibo del IBI (desglosado entre valor del *Suelo* y valor de la *Construcción*). _Es clave para calcular la amortización anual._
*   **Coste de Adquisición:** Cuánto te costó comprar la casa (Precio de compra + Impuestos de transmisión + Gastos de Notaría + Gastos de Registro).

### B. Contratos de Arrendamiento (✅ Ya disponible)
El sistema necesita saber cuándo está alquilada la casa y a quién:
*   Fechas de inicio y fin del contrato.
*   Si el alquiler es para uso de "Vivienda Habitual" (que da derecho a reducciones fiscales) o para otros usos (turístico, temporal, local).
*   Identificación de los inquilinos.
_Esto permitirá al sistema prorratear automáticamente los gastos: por ejemplo, deducir el seguro del hogar o el IBI solo por los días que la casa estuvo efectivamente alquilada._

### C. Ingresos y Gastos Clasificados (✅ Ya disponible)
Tu contabilidad diaria, pero con "ojos" fiscales:
*   **Clasificación Inteligente:** Al registrar un gasto (ej. una factura del fontanero), el sistema te pedirá clasificarlo según las categorías de Hacienda (reparación y conservación, seguros, tributos, suministros, etc.).
*   **Reglas Fiscales Integradas:** El sistema sabrá, por ejemplo, que los gastos de "Reparación y Conservación" no pueden superar los rendimientos íntegros obtenidos en el año y limitará su deducción de manera automática, guardando el remanente para los próximos 4 años.

---

## ⚙️ 3. ¿Qué hace el Motor Fiscal? (Cálculos Automáticos — ✅ Ya disponible)

Una vez que alimentas el sistema con los datos anteriores, el motor de cálculo trabaja en segundo plano para realizar las siguientes operaciones complejas por ti:

1.  **Cálculo de la Amortización:** Calcula automáticamente el 3% del mayor de los dos valores (Coste de adquisición o Valor Catastral), excluyendo siempre el valor del suelo.
2.  **Prorrateo de Gastos:** Identifica los días exactos que la vivienda estuvo alquilada en el año fiscal y aplica esa proporción a los gastos fijos (IBI, comunidad, seguros, amortización).
3.  **Tope de Gastos de Reparación e Intereses:** Suma los gastos de conservación, reparación e intereses de préstamos y se asegura de que no excedan tus ingresos anuales por esa propiedad, conforme dicta la Ley.
4.  **Aplicación de Reducciones:** Si el contrato es de larga duración (vivienda habitual), aplicará directamente la reducción legal correspondiente sobre el rendimiento neto positivo.

---

## 📄 4. El Resultado Final: Tu Informe / Borrador Fiscal

Al llegar la campaña de la Renta, puedes ir a la pestaña de Datos Fiscales de tu propiedad, seleccionar el año fiscal y consultar tu **Informe Fiscal Anual (✅ Ya disponible)**.

¿Qué te entregará este informe?
*   **Ingresos Íntegros Totales:** Suma exacta de tus alquileres.
*   **Gastos Deducibles Detallados:** Un listado estructurado exactamente en las mismas casillas que pide la Agencia Tributaria (modelo D-100).
*   **Rendimiento Neto Previo y Reducciones:** El cálculo matemático paso a paso para que sepas de dónde sale cada número.
*   **Rendimiento Neto Final:** La cantidad exacta que debes declarar.

_Este informe está diseñado para que puedas usarlo directamente para rellenar el borrador de Hacienda (Renta Web) o entregárselo a tu gestor de confianza, ahorrándote horas de recopilación de facturas y cálculos manuales con hojas de cálculo._
