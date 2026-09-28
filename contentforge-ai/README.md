# ContentForge AI — Enterprise Content Transformation Platform

ContentForge AI is an enterprise-grade AI-powered content transformation platform. It ingests source documents (PDF, DOCX, or raw text) and executes a single **Content Understanding Pass** to build a structured, immutable **Fact Registry**. Multi-channel generators then read from that Fact Registry to produce verified multi-format content (LinkedIn posts, Twitter threads, Advisories, Executive Summaries, Presentation slides, Infographics, and Video scripts) with full provenance traceability and zero hallucinations.

---

## 1. Project Overview

### What the Project Is
ContentForge AI is a multi-tenant web application that automates the process of converting complex documents (such as incident reports, technical advisories, research papers, and corporate eBooks) into publication-ready content across multiple media formats.

### What Problem It Solves
Traditional AI content creation often suffers from hallucinated facts, lost context, inconsistent metrics across formats, and a lack of auditability. ContentForge AI solves this by enforcing a strict **Fact Registry Architecture**:
- Source documents are chunked and analyzed once during an **Understanding Pass**.
- An immutable list of atomic facts is stored with exact source snippet provenance.
- Downstream AI generators are strictly bound to ground their outputs on these verified facts.

### Main Features
- **Multi-Format Ingestion**: Upload PDF, DOCX, or paste raw text up to 20MB.
- **Deep Security & File Inspection**: MIME inspection via `python-magic`, streaming ClamAV antivirus scanning, PII detection, and prompt injection defense.
- **Immutable Fact Registry**: Automated extraction of grounded facts with unique IDs (`[f1]`, `[f2]`), confidence scoring, and page references.
- **7 Target Output Channels**:
  1. *LinkedIn Post*: Hook, body, hashtags, call-to-action.
  2. *Twitter Thread*: Sequenced 1/N tweets with embedded citations.
  3. *Security Advisory*: Severity, affected scope, technical details, recommended mitigations.
  4. *Executive Summary*: Strategic takeaways, high-level summary, key metrics.
  5. *Infographic*: Key statistics, icon suggestions, narrative flow.
  6. *Presentation Slides*: Structured slide deck with bullet points and speaker notes.
  7. *Video Script Package*: Scene-by-scene narration, visual cues, subtitle text.
- **Interactive Traceability UI**: Click any generated sentence to view the exact backing fact and source chunk in the Fact Registry.
- **Semantic RAG & Vector Search**: BAAI `bge-m3` 1024-dimensional embeddings stored in PostgreSQL via `pgvector`.
- **Audience & Tone Customization**: Tailor outputs for technical, executive, or general audiences across concise, standard, or comprehensive detail levels.

### Main Components/Services
1. **Frontend**: Next.js App Router UI for file uploads, fact inspection, transformation studio, and interactive claim verification.
2. **Backend**: FastAPI REST API handling authentication, document processing, job management, and rate limiting.
3. **AI Services**: Orchestration engine for chunking, understanding passes, BGE-M3 embeddings, output routing, and schema validation.
4. **Database**: PostgreSQL 16 with `pgvector` extension for structured records and vector similarity search.
5. **Model Server**: Local Ollama server hosting LLM (`qwen2.5:7b-instruct`) and embedding model (`bge-m3:latest`).
6. **Async Workers**: Celery + Redis task queue for background job execution and daily retention policies.

---

## 2. Tech Stack

### Frontend Technology
- **Framework**: Next.js 14 (React 18, App Router)
- **Language**: TypeScript 5.6
- **Styling**: Tailwind CSS 3.4
- **State & Data Fetching**: `@tanstack/react-query` v5
- **Icons & UI Utilities**: `lucide-react`, `clsx`, `tailwind-merge`
- **Testing**: Jest 29, React Testing Library

### Backend Technology
- **Framework**: FastAPI 0.110+
- **Language**: Python 3.12+
- **ASGI Web Server**: Uvicorn 0.28+
- **ORM & Migrations**: SQLAlchemy 2.0+, Alembic 1.13+
- **Security & Rate Limiting**: Passlib (bcrypt), PyJWT (HS256), SlowAPI
- **File Processing**: PyMuPDF (`fitz`), `python-docx`, `python-magic`

### AI/ML Services & Models
- **Local LLM Model**: `qwen2.5:7b-instruct` (via Ollama API)
- **Embedding Model**: `bge-m3:latest` / `BAAI/bge-m3` (1024-dimensional vector embeddings)
- **Evaluation Engine**: DeepEval 0.21+ (Faithfulness, Relevancy, Recall scoring)

### Database
- **Primary Database**: PostgreSQL 16
- **Vector Search Extension**: `pgvector` (native `<=>` cosine distance operations)

### APIs & Protocols
- **API Architecture**: RESTful JSON HTTP endpoints
- **API Documentation**: OpenAPI / Swagger UI at `/docs`
- **Streaming & Async**: Celery with Redis broker

### Authentication & Authorization
- **Auth Token Standard**: JWT Bearer Tokens (`HS256`)
- **Password Hashing**: `bcrypt` (4.0.1)
- **Role-Based Access Control (RBAC)**: 4 Roles (`operator`, `reviewer`, `org_admin`, `system_admin`)

### Other Important Technologies
- **Caching & Message Broker**: Redis 7
- **Object Storage**: MinIO / S3 compatible storage
- **Antivirus Scanner**: ClamAV daemon
- **Observability**: Prometheus instrumentation (`prometheus-client`), Sentry SDK, Grafana dashboards

---

## 3. Project Structure

```
ContentX/
├── contentforge-ai/
│   ├── backend/                         # FastAPI backend application
│   │   ├── alembic/                     # Database migrations (0001, 0002, 0003)
│   │   ├── app/                         # Core FastAPI source code
│   │   │   ├── api/                     # REST API route handlers (auth, documents, generation)
│   │   │   ├── core/                    # Config, DB session, rate limits, security, metrics
│   │   │   ├── models/                  # SQLAlchemy ORM models (User, Document, FactRegistry, etc.)
│   │   │   ├── schemas/                 # Pydantic schemas for request/response validation
│   │   │   └── services/                # Business logic (PII scanner, document service, audit logs)
│   │   ├── tests/                       # Automated Pytest suite (44 backend tests)
│   │   ├── Dockerfile                   # Docker container manifest for backend
│   │   └── requirements.txt             # Python dependencies manifest
│   │
│   ├── frontend/                        # Next.js frontend web application
│   │   ├── app/                         # Next.js App Router pages (dashboard, output-selection, etc.)
│   │   ├── components/                  # React components (FactRegistryDrawer, ContentPreview, etc.)
│   │   ├── lib/                         # API client engine (api.ts, auth.ts)
│   │   ├── __tests__/                   # Frontend Jest test suites (13 tests)
│   │   ├── Dockerfile                   # Docker container manifest for frontend
│   │   └── package.json                 # Node.js dependencies and scripts
│   │
│   ├── ai-services/                     # AI Orchestration, RAG & Generation module
│   │   ├── extraction/                  # Text extraction (pdf_extractor, docx_extractor, chunker)
│   │   ├── understanding/               # Fact extraction, BGE-M3 embeddings, pgvector search
│   │   ├── orchestrator/                # Output router, context builder, audience profiles
│   │   ├── generators/                  # 7 format generators (linkedin, twitter, advisory, etc.)
│   │   ├── validation/                  # Schema validator and fact checker
│   │   ├── security/                    # Prompt injection scanner
│   │   ├── evaluation/                  # Golden dataset evaluator (DeepEval)
│   │   └── prompts/                     # Prompt templates with XML isolation boundaries
│   │
│   ├── worker/                          # Background processing queue
│   │   ├── celery_app.py                # Celery application configuration & beat schedules
│   │   └── tasks.py                     # Async generation tasks & data retention purge
│   │
│   ├── infra/                           # Infrastructure & deployment configuration
│   │   ├── docker-compose.yml           # Complete Docker Compose stack setup
│   │   ├── nginx/                       # Nginx reverse proxy configurations
│   │   ├── prometheus/                  # Prometheus scraping targets configuration
│   │   └── grafana/                     # Provisioned Grafana monitoring dashboards
│   │
│   └── .env.example                     # Environment template file
│
├── CONTENTX_LIVE_RAG_BGE_M3_PROOF_REPORT.md      # RAG & BGE-M3 runtime forensic proof report
├── CONTENTX_CONTENT_RELEVANCE_FORENSIC_AUDIT.md # Content relevance & metadata forensic report
└── README.md                            # Comprehensive project setup guide
```

---

## 4. Prerequisites

Before installing ContentForge AI, ensure the following runtimes and services are installed on your system:

### Required Runtimes & Languages
- **Python**: Version `3.12` or higher (`python --version`)
- **Node.js**: Version `20.x` or higher (`node --version`)
- **Package Managers**: `pip` (Python) and `npm` (Node.js)
- **Git**: Version `2.30+` (`git --version`)

### Required Database & Services
- **PostgreSQL**: Version `16+` with `pgvector` extension installed (`CREATE EXTENSION IF NOT EXISTS vector;`)
- **Ollama AI Server**: Running locally on `http://localhost:11434` with the following models pulled:
  ```bash
  ollama pull qwen2.5:7b-instruct
  ollama pull bge-m3:latest
  ```

### Optional Services (Production & Worker Acceleration)
- **Redis**: Version `7.0+` on port `6379` (Used for Celery task dispatch; backend falls back to inline execution if offline)
- **MinIO**: S3-compatible object storage on port `9000` (Backend falls back to local disk storage if offline)

---

## 5. Clone the Repository

Clone the project repository to your local system using Git:

```bash
git clone <repository-url>
cd ContentX/contentforge-ai
```

*(Replace `<repository-url>` with your actual Git repository clone URL).*

---

## 6. Environment Variables

Create a `.env` file inside the `contentforge-ai/` directory by copying `.env.example`:

```bash
cd contentforge-ai
cp .env.example .env
```

### Complete Environment Variable Reference

| Variable Name | Purpose | Status | Example / Default Value |
|---|---|---|---|
| `ENVIRONMENT` | Application environment mode (`development`, `production`, `testing`) | **Required** | `development` |
| `DEBUG` | Enables verbose debug logging | Optional | `true` |
| `APP_NAME` | Display title for the application | Optional | `"ContentForge AI"` |
| `API_V1_STR` | Base API URL prefix | Optional | `/api/v1` |
| `SECRET_KEY` | High-entropy secret key for JWT signing (minimum 32 chars) | **Required** | `your-32-character-secret-key-here` |
| `ALGORITHM` | Algorithm used for signing JWT tokens | Optional | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime duration in minutes | Optional | `60` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origin URLs | **Required** | `http://localhost:3000,http://localhost:8000` |
| `RATE_LIMIT_LOGIN` | SlowAPI rate limit for login endpoint | Optional | `"5/minute"` |
| `RATE_LIMIT_UPLOAD` | SlowAPI rate limit for document uploads | Optional | `"10/hour"` |
| `RATE_LIMIT_GENERATE` | SlowAPI rate limit for generation jobs | Optional | `"20/hour"` |
| `DATA_RETENTION_DAYS` | Auto-purge retention period for raw storage files | Optional | `90` |
| `POSTGRES_SERVER` | PostgreSQL server hostname | **Required** | `localhost` |
| `POSTGRES_PORT` | PostgreSQL server port | Optional | `5432` |
| `POSTGRES_USER` | PostgreSQL database user | **Required** | `contentforge` |
| `POSTGRES_PASSWORD` | PostgreSQL user password | **Required** | `your-database-password` |
| `POSTGRES_DB` | PostgreSQL database name | **Required** | `contentforge_db` |
| `DATABASE_URL` | Full SQLAlchemy connection string | **Required** | `postgresql://contentforge:your-password@localhost:5432/contentforge_db` |
| `REDIS_HOST` | Redis server hostname | Optional | `localhost` |
| `REDIS_PORT` | Redis server port | Optional | `6379` |
| `REDIS_URL` | Redis connection URL | Optional | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker connection string | Optional | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend connection string | Optional | `redis://localhost:6379/1` |
| `MINIO_ENDPOINT` | MinIO object storage host and port | Optional | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO admin access key | Optional | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO admin secret key | Optional | `minioadmin` |
| `MINIO_BUCKET_NAME` | Storage bucket name for raw documents | Optional | `contentforge-documents` |
| `MINIO_SECURE` | Enable SSL/TLS for MinIO connection | Optional | `false` |
| `CLAMAV_ENABLED` | Enable ClamAV antivirus scanning | Optional | `true` |
| `CLAMAV_HOST` | ClamAV antivirus daemon hostname | Optional | `localhost` |
| `CLAMAV_PORT` | ClamAV daemon port | Optional | `3310` |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum file upload size limit in bytes | Optional | `20971520` (20 MB) |
| `CHUNK_SIZE_TARGET` | Word target per document chunk | Optional | `600` |
| `CHUNK_OVERLAP` | Overlapping word count between consecutive chunks | Optional | `50` |
| `OLLAMA_BASE_URL` | Host URL for Ollama LLM & Embedding server | **Required** | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name for text generation | Optional | `qwen2.5:7b-instruct` |
| `EMBEDDING_MODEL` | Model name for vector embeddings | **Required** | `bge-m3:latest` |
| `RAG_CONTEXT_TOKEN_LIMIT` | Document word threshold triggering RAG search | Optional | `6000` |
| `PROMETHEUS_ENABLED` | Enable Prometheus metric scraping | Optional | `true` |
| `NEXT_PUBLIC_API_URL` | API Base URL consumed by Next.js frontend | **Required** | `http://localhost:8000` |

> **IMPORTANT**: Never commit `.env` or expose real secret keys in version control.

---

## 7. Installation Setup

Follow these step-by-step instructions to set up and run ContentForge AI locally.

---

### Step 1: Database Setup (PostgreSQL + pgvector)

1. Ensure PostgreSQL is running locally on port `5432`.
2. Access PostgreSQL via `psql` and create the user, database, and vector extension:

```sql
CREATE USER contentforge WITH PASSWORD 'your-database-password';
CREATE DATABASE contentforge_db OWNER contentforge;
GRANT ALL PRIVILEGES ON DATABASE contentforge_db TO contentforge;

-- Connect to contentforge_db and enable pgvector extension
\c contentforge_db
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### Step 2: AI Model Server Setup (Ollama)

1. Install and start Ollama locally (`http://localhost:11434`).
2. Pull the required LLM and embedding models:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull bge-m3:latest
```

---

### Step 3: Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd contentforge-ai/backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # On macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install required Python dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run database migrations using Alembic to create all tables:
   ```bash
   alembic upgrade head
   ```

5. Start the FastAPI backend server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The backend will start at `http://localhost:8000`. You can inspect interactive Swagger API documentation at `http://localhost:8000/docs`.

---

### Step 4: Frontend Setup (Next.js)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd contentforge-ai/frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

   The web interface will start at `http://localhost:3000`. Open your browser and navigate to `http://localhost:3000`.

---

### Step 5: Optional Background Worker (Celery + Redis)

*Note: If Redis is not installed, the FastAPI backend will automatically execute generation jobs inline.*

To run background async workers with Celery:
1. Ensure Redis is running on `localhost:6379`.
2. Start the Celery worker process:
   ```bash
   cd contentforge-ai
   celery -A worker.celery_app worker --loglevel=info
   ```

---

## 8. Running Tests

ContentForge AI includes complete test suites covering unit logic, integration routes, prompt security, and frontend components.

### Run Backend Unit & Security Tests (Pytest)
```bash
cd contentforge-ai
PYTHONPATH=backend:ai-services pytest backend/tests/ -v
```

### Run Frontend Unit & Component Tests (Jest)
```bash
cd contentforge-ai/frontend
npm test
```

### Run Full End-to-End Pipeline Verification
```bash
cd contentforge-ai
pytest backend/tests/test_full_pipeline_e2e.py -v -s
```

---

## 9. Verification & Health Check

Verify system health by sending a request to the backend health endpoint:

```bash
curl http://localhost:8000/health
```

Expected JSON response:
```json
{
  "status": "up",
  "service": "ContentForge AI",
  "environment": "development",
  "version": "1.0.0",
  "dependencies": {
    "database": { "status": "up", "details": "PostgreSQL reachable" },
    "ollama": { "status": "up", "details": "Ollama reachable (2 models available)" }
  }
}
```
