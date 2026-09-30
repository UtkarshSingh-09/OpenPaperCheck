#!/usr/bin/env bash
# ==============================================================================
# OpenPaperCheck Service & Snapshot Health Probe
# Inspects API responsiveness, database status, and data snapshot freshness.
# ==============================================================================

set -euo pipefail

API_URL="${OPC_API_URL:-http://127.0.0.1:8000}"
HEALTH_ENDPOINT="${API_URL}/v1/health"

echo "==> Probing OpenPaperCheck health at ${HEALTH_ENDPOINT}..."

RESPONSE=$(curl -s -f -m 5 "${HEALTH_ENDPOINT}" || echo "")

if [ -z "${RESPONSE}" ]; then
    echo "ERROR: Health check failed! No response from ${HEALTH_ENDPOINT}" >&2
    exit 1
fi

STATUS=$(echo "${RESPONSE}" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
DB_STATUS=$(echo "${RESPONSE}" | grep -o '"db":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
AS_OF=$(echo "${RESPONSE}" | grep -o '"as_of":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
RECORDS=$(echo "${RESPONSE}" | grep -o '"records_count":[0-9]*' | cut -d':' -f2 || echo "0")

echo "==> Service Status: ${STATUS}"
echo "==> Database Status: ${DB_STATUS}"
echo "==> Data As Of Date: ${AS_OF}"
echo "==> Indexed Records: ${RECORDS}"

if [ "${STATUS}" != "ok" ] || [ "${DB_STATUS}" != "ok" ]; then
    echo "ERROR: Unhealthy service components detected!" >&2
    exit 1
fi

echo "==> All health probes OK."
exit 0
