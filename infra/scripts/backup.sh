#!/usr/bin/env bash
# ==============================================================================
# OpenPaperCheck Encrypted Backup Script
# Creates an AES-256 encrypted archive of PostgreSQL data or SQLite snapshot.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${OPC_BACKUP_DIR:-./infra/backups}"
mkdir -p "${BACKUP_DIR}"

PASSPHRASE="${OPC_BACKUP_PASSPHRASE:-opc-secure-default-backup-key}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BASE_NAME="opc_backup_${TIMESTAMP}"
RAW_ARCHIVE="${BACKUP_DIR}/${BASE_NAME}.sql.gz"
ENCRYPTED_ARCHIVE="${BACKUP_DIR}/${BASE_NAME}.enc"

echo "==> [Backup] Initiating backup at ${TIMESTAMP}..."

# 1. Capture Database Dump
if command -v docker &>/dev/null && docker ps --format '{{.Names}}' | grep -q "opc-db"; then
    echo "==> Dumping from PostgreSQL container 'opc-db'..."
    docker exec opc-db pg_dump -U opc -d opc --clean --if-exists | gzip > "${RAW_ARCHIVE}"
elif [ -f "data/snapshots/retraction_records.sqlite" ]; then
    echo "==> Archiving local SQLite snapshot..."
    gzip -c "data/snapshots/retraction_records.sqlite" > "${RAW_ARCHIVE}"
elif [ -f "${HOME}/.cache/openpapercheck/retraction_records.sqlite" ]; then
    echo "==> Archiving cached SQLite snapshot..."
    gzip -c "${HOME}/.cache/openpapercheck/retraction_records.sqlite" > "${RAW_ARCHIVE}"
else
    echo "==> Creating mock schema archive for testing drill..."
    echo "-- OpenPaperCheck Schema Backup ${TIMESTAMP}" | gzip > "${RAW_ARCHIVE}"
fi

# 2. Encrypt with AES-256-CBC
echo "==> Encrypting archive with OpenSSL AES-256-CBC..."
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
    -in "${RAW_ARCHIVE}" \
    -out "${ENCRYPTED_ARCHIVE}" \
    -pass pass:"${PASSPHRASE}"

# 3. Compute Checksum
CHECKSUM=$(shasum -a 256 "${ENCRYPTED_ARCHIVE}" | cut -d' ' -f1)
echo "${CHECKSUM}  $(basename "${ENCRYPTED_ARCHIVE}")" > "${ENCRYPTED_ARCHIVE}.sha256"

# Clean up unencrypted raw archive
rm -f "${RAW_ARCHIVE}"

SIZE=$(du -h "${ENCRYPTED_ARCHIVE}" | cut -f1)
echo "==> [Backup] Encrypted backup created successfully:"
echo "    Archive:  ${ENCRYPTED_ARCHIVE} (${SIZE})"
echo "    Checksum: ${CHECKSUM}"

# 4. Optional Offsite S3 Upload
if [ -n "${BACKUP_S3_BUCKET:-}" ] && command -v aws &>/dev/null; then
    echo "==> Uploading encrypted archive to s3://${BACKUP_S3_BUCKET}/..."
    aws s3 cp "${ENCRYPTED_ARCHIVE}" "s3://${BACKUP_S3_BUCKET}/"
    aws s3 cp "${ENCRYPTED_ARCHIVE}.sha256" "s3://${BACKUP_S3_BUCKET}/"
fi

echo "==> [Backup] Done."
