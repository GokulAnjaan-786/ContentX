import os
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def compute_context_precision(query: str, retrieved_contexts: List[str], ground_truth: str) -> float:
    """Calculate Context Precision metric (0.0 - 1.0)."""
    if not retrieved_contexts:
        return 0.0

    gt_keywords = set(re_words(ground_truth.lower()))
    relevant_hits = 0

    for ctx in retrieved_contexts:
        ctx_words = set(re_words(ctx.lower()))
        overlap = len(gt_keywords.intersection(ctx_words))
        if overlap >= 3 or (len(gt_keywords) > 0 and overlap / len(gt_keywords) >= 0.2):
            relevant_hits += 1

    return round(relevant_hits / len(retrieved_contexts), 4)


def compute_context_recall(retrieved_contexts: List[str], ground_truth: str) -> float:
    """Calculate Context Recall metric (0.0 - 1.0)."""
    if not ground_truth or not ground_truth.strip():
        return 1.0

    combined_context = " ".join(retrieved_contexts).lower()
    gt_sentences = [s.strip() for s in ground_truth.split(".") if len(s.strip()) > 10]
    if not gt_sentences:
        return 1.0

    supported_count = 0
    for gt_s in gt_sentences:
        words = [w for w in re_words(gt_s.lower()) if len(w) > 3]
        if not words:
            supported_count += 1
            continue
        match_count = sum(1 for w in words if w in combined_context)
        if match_count / len(words) >= 0.4:
            supported_count += 1

    return round(supported_count / len(gt_sentences), 4)


def compute_context_relevancy(query: str, retrieved_contexts: List[str]) -> float:
    """Calculate Context Relevancy metric (0.0 - 1.0)."""
    if not retrieved_contexts:
        return 0.0

    query_keywords = set([w for w in re_words(query.lower()) if len(w) > 3])
    if not query_keywords:
        return 1.0

    relevant_contexts = 0
    for ctx in retrieved_contexts:
        ctx_words = set(re_words(ctx.lower()))
        if any(w in ctx_words for w in query_keywords):
            relevant_contexts += 1

    return round(relevant_contexts / len(retrieved_contexts), 4)


def compute_answer_relevancy(query: str, generated_answer: str) -> float:
    """Calculate Answer Relevancy metric (0.0 - 1.0)."""
    if not generated_answer or not generated_answer.strip():
        return 0.0

    query_keywords = set([w for w in re_words(query.lower()) if len(w) > 3])
    if not query_keywords:
        return 1.0

    ans_words = set(re_words(generated_answer.lower()))
    matches = sum(1 for w in query_keywords if w in ans_words)
    return round(matches / len(query_keywords), 4) if query_keywords else 1.0


def compute_faithfulness(generated_answer: str, retrieved_contexts: List[str]) -> float:
    """Calculate Faithfulness metric (0.0 - 1.0)."""
    if not generated_answer or not generated_answer.strip():
        return 1.0
    if not retrieved_contexts:
        return 0.0

    combined_context = " ".join(retrieved_contexts).lower()
    ans_sentences = [s.strip() for s in generated_answer.split(".") if len(s.strip()) > 10]
    if not ans_sentences:
        return 1.0

    faithful_count = 0
    for ans_s in ans_sentences:
        words = [w for w in re_words(ans_s.lower()) if len(w) > 3]
        if not words:
            faithful_count += 1
            continue
        match_count = sum(1 for w in words if w in combined_context)
        if match_count / len(words) >= 0.35:
            faithful_count += 1

    return round(faithful_count / len(ans_sentences), 4)


def re_words(text: str) -> List[str]:
    import re
    return re.findall(r"\b\w+\b", text)


class RagasEvaluator:
    """
    RAGAS & Custom Metric Evaluation Engine for ContentX.
    Evaluates:
    1. Context Precision
    2. Context Recall
    3. Context Relevancy
    4. Answer Relevancy
    5. Faithfulness
    """

    def evaluate_sample(
        self,
        query: str,
        retrieved_contexts: List[str],
        generated_answer: str,
        ground_truth: str = "",
    ) -> Dict[str, float]:
        prec = compute_context_precision(query, retrieved_contexts, ground_truth)
        rec = compute_context_recall(retrieved_contexts, ground_truth)
        rel = compute_context_relevancy(query, retrieved_contexts)
        ans_rel = compute_answer_relevancy(query, generated_answer)
        faith = compute_faithfulness(generated_answer, retrieved_contexts)

        overall_score = round((prec + rec + rel + ans_rel + faith) / 5.0, 4)

        results = {
            "context_precision": prec,
            "context_recall": rec,
            "context_relevancy": rel,
            "answer_relevancy": ans_rel,
            "faithfulness": faith,
            "ragas_overall_score": overall_score,
        }

        if os.getenv("RAG_DEBUG", "true").lower() in ("true", "1"):
            logger.info(
                f"RAGAS EVALUATION | Query: '{query[:40]}...' | Overall: {overall_score:.4f} | "
                f"Prec: {prec:.2f} | Rec: {rec:.2f} | Rel: {rel:.2f} | AnsRel: {ans_rel:.2f} | Faith: {faith:.2f}"
            )

        return results


ragas_evaluator = RagasEvaluator()
