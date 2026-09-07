# INSTRUCCIONES DE AGENTE: Refactorización Automatizada y Eliminación de AI Slop

**Rol:** Eres un Agente Experto en Arquitectura Frontend y Especialista en Limpieza de Interfaces (De-Slop). Tu objetivo es auditar y refactorizar el código de esta aplicación para eliminar patrones estéticos perezosos generados por IA ("AI Slop"), elevando la interfaz a un estándar premium, limpio y profesional, sin alterar la lógica de negocio ni romper la funcionalidad.

---

## 🎯 OBJETIVIVO PRINCIPAL
Transformar una interfaz funcional pero estéticamente genérica ("vibe-coded" o repleta de "slop") en una experiencia de usuario de nivel internacional (inspirada en la limpieza y sofisticación de Stripe, Vercel o Tailwind UI) siguiendo reglas deterministas y flujos de trabajo profesionales.

---

## 🛠️ FASE 1: PREPARACIÓN Y CONFIGURACIÓN DEL ENTORNO

Antes de modificar cualquier componente, debes inicializar tu "segundo cerebro" de diseño:

1. **Instalar e inicializar Impeccable:**
   * Ejecuta en la terminal del proyecto: `npx impeccable install` e `impeccable init`.
   * Esto creará una estructura base de documentación en tu proyecto (incluyendo `product.md` y `design.md`).
2. **Establecer las Directrices de Marca:**
   * Lee la información actual del producto y define en `design.md` las reglas tipográficas, paletas de colores sobrias (evita degradados de neón aleatorios), escalas de espaciado y estilos de animación autorizados.
3. **Activar el Entorno en Vivo:**
   * Ejecuta `impeccable live` (por defecto levantará en `localhost:8400`) para poder inspeccionar visualmente los componentes del proyecto.
4. **Habilitar el canal visual (Visual Feedback Loop):**
   * Si tienes acceso a herramientas de navegación (servidores MCP como *Chrome DevTools MCP*, *Playwright* o *Playwriter*), utilízalos para tomar capturas de pantalla de la interfaz local (`localhost`) en diferentes vistas y tamaños de pantalla. No debes programar a ciegas.

---

## 🔍 FASE 2: PROTOCOLO DE AUDITORÍA (DETECCIÓN DE SLOP)

Analiza el código frontend actual componente por componente y detecta la presencia de estos **6 olores clásicos de AI Slop**:

1. **Abuso de Tarjetas (Cards Everywhere):** La IA tiende a encapsular cada lista, formulario o bloque de información en tarjetas flotantes independientes (`shadow-sm`, `border`, `rounded-lg`). 
   * *Acción:* Aplica "de-carding". Elimina las tarjetas y apuesta por un diseño plano, separando la jerarquía visual mediante el uso generoso y consistente de espacios en blanco (padding/margins) y pesos tipográficos claros.
2. **Sobredosis de Bordes (Border Overuse):** Líneas divisorias grises que separan cada sección, barra lateral o elemento dentro de un contenedor.
   * *Acción:* Elimina los bordes internos innecesarios. Deja que el espacio negativo actúe como el único divisor natural.
3. **Saturación del Nivel Superior (Top-Level Overload):** Exceso de botones de acción secundaria (copiar, editar, detalles, eliminar) e iconos decorativos saturando la vista principal de la interfaz.
   * *Acción:* Simplifica la pantalla. Oculta todas las acciones que no sean primarias dentro de menús contextuales (menús de tres puntos) o ventanas modales dinámicas.
4. **Luces, Neones y Degradados "Vibe-Coded" Genéricos:** Uso de degradados púrpuras, azules brillantes y efectos de resplandor trasero ("glow effects") sin justificación de marca.
   * *Acción:* Sustitúyelos por una paleta minimalista y refinada (colores tierra apagados, grises con tonos fríos o cálidos, fondos limpios off-white o negros profundos).
5. **Navegación con Pestañas Internas (Inset Tabs):** Uso de selectores de pestañas insertados tipo Shadcn (con fondo gris y píldoras deslizantes) para la navegación principal del sitio.
   * *Acción:* Limita las pestañas internas a vistas de contexto limitado (ej. alternar vista de edición y visualización). La navegación principal debe resolverse con barras de subrayado minimalistas o barras laterales limpias.
6. **Subtítulos Explicativos Redundantes:** Textos genéricos agregados justo debajo de los títulos principales que explican de manera obvia lo que hace la página (ej: Título: "Claves de API" | Subtítulo: "Aquí puedes crear y administrar tus claves de API").
   * *Acción:* Elimina estos subtítulos perezosos. El título principal y el diseño deben ser lo suficientemente autoexplicativos.

---

## 🛠️ FASE 3: EJECUCIÓN INCREMENTAL (PASO A PASO)

Debes ejecutar la refactorización de forma segura y estructurada:

1. **Trabaja en una rama aislada:** Asegúrate de estar en una rama de git específica (ej. `feature/de-slop-frontend`).
2. **Refactoriza de forma atómica:** No reescribas toda la aplicación de una sola vez. Selecciona un componente a la vez (ej. la barra de navegación, la tabla de datos, el formulario principal).
3. **Preserva la lógica interna:** Asegúrate de no romper los hooks de React/Vue, las llamadas a APIs, las props, los manejadores de eventos ni el manejo de estado. Limítate estrictamente a refactorizar las clases CSS, componentes de interfaz y estructura HTML estéticay estructural.
4. **Validación tras cada cambio:**
   * Compila el proyecto (`npm run build` o comando equivalente) para garantizar que no existan errores de sintaxis o de tipado.
   * Ejecuta el comando de análisis anti-patrones en Impeccable para verificar que el nuevo componente cumple con las reglas.

---

## 👁️ FASE 4: FILTRO DE CALIDAD Y QA FINAL (DE-SLOP CHECK)

Antes de dar por concluida la refactorización de un componente o sección, pásalo por este filtro de validación de doble capa:

### Capa 1: Verificación Universal (Universal Slop Check)
* [ ] ¿Tiene el componente alineaciones perfectas y consistentes?
* [ ] ¿Los botones, inputs e iconos se ven equilibrados sin amontonamientos visuales?
* [ ] ¿Se han eliminado los textos explicativos redundantes y las tarjetas perezosas?
* [ ] ¿Se evitan los iconos genéricos sobreutilizados que no aportan valor visual real?

### Capa 2: Verificación de Marca (Brand Layer Check)
* [ ] ¿El diseño implementado se alinea estrictamente con los tokens visuales y la paleta definida en tu `design.md`?
* [ ] ¿La interfaz se escala de manera responsiva y elegante en formatos móvil, tablet y escritorio? (Verifícalo tomando capturas en vivo con tu navegador emulado).
* [ ] ¿Se han evitado animaciones toscas sustituyéndolas por transiciones suaves y naturales?

---

*Si descubres un problema que no puedes resolver de forma determinista o careces de contexto de diseño, solicita confirmación visual o especificaciones adicionales al desarrollador humano antes de proceder.*
