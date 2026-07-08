# 🚀 Guía de Trabajo: Spec-Driven Development con Antigravity CLI (AGY-SDD-WoW)

Este documento define nuestro **Way of Working (WoW)** para desarrollar la aplicación utilizando **Antigravity CLI** y la metodología **Spec-Driven Development (SDD)**. 

En este flujo, **tú eres el Orquestador, no el mecanógrafo**. Tu rol es definir qué hacer, revisar el diseño técnico propuesto y aprobar la ejecución. Antigravity se encargará de paralelizar el trabajo y picar el código mediante subagentes asíncronos.

---

## 📂 1. El Arnés de Archivos (¿Dónde está cada cosa?)

Nuestro proyecto utiliza una estructura híbrida que combina archivos de convención nativos de Antigravity con nuestra memoria externa de SDD.

*   **`agents.md` (El Agente Principal y Convenios):** Es el archivo nativo de Antigravity que actúa como la "Constitución" del proyecto. Contiene las reglas estrictas de Arquitectura Hexagonal, Domain-Driven Design (DDD) y las instrucciones de cómo los agentes deben escribir las especificaciones sin crear "monolitos".
*   **`feature_list.json` (El Backlog):** Es nuestra fuente de verdad manual. Aquí defines las features que quieres que la IA implemente, cambiando su estado a `"pending"`.
*   **`docs/architecture.md`:** Define las decisiones tecnológicas (Ej: Python, SQLite, Hexagonal). La IA siempre debe leerlo antes de planificar.
*   **`specs/<feature>/`:** Aquí es donde la IA generará el diseño técnico definitivo (`requirements.md` y `design.md`) para cada feature de forma aislada.

---

## 🔄 2. El Flujo de Trabajo Paso a Paso

Cada vez que quieras implementar una nueva característica, sigue este ciclo exacto:

### Paso 1: Definir el "Qué" (Intervención Humana)
Abre tu archivo `feature_list.json` y añade o actualiza la característica en la que quieres trabajar.
```json
{
  "id": "F-02", 
  "title": "Crear sistema de Login", 
  "status": "pending" 
}
```

### Paso 2: Planificación y Especificación Técnica
1. Abre tu terminal y lanza Antigravity con el comando `agy`.
2. Activa obligatoriamente el modo de planificación para evitar que escriba código a lo loco: `/planning`.
3. Lanza el prompt inicial orquestador:
   > *"Lee el `feature_list.json`. Inicia la planificación y el diseño técnico para la siguiente tarea pendiente respetando las reglas de `agents.md`."*

### Paso 3: Aprobación Humana (El paso más crítico)
Antigravity generará internamente un artefacto (`implementation_plan.md` y `tasks.md`) y se pausará esperando tu revisión.
1. Presiona **`Ctrl + R`** (o escribe `/artifact`) para abrir el panel interactivo de revisión de artefactos.
2. Lee el diseño técnico y el modelo de dominio propuesto.
3. **¿Hay errores o no respetó el arnés?** Presiona la tecla **`C`** para dejarle un comentario correctivo (Ej: *"Separa los Casos de Uso en `specs/F-02/design.md`, no crees un monolito"*).
4. **¿Está todo perfecto?** Presiona **Enter / Approve** para aprobar el plan.

### Paso 4: Ejecución y Subagentes Paralelos
Una vez aprobado, ordénale a Antigravity que ejecute el plan. 
> *"Ejecuta el plan aprobado."*

Para tareas complejas (frontend, backend, testing), Antigravity creará automáticamente **subagentes especializados** que trabajarán en paralelo en segundo plano.
*   Puedes escribir `/agents` en el chat en cualquier momento para ver a los subagentes trabajando en tiempo real.

### Paso 5: Gestión de Permisos y Testing
Mientras los subagentes programan y corren los tests definidos en el spec, es posible que intenten instalar dependencias o ejecutar scripts. 
*   Si un subagente se bloquea pidiendo permiso, la interfaz te avisará.
*   Presiona **`Alt + J`** para saltar al agente bloqueado y **`Ctrl + K`** para aprobar la ejecución del comando (ej: correr `pytest` en el `venv`).

Al finalizar, Antigravity marcará sus tareas internas como completadas y te entregará un resumen en el archivo interno `walkthrough.md`. Ya puedes actualizar tu `feature_list.json` a `"done"`.

---

## ⌨️ 3. Cheat Sheet: Comandos Nativos Esenciales

| Comando / Atajo | ¿Para qué sirve en este flujo? |
| :--- | :--- |
| `agy` | Inicia la sesión de Antigravity en la terminal. |
| `/planning` | **Crucial para SDD.** Obliga a la IA a crear un plan y pedir permiso antes de tocar el código fuente. |
| `Ctrl + R` o `/artifact` | Abre el panel para revisar el Spec Técnico propuesto por la IA. |
| `C` (dentro del artefacto) | Añade comentarios o correcciones de arquitectura al plan antes de aprobarlo. |
| `/agents` | Muestra el panel con todos los subagentes (Implementer, Reviewer) trabajando en paralelo. |
| `Alt + J` | Salta rápidamente al subagente que está solicitando permisos de consola. |
| `Ctrl + K` | Aprueba la solicitud de permiso del subagente actual (Ej: ejecutar un test o instalar dependencias). |
| `/permissions` | Abre el panel de reglas (Allow/Deny/Ask) por si quieres revisar las autorizaciones o darle más autonomía. |
| `Ctrl + V` | Pega una imagen directamente en la terminal (si tu terminal lo soporta) como contexto visual para la IA. |
| `/rewind` | Revierte la conversación a un punto anterior de la sesión si necesitas volver hacia atrás en el proceso. |
```