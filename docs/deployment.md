# Guía de Ejecución Local (Despliegue)

Este documento detalla los pasos necesarios para arrancar la aplicación de Gestión de Alquileres en tu entorno local. La aplicación está dividida en dos partes: el backend (FastAPI) y el frontend (React + Vite).

Para que la aplicación funcione correctamente, **ambos servicios deben estar ejecutándose simultáneamente** en pestañas de terminal separadas.

---

## 1. Arrancar el Backend (API)

El backend expone la API REST y sirve las imágenes almacenadas.

1. Abre una terminal y navega al directorio del proyecto:
   ```bash
   cd /home/carlos/rental-handler
   ```

2. Activa el entorno virtual (si no lo tienes activado):
   ```bash
   source venv/bin/activate
   ```

3. Arranca el servidor FastAPI usando `uvicorn`:
   ```bash
   uvicorn backend.api.main:app --reload --port 8000
   ```

**Verificación:**
- La API estará disponible en: `http://localhost:8000/api`
- La documentación interactiva (Swagger) estará en: `http://localhost:8000/docs`
- Mantén esta terminal abierta. Si la cierras, el backend se apagará.

---

## 2. Arrancar el Frontend (Web UI)

El frontend contiene la interfaz de usuario en React.

1. Abre una **nueva pestaña** de terminal y navega al directorio del frontend:
   ```bash
   cd /home/carlos/rental-handler/frontend
   ```

2. Arranca el servidor de desarrollo de Vite:
   ```bash
   npm run dev
   ```

**Verificación:**
- La terminal mostrará una URL local, por defecto: `http://localhost:5173/`
- Mantén esta terminal abierta.

---

## 3. Acceder a la Aplicación

Con ambos servidores funcionando:

1. Abre tu navegador web favorito (Chrome, Firefox, Safari, etc.).
2. Accede a la URL del frontend:
   **[http://localhost:5173/](http://localhost:5173/)**

¡Ya puedes utilizar la aplicación completa! El frontend se comunicará automáticamente con el backend en el puerto 8000.

---

### Notas Adicionales

- **Base de Datos:** El proyecto utiliza SQLite. El archivo de la base de datos se generará y guardará automáticamente en `data/rental.db`. No necesitas instalar ningún motor de base de datos extra.
- **Imágenes:** Las fotos que subas de las propiedades se guardarán localmente en la carpeta `data/images/`.
- **Apagar la aplicación:** Para detener cualquiera de los servidores, ve a la terminal correspondiente y presiona `Ctrl + C`.
