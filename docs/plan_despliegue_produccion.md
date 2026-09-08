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
                │                              │ (Standalone Zero-Dependencies)│
                │                              └───────────────┬───────────────┘
                │                                              │ (POST Webhook + Secret)
                ▼                                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Oracle Cloud Infrastructure (Always Free)                 │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐   │
│   │ Caddy Reverse Proxy (SSL automático Let's Encrypt + HTTP->HTTPS)     │   │
│   │ Dominio: api.arrendis.com (Puertos 80 y 443)                         │   │
│   └──────────────────────────────────┬───────────────────────────────────┘   │
│                                      │ (Red interna Docker)                  │
│   ┌──────────────────────────────────▼───────────────────────────────────┐   │
│   │ Contenedor Docker: Backend FastAPI (Python 3.12 en Ubuntu 22.04/24.04)│   │
│   │  - Pipeline Extracción Suministros (PyMuPDF + Regex / Gemini)        │   │
│   │  - Motor Fiscal AEAT (IRPF, Amortizaciones, Rendimiento Neto)        │   │
│   │  - Autenticación Segura (JWT Shielded + Bcrypt)                      │   │
│   │  - CORS configurado para Cloudflare Pages y dominio de producción    │   │
│   └──────────────────────────────────┬───────────────────────────────────┘   │
│                                      │ (Volumen Persistente)                 │
│   ┌──────────────────────────────────▼───────────────────────────────────┐   │
│   │ Disco NVMe Persistente (50 a 100 GB):                                │   │
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
4. Busca tu dominio (ej. `arrendis.com`).
5. El coste es el precio de coste fijado por el registro ICANN (~**9,50 € / año** sin comisiones ni sobreprecios).
6. Al comprarlo en Cloudflare, el dominio ya queda automáticamente configurado con DNS ultrarrápido y protección DDoS.

### Opción B: Si eliges `.es` (`arrendis.es`)
1. Cloudflare Registrar opera principalmente con TLDs globales (`.com`, `.net`, `.org`). Para dominios españoles `.es`, el registrador recomendado y sin sobreprecios ocultos en España es **DonDominio** o **Porkbun** (~**8-10 € / año**).
2. Tras comprar `arrendis.es`:
   - Añades el dominio a tu panel gratuito de Cloudflare ("Add a site").
   - Cloudflare te dará dos servidores DNS (ej. `ana.ns.cloudflare.com` y `bob.ns.cloudflare.com`).
   - En el panel de DonDominio, cambias las DNS por las de Cloudflare. Listo.

---

## 💻 Fase 2: Despliegue del Frontend (Cloudflare Pages — 100% Gratis)

Cloudflare Pages aloja aplicaciones React como archivos estáticos puros distribuidos por su CDN global, con ancho de banda ilimitado y SSL automático (**no necesita Docker**).

1. **Subir el código a GitHub:**
   Asegúrate de que tu repositorio esté subido a tu cuenta de GitHub (`Carloscg02/arrendis`).

2. **Crear el proyecto en Cloudflare Pages:**
   - En el panel de Cloudflare: ve a **Workers & Pages** (o **Compute**) > **Create application** > pestaña **Pages** (¡ojo, no en la pestaña Workers!) > **Connect to Git**.
   - Selecciona el repositorio de Arrendis.

3. **Configuración de Build:**
   - **Framework preset:** `Vite`
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - **Environment Variables:**
     - `VITE_API_URL`: `https://api.arrendis.com/api`

4. **Asignar Dominio Personalizado:**
   - En la pestaña **Custom domains** del proyecto en Pages: añade `app.arrendis.com` (o `arrendis.com`).
   - Cloudflare configurará el DNS y el certificado HTTPS automáticamente en segundos.

---

## 📬 Fase 3: Ingesta de Facturas por Email (Cloudflare Workers — 100% Gratis)

Permite que cualquier correo enviado a `facturas@arrendis.com` se procese y contabilice automáticamente.

1. **Activar Email Routing:**
   - En tu panel de Cloudflare, selecciona tu dominio > **Email Routing**.
   - Haz clic en **+ Onboard Domain** (o **Enable Email Routing**).
   - Cloudflare te mostrará los registros DNS (MX y SPF). Pulsa el botón para que Cloudflare los añada automáticamente.

2. **Crear el Worker:**
   - En **Workers & Pages** > **Create application** > selecciona **Start with Hello World!**.
   - Nómbralo: `arrendis-email-ingest`.
   - Haz clic en **Deploy**, luego entra a **Edit code**.
   - Borra el código de ejemplo y pega el contenido completo de [`scripts/cloudflare_email_worker.js`](file:///home/carlos/rental-handler/scripts/cloudflare_email_worker.js).
   - Haz clic en **Save and deploy**.

3. **Configurar Variables y Secretos del Worker:**
   - En la página principal del Worker > **Settings** > **Variables and Secrets** > **Add**:
     - Variable normal: `RENTAL_HANDLER_WEBHOOK_URL` = `https://api.arrendis.com/api/webhooks/inbound-email`
     - Secret (cifrado): `RENTAL_HANDLER_WEBHOOK_SECRET` = `302067091229670529e260dd3b4a67d7181888a571034436` (o la clave aleatoria que elijas; debe ser idéntica a la del `.env` del backend).
   - Guarda los cambios.

4. **Configurar la Regla de Reenvío:**
   - En **Email Routing** > **Routing Rules** > **Create rule**:
     - Custom address: `facturas@arrendis.com`
     - Action: **Send to a Worker** > Selecciona `arrendis-email-ingest`.
     - Guarda la regla.

---

## ⚙️ Fase 4: Despliegue del Backend y Base de Datos (FastAPI + SQLite + Caddy)

### Opción Recomendada: Oracle Cloud "Always Free" (Coste: 0,00 €/mes)

Oracle Cloud ofrece instancias gratuitas de por vida. La configuración ideal para Arrendis es **1 OCPU y 4 a 6 GB de RAM** con **50 GB de disco NVMe**, consumiendo una fracción mínima de tu cuota gratuita.

#### Paso 1: Crear la Red Virtual (VCN) y la Instancia
1. Regístrate en [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
   > [!TIP]
   > Si al crear la máquina Ampere recibes el error *"Out of capacity in availability domain"*, puedes hacer el **Upgrade to Pay-As-You-Go**. Oracle verifica la tarjeta (con una fianza temporal devuelta), elimina la cola de bots y te da acceso prioritario al hardware. La factura mensual sigue siendo **0,00 €** siempre que te mantengas dentro de los límites gratuitos.

2. **Crear la Red (VCN):**
   - Menú lateral > **Networking** > **Virtual Cloud Networks** > **Start VCN Wizard**.
   - Selecciona **Create VCN with Internet Connectivity** > ponle de nombre `main-vcn` > **Next** > **Create**.

3. **Crear la Máquina Virtual (Compute Instance):**
   - Menú lateral > **Compute** > **Instances** > **Create Instance**.
   - **Image:** Canonical Ubuntu 22.04 o 24.04 LTS.
   - **Shape:** `Ampere VM.Standard.A1.Flex` (1 OCPU, 4 a 6 GB RAM).
   - **Networking:**
     - Select existing virtual cloud network: `main-vcn`.
     - Subnet: `public subnet-main-vcn`.
     - **Public IPv4 address:** Comprobar que en el resumen final marque **`Yes`**.
   - **SSH Keys:** Selecciona *Generate SSH key pair for me* y pulsa **Save private key** para descargar el archivo `.key`.
   - **Boot Volume:** 50 GB.
   - Haz clic en **Create**.

4. **Abrir Puertos en el Firewall de Oracle (Security List):**
   - En la pantalla de la instancia creada, baja a **Attached VNICs** > haz clic en la subred pública.
   - Entra en **Default Security List for main-vcn** > **Add Ingress Rules**:
     - **Regla 1:** Source `0.0.0.0/0`, Protocol `TCP`, Destination Port `80`, Description `HTTP`.
     - **Regla 2:** Source `0.0.0.0/0`, Protocol `TCP`, Destination Port `443`, Description `HTTPS`.

#### Paso 2: Conectarse por SSH y preparar el Servidor
1. Desde tu terminal local, da permisos seguros a la clave descargada:
   ```bash
   chmod 600 /ruta/a/tu/clave.key
   ```
2. Conéctate a la máquina:
   ```bash
   ssh -i /ruta/a/tu/clave.key ubuntu@<IP_PUBLICA_DE_ORACLE>
   ```
3. Dentro de la máquina, instala Docker, **Docker Compose v2** y abre el firewall interno de Ubuntu:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git iptables-persistent
   sudo usermod -aG docker ubuntu
   newgrp docker

   # Abrir puertos 80 y 443 en iptables
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

#### Paso 3: Clonar el repositorio y configurar variables
```bash
git clone https://github.com/Carloscg02/arrendis.git arrendis
cd arrendis
```
*(Si te pide credenciales y quieres guardarlas permanentemente en local para no escribirlas en cada push, usa `git config --global credential.helper store`).*

Crea el archivo `.env` de producción:
```bash
echo 'DATABASE_PATH=data/rental.db
JWT_SECRET=1a354dc6b820188c7bf00107378fcc82998243a9d72ebaaf64f2f9ec567d7924
INBOUND_WEBHOOK_SECRET=302067091229670529e260dd3b4a67d7181888a571034436
INBOUND_EMAIL_ADDRESS=facturas@arrendis.com
GEMINI_API_KEY=tu-clave-de-gemini-aqui' > .env
```
*(Puedes obtener tu clave gratuita de Gemini en [Google AI Studio](https://aistudio.google.com/)).*

Crea el directorio persistente para SQLite y fotos:
```bash
mkdir -p data/images
```

#### Paso 4: Levantar Backend con Caddy (Docker Compose v2)
Los archivos `Dockerfile`, `docker-compose.prod.yml` y `Caddyfile` ya están incluidos en el repositorio.
Ejecuta el arranque con **Docker Compose v2** (`docker compose` con espacio):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```
> [!IMPORTANT]
> Usa siempre `docker compose` (con espacio) y no la versión antigua `docker-compose` (con guion), para evitar el error `KeyError: ContainerConfig`.

#### Paso 5: Apuntar el subdominio DNS en Cloudflare
En el panel DNS de Cloudflare para tu dominio:
- Añade un registro **A**:
  - **Type:** `A`
  - **Name:** `api`
  - **IPv4 address:** `<IP_PUBLICA_DE_ORACLE>`
  - **Proxy status:** DNS Only (nube gris) inicialmente, o Proxied con SSL en modo "Full".
  - Guarda el registro.

Si Caddy arrancó antes de existir el registro DNS, reinícialo para que obtenga el certificado de Let's Encrypt de inmediato:
```bash
docker compose -f docker-compose.prod.yml restart caddy
```

Comprueba que responde entrando en tu navegador a:  
👉 **`https://api.arrendis.com/docs`**

---

## 🔒 Fase 5: Estrategia de Copias de Seguridad (Backup de SQLite)

Dado que SQLite reside en un único archivo (`data/rental.db`), hacer una copia de seguridad perfecta sin detener el servidor es trivial gracias al comando oficial de SQLite `.backup`.

Crea un script diario en el servidor (`/home/ubuntu/backup.sh`):
```bash
#!/bin/bash
FECHA=$(date +%Y%m%d_%H%M%S)
mkdir -p /home/ubuntu/backups
sqlite3 /home/ubuntu/arrendis/data/rental.db ".backup '/home/ubuntu/backups/rental_$FECHA.db'"
find /home/ubuntu/backups/ -type f -mtime +30 -delete
```
Darle permisos de ejecución:
```bash
chmod +x /home/ubuntu/backup.sh
```

Añádelo al `crontab -e` para que se ejecute cada noche a las 03:00 AM:
```cron
0 3 * * * /home/ubuntu/backup.sh
```

---

## ✅ Fase 6: Checklist de Verificación Final en Producción

1. [ ] **Acceso Web:** Entrar a `https://app.arrendis.com` (o tu URL de Cloudflare Pages) y verificar que carga con candado verde HTTPS.
2. [ ] **Registro / Login:** Registrar tu usuario de administrador. Comprobar que no hay errores de CORS y que el token JWT redirige al Dashboard.
3. [ ] **Crear Propiedad:** Crear un inmueble y asignarle su CUPS de electricidad real.
4. [ ] **Reenvío Real desde Gmail:** Abrir tu correo y reenviar una factura PDF a `facturas@arrendis.com`.
5. [ ] **Contabilización Automática:** Refrescar la propiedad y comprobar que el gasto aparece automáticamente con estado **Verificado** y categoría fiscal de suministros.
