# Guía Didáctica: Fundamentos de DevOps y el Pipeline CI/CD de Arrendis

Esta guía explica desde los conceptos teóricos básicos de la cultura **DevOps** hasta el funcionamiento técnico exacto del pipeline que acabamos de poner en producción con **GitHub Actions**, **Docker** y **Oracle Cloud**.

---

## 🏛️ 1. ¿Qué es DevOps? (El Problema Histórico y la Solución)

Históricamente, en las empresas de software existían dos departamentos totalmente separados y enfrentados:

1. **Desarrolladores (Dev - Development):** Su trabajo era programar nuevas funcionalidades lo más rápido posible. Cuando terminaban, decían: *"Aquí tenéis el código, en mi ordenador funciona perfecto, ahora desplegadlo vosotros"*.
2. **Operaciones / Sistemas (Ops - Operations):** Su trabajo era mantener los servidores estables y que nada se cayera. Por tanto, odiaban los cambios porque cada despliegue de código nuevo podía romper la producción.

Cuando la web fallaba, se culpaban mutuamente:  
- *Dev:* "Es un problema de vuestro servidor".  
- *Ops:* "Es un bug de vuestro código".

### El nacimiento de DevOps:
**DevOps** no es un programa que se instala; es una **cultura y metodología** que une ambos mundos:
> **"Quien programa el código, es responsable de cómo se prueba, cómo se empaqueta y cómo se despliega en producción, de forma automatizada y sin fricción."**

---

## 🔄 2. ¿Qué significa CI/CD?

CI/CD son dos siglas que representan las dos mitades de una cadena de montaje moderna:

### A) CI: Integración Continua (*Continuous Integration*)
- **La idea:** En lugar de juntar meses de trabajo de diferentes programadores el día antes del lanzamiento (lo que provocaba el temido *"merge hell"*), los desarrolladores suben código a menudo (`git push`).
- **La regla:** Cada vez que alguien sube código, un robot independiente levanta una máquina limpia, compila el proyecto y **ejecuta toda la batería de tests automáticamente**.
- **El objetivo:** Detectar errores en minutos, no en meses. Si un test falla, el robot "rompe la build" (pone el semáforo en rojo) e impide que el fallo llegue a los usuarios.

### B) CD: Despliegue Continuo (*Continuous Deployment*)
- **La idea:** Si el robot de CI dice que el código compila y que el 100% de los tests están en verde, **el despliegue en producción debe ser automático**.
- **El objetivo:** Eliminar al humano del proceso de subir archivos por FTP o entrar por SSH a teclear comandos. El software pasa de estar en la mente del desarrollador a estar en manos de los usuarios en minutos.

---

## 🔍 3. Anatomía de GitHub Actions (Los Componentes del Robot)

Para implementar CI/CD usamos **GitHub Actions**. Sus conceptos clave son:

1. **Workflow (Flujo de trabajo):** Es el archivo de instrucciones en formato YAML que vive en `.github/workflows/deploy.yml`. Define qué hacer y cuándo.
2. **Events / Triggers (Disparadores):** El evento que despierta al robot. En nuestro caso:
   ```yaml
   on:
     push:
       branches: [ main, develop ]
   ```
   *(Cada vez que alguien hace `git push` a `main` o `develop`, arranca).*
3. **Runners (Ejecutores):** Son máquinas virtuales temporales que GitHub te presta en su nube (Ubuntu, Windows o Mac) de forma gratuita. En nuestro caso usamos `runs-on: ubuntu-latest`.
4. **Jobs (Trabajos):** Un conjunto de pasos que se ejecutan en un runner. Si tienes varios jobs, GitHub los ejecuta en paralelo para ahorrar tiempo.
5. **Steps (Pasos):** Las acciones individuales dentro de un job (instalar dependencias, correr comandos bash, etc.).

---

## 🛠️ 4. Análisis Línea por Línea del Pipeline de Arrendis

Veamos cómo está construido nuestro archivo [`.github/workflows/deploy.yml`](file:///home/carlos/rental-handler/.github/workflows/deploy.yml):

### Job 1: `test-backend` (Quality Gate de Python)
```yaml
  test-backend:
    name: Backend Tests (Pytest)
    runs-on: ubuntu-latest
    steps:
      # 1. Clona el repositorio dentro de la máquina de GitHub
      - name: Checkout Code
        uses: actions/checkout@v4

      # 2. Instala Python 3.12 y activa caché de pip para que vaya rápido
      - name: Setup Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      # 3. Instala librerías
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt pytest pytest-cov

      # 4. Ejecuta los 335 tests unitarios e integrados
      - name: Run Backend Tests
        env:
          TESTING: 1
          JWT_SECRET: test-secret-key-32-chars-minimum-for-ci
        run: pytest -v
```
> **¿Qué garantiza esto?**  
> Si mañana tocas una función de cálculo de IRPF o de autenticación y sin querer rompes un caso límite, `pytest` fallará aquí. El pipeline se detendrá y **tu servidor real de Oracle no se tocará**.

---

### Job 2: `test-frontend` (Validación de TypeScript y Vite)
```yaml
  test-frontend:
    name: Frontend Build Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install Frontend Dependencies
        working-directory: frontend
        run: npm ci

      # Verifica que no hay errores de sintaxis TypeScript y compila dist/
      - name: Test Build
        working-directory: frontend
        run: npm run build
```
> **¿Qué garantiza esto?**  
> Si te dejaste una llave sin cerrar, un tipo de TypeScript incompatible o una imagen que no existe, el build fallará antes de llegar a los usuarios.

---

### Job 3: `deploy-production` (El Despliegue Continuo por SSH)
```yaml
  deploy-production:
    name: Deploy Backend to Oracle Cloud
    needs: [test-backend, test-frontend]  # <-- ¡CRÍTICO! Solo corre si los dos anteriores pasaron
    if: github.ref == 'refs/heads/main' && github.event_name == 'push' # <-- Solo en rama main
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
            docker compose -f cicd/docker-compose.prod.yml up -d --build backend
```
> **¿Cómo funciona la magia aquí?**  
> 1. GitHub utiliza los **Repository Secrets** cifrados para autenticarse por SSH contra tu máquina de Oracle sin que nadie vea tu clave privada.
> 2. Una vez conectado, ejecuta remotamente el comando: descarga el código nuevo con `git pull` y le dice a Docker: *"recompila la imagen con los cambios y reinicia el contenedor de FastAPI"*.

---

## 🌐 5. ¿Y qué pasa con el Frontend? (La separación de caminos)

En nuestra arquitectura:
- **El Backend se despliega vía GitHub Actions ➔ Oracle Cloud (Docker).**
- **El Frontend se despliega vía Cloudflare Pages (Git Integration).**

Cloudflare Pages está conectado directamente a los webhooks de tu repositorio de GitHub. Cuando haces `git push origin main`:
1. GitHub Actions despierta para probar el código y actualizar el backend.
2. Al mismo tiempo, Cloudflare Pages despierta, compila el frontend de React y lo reparte por más de 300 centros de datos mundiales.

---

## 📊 6. El Ciclo de Vida Completo de un Cambio en Arrendis

```
1. Escribes código en tu ordenador (ej. nueva función en backend o nuevo botón en UI).
2. Compruebas que funciona en local con './start_local.sh'.
3. 'git add . && git commit -m "feat: mi cambio"'.
4. 'git push origin main'.
   │
   ├──► Cloudflare Pages compila y publica frontend en arrendis.com (~45 seg).
   │
   └──► GitHub Actions arranca:
        ├── Ejecuta 335 tests de backend en runner Ubuntu.
        ├── Compila frontend para verificar tipos en runner Ubuntu.
        └── Si todo está verde:
            └── Se conecta a Oracle Cloud por SSH y actualiza Docker backend (~15 seg).
```

### Resultado:
En menos de **1 minuto y medio**, tu cambio está en internet en alta disponibilidad, con certificados SSL, probado por una suite completa de tests, y tú solo has tenido que escribir: `git push`.
