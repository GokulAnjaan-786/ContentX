# ContentX — Architecture & Technical Overview

**Tagline**: *One Source. Every Format. Verified at Every Step.*

---

## PAGE 1 — ARCHITECTURE & WORKFLOW

### 1. Executive Problem Statement
Enterprise organizations process unstructured intelligence (PDF reports, advisories, research papers, financial statements) that must be transformed into multiple channels (Executive Briefings, Technical Advisories, LinkedIn Articles, Twitter Threads, Slide Decks). Traditional manual writing or unconstrained LLM prompts cause **factual drift**: numbers, dates, CVEs, and certainty levels are altered or hallucinated, destroying source traceability.

### 2. The ContentX Solution
ContentX introduces a **Single Source of Truth transformation pipeline**. Unstructured documents are parsed into an immutable **Fact Registry**, passed through **Importance-Aware Context Selection** and **Truth Compression**, and deterministically rendered into multiple formats with sentence-level claim traceability and cryptographic SHA-256 provenance.

### 3. End-to-End System Architecture

```
                       ┌─────────────────────────┐
                       │  SOURCE DOCUMENT (PDF)  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │   PyMuPDF Extraction    │
                       │  + Security Injection   │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ Smart Chunking (~450w)  │
                       │ + BGE-M3 (1024-dim)     │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │   PostgreSQL pgvector   │
                       │   Native <=> Cosine HNSW│
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │      FACT REGISTRY      │
                       │ Single Source of Truth  │
                       └────────────┬────────────┘
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
               BGE-M3 RAG Retrieval    Importance-Aware Context
                        │                       │
                        └───────────┬───────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │    TRUTH COMPRESSION    │
                       │   Audience Adaptor      │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ DETERMINISTIC GENERATOR │
                       │    (Ollama / Qwen2.5)   │
                       └────────────┬────────────┘
                                    │
       ┌───────────┬───────────┼───────────┬───────────┐
       ▼           ▼           ▼           ▼           ▼
   LinkedIn     Twitter     Advisory     Exec summary Presentation
       │           │           │           │           │
       └───────────┴───────────┼───────────┴───────────┘
                               ▼
                       ┌─────────────────────────┐
                       │   VALIDATION & CHECKS   │
                       │ Fact/Number/Entity/Cross│
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ TRACEABILITY & TRUST    │
                       │ Sentence Citation [f1]  │
                       │ + SHA-256 Fingerprint   │
                       └─────────────────────────┘
```

---

## PAGE 2 — SYSTEM SPECIFICATIONS & TECHNOLOGY STACK

### 4. Technology Stack & Component Classification

| Layer | Technology | Purpose & Implementation Status |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS | `VERIFIED`: 21/21 static & dynamic routes active. |
| **Backend API** | Python 3.12, FastAPI, SQLAlchemy 2.0 | `VERIFIED`: 89/89 Pytest suite passing (100%). |
| **Relational DB** | PostgreSQL 15 | `VERIFIED`: Storage for documents, jobs, facts, audit logs. |
| **Vector DB** | PostgreSQL `pgvector` v0.8.6 | `VERIFIED`: `vector(1024)` column with native `<=>` HNSW index. |
| **Embeddings** | Ollama + `bge-m3:latest` (1024-dim) | `VERIFIED`: Multilingual 1024-dim dense vector generation. |
| **Generator LLM** | Ollama + `qwen2.5:7b-instruct` | `VERIFIED`: Local structured JSON generation + fallback. |
| **Traceability** | `ClaimHighlighter.tsx` | `VERIFIED`: Sentence-level mapping to Fact ID & source page. |
| **Provenance** | `verification_service.py` | `VERIFIED`: SHA-256 content hash & `/verify/[recordId]` portal. |
| **Async Queue** | Celery + Redis / Async Inline | `PARTIALLY IMPLEMENTED`: Async inline active; Celery configured. |
| **Object Storage** | MinIO / Local Disk Storage | `PARTIALLY IMPLEMENTED`: Local disk active; MinIO integrated. |
| **Web3 Anchor** | Cryptographic Ledger Verification | `PLANNED`: SHA-256 hash verified; live Web3 transaction planned. |

### 5. Key Innovations

#### 5.1 Fact Registry (Single Source of Truth)
Decouples document understanding from output generation. Extracted facts are stored with assigned importance ranks (`high`, `medium`, `low`, `metadata`). All output formats are generated strictly from the same factual base.

#### 5.2 Truth Compression
Modifies **message complexity** without altering **underlying factual truth**:
- **Technical Profile**: Retains exact technical terminology, CVEs, version numbers, and code.
- **Executive Profile**: Focuses on strategic risk, operational impact, and recommendations.
- **General Public Profile**: Simplifies prose while preserving 100% of numbers, dates, and entities.

#### 5.3 Importance-Aware Context Selection
Prevents legal/copyright preambles from displacing core findings. Facts are ranked by `(importance_rank, output_relevance, domain_rank)` and capped dynamically per output type (LinkedIn: 8, Presentation: 15).

#### 5.4 Claim Traceability & Cryptographic Provenance
Every sentence is tagged with source citations (`[f1]`, `[f2]`). Clicking a claim highlights its exact Fact ID, source chunk, page number, and original PDF text. Content is fingerprinted via SHA-256 and accessible via a public verification portal (`/verify/[recordId]`).

### 6. Primary Enterprise Use Cases
- **Cybersecurity / Incident Response**: Convert a 50-page threat report into a SOC Advisory, Executive Briefing, LinkedIn Alert, and Slide Deck in 3 seconds.
- **Financial & Corporate Auditing**: Transform quarterly filings into executive summaries and investor posts without numeric distortion.
- **Academic & Policy Research**: Distill whitepapers into multi-audience summaries while maintaining strict citation grounding.
