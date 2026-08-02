# Propuesta de Arquitectura: Automatización de Gastos de Suministros vía Email

Objetivo Principal: Implementar una funcionalidad zero-cost (o de coste extremadamente bajo) y de bajo mantenimiento que permita a la aplicación de gestión de alquileres registrar automáticamente los gastos mensuales de suministros (luz, agua, gas) de los arrendatarios a partir de los correos electrónicos de facturación, y almacenar los recibos originales para su consulta.

## 1. El Problema a Resolver

Actualmente, el registro de facturas es un proceso manual. La opción ideal (conexión directa vía APIs bancarias o APIs de las compañías eléctricas) es inviable debido a los altos costes de licencias o integraciones complejas para un proyecto que busca mantenerse gratuito/low-cost.

## 2. Vías de Solución a Evaluar durante el Diseño

Se propone aprovechar el ecosistema del backend actual (Python) con la librería PyMuPDF (local, rápida y gratuita) para extraer el texto de los PDFs adjuntos. A partir de esa extracción textual, el sistema debe evaluar dos vías posibles para estructurar la información:

### Vía A: Extracción Local con Expresiones Regulares (Regex puro)

Antes de optar por IA, se debe evaluar la viabilidad de un motor de reglas local.

Requisito de Diseño: El sistema/equipo deberá recopilar un corpus de muestra (ej. 10-15 PDFs reales anonimizados) de las principales comercializadoras de España (Endesa, Iberdrola, Naturgy, Aqualia, etc.) a fecha de 2026.

Objetivo de la prueba: Determinar si la estructura de texto extraída por PyMuPDF es lo suficientemente predecible y estática como para que unas reglas Regex identifiquen el "Total", la "Fecha" y el "CUPS" sin alto margen de error.

### Vía B: Extracción Semántica (Híbrida: Python + IA Generativa Gratuita)

Si el análisis de la Vía A demuestra que el formato varía demasiado (incluso dentro de la misma compañía) o es frágil ante cambios de diseño, se utilizará el Free Tier de una API de IA (ej. Gemini Flash).

Flujo: Se envía el texto "en bruto" a la API. Mediante response_schema (JSON Mode), se obliga al LLM a devolver un objeto estructurado predefinido (Importe, Fecha, Proveedor, CUPS).

## 3. Flujo de Datos General (Agnóstico a la vía de extracción)

Recepción: Configuración de reenvío automático o buzón dedicado (ej. facturas@tuapp.com).

Ingesta: Conexión IMAP desde el backend (Python) para descargar PDFs de correos no leídos.

Extracción Textual: Paso del PDF a texto plano usando PyMuPDF.

Procesamiento (Regex o IA): Obtención del JSON estructurado con los datos del gasto.

Enrutamiento (Matching): Búsqueda del número CUPS (o contrato) en la base de datos de inmuebles para asignar el gasto al piso correspondiente.

Almacenamiento Documental: Guardado del archivo PDF original, vinculándolo al registro del gasto en la base de datos para que el usuario pueda visualizarlo o descargarlo desde la plataforma web (vital para justificaciones fiscales).

## 4. Puntos de Decisión para el Sistema Agéntico

Para redactar la especificación final, el sistema agéntico debe resolver las siguientes disyuntivas:

Regex vs. IA (Análisis de Fragilidad): Tras analizar los PDFs de muestra, ¿compensa el esfuerzo de mantener reglas Regex específicas por compañía para evitar depender de terceros, o la variabilidad es tan alta que justifica usar un LLM?

Almacenamiento de Archivos (Viabilidad Gratuita): Guardar PDFs (aprox. 100KB - 500KB cada uno) de forma recurrente consumirá espacio. Punto de decisión: ¿Qué servicio de Object Storage permite mantener el coste a cero a largo plazo? Se deben evaluar opciones como Cloudflare R2 (generosa capa gratuita), Amazon S3 (Free Tier limitado), Firebase Storage o almacenamiento en disco local del VPS, así como definir políticas de retención (ej. auto-borrado a los 5 años, que es el límite de prescripción de Hacienda).

Privacidad de Datos (GDPR): Si se opta por la Vía B (IA), se están enviando datos a una API externa. Punto de decisión: ¿Es necesario aplicar una capa de Regex previa solo para anonimizar/eliminar nombres propios y direcciones antes de enviar el prompt al LLM?

Validación Humana: Independientemente de la vía (Regex o IA), el sistema puede equivocarse. Punto de decisión: Definir en la interfaz de usuario un estado de "Gasto Pendiente de Revisión" para que el propietario confirme el dato importado antes de que afecte al rendimiento neto del inmueble.

Escalabilidad de la Ingesta: Evaluar si a futuro compensa sustituir la lectura IMAP por un servicio de Inbound Email (que transforme los correos entrantes en Webhooks hacia el backend).

Conclusión

El objetivo de la fase de diseño es encontrar el equilibrio perfecto entre coste cero, privacidad y bajo mantenimiento. El sistema agéntico debe priorizar la prueba de concepto con la Vía A (Regex) y usar la Vía B (IA Generativa) como la solución de robustez en caso de que los formatos de las facturas resulten inmanejables mediante reglas estáticas. Asimismo, debe resolver el reto del almacenamiento de archivos para garantizar que el archivo documental no suponga una carga financiera para la aplicación.