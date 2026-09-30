#!/usr/bin/env bash
# ==============================================================================
# OpenPaperCheck Pre-Deploy Safety Backup Script
# Creates an immediate point-in-time PostgreSQL snapshot before deploying migrations.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${OPC_BACKUP_DIR:-./infra/backups/pre-deploy}"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_FILE="${BACKUP_DIR}/opc_predeploy_${TIMESTAMP}.sql.gz"

echo "==> [Pre-Deploy] Starting database backup at ${TIMESTAMP}..."

if command -v docker &>/dev/null && docker ps --format '{{.Names}}' | grep -q "opc-db"; then
    echo "==> Dumping from Docker container 'opc-db'..."
    docker exec opc-db pg_dump -U opc -d opc --clean --if-exists | gzip > "${BACKUP_FILE}"
else
    echo "==> Notice: No running PostgreSQL container detected. Skipping pre-deploy DB dump."
    exit 0
fi

SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "==> [Pre-Deploy] Backup created successfully: ${BACKUP_FILE} (${SIZE})"
