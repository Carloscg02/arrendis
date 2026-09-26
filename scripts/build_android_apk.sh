#!/usr/bin/env bash
# ==============================================================================
# Arrendis — Pipeline de Compilación Local de APK Android (Capacitor)
# Feature: F-37 (Épica E-05)
# Genera el binario instalador app-debug.apk para pruebas directas (sideloading).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
ANDROID_DIR="${FRONTEND_DIR}/android"

echo "=========================================================="
echo "📱 ARRENDIS — COMPILADOR LOCAL DE APK ANDROID (CAPACITOR)"
echo "=========================================================="

echo "1. Compilando aplicación React y sincronizando con Capacitor..."
cd "${FRONTEND_DIR}"
npm run cap:sync

echo "2. Comprobando entorno de Android y Java..."
if ! command -v java &> /dev/null; then
    echo "⚠️ ADVERTENCIA: 'java' no encontrado en el PATH."
    echo "   Para compilar el .apk en local se requiere OpenJDK 17 o 21 (ej: sudo apt install openjdk-17-jdk)."
    echo "   Los ficheros nativos y la sincronización web ya están completos en frontend/android/."
    exit 0
fi

echo "3. Ejecutando Gradle Wrapper (assembleDebug)..."
cd "${ANDROID_DIR}"
if ./gradlew assembleDebug; then
    APK_PATH="${ANDROID_DIR}/app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "${APK_PATH}" ]; then
        echo "=========================================================="
        echo "✅ ¡APK GENERADO CON ÉXITO!"
        echo "   Ubicación: ${APK_PATH}"
        echo ""
        echo "   Para instalarlo en un móvil Android conectado por USB:"
        echo "   adb install -r ${APK_PATH}"
        echo "=========================================================="
    fi
else
    echo "⚠️ La compilación Gradle falló (probablemente falte configurar ANDROID_HOME en esta máquina)."
    echo "   Puedes abrir el proyecto en Android Studio ejecutando:"
    echo "   npm --prefix frontend run cap:open:android"
fi
