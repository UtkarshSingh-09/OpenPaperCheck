#!/usr/bin/env bash
# ==============================================================================
# OpenPaperCheck Nightly Retraction Ingest Script
# Runs nightly via cron or supercronic worker to fetch verified scholarly snapshots.
# ==============================================================================

set -euo pipefail

LOG_DIR="${OPC_LOG_DIR:-./infra/logs}"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/nightly_ingest.log"

exec > >(tee -a "${LOG_FILE}") 2>&1

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "================================================================================"
echo "Starting OpenPaperCheck Nightly Ingest at ${TIMESTAMP}"
echo "================================================================================"

# Execute snapshot update via CLI or Docker container
if command -v docker &>/dev/null && docker ps --format '{{.Names}}' | grep -q "opc-api"; then
    echo "==> Executing 'opc update' inside opc-api container..."
    docker exec opc-api opc update
    docker exec opc-api opc version
elif command -v opc &>/dev/null; then
    echo "==> Executing local 'opc update'..."
    opc update
    opc version
else
    echo "==> Executing python module update..."
    python3 -m openpapercheck.cli update || true
fi

echo "==> Nightly Ingest completed successfully at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
