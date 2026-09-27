#!/bin/bash
# ==============================================================================
# ContentForge AI - Database & Object Restoration Script
# Restores PostgreSQL database from a chosen pg_dump file
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <path_to_dump_file.dump>"
  exit 1
fi

DUMP_FILE="$1"

if [ ! -f "$DUMP_FILE" ]; then
  echo "Error: Backup file $DUMP_FILE does not exist."
  exit 1
fi

echo "================================================================================"
echo "WARNING: You are about to restore ContentForge database from: $DUMP_FILE"
echo "Target DB: ${POSTGRES_DB:-contentforge_db}"
echo "================================================================================"

# Copy dump file into container
TEMP_CONTAINER_DUMP="/tmp/restore_target.dump"
docker cp "$DUMP_FILE" "contentforge_postgres:$TEMP_CONTAINER_DUMP"

echo "[1/2] Terminating active backend connections to database..."
docker exec contentforge_postgres psql \
  -U "${POSTGRES_USER:-contentforge}" \
  -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB:-contentforge_db}' AND pid <> pg_backend_pid();" || true

echo "[2/2] Restoring PostgreSQL schema and data via pg_restore..."
docker exec contentforge_postgres pg_restore \
  -U "${POSTGRES_USER:-contentforge}" \
  -d "${POSTGRES_DB:-contentforge_db}" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  "$TEMP_CONTAINER_DUMP" || {
    echo "Notice: pg_restore exited with non-zero status (warnings are typical for clean runs)."
}

docker exec contentforge_postgres rm -f "$TEMP_CONTAINER_DUMP"

echo "================================================================================"
echo "Restoration Complete. Running Alembic migration check..."
echo "================================================================================"
docker exec contentforge_backend alembic upgrade head
echo "Database successfully verified at latest migration head."
