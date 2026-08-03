# Petición de Evaluación de Arquitectura Fiscal (Módulo IRPF)

Contexto: Nuestra aplicación genera un "Borrador Fiscal" anual para propietarios de alquileres en España. Actualmente, el motor de cálculo interno procesa correctamente los datos, pero necesitamos evaluar la estrategia de presentación (frontend/PDF) y asegurar la cobertura total de los casos de uso oficiales de la Agencia Tributaria (AEAT). En docs/manual_calculo_fiscal_aeat.md tenemos una explicación de los cálculos implementados en la web, revisable via inspección de código.

Tareas requeridas para el Sistema Agéntico:

Análisis de Fragilidad y Diseño (Casillas vs Conceptos):

Evalúa si debemos mantener en la vista de usuario y en el PDF final las referencias exactas a los números de casilla de la AEAT (ej. [0113], [0102]) o si debemos pivotar hacia un modelo "Agnóstico" que solo muestre los conceptos universales y agrupados (ej. "Servicios y Suministros", "Tributos").

Consideración: Los números de casilla cambian a menudo por reestructuraciones en el portal Renta Web, lo que nos obligaría a mantener y lanzar actualizaciones de la app cada campaña de la renta. Valora el coste de mantenimiento vs. la conveniencia visual para el usuario, proponiendo la mejor interfaz sin alterar el motor de cálculo subyacente. También valorar qué campos realmente aportan valor al usuario o aportan complejidad excesiva a la aplicación, y podemos omitirlos.

Gap Analysis (Cálculos y Categorías Faltantes):

Compara los cálculos que actualmente soporta nuestro sistema (Intereses, Reparación, IBI, Seguros, Suministros, Amortización de construcción) con el volcado oficial de la Sección C de la AEAT adjunto a continuación.

Identifica si nos falta implementar en nuestra base de datos alguna categoría deducible. Por ejemplo: ¿Deberíamos añadir soporte para Amortización de bienes muebles [0117] (electrodomésticos/muebles), Gastos de comunidad [0109] desglosados, o Saldos de dudoso cobro [0116] para casos de morosidad? Genera una lista de recomendaciones.

ANEXO: Estructura Oficial Renta Web AEAT (Sección C. Bienes Inmuebles)

Documento de referencia para el Gap Analysis. Corresponde exclusivamente al apartado de Inmuebles arrendados.

Datos del Inmueble y Arrendamiento

[0062-0066] Propiedad, Usufructo, Situación, Referencia Catastral.

[0067-0068] Naturaleza (Urbana / Rústica).

[0075] Uso: Arrendamiento.

[0091-0098] NIFs de los arrendatarios (solo aplicable y obligatorio en caso de vivienda habitual).

[0093] Fecha del contrato.

[0100] Marca si el arrendamiento tiene derecho a reducción (artículo 23.2 de la Ley del Impuesto).

[0101] Número de días en que el inmueble ha estado arrendado.

Ingresos Computables

[0102] Ingresos íntegros computables.

Gastos Deducibles

[0103] Importe pendiente de deducir de los ejercicios anteriores (4 años máximos).

[0105] Intereses de los capitales invertidos en la adquisición o mejora del inmueble y demás gastos de financiación en el ejercicio.

[0106] Gastos de reparación y conservación correspondientes al ejercicio.

> Nota del sistema: Límite conjunto aplicable: La suma aplicada en el año de Intereses + Reparaciones no puede superar el importe de la casilla [0102].

[0108] Importe generado en el ejercicio pendiente de deducir en los 4 años siguientes.

[0109] Gastos de comunidad.

[0110] Gastos de formalización del contrato.

[0111] Gastos de defensa jurídica.

[0112] Otras cantidades devengadas por terceros por servicios personales.

[0113] Servicios y suministros (electricidad, agua, internet, gas...).

[0114] Primas de contratos de seguro.

[0115] Tributos, recargos y tasas.

[0116] Saldos de dudoso cobro.

[0117] Amortización de bienes muebles.

Amortización del Inmueble (Construcción)

[0118-0119] Tipo de adquisición: Onerosa (compraventa, permuta) o Lucrativa (herencia, donación).

[0120-0122] Fechas de adquisición y transmisión, y número de días arrendado.

[0123] Valor catastral.

[0124] Valor catastral de la construcción.

[0126] Importe de adquisición.

[0127] Gastos y tributos inherentes a la adquisición.

[0128-0129] Importe de las mejoras realizadas en años anteriores y en el actual.

[0130] Base de la amortización.

[0131] Amortización del inmueble y la mejora.

Resultado y Reducciones LIRPF

[0148] Otros gastos fiscalmente deducibles.

[0149] Rendimiento neto (Ingresos íntegros menos todos los gastos deducibles y amortizaciones).

[0150] Reducción por arrendamiento de inmuebles destinados a vivienda (artículo 23.2 de la Ley del Impuesto).

[0151] Reducción por rendimientos generados en más de 2 años u obtenidos de forma notoriamente irregular.

[0152] Rendimiento mínimo computable en caso de parentesco.

[0154] Rendimiento neto reducido del capital inmobiliario.