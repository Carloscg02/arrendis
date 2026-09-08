# Plan Técnico: Pipeline Automatizado de CI/CD para Producción (GitHub Actions)

Este documento detalla la implementación del pipeline de **Integración Continua (CI)** y **Despliegue Continuo (CD)** para **Arrendis**. Su objetivo es garantizar que ningún cambio roto llegue a producción y automatizar al 100% la actualización del servidor en Oracle Cloud sin intervención manual por SSH.

---

## 🎯 Objetivos de la Tarea

1. **Quality Gate (CI Automático):** En cada `push` o `pull_request` a las ramas `develop` y `main`, ejecutar la suite de pruebas del backend (`pytest`) y validar la compilación del frontend (`tsc` + `vite build`). Si algo falla, el despliegue se cancela de inmediato.
2. **Despliegue Continuo (CD Automático):** Cuando se hace merge o push a `main` y todos los tests pasan en verde:
   - **Frontend:** Cloudflare Pages ya compila y despliega automáticamente.
   - **Backend:** Una GitHub Action se conecta por SSH a Oracle Cloud y ejecuta la actualización de Docker sin tiempo de caída.

---

## 🗺️ Diagrama del Flujo

```
Desarrollador hace 'git push origin main'
                │
                ▼
      [ GitHub Actions Runner ]
                │
                ├── 1. Checkout del código
                ├── 2. Setup Python 3.12 & Node.js
                ├── 3. Ejecución de Backend Tests (pytest)
                └── 4. Validación de Frontend Build (npm run build)
                │
         ¿Pasaron los tests?
          ├── NO ──► ❌ Bloqueo, notificación de fallo en GitHub
          └── SÍ ──► ✅ Proceder al despliegue
                       │
                       ▼
          [ Conexión SSH segura a Oracle Cloud ]
                       │
                       ├── git pull origin main
                       └── docker compose -f docker-compose.prod.yml up -d --build backend
```

---

## 🔑 1. Configuración de Secretos en GitHub (GitHub Secrets)

Para que GitHub Actions pueda conectarse de forma segura a tu servidor de Oracle Cloud sin exponer contraseñas:

1. Ve a tu repositorio en GitHub: **`Carloscg02/arrendis`** > pestaña **Settings**.
2. En el menú lateral izquierdo: **Secrets and variables** > **Actions**.
3. Haz clic en **New repository secret** y añade estos 3 secretos:

| Nombre del Secreto | Valor |
| :--- | :--- |
| `ORACLE_SSH_HOST` | Tu IP pública de Oracle Cloud (ej. `80.225.189.17`) |
| `ORACLE_SSH_USER` | `ubuntu` |
| `ORACLE_SSH_KEY` | El contenido de texto completo de tu archivo de clave privada `.key` (abierto con bloc de notas o editor de texto, incluyendo las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----`). |

---

## ⚙️ 2. Archivo del Pipeline (`.github/workflows/deploy.yml`)

El pipeline se ubica en el repositorio en la ruta `.github/workflows/deploy.yml`:

```yaml
name: CI/CD Pipeline Producción

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # ==========================================
  # FASE 1: CI (Continuous Integration - Tests)
  # ==========================================
  test-backend:
    name: Backend Tests (Pytest)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt pytest pytest-cov

      - name: Run Backend Tests
        env:
          TESTING: 1
          JWT_SECRET: test-secret-key-32-chars-minimum-for-ci
        run: pytest -v

  test-frontend:
    name: Frontend Build Check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install Frontend Dependencies
        working-directory: frontend
        run: npm ci

      - name: Test Build
        working-directory: frontend
        run: npm run build

  # ==========================================
  # FASE 2: CD (Continuous Deployment a Oracle)
  # ==========================================
  deploy-production:
    name: Deploy Backend to Oracle Cloud
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.ORACLE_SSH_HOST }}
          username: ${{ secrets.ORACLE_SSH_USER }}
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd /home/ubuntu/arrendis
            git pull origin main
            docker compose -f docker-compose.prod.yml up -d --build backend
```

---

## 📋 3. Pasos de Implementación

1. Crear los 3 secretos en el panel de GitHub Settings.
2. Crear la carpeta `.github/workflows/` y guardar el archivo `deploy.yml`.
3. Hacer push a `main`.
4. Verificar en la pestaña **Actions** de GitHub que los tests pasan y que el backend se despliega automáticamente en Oracle Cloud.
