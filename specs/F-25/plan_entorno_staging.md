# Plan Técnico: Entorno de Pre-producción (Staging) Aislado

Este documento detalla la arquitectura y pasos necesarios para implementar en el futuro un entorno completo de **Staging** (pre-producción) que permita validar en internet versiones de la rama `develop` antes de promoverlas a `main`, sin coste mensual adicional (0,00 €/mes).

---

## 🏗️ 1. Arquitectura de Staging vs Producción

```
Entorno Staging (Rama develop):
- Frontend: https://staging.arrendis.com (Cloudflare Pages Preview)
- Backend API: https://api-staging.arrendis.com (Puerto 8001 / Contenedor backend_staging)
- Base de datos: data_staging/rental.db (Aislada, con datos ficticios para pruebas)

Entorno Producción (Rama main):
- Frontend: https://app.arrendis.com / https://arrendis.com
- Backend API: https://api.arrendis.com (Puerto 8000 / Contenedor backend_prod)
- Base de datos: data/rental.db (Datos reales de usuarios)
```

Ambos entornos conviven en la misma máquina virtual de Oracle Cloud (Ubuntu 22.04, 6 GB RAM) gestionados por el mismo proxy Caddy.

---

## 🌐 2. Configuración en Cloudflare

1. **DNS (Cloudflare DNS Records):**
   - Añadir registro **A**:
     - Name: `api-staging`
     - IPv4 address: `<IP_PUBLICA_DE_ORACLE>`
     - Proxy status: DNS Only o Proxied.

2. **Frontend (Cloudflare Pages Preview Deployments):**
   - En el proyecto de Pages > **Settings** > **Builds & deployments**:
     - Configurar rama de preview: `develop`.
   - En **Settings** > **Environment variables**:
     - Producción: `VITE_API_URL` = `https://api.arrendis.com/api`
     - Preview (Staging): `VITE_API_URL` = `https://api-staging.arrendis.com/api`
   - En **Custom domains**:
     - Asignar `staging.arrendis.com` a la rama `develop`.

---

## ⚙️ 3. Configuración en el Servidor Oracle Cloud

### 3.1. Orquestación Docker Dual (`docker-compose.staging.yml` o ampliado)

```yaml
services:
  backend_staging:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    env_file: .env.staging
    volumes:
      - ./data_staging:/app/data
    expose:
      - "8000"
```

### 3.2. Enrutamiento en `Caddyfile`

```caddy
# Producción
api.arrendis.com {
    reverse_proxy backend_prod:8000
}

# Staging
api-staging.arrendis.com {
    reverse_proxy backend_staging:8000
}
```

### 3.3. Archivo de entorno `.env.staging` en el servidor

```bash
DATABASE_PATH=data/rental.db
JWT_SECRET=clave-aleatoria-distinta-para-staging
INBOUND_WEBHOOK_SECRET=secreto-distinto-para-staging
INBOUND_EMAIL_ADDRESS=facturas-staging@arrendis.com
GEMINI_API_KEY=
```

---

## 🔄 4. Flujo de Trabajo en Staging

1. Desarrollar una nueva funcionalidad en rama `feature/...`.
2. Merge a `develop`.
3. El CI/CD compila para `staging.arrendis.com` y reinicia `backend_staging`.
4. El desarrollador o tester accede a `staging.arrendis.com`, prueba la interfaz y sube facturas de prueba sin riesgo de ensuciar o borrar datos de clientes reales.
5. Una vez aprobado, se abre Pull Request de `develop` a `main` para ir a producción.
