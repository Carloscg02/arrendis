# Guía: Gestión de Variables de Entorno (`.env`) en Arrendis

Este documento explica cómo se gestionan las variables de entorno, contraseñas y claves de API en **Arrendis**, dónde reside cada archivo y cuál es el procedimiento exacto paso a paso para añadir nuevas variables en el futuro sin romper el despliegue automático.

---

## 🗺️ 1. Mapa Mental de Entornos

En Arrendis conviven **3 capas independientes**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. TU ORDENADOR LOCAL (Desarrollo)                                          │
│    Ubicación: /home/carlos/rental-handler/.env                              │
│    Uso: Se usa al ejecutar ./start_local.sh                                 │
│    Seguridad: Ignorado por Git (.gitignore). Nunca sube a GitHub.           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. CLOUDFLARE (Frontend y Worker de Correo)                                │
│    Ubicación: Panel web de Cloudflare (Settings > Environment Variables)    │
│    Variables:                                                               │
│      - Pages: VITE_API_URL = https://api.arrendis.com/api                  │
│      - Worker: RENTAL_HANDLER_WEBHOOK_URL, RENTAL_HANDLER_WEBHOOK_SECRET    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. SERVIDOR ORACLE CLOUD (Producción Backend)                               │
│    Ubicación: /home/ubuntu/arrendis/.env (En el disco del servidor)         │
│    Uso: Inyectado a los contenedores vía 'env_file: ../.env' en Docker      │
│    Seguridad: Reside en el servidor. Git Pull de GitHub Actions NO lo toca. │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 2. Variables Actuales del Sistema

A continuación se detalla qué hace cada variable que utiliza el backend:

| Variable | Propósito | Ejemplo / Valor actual |
| :--- | :--- | :--- |
| `DATABASE_PATH` | Ruta del archivo SQLite en disco | `data/rental.db` |
| `JWT_SECRET` | Clave criptográfica para firmar y validar tokens de sesión | Clave aleatoria hexadecimal de 64 caracteres |
| `INBOUND_WEBHOOK_SECRET` | Clave secreta compartida con Cloudflare Worker (Anti-spoofing) | Clave aleatoria (debe coincidir con la de Cloudflare) |
| `INBOUND_EMAIL_ADDRESS` | Dirección del buzón de recepción de facturas | `facturas@arrendis.com` |
| `GEMINI_API_KEY` | Clave gratuita de Google AI Studio para extracción inteligente | `AQ.Ab8RN...` |

---

## 🔒 3. ¿Por qué GitHub Actions no gestiona el `.env` del Backend?

- El archivo `.env` del servidor se creó una única vez de forma artesanal y segura en `/home/ubuntu/arrendis/.env`.
- Cuando GitHub Actions ejecuta:
  ```bash
  git pull origin main
  docker compose -f cicd/docker-compose.prod.yml up -d --build backend
  ```
- Git **ignora** el `.env` (gracias al `.gitignore`), por lo que **no se borra ni se sobreescribe**.
- Docker lee directamente el `.env` del disco del servidor y arranca la nueva versión con esas variables en memoria.

---

## ➕ 4. Procedimiento: Cómo Añadir una Nueva Variable en el Futuro

Si el día de mañana integras un nuevo servicio (por ejemplo, pagos con Stripe, envío de emails transaccionales con Resend o almacenamiento S3):

### Paso 1: Actualizar el código y la plantilla en Local
1. En tu código de Python, lee la variable con `os.getenv("NUEVA_VARIABLE")`.
2. Añade la variable a tu archivo local `.env` para tus pruebas:
   ```bash
   NUEVA_VARIABLE=valor_de_prueba_local
   ```
3. Añade la variable a la plantilla pública [`cicd/.env.example`](../cicd/.env.example) (con un valor ficticio o vacío):
   ```bash
   NUEVA_VARIABLE=tu_clave_aqui
   ```
4. Haz commit y push:
   ```bash
   git commit -am "feat: add support for NUEVA_VARIABLE"
   git push origin main
   ```

### Paso 2: Añadir la variable al Servidor de Producción (Oracle)
Conéctate por SSH al servidor de Oracle Cloud:
```bash
ssh -i /ruta/a/tu/clave.key ubuntu@80.225.189.17
```

Añade la nueva variable al final del archivo `.env`:
```bash
echo 'NUEVA_VARIABLE=valor_real_de_produccion' >> /home/ubuntu/arrendis/.env
```
*(O edítalo con `nano /home/ubuntu/arrendis/.env` si prefieres ver todo el archivo).*

### Paso 3: Reiniciar el Backend para que cargue la nueva variable
En la misma terminal del servidor, relanza el contenedor:
```bash
cd /home/ubuntu/arrendis
docker compose -f cicd/docker-compose.prod.yml up -d backend
```
*(O simplemente haz tu siguiente `git push origin main` y GitHub Actions lo reiniciará automáticamente leyendo la nueva variable).*

---

## 🚨 5. Buenas Prácticas y Seguridad

1. **NUNCA subas un archivo `.env` a GitHub**: Verifica siempre que esté listado en `.gitignore`.
2. **Si una clave se ve comprometida o filtrada**:
   - Cámbiala inmediatamente en el `.env` del servidor de Oracle.
   - En el caso de `INBOUND_WEBHOOK_SECRET`, cámbiala al mismo tiempo en el panel del Worker en Cloudflare.
   - Reinicia el contenedor con `docker compose -f cicd/docker-compose.prod.yml restart backend`.
