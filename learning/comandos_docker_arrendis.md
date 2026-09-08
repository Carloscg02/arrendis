# Guía Práctica: Comandos Clave de Docker y Docker Compose para Arrendis

Esta guía contiene los comandos fundamentales de Docker que necesitarás en el día a día para gestionar, monitorizar, depurar y actualizar el backend de **Arrendis** en tu servidor de producción (Oracle Cloud).

Todos los ejemplos están adaptados exactamente a tu configuración (`docker-compose.prod.yml`, contenedores `arrendis_backend_1` y `arrendis_caddy_1`).

---

## 🧭 Regla de Oro: Dónde ejecutar estos comandos
Siempre debes estar dentro de la carpeta del proyecto en el servidor:
```bash
cd /home/ubuntu/arrendis
```

---

## 1. 📊 Monitorización y Estado

### 1.1. Ver si los contenedores están vivos
Muestra el estado de tus dos servicios (`Up` o `Exit`), los puertos y los nombres de los contenedores.
```bash
docker compose -f cicd/docker-compose.prod.yml ps
```
> **Qué debes ver:**
> - `arrendis_backend_1`: Estado `Up` (puerto 8000 expuesto internamente).
> - `arrendis_caddy_1`: Estado `Up` (puertos 80 y 443 abiertos a internet).

### 1.2. Ver consumo de CPU y Memoria RAM en tiempo real
Para comprobar con tus propios ojos cuántos megabytes reales están gastando Caddy y FastAPI:
```bash
docker stats
```
*(Pulsa `Ctrl + C` para salir).*  
Verás que entre los dos no suelen pasar de 150-200 MB de RAM.

---

## 2. 📜 Inspección de Logs (Para depurar errores)

### 2.1. Ver los logs de ambos servicios a la vez
```bash
docker compose -f cicd/docker-compose.prod.yml logs
```

### 2.2. Ver logs en tiempo real (modo "seguir" / streaming)
Se queda escuchando en la terminal e imprime cada petición HTTP o error al instante:
```bash
docker compose -f cicd/docker-compose.prod.yml logs -f
```
*(Pulsa `Ctrl + C` para salir).*

### 2.3. Ver solo los logs del Backend (FastAPI)
Ideal cuando quieres ver qué pasa al crear una propiedad, procesar una factura o validar un token JWT:
```bash
docker compose -f cicd/docker-compose.prod.yml logs -f backend
```

### 2.4. Ver solo los logs de Caddy (Certificados SSL y Tráfico Web)
Ideal para verificar si Let's Encrypt ha emitido el certificado HTTPS correctamente:
```bash
docker compose -f cicd/docker-compose.prod.yml logs -f caddy
```

---

## 3. 🚀 Gestión del Ciclo de Vida (Encender, Apagar, Reiniciar)

### 3.1. Reiniciar un servicio sin tocar el otro
Si cambiaste algo rápido y quieres reiniciar solo el proceso de Python sin interrumpir Caddy:
```bash
docker compose -f cicd/docker-compose.prod.yml restart backend
```

### 3.2. Apagar los servicios ordenadamente
Detiene y elimina los contenedores y la red virtual, pero **respeta al 100% tu base de datos y archivos en `./data`**:
```bash
docker compose -f cicd/docker-compose.prod.yml down
```

### 3.3. Levantar todo de nuevo en segundo plano
Vuelve a encender los contenedores usando la imagen ya construida:
```bash
docker compose -f cicd/docker-compose.prod.yml up -d
```
*(El `-d` significa **detached**: se ejecuta en segundo plano y te devuelve el control de la terminal).*

---

## 4. 🔄 Actualizar el Backend con Nuevo Código (Despliegue de Cambios)

Cuando en tu ordenador hagas cambios en el código de Python, hagas commit y `git push origin main`, para aplicar los cambios en el servidor ejecutas esta secuencia:

```bash
# 1. Descargar el nuevo código de GitHub
git pull origin main

# 2. Reconstruir la imagen de Docker y reiniciar el backend sin tiempo de caída
docker compose -f cicd/docker-compose.prod.yml up -d --build backend
```
> **¿Por qué `--build`?**
> Porque el código de Python se copia dentro de la imagen en el `Dockerfile`. Al añadir `--build`, Docker detecta qué archivos han cambiado, recompila solo esas capas y reinicia el contenedor en 3 segundos.

---

## 5. 🕵️ Entrar "Dentro" del Contenedor (Sesión Interactiva / Shell)

A veces necesitas entrar dentro de la caja para ver los archivos como los ve Python, comprobar la base de datos o probar imports:

### 5.1. Abrir una terminal Bash dentro del backend
```bash
docker compose -f cicd/docker-compose.prod.yml exec backend bash
```
Una vez dentro (`root@...:/app#`):
- `ls -la`: Verás los archivos del backend tal como los empaquetó Docker.
- `python -c "import fitz; print(fitz.__version__)"`: Comprobar versiones de librerías instaladas.
- `sqlite3 data/rental.db ".tables"`: Ver las tablas de la base de datos.
- `exit`: Para salir del contenedor y volver a Ubuntu.

---

## 6. 🧹 Limpieza y Mantenimiento de Disco

Con el tiempo, al reconstruir imágenes de Docker tras varios despliegues, pueden quedar capas antiguas que ya no se usan ocupando espacio en el disco de 50 GB.

### 6.1. Ver cuánto espacio ocupa Docker en el disco
```bash
docker system df
```

### 6.2. Limpiar imágenes huérfanas y cachés viejas (Seguro)
Borra únicamente contenedores apagados, redes no utilizadas e imágenes sin nombre (dangling images). **No borra tus volúmenes ni tu base de datos**:
```bash
docker system prune -f
```

---

## 📋 Resumen Rápido (Los 4 comandos que más usarás)

| Necesidad | Comando |
| :--- | :--- |
| **¿Está todo funcionando?** | `docker compose -f cicd/docker-compose.prod.yml ps` |
| **Ver qué falla en tiempo real** | `docker compose -f cicd/docker-compose.prod.yml logs -f backend` |
| **Actualizar con nuevo código** | `git pull origin main && docker compose -f cicd/docker-compose.prod.yml up -d --build` |
| **Reiniciar el backend** | `docker compose -f cicd/docker-compose.prod.yml restart backend` |
