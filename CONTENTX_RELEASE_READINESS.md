# ContentX Release Readiness Guide

## 1. Product Overview

**ContentX** (ContentForge AI) is an enterprise-grade AI-powered content transformation platform. It accepts complex source documents (PDFs, DOCX, TXT) and deterministically transforms them into multi-format publishable artifacts (**LinkedIn, Twitter/X, Advisory, Executive Summary, Presentation, Infographic, Video Package**) while preserving 100% factual accuracy, claim traceability, numerical consistency, entity fidelity, and uncertainty tagging.

---

## 2. Current Architecture

ContentX is structured as a decoupled, multi-tier web application:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Next.js 14 Web Frontend                          │
│          (React, TailwindCSS, TypeScript, Lucide Icons, Shadcn UI)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / HTTP JSON (Port 8000)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            FastAPI Backend Server                           │
│  (Auth, Upload Stream, MIME Scanning, Job Router, Audit Logs, Provenance)  │
└──────────┬───────────────────────────┬───────────────────────────┬──────────┘
           │                           │                           │
┌──────────▼───────────┐   ┌───────────▼───────────┐   ┌───────────▼───────────┐
│ PostgreSQL + pgvector│   │    Ollama AI Models   │   │   Redis & Celery      │
│ (Vector DB & Facts)  │   │(BGE-M3 1024d + Qwen)  │   │  (Async Job Queue)    │
└──────────────────────┘   └───────────────────────┘   └───────────────────────┘
```

---

## 3. Verified AI Stack

- **Embedding Model**: Local Ollama `bge-m3:latest` (Native 1024-dimensional dense vectors)
- **Generator Model**: Local Ollama `qwen2.5:7b-instruct` (Context length 8,192 tokens)
- **Vector Database**: PostgreSQL 15+ with native `pgvector` v0.8.6 extension (`<=>` cosine distance operator)
- **Local Fallback**: Deterministic fallback vector generation active for offline resilience
- **External Paid APIs**: **Zero** (100% self-hosted local model stack; OpenRouter **not** used)

---

## 4. RAG Architecture

The ContentX Retrieval-Augmented Generation (RAG) system operates through a 9-stage sequence:

```mermaid
flowchart TD
    A["1. User Output Selection & Audience"] --> B["2. Query Construction (OUTPUT_RETRIEVAL_OBJECTIVES)"]
    B --> C["3. BGE-M3 Query Embedding (1024-dim Vector)"]
    C --> D["4. pgvector Cosine Distance Search (<=>)"]
    D --> E["5. Top-K Chunks Retrieved"]
    E --> F["6. Fact Registry Mapping"]
    F --> G["7. Importance-Aware Ranking (HIGH > MEDIUM > LOW)"]
    G --> H["8. Output-Specific Dynamic Context Cap (6-15 facts)"]
    H --> I["9. Existing Approved Generator Prompt Execution"]
```

---

## 5. Fact Registry

The **Fact Registry** is ContentX's single source of factual truth. During Stage 6 (Understanding Pass), raw extracted text is converted into atomic, immutable fact records stored in PostgreSQL `fact_registry`:

- **Fact ID**: Deterministic string identifier (`f1`, `f2`, `f3`, ...)
- **Source Chunk & Page**: Direct binding to `document_chunks.id` and page number
- **Fact Statement**: Concise factual sentence
- **Importance Tier**: `HIGH`, `MEDIUM`, `LOW`, or `INTERNAL`
- **Certainty Status**: `confirmed`, `suspected`, `potential`, `unconfirmed`
- **Entities & Metrics**: Extracted organization names, numbers, dates, CVE identifiers

---

## 6. Truth Compression

**Truth Compression** enables ContentX to adapt output tone, terminology, and explanation complexity for 4 target audience profiles without altering underlying facts:

1. **Technical**: Preserves detailed system metrics, technical jargon, and CVE identifiers.
2. **Executive**: Focuses on strategic risk, operational impact, and high-level summaries.
3. **Professional**: Standard business tone for corporate publishing.
4. **General Public**: Accessible, clear phrasing for non-technical stakeholders.

**Invariant Guarantee**: Audience adaptation changes *how* facts are stated, but **never** changes numbers, dates, entity names, status, or certainty.

---

## 7. Output Formats

ContentX supports 7 verified output formats:

1. **LinkedIn**: Professional post hook, structured paragraphs, key takeaways, and hashtags.
2. **Twitter/X**: Structured thread steps (1/N), concise insights, constrained to <= 280 chars per tweet.
3. **Advisory**: Formal security/operational notice with severity, scope, technical details, and mitigations.
4. **Executive Summary**: Strategic overview, key findings, operational impact, and unresolved risks.
5. **Presentation**: Structured slide deck (Title, Slide Number, Bullet Points, Speaker Notes, Visual Suggestion).
6. **Infographic**: Visual data breakdown with structured stats, section milestones, and icon suggestions.
7. **Video Package**: Broadcast script containing narrative hook, visual telemetry cues, and speaker lines.

---

## 8. Validation

Every generated output passes through a 2-stage automated validation pipeline:

1. **Schema Validation**: Pydantic model validation (`validate_output_schema()`) enforcing strict JSON output structures.
2. **Fact Grounding Check**: Claim verification against the document's Fact Registry (`verify_output_facts()`).
   - `validation_score >= 0.70`: Status `completed`
   - `validation_score < 0.70` or unverified claims: Status `completed_with_warnings`

---

## 9. Traceability

Every generated claim maintains end-to-end audit traceability:

$$\text{Generated Claim} \longrightarrow \text{Fact ID} \longrightarrow \text{Source Chunk ID} \longrightarrow \text{Source Document} \longrightarrow \text{Source Page}$$

Users can click any claim in the **Claim Inspector** or **Output Studio** to inspect its exact source page evidence.

---

## 10. Security

- **Prompt Injection Defense**: Source documents are treated strictly as passive text DATA under system prompt boundaries. Injection payloads (`"Ignore previous instructions..."`) are rendered harmlessly as text data.
- **ClamAV Antivirus Scanning**: Real-time stream scanning on uploaded files.
- **Magic MIME Inspection**: Verifies binary headers to prevent file extension spoofing (`.exe` disguised as `.pdf`).
- **PII Detection**: Automatic scanning for email addresses and phone numbers.
- **Rate Limiting**: Dynamic SlowAPI rate limiting per IP and user account.

---

## 11. Provenance & Trust Chain

Every completed transformation calculates a cryptographic SHA-256 content fingerprint stored in `trust_records`:

- **Fingerprint**: `SHA256(Document ID + Output Content + Fact IDs)`
- **Trust Chain**: Verification record containing timestamp, issuer signature, and approval status.
- **Verification Page**: Public verification route (`/verify/[recordId]`) with QR code rendering.
- **Blockchain**: Optional anchor support (never required for normal operation).

---

## 12. Deployment Requirements

- **CPU**: 4+ Cores (8+ Cores recommended)
- **RAM**: 16 GB minimum (32 GB recommended for smooth LLM inference)
- **Disk Space**: 20 GB free (for Ollama model weights & PostgreSQL vector storage)
- **Software Dependencies**:
  - Python 3.12+
  - Node.js v20.x
  - PostgreSQL 15+ with `pgvector`
  - Redis 7.x
  - Ollama v0.1.30+

---

## 13. Environment Variables

Key configuration variables (`.env` / `.env.example`):

```ini
ENVIRONMENT=development
DEBUG=true
APP_NAME="ContentForge AI"
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contentforge_db
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
EMBEDDING_MODEL=bge-m3:latest
NEXT_PUBLIC_API_URL=http://localhost:8000
SECRET_KEY=change-this-to-a-super-secret-hex-key-minimum-32-chars-long
```

---

## 14. Local Development Setup

1. **Clone & Setup Environment**:
   ```bash
   git clone <repo-url>
   cd ContentX/contentforge-ai
   cp .env.example .env
   ```

2. **Start Local Dependencies**:
   - Ensure PostgreSQL (Port 5432) and Redis (Port 6379) are running.
   - Run database migrations: `alembic upgrade head`

3. **Start Ollama & Load Models**:
   ```bash
   ollama pull bge-m3:latest
   ollama pull qwen2.5:7b-instruct
   ```

4. **Start Backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

5. **Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 15. Production Setup

For containerized production deployment using Docker Compose:

```bash
docker-compose up -d --build
```

Services started:
- `frontend`: Next.js production server (Port 3000)
- `backend`: FastAPI API server (Port 8000)
- `postgres`: PostgreSQL 16 + pgvector (Port 5432)
- `redis`: Redis cache & broker (Port 6379)
- `ollama`: Model inference server (Port 11434)

---

## 16. Known Warnings

1. **Model Probe Route Retry**: `model_client.py` logs an internal warning (`404 Not Found on /api/generate`) during model probe initialization before falling back cleanly to Ollama `/api/chat`.
2. **Short Document Precision Metric**: Documents with <= 4 chunks (e.g. `Blackbelt_Capstone.pdf`) show Precision@4 = 50% because retrieving all 4 chunks includes 2 technical chunks and 2 administrative guideline chunks. Context selection automatically demotes noise facts.

---

## 17. Known Limitations

- **Maximum Upload Size**: Default configuration caps uploads at 20 MB per file.
- **Context Window**: Maximum context window capped at 15 facts for `presentation` and 12 facts for `executive_summary` to prevent LLM context degradation.

---

## 18. Demo Workflow

Follow this clean 14-step workflow for live demonstration:

1. Open browser to `http://localhost:3000`.
2. Log in with user credentials.
3. Click **New Transformation** on the Dashboard.
4. Upload `ContentForge_Cybersecurity_Test_Report.pdf`.
5. View real-time upload, MIME validation, and security scan status.
6. Observe automatic text extraction and domain detection (`cybersecurity`).
7. Review extracted facts in **Fact Information / Fact Registry**.
8. Navigate to **Select Outputs** and check `LinkedIn`, `Executive Summary`, and `Presentation`.
9. Select Target Audience (e.g. `Executive` or `Technical`).
10. Click **Generate Content**.
11. View generated multi-format output cards in **Output Studio**.
12. Click any claim in the text to open **Claim Inspector** showing exact source page evidence.
13. View **Validation Center** metrics showing 100% grounding and accuracy.
14. Open **Provenance & Verification** to inspect SHA-256 fingerprint and QR code.

---

## 19. Troubleshooting

- **Ollama Unreachable**: Verify `ollama list` in terminal. Ensure service is active on `http://localhost:11434`.
- **pgvector Extension Missing**: Run `CREATE EXTENSION IF NOT EXISTS vector;` in PostgreSQL.
- **Database Connection Error**: Verify `DATABASE_URL` credentials in `.env`.
