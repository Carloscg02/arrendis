#!/bin/bash
set -euo pipefail

BACKUP_DIR="/home/ubuntu/backups"
DB_SOURCE="/home/ubuntu/arrendis/data/rental.db"
FECHA=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/rental_${FECHA}.db"
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "${BACKUP_DIR}"

if [ -f "${DB_SOURCE}" ]; then
    # Copia de seguridad atómica en caliente (sin bloquear escrituras en producción)
    sqlite3 "${DB_SOURCE}" ".backup ${BACKUP_FILE}"
    
    # Comprimir con gzip para reducir el tamaño entre un 80% y un 90%
    gzip -f "${BACKUP_FILE}"
    
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Backup creado y comprimido con exito: ${BACKUP_FILE}.gz" >> "${LOG_FILE}"
else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - ADVERTENCIA: No se encontro ${DB_SOURCE}" >> "${LOG_FILE}"
fi

# Eliminar copias de mas de 14 dias para mantener el disco limpio y holgado
find "${BACKUP_DIR}" -type f -name "rental_*.db.gz" -mtime +14 -delete
find "${BACKUP_DIR}" -type f -name "rental_*.db" -mtime +14 -delete
