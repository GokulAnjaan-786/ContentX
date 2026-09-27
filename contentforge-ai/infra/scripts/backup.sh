#!/bin/bash
# ==============================================================================
# ContentForge AI - Automated Nightly Backup Script
# Performs PostgreSQL pg_dump, confirms MinIO object versioning, and rotates old dumps
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/contentforge}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_DUMP_FILE="${BACKUP_DIR}/db_contentforge_${TIMESTAMP}.dump"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"

echo "================================================================================"
echo "Starting ContentForge AI Backup - ${TIMESTAMP}"
echo "================================================================================"

# 1. Execute PostgreSQL pg_dump using custom binary format (-Fc)
echo "[1/3] Creating PostgreSQL database dump..."
docker exec contentforge_postgres pg_dump \
  -U "${POSTGRES_USER:-contentforge}" \
  -d "${POSTGRES_DB:-contentforge_db}" \
  -Fc \
  -f "/tmp/backup_${TIMESTAMP}.dump"

# Copy dump from container to host backup storage
docker cp "contentforge_postgres:/tmp/backup_${TIMESTAMP}.dump" "$DB_DUMP_FILE"
docker exec contentforge_postgres rm -f "/tmp/backup_${TIMESTAMP}.dump"

DUMP_SIZE=$(du -h "$DB_DUMP_FILE" | cut -f1)
echo "      Database dump successfully created: $DB_DUMP_FILE (Size: $DUMP_SIZE)"

# 2. Confirm MinIO Bucket Versioning is active
echo "[2/3] Verifying MinIO Object Storage Bucket Versioning..."
docker exec contentforge_minio_init /usr/bin/mc version info "myminio/${MINIO_BUCKET_NAME:-contentforge-documents}" || {
  echo "      Enabling versioning on bucket ${MINIO_BUCKET_NAME:-contentforge-documents}..."
  docker exec contentforge_minio_init /usr/bin/mc version enable "myminio/${MINIO_BUCKET_NAME:-contentforge-documents}"
}
echo "      MinIO bucket versioning verified."

# 3. Rotate Old Database Dumps (Prune older than RETENTION_DAYS)
echo "[3/3] Pruning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "db_contentforge_*.dump" -mtime +"$RETENTION_DAYS" -exec rm -vf {} \;

echo "================================================================================"
echo "Backup Completed Successfully at $(date -u +"%Y-%m-%d %H:%M:%SZ")"
echo "================================================================================"
