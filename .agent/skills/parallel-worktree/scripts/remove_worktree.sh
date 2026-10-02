#!/usr/bin/env bash
set -euo pipefail

# Script helper para eliminación y limpieza de un worktree
# Uso: remove_worktree.sh <feature_slug> [--delete-branch]

FEATURE_INPUT="${1:-}"
DELETE_BRANCH="${2:-}"

if [ -z "$FEATURE_INPUT" ]; then
    echo "Error: Debes indicar el nombre o identificador del worktree (ej: f22 o rental-f22)."
    exit 1
fi

GIT_COMMON="$(git rev-parse --git-common-dir)"
MAIN_REPO="$(cd "$GIT_COMMON/.." && pwd)"
PARENT_DIR="$(dirname "$MAIN_REPO")"

CLEAN_SLUG=$(echo "$FEATURE_INPUT" | tr '[:upper:]' '[:lower:]' | sed -E 's/^rental-//' | sed -E 's/^feature\///' | sed -E 's/[^a-z0-9_-]+/-/g')
BRANCH_NAME="feature/${CLEAN_SLUG}"
WORKTREE_PATH="${PARENT_DIR}/rental-${CLEAN_SLUG}"

if [ ! -d "$WORKTREE_PATH" ]; then
    if [ -d "$FEATURE_INPUT" ]; then
        WORKTREE_PATH="$FEATURE_INPUT"
    else
        echo "Error: No se encontró el directorio del worktree en $WORKTREE_PATH"
        exit 1
    fi
fi

echo "Eliminando worktree en: $WORKTREE_PATH"
git worktree remove "$WORKTREE_PATH"
git worktree prune

if [ "$DELETE_BRANCH" = "--delete-branch" ] || [ "$DELETE_BRANCH" = "-d" ]; then
    echo "Eliminando rama local: $BRANCH_NAME"
    git branch -d "$BRANCH_NAME" || {
        echo "Aviso: La rama no está totalmente fusionada. ¿Deseas forzar el borrado manual con git branch -D $BRANCH_NAME?"
    }
fi

echo "=========================================================="
echo "Worktree $WORKTREE_PATH eliminado y podado correctamente."
echo "=========================================================="
