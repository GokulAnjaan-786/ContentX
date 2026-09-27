# ContentForge AI - Disaster Recovery & Backup Runbook

This runbook establishes standard operational procedures for data protection, scheduled backups, point-in-time database restoration, object versioning, and deployment rollback.

---

## 1. Automated Backup Strategy

The backup architecture provides protection across two data planes:
1. **Relational & Vector Data (PostgreSQL + pgvector)**: Nightly compressed binary dump (`pg_dump -Fc`).
2. **Raw Document Files (MinIO / S3)**: Object versioning enabled on the bucket, with 90-day retention policies managed via Celery Beat.

### 1.1 Scheduling Nightly Backups via Cron

Install the backup script as a root cron job on the VPS host:

```bash
# Open crontab editor
crontab -e

# Run nightly at 02:00 AM UTC and append logs
0 2 * * * /opt/contentforge/infra/scripts/backup.sh >> /var/log/contentforge_backup.log 2>&1
```

### 1.2 Backup Storage & Rotation

- Dumps are stored by default in `/var/backups/contentforge/`.
- File naming pattern: `db_contentforge_YYYYMMDD_HHMMSS.dump`.
- Backups older than 14 days (`RETENTION_DAYS=14`) are automatically pruned.
- **Recommended Offsite Replication**: Sync backups daily to cold cloud storage (e.g. AWS S3 Glacier or Cloudflare R2):
  ```bash
  aws s3 sync /var/backups/contentforge/ s3://company-contentforge-cold-backups/ --delete
  ```

---

## 2. MinIO Object Storage Versioning & Recovery

MinIO object versioning is enabled upon container initialization:

```bash
# Check versioning status
docker exec contentforge_minio_init /usr/bin/mc version info myminio/contentforge-documents

# Enable versioning manually if needed
docker exec contentforge_minio_init /usr/bin/mc version enable myminio/contentforge-documents
```

### 2.1 Restoring Accidentally Deleted Raw Files

When versioning is active, deleting an object inserts a *delete marker* without deleting previous binary versions:

```bash
# List all versions including delete markers
docker exec contentforge_minio_init /usr/bin/mc ls --versions myminio/contentforge-documents/

# Restore a deleted object by removing the delete marker
docker exec contentforge_minio_init /usr/bin/mc rm --version-id "<DELETE_MARKER_ID>" myminio/contentforge-documents/<file_path>
```

---

## 3. Database Restoration Procedure

In the event of database corruption, accidental loss, or infrastructure failure:

### Step 1: Identify the Latest Known-Good Backup

```bash
ls -lh /var/backups/contentforge/db_contentforge_*.dump
```

### Step 2: Stop Incoming API Traffic

Prevent concurrent writes by scaling down or pausing the backend service:

```bash
docker compose -f infra/docker-compose.yml stop backend worker celery-beat
```

### Step 3: Execute Restoration Script

```bash
./infra/scripts/restore.sh /var/backups/contentforge/db_contentforge_20260926_020000.dump
```

The script executes:
1. `SELECT pg_terminate_backend(pid)` to close hanging connections.
2. `pg_restore --clean --if-exists` to rebuild tables, indexes, and vector embeddings.
3. `alembic upgrade head` to verify schema migration alignment.

### Step 4: Restart Backend Services & Validate Health

```bash
docker compose -f infra/docker-compose.yml up -d backend worker celery-beat
curl -s http://localhost:8000/health | jq .
```

---

## 4. Production Rollback Procedure

If a newly deployed release introduces unexpected defects, regressions, or performance bottlenecks:

### Step 1: Identify Last Stable Docker Image Tags

Image tags are tagged with git commit hashes in CI/CD (e.g. `ghcr.io/org/contentforge-backend:c4e3f1a`):

```bash
# View recent images
docker images | grep contentforge
```

### Step 2: Rollback Docker Containers

Deploy the previous stable image tag:

```bash
# Set rollback image tags
export BACKEND_IMAGE_TAG="sha-prev-commit-hash"
export FRONTEND_IMAGE_TAG="sha-prev-commit-hash"

# Pull and redeploy
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d --no-deps backend frontend worker celery-beat
```

### Step 3: Revert Database Migrations (If Schema Was Altered)

If the failed release introduced an incompatible Alembic migration:

```bash
# Check current migration revision
docker exec contentforge_backend alembic current

# Downgrade by 1 revision (or to a specific revision ID)
docker exec contentforge_backend alembic downgrade -1

# Confirm current revision matches expected previous state
docker exec contentforge_backend alembic current
```

### Step 4: Verification Checklist

1. Probing `GET /health`: All backing dependencies (`database`, `redis`, `minio`, `ollama`) must report `"up"`.
2. Probing `GET /metrics`: Confirm metric collection resumes without elevated 5xx error spikes.
3. Run the automated integration test:
   ```bash
   pytest backend/tests/test_full_pipeline_e2e.py -v
   ```
4. Check Celery Flower dashboard at `http://<domain>/flower/` for task queue health.
