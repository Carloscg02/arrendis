# Plan de Despliegue a Producción — Arrendis (100% Gratuito)

Este documento detalla la hoja de ruta técnica completa y paso a paso para llevar **Arrendis** desde el entorno de desarrollo local (`localhost`) a producción en internet, con tu propio dominio comercial (**`arrendis.com`** o **`arrendis.es`**), coste de servidor mensual de **0,00 €/mes** y capacidad para soportar cientos de miles de visitas.

---

## 🗺️ Mapa de Arquitectura en Producción

```
[ Usuario en Navegador ]                    [ Propietario reenvía factura ]
          │                                                │
          ▼ (HTTPS)                                        ▼ (SMTP)
┌───────────────────────────────┐              ┌───────────────────────────────┐
│       Cloudflare Pages        │              │   Cloudflare Email Routing    │
│  (Frontend React + Vite SPA)  │              │    (facturas@arrendis.com)    │
│   Dominio: app.arrendis.com   │              └───────────────┬───────────────┘
└───────────────┬───────────────┘                              │ (Dispara evento)
                │                                              ▼
                │ (Peticiones API)             ┌───────────────────────────────┐
                │                              │    Cloudflare Email Worker    │
                │                              │   (Parsea PDF y multipart)    │
                │                              └───────────────┬───────────────┘
                │                                              │ (POST Webhook + Secret)
                ▼                                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Oracle Cloud Infrastructure (Always Free)                 │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐   │
│   │ Caddy / Nginx Reverse Proxy (SSL automático Let's Encrypt)           │   │
│   │ Dominio: api.arrendis.com                                            │   │
│   └──────────────────────────────────┬───────────────────────────────────┘   │
│                                      │                                       │
│   ┌──────────────────────────────────▼───────────────────────────────────┐   │
│   │ Contenedor Docker: Backend FastAPI (Python 3.12 / 3.14)              │   │
│   │  - Pipeline Extracción Suministros (PyMuPDF + Regex / Gemini)        │   │
│   │  - Motor Fiscal AEAT (IRPF, Amortizaciones, Rendimiento Neto)        │   │
│   │  - Autenticación Segura (JWT Shielded + Bcrypt)                      │   │
│   └──────────────────────────────────┬───────────────────────────────────┘   │
│                                      │ (Volumen Persistente)                 │
│   ┌──────────────────────────────────▼───────────────────────────────────┐   │
│   │ Disco NVMe Persistente (200 GB):                                     │   │
│   │  - data/rental.db (SQLite en modo WAL)                               │   │
│   │  - data/images/   (Imágenes de propiedades)                          │   │
│   └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏷️ Fase 1: Compra del Dominio por ~10 €/año

Para evitar registradores que cobran precios inflados tras el primer año (como GoDaddy o 1&1), el estándar es comprar el dominio al **precio mayorista de coste**.

### Opción A: Si eliges `.com` (`arrendis.com`)
1. Ve a [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/).
2. Crea una cuenta gratuita en Cloudflare.
3. En el menú lateral, ve a **Domain Registration** > **Register Domain**.
4. Busca `arrendis.com`.
5. El coste es el precio de coste fijado por el registro ICANN (~**9,50 € / año** sin comisiones ni sobreprecios).
6. Al comprarlo en Cloudflare, el dominio ya queda automáticamente configurado con DNS ultrarrápido y protección DDoS.

### Opción B: Si eliges `.es` (`arrendis.es`)
1. Cloudflare Registrar opera principalmente con TLDs globales (`.com`, `.net`, `.org`). Para dominios españoles `.es`, el registrador más recomendado, limpio y sin sobreprecios ocultos en España es **DonDominio** o **Porkbun** (~**8-10 € / año**).
2. Tras comprar `arrendis.es` en DonDominio:
   - Añades el dominio a tu panel gratuito de Cloudflare ("Add a site").
   - Cloudflare te dará dos servidores DNS (ej. `ana.ns.cloudflare.com` y `bob.ns.cloudflare.com`).
   - En el panel de DonDominio, cambias las DNS por las de Cloudflare. Listo.

---

## 💻 Fase 2: Despliegue del Frontend (Cloudflare Pages — 100% Gratis)

Cloudflare Pages aloja aplicaciones React con tráfico y ancho de banda ilimitados, CDN global y SSL automático.

1. **Subir el código a GitHub:**
   Asegúrate de que tu repositorio (puede ser privado) esté subido a tu cuenta de GitHub.

2. **Crear el proyecto en Cloudflare Pages:**
   - En el panel de Cloudflare: **Workers & Pages** > **Create application** > pestaña **Pages** > **Connect to Git**.
   - Selecciona el repositorio de Arrendis.

3. **Configuración de Build:**
   - **Framework preset:** `Vite`
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - **Variables de entorno (Environment Variables):**
     - `VITE_API_URL`: `https://api.arrendis.com/api`

4. **Asignar Dominio Personalizado:**
   - En la pestaña **Custom domains** del proyecto en Pages: añade `app.arrendis.com` (o `arrendis.com`).
   - Cloudflare configurará el DNS y el certificado HTTPS automáticamente en segundos.

---

## 📬 Fase 3: Ingesta de Facturas por Email (Cloudflare Workers — 100% Gratis)

Permite que cualquier correo enviado a `facturas@arrendis.com` se procese y contabilice automáticamente.

1. **Activar Email Routing:**
   - En tu panel de Cloudflare, selecciona tu dominio `arrendis.com` > **Email Routing**.
   - Haz clic en **Enable Email Routing** (Cloudflare añade los registros MX y SPF automáticamente).

2. **Crear el Worker:**
   - En **Workers & Pages** > **Create application** > **Create Worker**.
   - Nómbralo: `arrendis-email-ingest`.
   - Pega el código del script que dejamos preparado en `scripts/cloudflare_email_worker.js`.
   - En **Settings** > **Variables**:
     - Variable: `RENTAL_HANDLER_WEBHOOK_URL` = `https://api.arrendis.com/api/webhooks/inbound-email`
     - Secret (cifrado): `RENTAL_HANDLER_WEBHOOK_SECRET` = `tu-clave-secreta-super-segura`

3. **Configurar la Regla de Reenvío:**
   - En **Email Routing** > **Routing Rules** > **Create rule**:
     - Custom address: `facturas@arrendis.com`
     - Action: **Send to a Worker** > Selecciona `arrendis-email-ingest`.
     - Guarda la regla.

---

## ⚙️ Fase 4: Despliegue del Backend y Base de Datos (FastAPI + SQLite)

Para que SQLite y las imágenes no se borren nunca, el backend necesita un entorno con almacenamiento persistente.

### Opción Recomendada: Oracle Cloud "Always Free" (Coste: 0,00 €/mes)

Oracle Cloud regala de por vida instancias ARM de hasta **4 núcleos, 24 GB de RAM y 200 GB de disco NVMe**.

#### Paso 1: Crear la cuenta y la Máquina Virtual
1. Regístrate en [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).  
   *(Pide tarjeta para verificar identidad; hace un cargo temporal de ~1€ que se reembolsa al instante).*
2. En el panel de OCI: **Compute** > **Instances** > **Create Instance**.
   - **Image:** Ubuntu 22.04 o 24.04 LTS.
   - **Shape:** `Ampere VM.Standard.A1.Flex` (Configura 2 o 4 OCPUs y 12 a 24 GB de RAM).
   - **Boot Volume:** 50 a 100 GB.
   - Descarga la clave privada SSH (`id_rsa`).
3. En la sección de Red (Virtual Cloud Network / Security Lists): abre los puertos `80` (HTTP) y `443` (HTTPS) en el Firewall.

#### Paso 2: Conectarse y preparar Docker
Conéctate por terminal a tu máquina:
```bash
ssh -i id_rsa ubuntu@<IP_PUBLICA_DE_ORACLE>
```

Instala Docker y Docker Compose:
```bash
sudo apt update && sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu
```

#### Paso 3: Clonar el repositorio y configurar producción
```bash
git clone https://github.com/tu-usuario/rental-handler.git arrendis
cd arrendis
```

Crea el archivo `.env` de producción:
```bash
cat << 'EOF' > .env
DATABASE_PATH=data/rental.db
JWT_SECRET=genera-una-cadena-aleatoria-de-64-caracteres
INBOUND_WEBHOOK_SECRET=tu-clave-secreta-super-segura
INBOUND_EMAIL_ADDRESS=facturas@arrendis.com
GEMINI_API_KEY=tu-clave-de-gemini-opcional
EOF
```

#### Paso 4: Levantar Backend con Caddy (HTTPS automático)
Crea un `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    env_file: .env
    volumes:
      - ./data:/app/data
    expose:
      - "8000"

  caddy:
    image: caddy:2-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend

volumes:
  caddy_data:
  caddy_config:
```

Crea el archivo `Caddyfile` (Caddy gestiona automáticamente los certificados SSL con Let's Encrypt):
```caddy
api.arrendis.com {
    reverse_proxy backend:8000
}
```

Crea el `Dockerfile` optimizado:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Lanza el servicio:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Paso 5: Apuntar el subdominio DNS en Cloudflare
En el panel DNS de Cloudflare para `arrendis.com`:
- Añade un registro **A**:
  - **Name:** `api`
  - **IPv4 address:** `<IP_PUBLICA_DE_ORACLE>`
  - **Proxy status:** Proxied (nube naranja activada) o DNS Only.

---

## 🔒 Fase 5: Estrategia de Copias de Seguridad (Backup de SQLite)

Dado que SQLite reside en un único archivo (`data/rental.db`), hacer una copia de seguridad perfecta sin detener el servidor es trivial gracias al comando oficial de SQLite `.backup`.

Crea un script diario en el servidor (`/home/ubuntu/backup.sh`):
```bash
#!/bin/bash
FECHA=$(date +%Y%m%d_%H%M%S)
sqlite3 /home/ubuntu/arrendis/data/rental.db ".backup '/home/ubuntu/backups/rental_$FECHA.db'"
find /home/ubuntu/backups/ -type f -mtime +30 -delete
```

Añádelo al `crontab -e` para que se ejecute cada noche a las 03:00 AM:
```cron
0 3 * * * /home/ubuntu/backup.sh
```

---

## ✅ Fase 6: Checklist de Verificación Final en Producción

Una vez completado el despliegue:

1. [ ] **Acceso Web:** Entrar a `https://app.arrendis.com` y verificar que carga con candado verde HTTPS.
2. [ ] **Registro / Login:** Registrar tu usuario de administrador y verificar que el token JWT funciona.
3. [ ] **Crear Propiedad:** Crear un inmueble y asignarle su CUPS de electricidad real.
4. [ ] **Reenvío Real desde Gmail:** Abrir tu aplicación de correo y reenviar una factura PDF a `facturas@arrendis.com`.
5. [ ] **Contabilización:** Refrescar la propiedad y comprobar que el gasto aparece automáticamente con estado **Verificado** y categoría fiscal de suministros.
