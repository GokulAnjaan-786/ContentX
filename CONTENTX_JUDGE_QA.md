# ContentX — Technical Judge Questions & Answers

This document provides 20 authoritative technical questions and answers based on the actual ContentX implementation.

---

### Q1: Why did you choose BGE-M3 as your embedding model?
**Answer**: BAAI's BGE-M3 (`bge-m3:latest`) is a state-of-the-art multilingual embedding model that natively outputs **1024-dimensional dense vectors**. Unlike standard 384-dim or 768-dim models, BGE-M3 exhibits superior semantic retrieval precision across technical, cybersecurity, and financial text. It runs locally via Ollama with zero external API latency or cost.

### Q2: Why use PostgreSQL `pgvector` instead of a dedicated vector database like Pinecone or Milvus?
**Answer**: `pgvector` (v0.8.6) allows us to store 1024-dimensional vectors directly inside our primary relational PostgreSQL database. This eliminates dual-database synchronization complexity, maintains ACID transaction guarantees across documents and embeddings, and executes native `<=>` cosine distance HNSW vector searches in **< 45 milliseconds**.

### Q3: Why PostgreSQL for the core database?
**Answer**: PostgreSQL 15 provides robust relational data modeling, JSONB support for dynamic schemas, strong ACID compliance, and native extension capabilities (`pgvector`). It reliably stores user accounts, documents, audit logs, Fact Registry items, and generated outputs in a single, scalable instance.

### Q4: Why implement RAG instead of passing the entire document directly into the LLM context window?
**Answer**: Enterprise PDFs often exceed 50 to 200 pages (~50,000+ words). Passing whole documents into an LLM context window causes severe attention degradation ("lost in the middle" phenomenon), increases inference latency, dramatically inflates memory consumption, and increases hallucination rates. RAG selectively retrieves only the most relevant, high-importance chunks.

### Q5: How does ContentX prevent LLM hallucinations?
**Answer**: ContentX uses a multi-layered defense:
1. **Fact Registry**: Decouples document facts from LLM generation.
2. **Strict System Instructions**: Generators are constrained to construct claims strictly from provided Fact Registry items.
3. **Low Temperature ($T = 0.1$)**: Minimizes stochastic sampling variation.
4. **Validation Engine**: `fact_checker.py` performs post-generation claim verification, checking every sentence against the Fact Registry.

### Q6: How do you ensure cross-output consistency between different formats (e.g. LinkedIn vs Executive Summary)?
**Answer**: All output generators read from the exact same **Fact Registry** for a given document. Whether generating a 6-tweet thread or a 12-bullet executive briefing, both formats draw from the exact same verified statements, numbers, and entity records.

### Q7: What is the Fact Registry and why is it essential?
**Answer**: The Fact Registry is ContentX's **Single Source of Truth**. Upon document ingestion, key factual statements are extracted, assigned confidence scores, classified by importance (`high`, `medium`, `low`, `metadata`), and stored in an immutable table linked to original PDF chunk IDs and page numbers.

### Q8: What is Truth Compression?
**Answer**: Truth Compression is ContentX's core innovation: *"Change the complexity of the message, not the truth behind it."* It adapts vocabulary and explanation style for different target audiences (`technical`, `executive`, `professional`, `general_public`) while keeping underlying numbers, dates, CVEs, certainty levels, and facts 100% identical.

### Q9: How does ContentX handle different target audiences?
**Answer**: The user selects an audience profile. The prompt and context builder apply audience-specific phrasing constraints (e.g., technical depth for engineers vs. strategic risk for executives) without altering the source facts supplied by the Fact Registry.

### Q10: How does ContentX protect against Prompt Injection attacks embedded inside uploaded PDFs?
**Answer**: Uploaded document text is treated strictly as **passive data** inside delimited XML context tags (`<source_document_context>`). System instructions explicitly instruct the LLM to ignore any embedded commands (such as *"Ignore previous instructions"*). Furthermore, `security_scanner.py` pre-scans text for injection patterns.

### Q11: How does sentence-level claim traceability work?
**Answer**: Generated outputs include citation markers (`[f1]`, `[f2]`). In the Output Studio, `ClaimHighlighter.tsx` renders clickable sentence spans. Clicking a claim opens `TraceabilityPanel.tsx`, which displays the matching Fact ID, source chunk ID, PDF page number, confidence score, and original text snippet.

### Q12: How does ContentX handle very long documents (> 200 pages)?
**Answer**: For documents exceeding context limits, `build_document_context()` automatically triggers a selective RAG pass. It embeds chunks, performs diversity-aware vector retrieval across early, middle, and late sections of the PDF, and constructs a representative Fact Registry across the entire document length.

### Q13: What happens if a requested fact or metric is missing from the source document?
**Answer**: ContentX enforces strict non-hallucination rules. If a metric (such as attacker identity or financial breakdown) is absent from the source PDF, the generator outputs: *"Not specified in source document,"* rather than inventing plausible data.

### Q14: Why choose Ollama over cloud LLM providers?
**Answer**: Ollama enables complete self-hosted, offline AI inference. Enterprise users (defense, cybersecurity, finance) cannot send confidential internal PDFs to third-party APIs. Ollama provides complete data privacy, zero recurring API token costs, and predictable local performance.

### Q15: Why not use OpenRouter or paid external LLM APIs?
**Answer**: OpenRouter introduces external API costs, network latency, data privacy risks, and potential service downtime. ContentX was engineered to be a standalone, self-contained enterprise application operating entirely within the customer's private infrastructure.

### Q16: How does ContentX support the Cybersecurity domain?
**Answer**: ContentX includes a specialized `cybersecurity` domain pack that recognizes CVE identifiers, CVSS scores, malware families, threat actor handles, and attack vectors. It formats technical advisories with severity rankings and mitigation steps.

### Q17: How does ContentX support the Blockchain / Web3 domain?
**Answer**: The `blockchain` domain pack detects smart contract addresses, transaction hashes, protocol names, and gas metrics, tailoring LinkedIn posts and summaries with relevant Web3 hashtags (`#SmartContracts`, `#Web3`, `#DeFi`).

### Q18: What is ContentX's biggest current limitation?
**Answer**: Scanned, image-only PDFs currently require native text extraction or OCR pre-processing. Additionally, complex graphical formats (Infographic, Video Package) produce structured layout/script specifications; final visual rendering requires downstream graphics/video engines.

### Q19: What is the future technical scope for ContentX?
**Answer**: Future roadmap items include:
1. Native Tesseract OCR for scanned PDF ingestion.
2. OpenAI Whisper integration for raw audio/video transcript processing.
3. Live Web3 Smart Contract anchoring on Ethereum/Polygon for immutable trust registry verification.
4. Automated multimodal image generation for infographic slide rendering.

### Q20: How do you verify content provenance?
**Answer**: Upon output generation, `verification_service.py` computes a SHA-256 fingerprint of the source document and output payload. This record is stored with an issuer signature and timestamp, generating a unique Verification ID and QR code accessible via our public `/verify/[recordId]` portal.
