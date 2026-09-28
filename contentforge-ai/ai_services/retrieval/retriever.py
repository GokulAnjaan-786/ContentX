import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from ai_services.understanding.embeddings import (
    generate_and_store_chunk_embeddings,
    search_relevant_chunks,
)
from ai_services.retrieval.query_intent import detect_query_intent, QueryIntent
from ai_services.retrieval.content_filter import filter_candidate_chunks
from ai_services.retrieval.reranker import rerank_candidate_chunks

logger = logging.getLogger(__name__)

TOP_K_CANDIDATE_RETRIEVAL = 20
TOP_N_FINAL_SELECTION = 8


def retrieve_relevant_content_chunks(
    db: Session,
    document_id: uuid.UUID,
    query: str,
    target_format: str = "general",
    top_k_candidates: int = TOP_K_CANDIDATE_RETRIEVAL,
    top_n_final: int = TOP_N_FINAL_SELECTION,
) -> Dict[str, Any]:
    """
    Execute high-precision multi-stage content retrieval:
    1. Query Intent Classification
    2. Candidate Retrieval via BGE-M3 + pgvector (top_k_candidates=20)
    3. Content-Type & Metadata Filtering (Separates metadata from useful content)
    4. Composite Semantic Reranking
    5. Returns dict with top_n_final relevant chunks, intent, and debug info.
    """
    # Step 1: Detect Query Intent
    query_intent = detect_query_intent(query, target_format=target_format)

    # Step 2: Ensure embeddings exist and query candidate chunks via BGE-M3 + pgvector
    try:
        generate_and_store_chunk_embeddings(db, document_id)
        candidate_chunks = search_relevant_chunks(
            db=db,
            document_id=document_id,
            query=query,
            top_k=top_k_candidates,
        )
    except Exception as e:
        logger.error(f"Error executing vector candidate retrieval for doc {document_id}: {e}")
        candidate_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).limit(top_k_candidates).all()

    # Step 3: Filter Metadata & Noise Chunks based on Query Intent
    filtered_tuples = filter_candidate_chunks(
        chunks=candidate_chunks,
        query_intent=query_intent,
        max_candidates=top_k_candidates,
    )

    # Step 4: Rerank Filtered Candidate Chunks
    reranked_tuples = rerank_candidate_chunks(
        query=query,
        candidate_tuples=filtered_tuples,
        query_intent=query_intent,
        top_n=top_n_final,
    )

    selected_chunks = [t[0] for t in reranked_tuples]

    # Debug / Observability payload
    debug_info = {
        "query": query,
        "target_format": target_format,
        "detected_intent": query_intent.to_dict(),
        "candidates_retrieved_count": len(candidate_chunks),
        "candidates_filtered_count": len(filtered_tuples),
        "final_selected_count": len(selected_chunks),
        "selected_chunks_detail": [
            {
                "chunk_id": str(c.id),
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "score": score,
                "content_type": ct,
                "snippet": (c.text[:150] + "...") if hasattr(c, "text") else str(c)[:150],
            }
            for c, score, ct in reranked_tuples
        ],
    }

    if os.getenv("RAG_DEBUG", "true").lower() in ("true", "1"):
        logger.info(
            f"RETRIEVAL COMPLETE | Query Intent: {query_intent.intent_type.value} | "
            f"Candidates: {len(candidate_chunks)} -> Filtered: {len(filtered_tuples)} -> Selected: {len(selected_chunks)}"
        )

    return {
        "intent": query_intent,
        "selected_chunks": selected_chunks,
        "reranked_detail": reranked_tuples,
        "debug_info": debug_info,
    }
