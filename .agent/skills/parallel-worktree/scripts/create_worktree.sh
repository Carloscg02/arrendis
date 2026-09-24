#!/usr/bin/env bash
set -euo pipefail

# Scripts helper para creación de worktree en paralelo
# Uso: create_worktree.sh <feature_slug> [base_branch]

FEATURE_INPUT="${1:-}"
BASE_BRANCH="${2:-develop}"

if [ -z "$FEATURE_INPUT" ]; then
    echo "Error: Debes indicar el nombre o identificador de la feature (ej: f20-subida-facturas o F-20)."
    exit 1
fi

# Normalizar nombre de feature y de rama
# Quitar prefijos si los trae y generar slug limpio
CLEAN_SLUG=$(echo "$FEATURE_INPUT" | tr '[:upper:]' '[:lower:]' | sed -E 's/^feature\///' | sed -E 's/[^a-z0-9_-]+/-/g')
BRANCH_NAME="feature/${CLEAN_SLUG}"

# Directorio raíz del repositorio principal
MAIN_REPO="$(git rev-parse --show-toplevel)"
PARENT_DIR="$(dirname "$MAIN_REPO")"
WORKTREE_PATH="${PARENT_DIR}/rental-${CLEAN_SLUG}"

echo "Preparando worktree en: $WORKTREE_PATH"
echo "Rama: $BRANCH_NAME (desde $BASE_BRANCH)"

# Verificar si el directorio ya existe
if [ -d "$WORKTREE_PATH" ]; then
    echo "Error: El directorio $WORKTREE_PATH ya existe."
    exit 1
fi

# Verificar si la rama ya existe
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Aviso: La rama $BRANCH_NAME ya existe. Conectando al worktree..."
    git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
else
    git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH"
fi

# Enlazar venv
if [ -d "$MAIN_REPO/venv" ]; then
    ln -s "$MAIN_REPO/venv" "$WORKTREE_PATH/venv"
    echo "Enlace creado: venv -> $MAIN_REPO/venv"
fi

# Enlazar node_modules en frontend
if [ -d "$MAIN_REPO/frontend/node_modules" ]; then
    mkdir -p "$WORKTREE_PATH/frontend"
    ln -s "$MAIN_REPO/frontend/node_modules" "$WORKTREE_PATH/frontend/node_modules"
    echo "Enlace creado: frontend/node_modules -> $MAIN_REPO/frontend/node_modules"
fi

# Copiar .env si existe
if [ -f "$MAIN_REPO/.env" ]; then
    cp "$MAIN_REPO/.env" "$WORKTREE_PATH/.env"
    echo "Archivo .env copiado."
fi

# Crear directorio data/
mkdir -p "$WORKTREE_PATH/data"

echo ""
echo "=========================================================="
echo "Worktree listo con éxito en: $WORKTREE_PATH"
echo "Para arrancar tu sesión paralela de Antigravity:"
echo "  cd $WORKTREE_PATH && agy"
echo "=========================================================="
