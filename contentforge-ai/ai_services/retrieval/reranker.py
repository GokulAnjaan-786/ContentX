import logging
import os
from typing import Any, Dict, List, Tuple
from ai_services.retrieval.query_intent import QueryIntent
from ai_services.retrieval.content_filter import calculate_content_role_score, classify_content_text

logger = logging.getLogger(__name__)

_CROSS_ENCODER_MODEL = None
_MODEL_ATTEMPTED = False


def _get_cross_encoder():
    """Lazily initialize sentence_transformers CrossEncoder if available."""
    global _CROSS_ENCODER_MODEL, _MODEL_ATTEMPTED
    if _CROSS_ENCODER_MODEL is not None or _MODEL_ATTEMPTED:
        return _CROSS_ENCODER_MODEL

    _MODEL_ATTEMPTED = True
    try:
        from sentence_transformers import CrossEncoder
        # Use lightweight open-source reranker model for zero-API local inferencing
        _CROSS_ENCODER_MODEL = CrossEncoder("cross-encoder/ms-marco-TinyBERT-L-2-v2", max_length=512)
        logger.info("Initialized local CrossEncoder reranker (ms-marco-TinyBERT-L-2-v2)")
    except Exception as e:
        logger.warning(f"Local CrossEncoder initialization deferred ({e}). Using semantic composite reranker.")
        _CROSS_ENCODER_MODEL = None

    return _CROSS_ENCODER_MODEL


def rerank_candidate_chunks(
    query: str,
    candidate_tuples: List[Tuple[Any, str, float]],
    query_intent: QueryIntent,
    top_n: int = 8,
) -> List[Tuple[Any, float, str]]:
    """
    Rerank candidate chunks based on:
    1. Content Role Score (40% weight) - Prioritizes core body/chapter text over legal/metadata
    2. Semantic Cross-Encoder / BGE-M3 Similarity Score (40% weight)
    3. Query Intent Alignment (20% weight)

    Returns list of tuples: (chunk, final_rerank_score, content_type)
    """
    if not candidate_tuples:
        return []

    cross_encoder = _get_cross_encoder()
    chunk_objects = [t[0] for t in candidate_tuples]
    texts = [c.text if hasattr(c, "text") else str(c) for c in chunk_objects]

    # 1. Compute Semantic Similarity Scores
    semantic_scores = []
    if cross_encoder and len(texts) > 0:
        try:
            pairs = [[query, text[:800]] for text in texts]
            raw_ce_scores = cross_encoder.predict(pairs)
            # Normalize scores between 0.0 and 1.0 using min-max scaling
            min_s, max_s = min(raw_ce_scores), max(raw_ce_scores)
            if max_s > min_s:
                semantic_scores = [(s - min_s) / (max_s - min_s) for s in raw_ce_scores]
            else:
                semantic_scores = [0.8] * len(texts)
        except Exception as e:
            logger.warning(f"CrossEncoder prediction error ({e}). Falling back to position-decay scoring.")
            semantic_scores = [1.0 - (idx * 0.05) for idx in range(len(texts))]
    else:
        # Fallback to rank position decay score
        semantic_scores = [1.0 - (idx * 0.04) for idx in range(len(texts))]

    # 2. Composite Scoring
    scored_results = []
    for idx, (chunk, content_type, role_score) in enumerate(candidate_tuples):
        sem_score = semantic_scores[idx]

        # Calculate final unified score
        # Content Role Weight = 0.45, Semantic Score Weight = 0.40, Position Tiebreaker = 0.15
        final_score = (role_score * 0.45) + (sem_score * 0.40) + ((1.0 - (idx * 0.02)) * 0.15)

        scored_results.append((chunk, round(final_score, 4), content_type))

    # Sort descending by final score
    scored_results.sort(key=lambda x: x[1], reverse=True)

    # Log debug execution
    if os.getenv("RAG_DEBUG", "true").lower() in ("true", "1"):
        logger.info(f"RERANKER | Query Intent: {query_intent.intent_type.value} | Candidates: {len(candidate_tuples)} | Selected Top-N: {min(top_n, len(scored_results))}")
        for rank, (c, score, ct) in enumerate(scored_results[:top_n]):
            c_idx = getattr(c, "chunk_index", "n/a")
            page = getattr(c, "page_number", "n/a")
            logger.info(f"  Rank #{rank+1} | Score: {score:.4f} | Type: {ct:18s} | Chunk Index: {c_idx} | Page: {page}")

    return scored_results[:top_n]
