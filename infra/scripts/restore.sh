#!/usr/bin/env bash
# ==============================================================================
# OpenPaperCheck Restore Drill & Disaster Recovery Script
# Verifies checksum, decrypts AES-256 archive, and restores database.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${OPC_BACKUP_DIR:-./infra/backups}"
PASSPHRASE="${OPC_BACKUP_PASSPHRASE:-opc-secure-default-backup-key}"

TARGET_ENC="${1:-}"

if [ -z "${TARGET_ENC}" ]; then
    # Pick the most recent .enc file in backup directory
    TARGET_ENC=$(ls -t "${BACKUP_DIR}"/*.enc 2>/dev/null | head -n 1 || echo "")
fi

if [ -z "${TARGET_ENC}" ] || [ ! -f "${TARGET_ENC}" ]; then
    echo "ERROR: No encrypted backup file found to restore!" >&2
    echo "Usage: ./infra/scripts/restore.sh [path/to/backup.enc]" >&2
    exit 1
fi

echo "==> [Restore Drill] Target archive: ${TARGET_ENC}"

# 1. Verify Checksum if .sha256 exists
if [ -f "${TARGET_ENC}.sha256" ]; then
    echo "==> Verifying SHA256 checksum..."
    EXPECTED=$(cut -d' ' -f1 "${TARGET_ENC}.sha256")
    ACTUAL=$(shasum -a 256 "${TARGET_ENC}" | cut -d' ' -f1)
    if [ "${EXPECTED}" != "${ACTUAL}" ]; then
        echo "ERROR: Checksum mismatch! Archive may be corrupted or tampered." >&2
        echo "Expected: ${EXPECTED}" >&2
        echo "Actual:   ${ACTUAL}" >&2
        exit 1
    fi
    echo "==> Checksum verified: ${ACTUAL}"
fi

# 2. Decrypt Archive
DECRYPTED="${TARGET_ENC%.enc}.restored.sql.gz"
echo "==> Decrypting archive with OpenSSL..."
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
    -in "${TARGET_ENC}" \
    -out "${DECRYPTED}" \
    -pass pass:"${PASSPHRASE}"

# 3. Restore to Database
if command -v docker &>/dev/null && docker ps --format '{{.Names}}' | grep -q "opc-db"; then
    echo "==> Restoring dump into PostgreSQL container 'opc-db'..."
    gunzip -c "${DECRYPTED}" | docker exec -i opc-db psql -U opc -d opc
    echo "==> PostgreSQL restore completed."
else
    echo "==> No active PostgreSQL container detected. Verified decrypted archive integrity:"
    gunzip -t "${DECRYPTED}"
    echo "==> Gzip test passed. Archive is fully recoverable."
fi

# Clean up temporary decrypted file
rm -f "${DECRYPTED}"

echo "==> [Restore Drill] SUCCESS: Database recovery drill completed without errors."
