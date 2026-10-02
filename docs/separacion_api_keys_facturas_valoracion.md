# Tarea Backlog: Separación de API Keys (Facturas vs Valoración de Mercado)

## 📌 Contexto y Objetivo
Actualmente la aplicación utiliza una única clave de Google Gemini (`GEMINI_API_KEY`) para dos funciones muy diferentes:
1. **Extracción y procesamiento de facturas de suministros (Épica E-02):** Solo requiere comprensión de documentos PDF/imágenes. No necesita conexión web ni búsqueda en Google.
2. **Valoración de mercado inmobiliario (Épica E-03):** Utiliza *Google Search Grounding* para consultar en tiempo real testigos y precios actualizados en portales líderes (Idealista, Fotocasa).

### El problema de usar una sola clave
Al activar el nivel de prepago o facturación en un proyecto de Google Cloud para desbloquear la búsqueda en Google:
- Las búsquedas web son gratuitas (5.000/mes a coste 0 €).
- Pero Google pasa a facturar las fracciones de céntimo de los tokens de entrada/salida de ese proyecto.
- Si una factura entra por el fallback de IA usando esa misma clave, consume saldo del monedero prepago.

### La solución arquitectónica
Desacoplar las claves en dos variables de entorno independientes:
- `GEMINI_INVOICE_API_KEY`: Clave de un proyecto **Free Tier 100% gratuito** (sin tarjeta ni prepago). Procesa facturas con coste **0,00 € indefinido**.
- `GEMINI_VALUATION_API_KEY`: Clave del proyecto con prepago/búsqueda habilitada para valoraciones de mercado en tiempo real.

---

## 🛠️ Guía Paso a Paso: Cómo Generar la Clave Gratuita para Facturas

### Paso 1: Entrar a Google AI Studio
1. Abre tu navegador y accede a: [Google AI Studio - Claves API](https://aistudio.google.com/app/apikey).
2. Inicia sesión con tu cuenta de Google.

### Paso 2: Crear una nueva clave en un proyecto sin facturación
1. Pulsa en el botón azul **"Create API key"**.
2. En el desplegable, selecciona **"Create API key in new project"** *(Crear clave de API en un nuevo proyecto)*.
   > **Nota importante:** Al crear un proyecto nuevo desde AI Studio sin asociarle tarjeta, Google le asigna por defecto el **Free Tier permanente**.
3. Copia la clave generada (empieza por `AIzaSy...`).

### Paso 3: Configurar las variables en el entorno
En tu archivo `.env` local (`/home/carlos/rental-handler/.env`) y en el servidor de producción (`/home/ubuntu/arrendis/.env`):

```bash
# Clave 1: Free Tier 100% gratuita para extracción de facturas por IA
GEMINI_INVOICE_API_KEY=AIzaSy_clave_gratuita_facturas_aqui

# Clave 2: Proyecto con búsqueda web para valoración de mercado
GEMINI_VALUATION_API_KEY=AQ_clave_prepago_valoracion_aqui

# Mantener compatibilidad hacia atrás
GEMINI_API_KEY=AIzaSy_clave_gratuita_facturas_aqui
```

---

## 💻 Cambios de Código Pendientes (Estimación: 0.5 SP)
1. En `backend/api/dependencies.py`:
   - `get_llm_provider()`: Usar `os.getenv("GEMINI_INVOICE_API_KEY") or os.getenv("GEMINI_API_KEY")`.
   - `get_market_valuation_port()`: Usar `os.getenv("GEMINI_VALUATION_API_KEY") or os.getenv("GEMINI_API_KEY")`.
2. Actualizar tests unitarios para verificar el desacoplamiento.
