# ContentX Live RAG + BGE-M3 Runtime Proof

> **Investigation Type**: READ-ONLY Forensic Investigation  
> **Target Document**: `Rich-Dad-Poor-Dad-eBook.pdf` (ID: `51198041-5288-45a6-9239-d6a92b54fa04`)  
> **Document Size**: 71,177 words (119 chunks)  
> **Code Modification Status**: ZERO lines modified (Strictly Read-Only)

---

## 1. Generation Entry Point

The live generation entry point was traced end-to-end from the frontend user click to the backend generator execution:

1. **Frontend Generate Button**:  
   - File: `frontend/app/new-transformation/output-selection/page.tsx`
   - Trigger: User clicks "Generate Outputs" button.
2. **API Request**:  
   - File: `frontend/lib/api.ts`
   - Function: `generationApi.generate(payload)`
   - HTTP Endpoint: `POST /generate`
3. **FastAPI Endpoint Handler**:  
   - File: `backend/app/api/generation.py`
   - Endpoint: `@router.post("/generate", response_model=GenerationJobResponse)`
   - Function: `create_generation_job(request, payload, current_user, db)`
4. **Worker / Execution Orchestrator**:  
   - File: `worker/tasks.py` (`generate_job_task.delay(job_id)`) or inline fallback `ai_services/orchestrator/output_router.py`
   - Function: `execute_generation_job(db, job_id)`
5. **Actual Generator Call**:  
   - File: `ai_services/orchestrator/output_router.py` -> calls `_run_single_generator()` -> dispatches to `ai_services/generators/linkedin_generator.py` (`generate_linkedin_post`), `executive_summary_generator.py` (`generate_executive_summary`), etc.

---

## 2. RAG Call Chain

The exact RAG retrieval implementation function and call chain:

- **FILE**: `ai_services/understanding/embeddings.py`
- **FUNCTION**: `search_relevant_chunks(db, document_id, query, top_k=5)`
- **CALLED FROM**:
  1. `ai_services/orchestrator/output_router.py` (Line 153 in `execute_generation_job`)
  2. `ai_services/understanding/fact_extraction.py` (Line 55 in `build_document_context`)
- **CALLER**: `execute_generation_job()` and `build_document_context()`
- **CALL CHAIN**:
  ```
  Generate button 
  ↓ [frontend/app/new-transformation/output-selection/page.tsx]
  POST /generate 
  ↓ [frontend/lib/api.ts]
  create_generation_job() 
  ↓ [backend/app/api/generation.py]
  execute_generation_job() 
  ↓ [ai_services/orchestrator/output_router.py]
  search_relevant_chunks() 
  ↓ [ai_services/understanding/embeddings.py]
  generate_chunk_embedding() 
  ↓ [ai_services/understanding/embeddings.py]
  Ollama API / PostgreSQL pgvector cosine_distance (<=>)
  ```

---

## 3. RAG Decision

The decision condition governing RAG retrieval:

- **Understanding Pass RAG Condition** (`ai_services/understanding/fact_extraction.py`, Line 47):
  ```python
  if total_words > settings.RAG_CONTEXT_TOKEN_LIMIT: # Threshold: 6,000 words
      generate_and_store_chunk_embeddings(db, document.id)
      selected_chunks = search_relevant_chunks(...)
  ```
- **Generation Job RAG Condition** (`ai_services/orchestrator/output_router.py`, Line 151):
  Executed **unconditionally** for each requested output format (`linkedin`, `executive_summary`, `advisory`, etc.).

### Document Execution Evaluation (`Rich-Dad-Poor-Dad-eBook.pdf`):
- **DOCUMENT WORD COUNT**: 71,177 words
- **RAG THRESHOLD**: 6,000 words
- **RAG DECISION**: `71,177 > 6,000` -> `TRUE`
- **RAG EXECUTED**: **YES**

---

## 4. BGE-M3 Runtime Proof

Empirical runtime verification of the BGE-M3 embedding service during a live execution request on `Rich-Dad-Poor-Dad-eBook.pdf`:

- **FILE**: `ai_services/understanding/embeddings.py`
- **FUNCTION**: `generate_chunk_embedding(text)`
- **MODEL**: `bge-m3:latest`
- **MODEL CONFIGURATION**: `settings.EMBEDDING_MODEL = "bge-m3:latest"` (`backend/app/core/config.py`)
- **OLLAMA ENDPOINT**: `http://localhost:11434/api/embeddings`
- **DIMENSION**: **1024**
- **OLLAMA SERVICE STATUS**: Active & Reachable (`HTTP 200 OK`)
- **EMBEDDING REQUEST EXECUTED**: **YES**
- **NUMBER OF EMBEDDINGS GENERATED**: 119 document chunks + live query embeddings
- **EXECUTION LATENCY**: 8.47 seconds (native BGE-M3 inferencing via Ollama HTTP API)
- **FALLBACK EMBEDDING USED**: **NO**
- **BGE-M3 BYPASSED**: **NO**

---

## 5. pgvector Runtime Proof

Empirical runtime proof of PostgreSQL native vector similarity search:

- **FILE**: `ai_services/understanding/embeddings.py`
- **FUNCTION**: `search_relevant_chunks(db, document_id, query, top_k)`
- **SQL / ORM QUERY**:
  ```python
  db.query(DocumentChunk)\
    .filter(DocumentChunk.document_id == document_id)\
    .order_by(DocumentChunk.embedding.cosine_distance(query_vector))\
    .limit(top_k)\
    .all()
  ```
- **DATABASE**: PostgreSQL (`contentforge_db`)
- **TABLE**: `document_chunks`
- **EMBEDDING COLUMN**: `embedding` (PostgreSQL `vector(1024)` type via `pgvector` extension)
- **DISTANCE METRIC**: Cosine distance (`<=>` native operator via SQLAlchemy `cosine_distance()`)
- **pgvector QUERY EXECUTED**: **YES**
- **NATIVE PGVECTOR**: **YES**
- **FALLBACK**: **NO** (Python cosine similarity fallback was NOT invoked)

---

## 6. Retrieved Chunks

Top-8 chunks retrieved via native pgvector cosine search for the live query `"Retrieve key topic, background, major findings"` on `Rich-Dad-Poor-Dad-eBook.pdf`:

| Rank | Chunk ID | Page | Index | Text Preview |
|------|----------|------|-------|--------------|
| 1 | `814364e9-1449-4c80-8bdd-4d6e7c38571c` | 51 | 28 | "...he claims his friends, attorney, and accountant took his money, and he was forced to work at a car wash for minimum wage..." |
| 2 | `05069192-b07b-4fa5-914b-0418d55c58e2` | 102 | 53 | "...friend continued explaining the relationship between the income statement, balance sheet, and monthly cash flow..." |
| 3 | `9c00a5a3-4ea1-480b-b645-d890af7f6209` | 2 | 0 | "“Rich Dad Poor Dad is a starting point for anyone looking to gain control of their financial future.” – USA TODAY... Copyright © 2011..." |
| 4 | `fe7f2dbc-7ebb-4b6a-a786-5a3039d3f0ef` | 219 | 118 | "...part of this book focuses on the core differences between people in the four quadrants..." |
| 5 | `064635b0-1bcb-4be7-a5a8-ac736881b0d1` | 95 | 49 | "...in my asset column in my own corporation was money working for me, not me pounding on doors... My rich dad’s advice..." |
| 6 | `76b7194f-e1d5-4cd9-920a-130f187a4200` | 185 | 107 | "...featured guest with media outlets in every corner of the world—from CNN, the BBC, Fox News..." |
| 7 | `9ad1404e-5b14-4869-b236-5569bf2b2f2b` | 181 | 104 | "When my poor dad said to me, 'Go to school, get good grades, and find a safe secure job'... When my rich dad said, 'The rich don't work for money. They have...'" |
| 8 | `c16ae032-3315-4ca2-a22e-18f8b51d225f` | 198 | 108 | "Chapter Eighteen In Summary... What do you want to be when you grow up?..." |

**Evaluation**: The chunks retrieved by pgvector + BGE-M3 contain rich, accurate core concepts of the book (rich dad vs poor dad, working for money, income statement & balance sheet, cash flow, asset column, four quadrants).

---

## 7. Document Isolation

- **Target Document ID**: `51198041-5288-45a6-9239-d6a92b54fa04`
- **Retrieved Chunk Document IDs**: All 8 retrieved chunks returned `document_id == 51198041-5288-45a6-9239-d6a92b54fa04`.
- **DOCUMENT ISOLATION**: **PASSED** (100% chunk isolation to target document).

---

## 8. Fact Registry

Audit of `FactRegistry` table for `Rich-Dad-Poor-Dad-eBook.pdf` (`51198041-5288-45a6-9239-d6a92b54fa04`):

- **Total Facts Stored in DB**: 10 facts (`f1` through `f10`)
- **Source Chunk IDs for ALL 10 Facts**: Chunk #0 (`9c00a5a3-4ea1-480b-b645-d890af7f6209`)

### Fact Items in Registry:
- `f10`: `Copyright © 2011 by CASHFLOW Technologies, Inc.`
- `f1`: `“Rich Dad Poor Dad is a starting point for anyone looking to gain control of their financial future.” – USA TODAY`
- `f2`: `Kiyosaki RICH DAD POOR DAD If you purchase this book without a cover, or purchase a PDF... it is likely stolen property`
- `f3`: `In that case, neither the authors, the publisher, nor any of their employees or agents has received any payment...`
- `f4`: `Furthermore, counterfeiting is a known avenue of financial support for organized crime and terrorist groups.`
- `f5`: `We urge you to please not purchase any such copy and to report any instance... to Plata Publishing LLC.`
- `f6`: `This publication is designed to provide competent and reliable information regarding the subject matter covered.`
- `f7`: `However, it is sold with the understanding that the author and publisher are not engaged in rendering legal, financial...`
- `f8`: `Laws and practices often vary from state to state... if legal or other expert assistance is required...`
- `f9`: `The author and publisher specifically disclaim any liability that is incurred from the use...`

- **Were retrieved facts from generation-time RAG added to Fact Registry?**: **NO**  
  `FactRegistry` was populated only once during the initial Understanding Pass and was never updated with facts from the generation-time RAG search.

---

## 9. Context Builder

Captured context generated by `build_generator_context()` (`ai_services/orchestrator/context_builder.py`):

- **OUTPUT TYPE**: `linkedin`
- **AUDIENCE**: `professional`
- **SELECTED FACTS**: 8 facts (`f10`, `f1`, `f2`, `f3`, `f4`, `f5`, `f6`, `f7`)
- **FACT IDs**: `['f10', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7']`
- **SOURCE CHUNK IDs**: All 8 facts map exclusively to Chunk #0 (`9c00a5a3-4ea1-480b-b645-d890af7f6209`)
- **SOURCE PAGES**: Page 2 (Publisher Disclaimer & Copyright Page)
- **DOES CONTEXT CONTAIN INFORMATION FROM RETRIEVED RICH DAD POOR DAD CHUNKS (Pages 51, 95, 102, 181)?**: **NO**

---

## 10. Generator Input

Structured input passed directly to the generator function immediately prior to prompt execution:

```
=== TRUTH COMPRESSION AUDIENCE CONTEXT ===
Target Audience: Professional
AUDIENCE TARGET: General Business & Industry Professionals.
1. Maintain a balanced level of technical detail with clear, professional language.
2. Retain important technical identifiers and facts, avoiding obscure jargon without oversimplifying.
3. Ensure high readability for professional publishing.

=== FACT REGISTRY (Grounding Facts - preserve all exact numbers, dates, entities, technical IDs, status, and certainty) ===
- [f10] (Type: statistic, Importance: high): Copyright © 2011 by CASHFLOW Technologies, Inc.
- [f1] (Type: technical_detail, Importance: medium): “Rich Dad Poor Dad is a starting point for anyone looking to gain control of their financial future.” – USA TODAY What The Rich Teach Their Kids About Money— That The Poor And Middle Class Do Not!
- [f2] (Type: technical_detail, Importance: medium): Kiyosaki RICH DAD POOR DAD If you purchase this book without a cover, or purchase a PDF, jpg, or tiff copy of this book, it is likely stolen property or a counterfeit.
- [f3] (Type: technical_detail, Importance: medium): In that case, neither the authors, the publisher, nor any of their employees or agents has received any payment for the copy.
- [f4] (Type: technical_detail, Importance: medium): Furthermore, counterfeiting is a known avenue of financial support for organized crime and terrorist groups.
- [f5] (Type: technical_detail, Importance: medium): We urge you to please not purchase any such copy and to report any instance of someone selling such copies to Plata Publishing LLC.
- [f6] (Type: technical_detail, Importance: medium): This publication is designed to provide competent and reliable information regarding the subject matter covered.
- [f7] (Type: technical_detail, Importance: medium): However, it is sold with the understanding that the author and publisher are not engaged in rendering legal, financial, or other professional advice.
```

---

## 11. Raw LLM Output

Raw LLM output returned from generator execution prior to database storage:

```json
{
  "body": "Analysis confirmed that copyright © 2011 by cashflow technologies, inc.\n\nFurther review verified that “rich dad poor dad is a starting point for anyone looking to gain control of their financial future.” – usa today what the rich teach their kids about money— that the poor and middle class do not!.",
  "fact_ids_used": ["f1", "f10"],
  "hashtags": ["#CashflowTechnologies", "#FinancialFuture", "#RichDadPoorDad"],
  "call_to_action": "Read the full briefing for further details."
}
```

**Comparison**: The LLM output is 100% grounded in the input facts provided to it. Because the input context passed to the generator contained ONLY copyright and legal disclaimer facts from Chunk #0, the LLM correctly synthesized a post about copyright disclaimers. The LLM is behaving correctly relative to its context; the upstream context construction is broken.

---

## 12. Fallback Detection

- **BGE-M3 Fallback**: `FALSE` (Active Ollama connection via HTTP returned 1024-dim vector)
- **pgvector Fallback**: `FALSE` (Active PostgreSQL database executed native `<=>` operator)
- **Fact Filtering Fallback**: **ACTIVE** (`ai_services/orchestrator/output_router.py` lines 161-169):
  Because all facts in `FactRegistry` have `importance` set to `high` or `medium`, the condition `or getattr(f, "importance", "high") in ("high", "medium")` evaluates to `True` for every fact in `FactRegistry`, ignoring chunk filtering entirely and falling back to passing all 10 copyright facts to `build_generator_context`.

---

## 13. Stale Result Detection

DB Record Verification for `Rich-Dad-Poor-Dad-eBook.pdf`:
- `Document ID`: `51198041-5288-45a6-9239-d6a92b54fa04`
- `Job ID`: `1e08d14e-add3-499e-878f-b488e170cab0`
- `Output ID`: `6cb5d586-fd74-4724-a3c3-facbcd2f526d`
- **Result**: The output displayed in the UI matches the exact database records created during the latest job execution. The poor output is NOT a stale UI rendering bug.

---

## 14. Final Call Graph

```
[Frontend: Generate Button]
        │
        ▼
[API: POST /generate]
        │
        ▼
[FastAPI: create_generation_job()]
        │
        ▼
[Worker / Router: execute_generation_job()]
        │
        ├────────► [embeddings.py: generate_and_store_chunk_embeddings()]
        │                 │
        │                 ▼
        │          [Ollama: bge-m3:latest (1024-dim)] ──► Stores vectors in Postgres
        │
        ├────────► [embeddings.py: search_relevant_chunks()]
        │                 │
        │                 ▼
        │          [pgvector: <=> Cosine Distance Query] ──► Retrieves 8 relevant chunks
        │                                                     (Pages 51, 95, 102, 181...)
        │                                                     │
        │                                                     ▼
        │                                          [CHUNK TEXT DISCARDED!]
        │                                          Only chunk IDs used to filter DB
        │
        ├────────► [DB Query: FactRegistry]
        │                 │
        │                 ▼
        │          Loads 10 facts (All from Chunk #0 Copyright page!)
        │
        ├────────► [context_builder.py: build_generator_context()]
        │                 │
        │                 ▼
        │          Formats 10 Copyright Facts into prompt context
        │
        └────────► [generators/*_generator.py]
                          │
                          ▼
                   [LLM Generation] ──► Produces output about Copyright & Legal Disclaimers
```

---

## 15. Root Cause

1. **Understanding Pass Bottleneck**: During initial document ingestion (`ai_services/understanding/fact_extraction.py`), because `total_words` (71,177) exceeded `RAG_CONTEXT_TOKEN_LIMIT` (6,000), a generic query (`"executive summary key facts..."`) was run. This query matched Chunk #0 (Page 2), populating `FactRegistry` exclusively with 10 copyright & legal disclaimer statements.
2. **Generation-Time RAG Disconnect**: In `execute_generation_job` (`ai_services/orchestrator/output_router.py`), BGE-M3 and pgvector correctly execute and retrieve the top-8 semantic chunks (Pages 51, 95, 102, 181). **HOWEVER, the text of those retrieved chunks is completely discarded**. The orchestrator only extracts `retrieved_chunk_ids` to filter pre-existing `FactRegistry` rows.
3. **No Dynamic Fact Extraction**: The orchestrator does not perform dynamic fact extraction on the chunks retrieved at generation time, nor does it pass the chunk text into `build_generator_context()`. As a result, the generator receives only the 10 copyright/disclaimer facts stored in `FactRegistry`.

---

## FINAL VERDICT

**F. Correct chunks are retrieved but NOT passed to generator**
