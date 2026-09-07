# Plan Técnico: CI/CD Automatizado y Entorno de Staging (100% Gratuito)

Este documento describe la arquitectura, flujo de trabajo y configuración técnica para disponer de un entorno de **Staging** (pre-producción) y un pipeline de **CI/CD con GitHub Actions**, manteniendo el coste operativo mensual en **0,00 €/mes** sobre la infraestructura existente (Cloudflare + Oracle Cloud Always Free).

> [!NOTE]
> Esta fase se ejecutará una vez completado y verificado el primer despliegue manual a producción (F-23).

---

## 🏗️ 1. Arquitectura de Entornos Dual (Staging vs Producción)

```
[ Git Push / Merge ]
         │
         ├─── Rama 'develop' ──► GitHub Actions (Tests) ──► Staging
         │                                                    ├── Frontend: staging.arrendis.com (Cloudflare Pages)
         │                                                    └── Backend:  api-staging.arrendis.com (Oracle VM / Docker)
         │
         └─── Rama 'main'    ──► GitHub Actions (Tests) ──► Producción
                                                              ├── Frontend: app.arrendis.com (Cloudflare Pages)
                                                              └── Backend:  api.arrendis.com (Oracle VM / Docker)
```

### Tabla Comparativa de Componentes

| Parámetro | Entorno de Staging | Entorno de Producción | Coste Adicional |
| :--- | :--- | :--- | :--- |
| **Rama Git** | `develop` | `main` | 0 € |
| **Frontend URL** | `https://staging.arrendis.com` | `https://app.arrendis.com` | 0 € (Subdominio Cloudflare) |
| **Hosting Frontend** | Cloudflare Pages (Branch Deployment) | Cloudflare Pages (Production) | 0 € |
| **Backend API URL** | `https://api-staging.arrendis.com` | `https://api.arrendis.com` | 0 € (Subdominio Cloudflare) |
| **Puerto Docker Host** | `8001` (contenedor `backend_staging`) | `8000` (contenedor `backend_prod`) | 0 € (Misma VM Oracle) |
| **Base de Datos SQLite** | `data/staging/rental.db` | `data/rental.db` | 0 € (Disco persistente NVMe) |
| **Base de Datos Estado** | Datos volátiles / de prueba | Datos reales persistentes y con backup | 0 € |

---

## 🔄 2. Flujo de Trabajo (Developer Experience)

1. **Desarrollo:** Desarrollas una nueva funcionalidad en una rama feature (`feature/nueva-funcionalidad`) y abres PR a `develop`.
2. **CI Automatizado (Test Gate):**
   - GitHub Actions levanta un runner con Python y Node.js.
   - Ejecuta la suite de pruebas del backend (`pytest`) y comprobaciones del frontend.
   - Si algún test falla, el PR queda bloqueado.
3. **Despliegue a Staging (Automático al hacer push a `develop`):**
   - Cloudflare Pages detecta el push a `develop` y compila para `staging.arrendis.com`.
   - GitHub Actions se conecta por SSH a Oracle Cloud y levanta el contenedor de Staging.
   - **Pruebas en vivo:** Puedes entrar con tu navegador o móvil a `staging.arrendis.com`, subir PDFs de prueba y verificar que no hay regresiones.
4. **Pase a Producción (Merge `develop` ➔ `main`):**
   - Al estar 100% verificado en staging, haces merge de `develop` a `main`.
   - GitHub Actions pasa tests y despliega automáticamente en `app.arrendis.com` y `api.arrendis.com`.

---

## 🛠️ 3. Especificación Técnica de Implementación

### 3.1. Orquestación Docker Dual en Oracle Cloud (`docker-compose.yml`)

En el servidor se gestionan ambos servicios de forma aislada compartiendo el proxy inverso Caddy:

```yaml
version: '3.8'

services:
  # ==========================================
  # PRODUCCIÓN
  # ==========================================
  backend_prod:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    env_file: .env
    volumes:
      - ./data:/app/data
    expose:
      - "8000"

  # ==========================================
  # STAGING
  # ==========================================
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

  # ==========================================
  # REVERSE PROXY & SSL (Caddy)
  # ==========================================
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
      - backend_prod
      - backend_staging

volumes:
  caddy_data:
  caddy_config:
```

### 3.2. Configuración de Caddy (`Caddyfile`)

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

### 3.3. Pipeline de GitHub Actions (`.github/workflows/deploy.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop, main ]

jobs:
  test:
    name: Run Test Suite
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Backend Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt pytest pytest-cov

      - name: Run Backend Tests
        env:
          TESTING: 1
          JWT_SECRET: test-secret-key-32-chars-minimum
        run: pytest --maxfail=1 -v

  deploy-staging:
    name: Deploy to Staging (Oracle Cloud)
    needs: test
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.ORACLE_SSH_HOST }}
          username: ubuntu
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd /home/ubuntu/arrendis-staging
            git pull origin develop
            docker-compose up -d --build backend_staging

  deploy-prod:
    name: Deploy to Production (Oracle Cloud)
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.ORACLE_SSH_HOST }}
          username: ubuntu
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd /home/ubuntu/arrendis
            git pull origin main
            docker-compose up -d --build backend_prod
```

---

## 📋 4. Pasos para su Activación Futura

1. Crear en Cloudflare DNS los registros A para `api-staging.arrendis.com` y configurar el branch preview en Cloudflare Pages para `staging.arrendis.com`.
2. Guardar en **GitHub Repository Secrets**:
   - `ORACLE_SSH_HOST`: IP pública de la instancia de Oracle.
   - `ORACLE_SSH_KEY`: Clave privada SSH.
3. Crear el workflow `.github/workflows/deploy.yml` en el repositorio.
4. Crear `.env.staging` en la máquina de Oracle con su propia base de datos aislada (`data_staging/rental.db`).
