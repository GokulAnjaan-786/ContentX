import hashlib
import json
import logging
import math
import uuid
from typing import List, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536


def generate_fallback_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generate a normalized deterministic 1536-dimensional embedding vector
    for local development, testing, and offline resilience.
    """
    vec = [0.0] * dim
    words = text.lower().split()
    for w in words:
        h = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0

    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]


_OLLAMA_REACHABLE: Optional[bool] = None


def is_ollama_available() -> bool:
    global _OLLAMA_REACHABLE
    if _OLLAMA_REACHABLE is False:
        return False
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/"
        with httpx.Client(timeout=httpx.Timeout(2.0, connect=1.0)) as client:
            resp = client.get(url)
            _OLLAMA_REACHABLE = (resp.status_code == 200)
            return _OLLAMA_REACHABLE
    except Exception:
        _OLLAMA_REACHABLE = False
        return False


def generate_chunk_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Ollama BGE-M3 model,
    falling back to deterministic semantic vectors if Ollama is unreachable.
    """
    if settings.ENVIRONMENT == "testing" or not is_ollama_available():
        return generate_fallback_embedding(text)

    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
        payload = {
            "model": settings.EMBEDDING_MODEL,
            "prompt": text,
        }
        with httpx.Client(timeout=httpx.Timeout(10.0, connect=1.5)) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                raw_emb = resp.json().get("embedding", [])
                if raw_emb:
                    # Pad or truncate to 1536 dimensions
                    if len(raw_emb) < EMBEDDING_DIM:
                        raw_emb = raw_emb + [0.0] * (EMBEDDING_DIM - len(raw_emb))
                    elif len(raw_emb) > EMBEDDING_DIM:
                        raw_emb = raw_emb[:EMBEDDING_DIM]
                    return raw_emb
    except Exception as e:
        logger.debug(f"Ollama embedding call failed ({e}), using fallback embedding.")

    return generate_fallback_embedding(text)


def generate_and_store_chunk_embeddings(db: Session, document_id: uuid.UUID) -> int:
    """
    Compute and persist vector embeddings for all chunks belonging to a document.
    """
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    count = 0
    for chunk in chunks:
        if chunk.embedding is None:
            vec = generate_chunk_embedding(chunk.text)
            chunk.embedding = vec
            count += 1

    db.commit()
    logger.info(f"Stored embeddings for {count} chunks in document {document_id}")
    return count


def search_relevant_chunks(
    db: Session,
    document_id: uuid.UUID,
    query: str,
    top_k: int = 5,
) -> List[DocumentChunk]:
    """
    Retrieve top-K most relevant chunks using vector similarity.
    Compatible with PostgreSQL pgvector and SQLite fallback.
    """
    query_vector = generate_chunk_embedding(query)
    dialect_name = db.bind.dialect.name if db.bind else "sqlite"

    if dialect_name == "postgresql":
        try:
            # Native pgvector cosine distance query
            results = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
                .limit(top_k)
                .all()
            )
            return results
        except Exception as pg_vec_err:
            logger.warning(f"PostgreSQL pgvector query error ({pg_vec_err}), falling back to Python cosine similarity.")
            try:
                db.rollback()
            except Exception:
                pass

    # Python cosine similarity fallback for SQLite/test environments
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    scored = []
    for c in chunks:
        vec = c.embedding
        if isinstance(vec, str):
            try:
                vec = json.loads(vec)
            except Exception:
                vec = generate_fallback_embedding(c.text)
        elif not vec:
            vec = generate_fallback_embedding(c.text)

        # Dot product of normalized vectors
        dot = sum(a * b for a, b in zip(query_vector, vec))
        scored.append((dot, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_k]]
