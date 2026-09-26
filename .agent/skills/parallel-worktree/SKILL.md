---
name: parallel-worktree
description: >-
  Crea, gestiona y elimina Git Worktrees para permitir el desarrollo concurrente de features y épicas en entornos aislados con sus dependencias enlazadas (venv y node_modules) sin colisiones de ramas ni bloqueos entre sesiones de Antigravity (agy).
---

# Parallel Worktrees Skill

Esta skill proporciona los procedimientos, guías y scripts automatizados para trabajar en múltiples features o épicas de forma concurrente mediante **Git Worktrees** junto con **Antigravity CLI (`agy`)**.

## ¿Cuándo utilizar esta skill?

- Tienes una sesión de Antigravity (`agy`) activa trabajando en una rama o épica (por ejemplo, `feature/E-03-valoracion-mercado`) y deseas avanzar en otra feature (ej: `F-22`, `F-15`, hotfixes, etc.) sin interferir con los ficheros, estado de tests ni historial de commits de la sesión activa.
- Deseas evitar bloqueos y alternancias destructivas de ramas (`git checkout` / `git switch`) mientras hay servidores locales o sesiones de IA en curso.
- Quieres optimizar el almacenamiento en disco enlazando los entornos virtuales (`venv/`) y dependencias de frontend (`node_modules/`) sin duplicarlos en cada copia.

---

## Estructura de un Worktree

Cada worktree secundario se crea como un directorio hermano al repositorio principal:
```
/home/carlos/
├── rental-handler/                  # Repositorio principal (con venv original y frontend/node_modules)
├── rental-handler-worktree/         # Worktree secundario de pruebas / staging
└── rental-<feature_slug>/           # Worktree dedicado para una feature específica
    ├── venv -> /home/carlos/rental-handler/venv  (symlink)
    ├── frontend/node_modules -> ...              (symlink)
    ├── .env                                      (copia de configuración)
    └── data/                                     (almacenamiento local)
```

---

## 🛠️ Procedimientos y Scripts

### 1. Crear un Worktree para una nueva feature

Usa el script helper automatizado:

```bash
.agent/skills/parallel-worktree/scripts/create_worktree.sh <feature_slug> [base_branch]
```

**Ejemplo:**
```bash
# Para la feature F-22 (a partir de develop por defecto):
.agent/skills/parallel-worktree/scripts/create_worktree.sh f22-refactor-persistence

# O indicando rama base explícita:
.agent/skills/parallel-worktree/scripts/create_worktree.sh F-15 main
```

**Qué hace automáticamente:**
1. Sanitiza el nombre creando la rama `feature/<feature_slug>`.
2. Crea el directorio `/home/carlos/rental-<feature_slug>` y enlaza el worktree a la rama.
3. Genera enlaces simbólicos (`symlinks`) para `venv` y `frontend/node_modules`.
4. Copia `.env` y crea el directorio `data/`.

---

### 2. Iniciar la sesión de Antigravity en el Worktree

Abre una nueva terminal (o panel) y navega al directorio del nuevo worktree para arrancar una sesión completamente aislada:

```bash
cd /home/carlos/rental-<feature_slug>
agy
```

> [!IMPORTANT]
> Cada sesión de `agy` trabaja con el directorio en el que fue lanzada. Para que una sesión no toque ni colisione con el worktree de la Epic 3, la sesión debe ejecutarse en el path de su propio worktree.

---

### 3. Desarrollo y Verificación (Metodología SDD)

En la nueva sesión de `agy`:
1. Especificación: crea `specs/<feature>/design.md` con su correspondiente *Rincón del Estudiante*.
2. Plan de implementación y aprobación humana (`/planning`).
3. Implementación mediante subagentes.
4. Ejecución de tests:
   ```bash
   pytest
   ```
   *(El entorno `venv` ya está disponible y enlazado)*.

---

### 4. Integración y Limpieza del Worktree

Una vez finalizada la feature y verificados todos los tests:

1. **Fusionar en `develop`:**
   ```bash
   git checkout develop
   git merge feature/<feature_slug>
   git push origin develop
   ```

2. **Eliminar el worktree:**
   Usa el script helper:
   ```bash
   .agent/skills/parallel-worktree/scripts/remove_worktree.sh <feature_slug> [--delete-branch]
   ```
   O manualmente con Git:
   ```bash
   git worktree remove /home/carlos/rental-<feature_slug>
   git worktree prune
   git branch -d feature/<feature_slug>
   ```

---

## ⚠️ Buenas Prácticas Anti-Conflictos

1. **Puertos de Red:** Si ejecutas el backend (`8000`) o frontend (`5173`) en ambos worktrees a la vez, asigna puertos alternativos en el segundo entorno (ej: `PORT=8001` o `npm run dev -- --port 5174`).
2. **Base de Datos SQLite:** Cada worktree tiene su propia carpeta `data/` local, por lo que las operaciones de prueba y migraciones no afectarán a la base de datos de la otra sesión.
3. **No tocar ramas cruzadas:** Cada sesión solo debe commitear y modificar ficheros dentro de su propio árbol de trabajo.
