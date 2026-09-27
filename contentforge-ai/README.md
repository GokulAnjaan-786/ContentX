# ContentForge AI — Enterprise Content Transformation Platform

**ContentForge AI** is an enterprise-grade AI-powered content transformation platform. Operators upload source content (PDF, DOCX, or raw text — such as incident reports, technical articles, and regulatory advisories), and the system executes a single, rigorous **Content Understanding Pass** to build a structured, immutable **Fact Registry**. All downstream multi-channel generators (LinkedIn, Twitter Threads, Advisories, Executive Summaries, Presentations, Infographics, Video Packages) read strictly from that same Fact Registry — guaranteeing factual consistency, full provenance traceability, and zero hallucinations across channels.

---

## Architecture Overview (Parts 1–4 Unified)

```
                            [ Web Browser / Client ]
                                        │
                                        ▼ (HTTPS:443 / HTTP:80)
                             [ Nginx Reverse Proxy ]
                          (TLS Termination, Rate Limit)
                                        │
                   ┌────────────────────┴────────────────────┐
                   ▼                                         ▼
         [ Next.js Frontend ]                       [ FastAPI Backend ]
       (React, Tailwind, Query)                (Auth, Security, Routes, APIs)
                                                             │
                  ┌───────────────────────┬──────────────────┴──────────────────┐
                  ▼                       ▼                                     ▼
        [ PostgreSQL 16 ]            [ Redis 7 ]                         [ MinIO Storage ]
        (pgvector, Facts,          (Broker, Limits,                       (S3 Multi-Tenant
         Users, Audit Logs)         Task Queues)                         Encrypted Buckets)
                  ▲                       ▲                                     ▲
                  │                       │                                     │
                  └───────────────────────┼─────────────────────────────────────┘
                                          ▼
                                   [ Celery Worker ]
                         (Extraction, Understanding Pass,
                            Multi-Format AI Generators)
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [ ClamAV Daemon ]                               [ Ollama Model Server ]
      (Streaming Antivirus)                            (Qwen 2.5 7B, BAAI/bge-m3)
```

---

## Key Capabilities by Build Phase

### Part 1: Secure Ingestion & Document Processing Foundation
- **Authentication & RBAC**: JWT Bearer auth, bcrypt password hashing, 4 roles (`operator`, `reviewer`, `org_admin`, `system_admin`), token expiration.
- **Deep File Validation**: True MIME inspection via `python-magic` rejecting disguised files (e.g., `.exe` renamed to `.pdf`), 20MB file size limit.
- **Antivirus Inspection**: In-memory streaming virus scanning via ClamAV daemon.
- **Document Chunking Engine**: PyMuPDF (PDF) and python-docx (DOCX) text extraction, repeated header/footer removal, hyphenated word repair, and sliding-window chunking (~600 words, 50-word overlap) preserving page and section references.
- **Object Storage**: Multi-tenant encrypted file storage in MinIO.

### Part 2: Content Understanding & Fact Registry Core
- **Single Understanding Pass**: AI model reads the document only once, producing an immutable Fact Registry with atomic facts, unique IDs (`[f1]`, `[f2]`), category, confidence score, and source chunk provenance.
- **Semantic Embeddings**: `BAAI/bge-m3` vectors stored in PostgreSQL via `pgvector` for similarity search.
- **7 Coordinated Output Generators**:
  1. *LinkedIn Post*: Hook, structured body, hashtags, call-to-action.
  2. *Twitter Thread*: Numbered 1/N sequence of punchy tweets with embedded citations.
  3. *Security Advisory*: Severity level, affected systems, root cause, actionable remediation steps.
  4. *Executive Summary*: Headline, high-level overview, key metrics, strategic takeaways.
  5. *Infographic Data Points*: Key stats, narrative flow, layout recommendations, color themes.
  6. *Presentation Slides*: Structured slide decks with titles, bullet points, and speaker notes.
  7. *Video Script Package*: 30s/60s hook, scene-by-scene visual cues, voiceover narration, outro.
- **Hallucination Guard & Cross-Output Consistency**: Automated validation rejecting unverified statements, enforcing JSON schemas, and detecting cross-output metric/date contradictions.

### Part 3: Interactive Operator Dashboard & Traceability UI
- **Modern Dashboard**: Next.js App Router, React Query, and Tailwind CSS.
- **Document Hub & Real-Time Polling**: Upload with drag-and-drop, sensitivity tagging, and live status progress.
- **Fact Registry Viewer**: Search, filter, and inspect verified facts with source chunk links.
- **Channel Selector & Generation Studio**: Configure tone, audience, detail level, and target objective.
- **Interactive Traceability Drawer**: Click any generated sentence to highlight the exact backing fact in the Fact Registry, with clear amber warnings for unverified statements.
- **Multi-Format Export**: Export verified outputs to Markdown, JSON, or plaintext.

### Part 4: Production Hardening, Security, Monitoring & CI/CD
- **Prompt Injection Defense**:
  - Audited all generator prompt templates wrapping inputs in `<source_document>` and `<fact_registry>` XML delimiters with an immutable system instruction boundary.
  - Pre-processing adversarial scanner (`ai-services/security/injection_scanner.py`) detecting direct overrides, persona hijacks, and delimiter escapes before sending to LLM.
- **PII Detection Engine**:
  - Regex-based scanner (`app/services/pii_service.py`) detecting emails, phone numbers, SSNs, credit cards (Luhn validated), and national IDs.
  - Stored in database via Alembic migration (`0003_add_pii_and_security_flags.py`) and surfaced via warning banners on frontend preview.
- **Extended Dynamic Rate Limiting**: `slowapi` rate limiting on `/documents/upload` (10/hr) and `/generate` (20/hr), configurable via `.env`.
- **Complete Lifecycle Audit Logging**: Immutable logs recording uploads, understanding passes, generation jobs, edits, exports, and login/logout.
- **Automated Data Retention Policy**: Scheduled daily Celery Beat task deleting raw MinIO documents older than `DATA_RETENTION_DAYS` (default: 90 days) while preserving minimal audit trails.
- **Unified Health Endpoint (`GET /health`)**: Verifies PostgreSQL, Redis, MinIO, and Ollama server availability with HTTP 200/503 status codes.
- **Prometheus & Sentry Observability**:
  - Automatic request count, duration, and error rate middleware on `/metrics`.
  - Custom metrics tracking AI generation latency per format and model failure rates (`app/core/metrics.py`).
  - 3 pre-provisioned Grafana dashboards: *API Health*, *Celery Queue & Workers*, and *AI Generation Performance*.
  - Sentry exception tracking across backend and frontend.
- **AI Evaluation Pipeline (DeepEval / RAGAS)**:
  - 16 curated golden test documents with verified ground-truth facts (`ai-services/evaluation/golden_dataset.py`).
  - Automated evaluation script (`ai-services/evaluation/evaluator.py`) scoring *Faithfulness*, *Answer Relevancy*, and *Contextual Recall*.
  - Admin endpoint `GET /admin/evaluation-report` reporting latest model performance scores.
- **Comprehensive Testing Suite**:
  - 44 backend tests (100% passing) covering unit, integration, and security scenarios (SQLi resilience, rate limiting 429, prompt injection, PII).
  - 13 frontend Jest tests (100% passing).
  - Full E2E integration test (`test_full_pipeline_e2e.py`) verifying 5-page PDF upload, chunking, understanding, 4 outputs, schema compliance, and performance (<60s).
  - Locust load testing script (`infra/load_testing/locustfile.py`) simulating 50 concurrent users.
- **Deployment Infrastructure**: Complete Docker Compose stack (13 services), production override (`docker-compose.prod.yml`), Nginx reverse proxy with TLS termination and Let's Encrypt support, automated database backups (`infra/scripts/backup.sh`), and GitHub Actions CI/CD workflows (`.github/workflows/ci.yml` & `deploy.yml`).

---

## Directory Structure

```
contentforge-ai/
├── .github/workflows/
│   ├── ci.yml                           # GitHub Actions CI: Pytest, Jest, Ruff, Docker build
│   └── deploy.yml                       # GitHub Actions CD: GHCR build & SSH VPS deploy
├── backend/
│   ├── app/
│   │   ├── api/                         # auth.py, documents.py, generation.py, admin.py, deps.py
│   │   ├── core/                        # config.py, database.py, security.py, rate_limit.py, metrics.py
│   │   ├── models/                      # user.py, document.py, fact_registry.py, generation_job.py, etc.
│   │   ├── schemas/                     # auth.py, document.py, generation.py, fact_registry.py
│   │   ├── services/                    # pii_service.py, document_service.py, health_service.py, etc.
│   │   └── main.py                      # FastAPI entrypoint, Prometheus middleware, Sentry init
│   ├── alembic/                         # Database migrations (0001, 0002, 0003)
│   ├── tests/                           # 44 passing pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── ai-services/
│   ├── extraction/                      # pdf_extractor.py, docx_extractor.py, cleaner.py, chunker.py
│   ├── understanding/                   # fact_extraction.py, embeddings.py
│   ├── orchestrator/                    # output_router.py, context_builder.py
│   ├── generators/                      # 7 format generators (linkedin, twitter, advisory, etc.)
│   ├── validation/                      # schema_validator.py, fact_checker.py
│   ├── security/                        # injection_scanner.py (prompt injection defense)
│   ├── evaluation/                      # golden_dataset.py, evaluator.py, results/
│   └── prompts/                         # 8 audited prompt templates with strict delimiters
├── frontend/
│   ├── app/                             # Next.js App Router (dashboard, auth, preview, results)
│   ├── components/                      # ContentPreview, FactRegistryDrawer, GenerationConfig, etc.
│   ├── lib/                             # api.ts (JWT client & error interceptors)
│   ├── __tests__/                       # 13 passing Jest test suites
│   ├── Dockerfile
│   └── package.json
├── worker/
│   ├── celery_app.py                    # Celery application & beat schedule (daily retention)
│   ├── tasks.py                         # Background processing & data retention purge
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml               # 13 services (backend, frontend, postgres, redis, minio, etc.)
│   ├── docker-compose.prod.yml          # Production override (port restrictions, restart: always, certbot)
│   ├── nginx/                           # default.conf, proxy_rules.inc, nginx.conf
│   ├── prometheus/                      # prometheus.yml (FastAPI & Celery Flower scrape targets)
│   ├── grafana/                         # Provisioning & 3 pre-built dashboards (API, Celery, AI)
│   ├── scripts/                         # backup.sh, restore.sh
│   ├── load_testing/                    # locustfile.py, run_load_test.sh
│   └── DISASTER_RECOVERY.md             # Complete backup, restore, and rollback runbook
├── .env.example                         # Unified environment template with Vault swap guide
├── PRODUCTION_READINESS.md              # Complete 34-point production audit checklist
└── README.md
```

---

## Production Deployment (Single VPS with Docker Compose)

### 1. Prerequisites
- Docker Engine 24+ and Docker Compose v2+
- Linux VPS (Ubuntu 22.04 / 24.04 LTS recommended, 4+ CPU cores, 16GB+ RAM)
- Domain name pointing to your VPS IP address (e.g., `contentforge.ai`)

### 2. Clone and Configure
```bash
git clone https://github.com/your-org/contentforge-ai.git /opt/contentforge
cd /opt/contentforge

# Create production environment file from example
cp .env.example .env

# Generate high-entropy secret keys
sed -i "s/change-this-to-a-super-secret-hex-key.*/$(openssl rand -hex 32)/" .env
```

### 3. Launch Complete Stack
```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d --build
```

### 4. Verify System Health
```bash
curl -s http://localhost:8000/health | jq .
```

All backing dependencies (`database`, `redis`, `minio`, `ollama`) will report `"up"`.

---

## Local Development (Without Docker)

### 1. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the ContentForge AI dashboard.

---

## Running the Automated Test Suites

### 1. Backend Unit, Security & Integration Suite (Pytest)
```bash
cd contentforge-ai
PYTHONPATH=backend:ai-services pytest backend/tests/ -v
```
*Expected: 44 passed.*

### 2. Frontend Unit & Component Suite (Jest)
```bash
cd frontend
npm test
```
*Expected: 13 passed.*

### 3. Full End-to-End Pipeline & Performance Benchmark
```bash
pytest backend/tests/test_full_pipeline_e2e.py -v -s
```
*Uploads sample 5-page PDF, executes sliding-window chunking, triggers single Understanding Pass, generates 4 parallel channels, verifies schema compliance, and asserts completion time < 60 seconds.*

### 4. AI Quality Evaluation Pipeline (DeepEval Golden Dataset)
```bash
PYTHONPATH=backend:ai-services python3 ai-services/evaluation/evaluator.py --limit 4
```
*Calculates Faithfulness, Answer Relevancy, and Contextual Recall scores, saving reports to `ai-services/evaluation/results/`.*

### 5. Load Testing (Locust)
```bash
./infra/load_testing/run_load_test.sh http://localhost:8000 50 10 30s
```
*Simulates 50 concurrent operators triggering generation jobs to verify Celery/Redis queue backpressure.*

---

## Monitoring & Observability Dashboards

Once deployed, access the monitoring stack:
- **Prometheus UI**: `http://<domain>:9090`
- **Grafana Dashboards**: `http://<domain>:3001` (Default user: `admin`, Password: `${GRAFANA_ADMIN_PASSWORD}`)
  - *ContentForge AI - API Health & Latency*
  - *ContentForge AI - Celery Queue & Worker Health*
  - *ContentForge AI - Generation & Model Performance*
- **Celery Flower Task Monitor**: `http://<domain>/flower/`
- **Application Health Check**: `http://<domain>/health`
- **Prometheus Metrics Stream**: `http://<domain>/metrics`

---

## Data Protection, Backups & Disaster Recovery

- **Nightly PostgreSQL Backup**:
  ```bash
  ./infra/scripts/backup.sh
  ```
  Creates compressed `.dump` files in `/var/backups/contentforge/` and verifies MinIO bucket versioning.
- **Database Restoration**:
  ```bash
  ./infra/scripts/restore.sh /var/backups/contentforge/db_contentforge_latest.dump
  ```
- **Automated Data Retention**: Scheduled Celery Beat job purges raw MinIO files older than 90 days.
- **Disaster Recovery Guide**: See [infra/DISASTER_RECOVERY.md](file:///Users/user/Desktop/ContentX/contentforge-ai/infra/DISASTER_RECOVERY.md) for full runbooks and rollback steps.

---

## Part 5: Blockchain Trust Layer & Public Verification Portal

In cybersecurity and critical enterprise communications, official-looking bulletins, threat advisories, and executive summaries can be spoofed, altered, or weaponized. ContentForge AI solves this by introducing a **cryptographic trust layer** that makes every approved output provably tamper-evident and publicly verifiable without exposing confidential content.

### 1. How the Hash-Chain Works (In Simple Terms)

A hash-chain is an ordered cryptographic ledger where each record contains the exact cryptographic fingerprint (SHA-256) of the preceding block:

$$\text{record\_hash}_i = \text{SHA-256}(\text{chain\_index}_i \mathbin{\Vert} \text{previous\_record\_hash}_i \mathbin{\Vert} \text{content\_hash}_i \mathbin{\Vert} \text{record\_type}_i \mathbin{\Vert} \text{organisation\_id})$$

If an attacker tries to alter a historical document or change one word in an approved advisory:
1. That record's `content_hash` changes.
2. Its `record_hash` recalculates to a completely different value.
3. The *next* record in the chain still expects the original `previous_record_hash`.
4. The cryptographic link breaks, and `verify_chain()` immediately reports the exact block index of the tampering.

#### Worked Example: 3 Linked Records

```
┌────────────────────────────────────────────────────────┐
│ Block #0: Genesis Upload (Source Incident Report PDF)  │
├────────────────────────────────────────────────────────┤
│ chain_index:          0                                │
│ previous_record_hash: 00000000000000000000000000000000 │
│ content_hash:         4f53cda18c2baa0c0354bb5f9a3ecbe5 │
│ record_hash:          9a72b14c3e80d216f409bc2e11894d3a │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼ (Linked by previous_record_hash)
┌────────────────────────────────────────────────────────┐
│ Block #1: Generated Output (Security Advisory JSON)    │
├────────────────────────────────────────────────────────┤
│ chain_index:          1                                │
│ previous_record_hash: 9a72b14c3e80d216f409bc2e11894d3a │
│ content_hash:         e3b0c44298fc1c149afbf4c8996fb924 │
│ record_hash:          d41d8cd98f00b204e9800998ecf8427e │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼ (Linked by previous_record_hash)
┌────────────────────────────────────────────────────────┐
│ Block #2: Generated Output (Executive Summary JSON)    │
├────────────────────────────────────────────────────────┤
│ chain_index:          2                                │
│ previous_record_hash: d41d8cd98f00b204e9800998ecf8427e │
│ content_hash:         8b1a9953c4611296a827abf8c47804d7 │
│ record_hash:          c4ca4238a0b923820dcc509a6f75849b │
└────────────────────────────────────────────────────────┘
```

---

### 2. Independent Reviewer Signature Verification (Step-by-Step)

Approving an output signs its content hash using the reviewer's private Ed25519 key. Anyone outside the organisation can independently verify the authenticity of an output without needing a ContentForge account or access to the database:

1. Retrieve the signature and public key from `GET /outputs/{id}/signature` or the public verification metadata.
2. Run this independent Python snippet using standard cryptography primitives:

```python
from cryptography.hazmat.primitives.asymmetric import ed25519
import hashlib
import json

# Inputs from verification metadata
public_key_hex = "7dc43fe75e43a91b2c45f8e91024bb6a3012de94ff6c12ab8e4210a51c9d2f0a"
signature_hex = "20056c557a9f813c9e6d0124ba91d29384501a9df8e763102d84c102a9e34c9103948192a839f8291039d0129a8f..."
content_payload = {"title": "Zero-Day Infiltration Advisory", "severity": "CRITICAL"}

# 1. Canonical SHA-256 hash of the content
canonical_json = json.dumps(content_payload, sort_keys=True, separators=(',', ':'))
content_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

# 2. Verify with standard RFC 8032 Ed25519
public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
try:
    public_key.verify(bytes.fromhex(signature_hex), content_hash.encode('utf-8'))
    print("✅ Signature is mathematically valid! The reviewer approved this exact content.")
except Exception as e:
    print("❌ Invalid signature! Content has been modified.")
```

---

### 3. Public Blockchain Anchoring (Polygon Amoy Testnet)

ContentForge AI includes a toggleable public testnet anchor module (`backend/app/services/public_anchor_service.py`).
- **Default Mode (Local Ledger)**: `ENABLE_PUBLIC_ANCHOR=false`. The system is 100% operational using the local tamper-evident PostgreSQL hash chain alone.
- **Optional Public Mode**: `ENABLE_PUBLIC_ANCHOR=true`. Periodically notarizes the latest chain head hash to Polygon Amoy testnet.

#### Free Polygon Amoy Testnet Setup:
1. **Get Free Test MATIC**:
   - Visit the official Polygon Faucet: [faucet.polygon.technology](https://faucet.polygon.technology/)
   - Select **Polygon PoS (Amoy)** and paste your test wallet address.
2. **Configure `.env`**:
   ```env
   ENABLE_PUBLIC_ANCHOR=true
   POLYGON_AMOY_RPC_URL="https://rpc-amoy.polygon.technology"
   POLYGON_AMOY_CHAIN_ID=80002
   PUBLIC_ANCHOR_PRIVATE_KEY="0x_your_amoy_testnet_private_key"
   ```
3. When enabled, transactions submit only the 32-byte hash `CF_ANCHOR:{record_hash}`, ensuring **zero confidential data ever touches the public blockchain**.

---

### 4. Public Verification Portal

- **URL by Record ID**: `http://localhost:3000/verify/[recordId]`
  - Accessible to anyone with zero login required.
  - Displays big green **"✅ VERIFIED"** badge with issuing organization, approver, and chain integrity, or red **"❌ NOT VERIFIED"** if altered.
  - Never leaks raw document or output content.
- **Verify by Content**: `http://localhost:3000/verify`
  - Allows pasting forwarded advisory text or uploading a file to check if its cryptographic hash exists in the official ledger.
- **Interactive Live Demo Script**: See [DEMO_SCRIPT.md](file:///Users/user/Desktop/ContentX/contentforge-ai/DEMO_SCRIPT.md) for live presentation steps.

---

## License

ContentForge AI is distributed under the MIT Open Source License.

