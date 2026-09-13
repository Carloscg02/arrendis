#!/usr/bin/env bash

# Directorio base del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "    Iniciando Gestión de Alquileres (Local)       "
echo "=================================================="

# Limpieza al salir (Ctrl+C o cierre)
cleanup() {
    echo ""
    echo "Deteniendo servicios locales..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
    wait "$BACKEND_PID" 2>/dev/null
    wait "$FRONTEND_PID" 2>/dev/null
    echo "Servicios detenidos."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Iniciar Backend
echo "[1/2] Iniciando Backend en http://localhost:8000..."
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

uvicorn backend.api.main:app --reload --port 8000 > /tmp/rental_backend.log 2>&1 &
BACKEND_PID=$!

# 2. Iniciar Frontend
echo "[2/2] Iniciando Frontend en http://localhost:5173..."
cd "$PROJECT_ROOT/frontend"
npm run dev > /tmp/rental_frontend.log 2>&1 &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

# Esperar unos instantes a que levanten los servicios
sleep 2

echo ""
echo "=================================================="
echo " Aplicación lista para pruebas:"
echo " Copia y pega en tu navegador:"
echo ""
echo "   http://localhost:5173/"
echo ""
echo " Backend API:  http://localhost:8000/api"
echo " Backend Docs: http://localhost:8000/docs"
echo " Logs backend:  /tmp/rental_backend.log"
echo " Logs frontend: /tmp/rental_frontend.log"
echo "=================================================="
echo "Presiona Ctrl + C para detener ambos servicios."
echo ""

# Esperar a que los procesos finalicen
wait
