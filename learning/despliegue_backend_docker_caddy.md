# Guía Didáctica: ¿Cómo funciona el despliegue del Backend? (Docker, Dockerfile, Docker Compose y Caddy)

Esta guía explica desde cero y con analogías intuitivas las piezas que hacen funcionar el backend de **Arrendis** en un servidor de producción.

---

## 🧩 1. La Gran Pregunta: ¿Por qué necesitamos todo esto?

En tu ordenador local (`localhost`):
1. Tienes instalado Python 3.12/3.14.
2. Tienes tu entorno virtual `venv` con librerías instaladas.
3. Ejecutas `uvicorn backend.api.main:app` y funciona.

**El problema al ir a un servidor en internet:**
Si contratas un servidor virgen en la nube (como Ubuntu en Oracle Cloud), el servidor viene **vacío**: no tiene tus librerías de C/C++ que necesita PyMuPDF para leer PDFs, no tiene tus dependencias exactas de Python y no tiene certificados de seguridad HTTPS. 

Para resolver el clásico problema de *"en mi máquina sí funciona pero en el servidor falla"*, nació **Docker**.

---

## 📦 2. ¿Qué es Docker? (La Analogía del Contenedor de Barco)

Antes de los contenedores marítimos de transporte, meter mercancía en un barco era un caos: sacos de grano, cajas sueltas, coches... Si llovía, la comida se pudría; si se movía el barco, se rompía la carga.
El contenedor estándar resolvió esto: da igual lo que haya dentro (ordenadores, plátanos o muebles), **por fuera es una caja rectangular estándar que encaja en cualquier grúa o barco del mundo**.

En software, **Docker hace exactamente lo mismo**:
- Empaqueta tu aplicación junto con su versión exacta de Python, sus librerías del sistema operativo y tu código dentro de una "caja cerrada" (**Contenedor**).
- Esa caja funciona **exactamente igual** en tu portátil con Linux, en un MacBook o en el servidor de Oracle Cloud.

---

## 📜 3. ¿Qué es un `Dockerfile`? (La Receta de Cocina)

Un **`Dockerfile`** es un archivo de texto con las instrucciones paso a paso para **construir esa caja** (llamada **Imagen de Docker**).

Revisemos el [Dockerfile](file:///home/carlos/rental-handler/Dockerfile) de nuestro proyecto línea por línea:

```dockerfile
# 1. ¿De qué base partimos? Un Linux Debian ultra ligero con Python 3.12 ya puesto.
FROM python:3.12-slim

# 2. ¿En qué carpeta dentro del contenedor vamos a trabajar?
WORKDIR /app

# 3. Instalar librerías de C necesarias en Linux para compilar ciertas dependencias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar la lista de paquetes de Python e instalarlos dentro del contenedor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar todo el código de Arrendis dentro del contenedor
COPY . .

# 6. Indicar que el contenedor responderá por el puerto 8000
EXPOSE 8000

# 7. El comando que se ejecuta automáticamente al encender el contenedor
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

> **Diferencia clave:**
> - **Imagen:** Es el resultado congelado de seguir la receta (el instalador o molde).
> - **Contenedor:** Es la imagen "en ejecución" (el proceso vivo corriendo en la memoria del servidor).

---

## 🎼 4. ¿Qué es Docker Compose? (El Director de Orquesta)

Una aplicación real rara vez tiene una sola pieza. En nuestro caso necesitamos:
1. El contenedor del **Backend** (FastAPI).
2. El contenedor de **Caddy** (el servidor web / proxy seguro).

Podrías arrancar cada contenedor a mano con comandos larguísimos de terminal (`docker run -p 80:80 -v ... --net ...`), pero es incómodo y fácil de olvidar.

**Docker Compose** es una herramienta que lee un archivo YAML (`docker-compose.prod.yml`) y **levanta, conecta y configura todos los contenedores a la vez con un solo comando**:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### ¿Qué hace nuestro `docker-compose.prod.yml`?

1. **Crea una red interna privada:**  
   El backend y Caddy se pueden comunicar entre ellos por su nombre (Caddy puede llamar a `http://backend:8000`), sin exponer el backend directamente a todo internet.

2. **Define Volúmenes Persistentes (`volumes`):**  
   Por defecto, cuando un contenedor se apaga o se actualiza, **todo lo que hay dentro se destruye**.  
   Para que nuestra base de datos SQLite (`rental.db`) y las fotos de propiedades no se borren nunca, conectamos una carpeta del disco duro real del servidor con el contenedor:
   ```yaml
   volumes:
     - ./data:/app/data
   ```
   Cualquier cambio que el backend guarde en `/app/data` se escribe físicamente en el disco NVMe de tu servidor Oracle.

3. **Inyecta las Variables de Entorno (`env_file: .env`):**  
   Le pasa al contenedor de FastAPI las contraseñas, secretos y rutas sin escribirlas en el código.

---

## 🛡️ 5. ¿Qué es Caddy? (El Portero del Edificio con Candado HTTPS)

Cuando pones un servidor en internet, los navegadores (Chrome, Safari) exigen comunicarse por **HTTPS** (puerto 443 seguro con candado verde). Si intentan entrar por HTTP plano (puerto 80), avisan de "Sitio no seguro".

Para tener HTTPS necesitas un **Certificado SSL/TLS** (emitido por entidades como Let's Encrypt), que demuestra que `api.arrendis.com` realmente te pertenece. Antiguamente, renovar certificados cada 90 días con Nginx o Apache era una pesadilla técnica de scripts y cronjobs.

**Aquí entra Caddy:**
* **Caddy** es un servidor web y *Reverse Proxy* (proxy inverso) de última generación escrito en Go.
* Su superpoder: **Gestión automática de HTTPS**. 
* En cuanto lo enciendes, Caddy contacta con Let's Encrypt, demuestra la propiedad de tu dominio, descarga los certificados SSL y los renueva de por vida automáticamente en segundo plano sin que tú muevas un dedo.

### ¿Qué hace nuestro `Caddyfile`?

El archivo de configuración de Caddy tiene solo 3 líneas:

```caddy
api.arrendis.com {
    reverse_proxy backend:8000
}
```

**Flujo en la vida real:**
1. Alguien hace una petición desde el navegador o la app a `https://api.arrendis.com/api/properties`.
2. La petición llega al puerto `443` del servidor.
3. **Caddy** atiende la llamada:
   - Valida el cifrado SSL (candado verde).
   - Hace de "escudo" protector contra ataques y peticiones malformadas.
   - Pasa la petición limpia internamente a tu contenedor de FastAPI: `backend:8000`.
4. FastAPI responde con el JSON y Caddy se lo devuelve cifrado al usuario.

---

## 🗺️ 6. Resumen Visual del Flujo Completo

```
Internet (Usuario / Cloudflare Worker / App Móvil)
                     │
                     ▼ (Petición HTTPS segura :443)
┌────────────────────────────────────────────────────────┐
│ Servidor Oracle Cloud (Ubuntu VM)                      │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Contenedor Caddy                                 │  │
│  │  - Certificados SSL automáticos (Let's Encrypt)  │  │
│  │  - Redirige tráfico :80 (HTTP) -> :443 (HTTPS)   │  │
│  └──────────────────────────┬───────────────────────┘  │
│                             │                          │
│                             ▼ (Red interna Docker)     │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Contenedor Backend (FastAPI en Python 3.12)       │  │
│  │  - Construido según las reglas del Dockerfile    │  │
│  │  - Arrancado y gestionado por Docker Compose     │  │
│  └──────────────────────────┬───────────────────────┘  │
│                             │                          │
│                             ▼ (Volumen montado)        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Disco Real del Servidor (/data/rental.db)        │  │
│  │  - Los datos NUNCA se pierden al reiniciar       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## ⚡ 7. Chuleta de Comandos Útiles en Producción

Cuando estés conectado por SSH a la máquina de Oracle Cloud, estos son los únicos comandos que usarás:

| Comando | Para qué sirve |
| :--- | :--- |
| `docker-compose -f docker-compose.prod.yml up -d --build` | Construye y arranca todo en segundo plano (modo daemon `-d`). |
| `docker-compose -f docker-compose.prod.yml ps` | Muestra el estado de los contenedores (si están corriendo o parados). |
| `docker-compose -f docker-compose.prod.yml logs -f backend` | Ver los logs en tiempo real del backend (para depurar errores). |
| `docker-compose -f docker-compose.prod.yml logs -f caddy` | Ver los logs de Caddy y la emisión de certificados SSL. |
| `docker-compose -f docker-compose.prod.yml down` | Apaga los contenedores de forma ordenada (sin borrar los datos del disco). |
| `docker-compose -f docker-compose.prod.yml restart backend` | Reinicia únicamente el proceso del backend. |

---

## 🚪 8. Reverse Proxy vs API Gateway: ¿Cuál es la diferencia y cómo encaja en tu arquitectura?

### ¿El Reverse Proxy solo sirve para HTTPS?
**No**, aunque el cifrado SSL/TLS automático es su superpoder más visible, un Reverse Proxy como **Caddy** (o Nginx) hace mucho más:
1. **Ocultación de infraestructura interna:** El cliente externo solo conoce `api.arrendis.com:443`. Nadie sabe qué puertos internos (`8000`, `8001`), IPs privadas o tecnologías corren por detrás.
2. **Compresión al vuelo:** Puede comprimir respuestas JSON pesadas con Gzip o Zstandard automáticamente antes de mandarlas por la red para que viajen más rápido.
3. **Manejo de terminación SSL eficiente:** Quita la carga criptográfica pesada al proceso de Python, dejándolo libre solo para ejecutar la lógica de negocio.
4. **Protección básica contra Slowloris y ataques DoS:** Gestiona miles de conexiones TCP simultáneas de forma ultra eficiente en Go sin colapsar el hilo de FastAPI.

---

### Reverse Proxy vs API Gateway: ¿Qué hace cada uno?

| Capacidad | Reverse Proxy (Caddy / Nginx) | API Gateway (Kong, Traefik, o FastAPI Middleware) |
| :--- | :--- | :--- |
| **Cifrado HTTPS y Certificados SSL** | Sí (Caddy lo hace nativo y gratis) | Sí (o se delega al proxy) |
| **Enrutamiento por subdominio / path** | Sí (`api.arrendis.com` -> `backend:8000`) | Sí (`/v1/users` -> `auth_service`, etc.) |
| **Rate Limiting (Control de peticiones/min)** | Básico (por IP) | Avanzado (por IP, por usuario, por API Key, por Tier) |
| **Autenticación y RBAC (Roles/Permisos)** | Muy limitado / complejo | Sí (Valida JWT, roles, scopes antes de tocar la app) |
| **Manipulación y validación de Headers** | Sí | Sí |
| **Transformación de peticiones / respuestas** | No | Sí (ej. transformar XML antiguo a JSON moderno) |

---

### ¿Encajaría un API Gateway en tu arquitectura o sería muy complejo?

**Encajaría perfectamente y es cero complejo**, porque tienes **dos formas muy elegantes de implementarlo**:

#### Enfoque A: "In-App Gateway" mediante Middlewares y Dependencias de FastAPI (El más recomendado ahora)
FastAPI ya está diseñado internamente con el patrón Gateway mediante su sistema de **Middlewares y Dependencias (`Depends`)**:
1. **Rate Limiting:** Se añade con una librería estándar de Python como `slowapi` (basada en Redis o en memoria). Puedes poner:
   ```python
   @router.post("/auth/login")
   @limiter.limit("5/minute")  # Máximo 5 intentos por minuto contra ataques de fuerza bruta
   async def login(...): ...
   ```
2. **RBAC (Control de Acceso Basado en Roles):** Tu sistema actual de autenticación (`backend/adapters/auth_adapter.py`) ya extrae el JWT. Solo requiere añadir una dependencia que compruebe si el usuario tiene rol `admin`, `landlord` o `tenant`.
3. **Security Headers:** FastAPI tiene middleware directo para inyectar cabeceras CORS, HSTS, X-Content-Type-Options y Content-Security-Policy.

👉 **Ventajas:** Cero infraestructura extra, todo en código Python tipado, testeable con `pytest` y desplegado dentro del mismo contenedor de Docker sin consumir más RAM.

#### Enfoque B: API Gateway Externo dedicado (Kong / Traefik / Cloudflare)
Si en el futuro tu backend se dividiera en microservicios independientes:
- Podrías colocar **Cloudflare** como primer API Gateway en el borde (Cloudflare ya tiene Rate Limiting y WAF activables con un clic en su panel).
- O añadir un contenedor ligero como **Traefik** o **Kong** entre Caddy y los servicios.

### Conclusión
Caddy se queda en la frontera recibiendo el tráfico HTTPS, y FastAPI actúa de forma nativa como tu API Gateway para Rate Limit, Headers y RBAC con un control total y sin añadir complejidad a tus servidores.
