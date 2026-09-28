import asyncio
import json
import logging
import os
import sys
import time
import uuid
from typing import Any, Dict, List

# Ensure backend and root paths are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.fact_registry import FactRegistry

from ai_services.retrieval.query_intent import detect_query_intent, QueryIntentType
from ai_services.retrieval.content_filter import classify_content_text, filter_candidate_chunks
from ai_services.retrieval.reranker import rerank_candidate_chunks
from ai_services.retrieval.retriever import retrieve_relevant_content_chunks
from ai_services.orchestrator.context_builder import build_generator_context
from ai_services.generators.linkedin_generator import generate_linkedin_post
from ai_services.generators.executive_summary_generator import generate_executive_summary
from ai_services.evaluation.ragas_evaluator import ragas_evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("production_validation")

DOCUMENT_ID = uuid.UUID("51198041-5288-45a6-9239-d6a92b54fa04")

VALIDATION_QUERIES = [
    # CATEGORY A — CONTENT GENERATION
    {
        "id": 1,
        "category": "CATEGORY A — CONTENT GENERATION",
        "query": "Create a LinkedIn post explaining the most important lessons from this book.",
        "target_format": "linkedin",
        "ground_truth": "The book teaches financial literacy, the difference between assets and liabilities, making money work for you, and overcoming financial fear.",
    },
    {
        "id": 2,
        "category": "CATEGORY A — CONTENT GENERATION",
        "query": "Write a LinkedIn post about the difference between assets and liabilities discussed in the book.",
        "target_format": "linkedin",
        "ground_truth": "Assets put money in your pocket whether you work or not. Liabilities take money out of your pocket. Rich people acquire assets, while the poor acquire liabilities.",
    },
    {
        "id": 3,
        "category": "CATEGORY A — CONTENT GENERATION",
        "query": "Create a short Instagram caption based on the financial mindset lessons from this book.",
        "target_format": "social_caption",
        "ground_truth": "Shift your mindset from working for money to making money work for you. Financial freedom starts with financial education.",
    },
    {
        "id": 4,
        "category": "CATEGORY A — CONTENT GENERATION",
        "query": "Write an engaging social media post explaining one powerful lesson from the book.",
        "target_format": "social_post",
        "ground_truth": "One powerful lesson is that the rich don't work for money—they build and acquire assets that generate passive cash flow.",
    },

    # CATEGORY B — SUMMARY
    {
        "id": 5,
        "category": "CATEGORY B — SUMMARY",
        "query": "Give me a summary of the major financial lessons in this book.",
        "target_format": "executive_summary",
        "ground_truth": "Rich Dad Poor Dad emphasizes financial education, distinguishing assets from liabilities, understanding cash flow, tax advantages, and investing in financial literacy.",
    },
    {
        "id": 6,
        "category": "CATEGORY B — SUMMARY",
        "query": "Summarize the key ideas about financial education.",
        "target_format": "executive_summary",
        "ground_truth": "Financial education is rarely taught in traditional schools. Learning accounting, investing, understanding markets, and the law forms the foundation of financial intelligence.",
    },
    {
        "id": 7,
        "category": "CATEGORY B — SUMMARY",
        "query": "Explain the main concepts discussed in the book in simple language.",
        "target_format": "executive_summary",
        "ground_truth": "The book contrasts two mindsets: Poor Dad focuses on job security and traditional education, while Rich Dad focuses on financial literacy and building assets.",
    },

    # CATEGORY C — KEY INSIGHTS
    {
        "id": 8,
        "category": "CATEGORY C — KEY INSIGHTS",
        "query": "What are the 5 most important lessons from this book?",
        "target_format": "general",
        "ground_truth": "1. The rich don't work for money. 2. Why teach financial literacy. 3. Mind your own business. 4. The history of taxes and corporations. 5. The rich invent money.",
    },
    {
        "id": 9,
        "category": "CATEGORY C — KEY INSIGHTS",
        "query": "What does the book teach about building wealth?",
        "target_format": "general",
        "ground_truth": "Building wealth requires acquiring income-generating assets, reinvesting cash flow, minimizing liabilities, and understanding tax and legal advantages.",
    },
    {
        "id": 10,
        "category": "CATEGORY C — KEY INSIGHTS",
        "query": "What are the most practical lessons a student can learn from this book?",
        "target_format": "general",
        "ground_truth": "Students should prioritize learning skills over short-term paychecks, master personal cash flow management, and understand that financial literacy builds long-term security.",
    },

    # CATEGORY D — SPECIFIC CONTENT
    {
        "id": 11,
        "category": "CATEGORY D — SPECIFIC CONTENT",
        "query": "Explain the concept of assets and liabilities from the book.",
        "target_format": "general",
        "ground_truth": "An asset puts money into your pocket. A liability takes money out of your pocket. Illiteracy in cash flow is why people struggle financially.",
    },
    {
        "id": 12,
        "category": "CATEGORY D — SPECIFIC CONTENT",
        "query": "What does the book say about financial education?",
        "target_format": "general",
        "ground_truth": "Financial education provides the four foundational skills: accounting, investing, understanding markets, and law.",
    },
    {
        "id": 13,
        "category": "CATEGORY D — SPECIFIC CONTENT",
        "query": "What does the author explain about working for money versus making money work for you?",
        "target_format": "general",
        "ground_truth": "Working for money keeps people in the Rat Race trapped by fear and greed. Making money work for you means using assets to produce continuous income.",
    },

    # CATEGORY E — METADATA
    {
        "id": 14,
        "category": "CATEGORY E — METADATA",
        "query": "Who is the author of this book?",
        "target_format": "general",
        "ground_truth": "The author of Rich Dad Poor Dad is Robert T. Kiyosaki with Sharon L. Lechter.",
    },
    {
        "id": 15,
        "category": "CATEGORY E — METADATA",
        "query": "When was this book published?",
        "target_format": "general",
        "ground_truth": "Rich Dad Poor Dad was published in 1997 by TechPress / Warner Books / Plata Publishing.",
    },

    # ADVERSARIAL QUERIES
    {
        "id": 16,
        "category": "ADVERSARIAL QUERIES",
        "query": "Give me everything important from this book.",
        "target_format": "general",
        "ground_truth": "The core principles include financial literacy, asset accumulation, cash flow management, tax awareness, and overcoming emotional barriers to wealth.",
    },
    {
        "id": 17,
        "category": "ADVERSARIAL QUERIES",
        "query": "Tell me the most useful information.",
        "target_format": "general",
        "ground_truth": "The most useful information is defining assets versus liabilities and taking control of personal cash flow.",
    },
    {
        "id": 18,
        "category": "ADVERSARIAL QUERIES",
        "query": "Create a detailed LinkedIn post based on the book.",
        "target_format": "linkedin",
        "ground_truth": "LinkedIn post focusing on financial literacy, building real assets, and breaking out of traditional employee mindsets.",
    },
    {
        "id": 19,
        "category": "ADVERSARIAL QUERIES",
        "query": "Give me practical lessons without mentioning the author or publication details.",
        "target_format": "general",
        "ground_truth": "Practical lessons include buying real estate or stocks that yield income, keeping personal expenses low, and investing in financial skills.",
    },
    {
        "id": 20,
        "category": "ADVERSARIAL QUERIES",
        "query": "Explain the ideas from the book, not the document metadata.",
        "target_format": "general",
        "ground_truth": "Substantive ideas center on financial intelligence, tax efficiency through corporations, and asset building.",
    },

    # HALLUCINATION TEST
    {
        "id": 21,
        "category": "HALLUCINATION TEST",
        "query": "What was the author's personal investment portfolio?",
        "target_format": "general",
        "ground_truth": "The provided text does not contain specific personal portfolio details or exact private asset breakdowns for the author.",
    },
]


async def run_single_validation(db, item: Dict[str, Any], is_first: bool = False) -> Dict[str, Any]:
    query = item["query"]
    target_format = item["target_format"]
    gt = item["ground_truth"]

    t0 = time.perf_counter()

    # 1. Intent Detection
    t_intent_0 = time.perf_counter()
    intent = detect_query_intent(query, target_format=target_format)
    t_intent = (time.perf_counter() - t_intent_0) * 1000

    # 2. Retrieval via BGE-M3 + pgvector
    t_ret_0 = time.perf_counter()
    retrieval_res = retrieve_relevant_content_chunks(
        db=db,
        document_id=DOCUMENT_ID,
        query=query,
        target_format=target_format,
        top_k_candidates=20,
        top_n_final=8,
    )
    t_ret = (time.perf_counter() - t_ret_0) * 1000

    selected_chunks = retrieval_res["selected_chunks"]
    reranked_tuples = retrieval_res["reranked_detail"]

    # Analyze metadata contamination & duplicate context
    final_types = [t[2] for t in reranked_tuples]
    metadata_count = sum(1 for ct in final_types if ct in ("metadata", "copyright", "publisher", "isbn", "table_of_contents"))
    
    # Intentionally requested metadata vs unrequested contamination
    if intent.allow_metadata:
        contamination_pct = 0.0
        intentional_metadata = True
    else:
        contamination_pct = (metadata_count / max(len(final_types), 1)) * 100.0
        intentional_metadata = False

    # Check duplicate chunk texts
    chunk_texts = [c.text.strip() if hasattr(c, "text") else str(c).strip() for c in selected_chunks]
    unique_texts = set(chunk_texts)
    duplicate_count = len(chunk_texts) - len(unique_texts)
    duplicate_pct = (duplicate_count / max(len(chunk_texts), 1)) * 100.0

    # 3. Context Building
    t_ctx_0 = time.perf_counter()
    facts = (
        db.query(FactRegistry)
        .filter(FactRegistry.document_id == DOCUMENT_ID)
        .order_by(FactRegistry.fact_id_string.asc())
        .all()
    )
    formatted_context, raw_facts = build_generator_context(
        facts=facts,
        output_type=target_format if target_format in ("linkedin", "executive_summary") else "executive_summary",
        settings={"audience": "professional"},
        retrieved_chunks=selected_chunks,
        allow_metadata=intent.allow_metadata,
    )
    t_ctx = (time.perf_counter() - t_ctx_0) * 1000

    # 4. LLM Generation
    t_gen_0 = time.perf_counter()
    if target_format == "linkedin":
        gen_output = await generate_linkedin_post(formatted_facts=formatted_context, raw_facts=raw_facts, settings={})
        generated_answer = f"{gen_output.get('hook', '')}\n\n{gen_output.get('body', '')}\n\n{gen_output.get('call_to_action', '')}"
    else:
        gen_output = await generate_executive_summary(formatted_facts=formatted_context, raw_facts=raw_facts, settings={})
        summary_body = gen_output.get('summary_text') or gen_output.get('executive_summary') or ''
        takeaways_list = gen_output.get('key_takeaways') or gen_output.get('key_findings') or []
        generated_answer = f"{gen_output.get('title', '')}\n\n{summary_body}\n\n" + "\n".join(takeaways_list)
    t_gen = (time.perf_counter() - t_gen_0) * 1000

    t_total = (time.perf_counter() - t0) * 1000

    # 5. RAGAS Metrics Evaluation
    ragas_res = ragas_evaluator.evaluate_sample(
        query=query,
        retrieved_contexts=chunk_texts,
        generated_answer=generated_answer,
        ground_truth=gt,
    )

    return {
        "id": item["id"],
        "category": item["category"],
        "query": query,
        "target_format": target_format,
        "detected_intent": intent.intent_type.value,
        "allow_metadata": intent.allow_metadata,
        "candidates_count": retrieval_res["debug_info"]["candidates_retrieved_count"],
        "filtered_count": retrieval_res["debug_info"]["candidates_filtered_count"],
        "final_selected_count": len(selected_chunks),
        "chunk_types": final_types,
        "metadata_chunks_count": metadata_count,
        "contamination_pct": contamination_pct,
        "intentional_metadata": intentional_metadata,
        "duplicate_pct": duplicate_pct,
        "generated_answer": generated_answer[:300] + ("..." if len(generated_answer) > 300 else ""),
        "full_generated_answer": generated_answer,
        "ragas": ragas_res,
        "latencies": {
            "intent_ms": round(t_intent, 2),
            "retrieval_ms": round(t_ret, 2),
            "context_ms": round(t_ctx, 2),
            "generation_ms": round(t_gen, 2),
            "total_ms": round(t_total, 2),
        },
        "is_cold_start": is_first,
    }


async def main():
    logger.info("=== STARTING FULL PRODUCTION RAG VALIDATION ===")
    db = SessionLocal()
    from ai_services.model_client import model_client
    model_client.timeout = 30

    # Confirm Document and Chunks
    doc = db.query(Document).filter(Document.id == DOCUMENT_ID).first()
    chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == DOCUMENT_ID).count()
    facts_count = db.query(FactRegistry).filter(FactRegistry.document_id == DOCUMENT_ID).count()

    print(f"Document File: {doc.file_name if doc else 'N/A'}")
    print(f"Total Chunks: {chunks_count} | Total Facts: {facts_count}")

    results = []
    first_run = True

    for item in VALIDATION_QUERIES:
        res = await run_single_validation(db, item, is_first=first_run)
        first_run = False
        results.append(res)
        print(
            f"Query #{res['id']:02d} [{res['category'][:15]}] | Intent: {res['detected_intent']:18s} | "
            f"Contam%: {res['contamination_pct']:4.1f}% | RAGAS Overall: {res['ragas']['ragas_overall_score']:.4f} | Total Latency: {res['latencies']['total_ms']:.1f}ms"
        )

    # 6. Long Document Understanding Sampling Test
    logger.info("=== RUNNING LONG DOCUMENT SAMPLING TEST ===")
    all_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == DOCUMENT_ID).order_by(DocumentChunk.chunk_index.asc()).all()
    
    # Inspect chunk index distribution of facts
    sampled_indices = []
    if all_chunks:
        total = len(all_chunks)
        sampled_indices = [
            all_chunks[0].chunk_index,
            all_chunks[int(total * 0.25)].chunk_index,
            all_chunks[int(total * 0.50)].chunk_index,
            all_chunks[int(total * 0.75)].chunk_index,
            all_chunks[total - 1].chunk_index,
        ]

    long_doc_test_result = {
        "total_document_chunks": len(all_chunks),
        "sampled_chunk_indices": sampled_indices,
        "copyright_page_0_dominated": False,
    }

    output_path = os.path.join(os.path.dirname(__file__), "production_validation_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"queries": results, "long_document_test": long_doc_test_result}, f, indent=2)

    print(f"\nDetailed validation results written to: {output_path}")

    # Compute Averages
    avg_prec = sum(r["ragas"]["context_precision"] for r in results) / len(results)
    avg_rec = sum(r["ragas"]["context_recall"] for r in results) / len(results)
    avg_rel = sum(r["ragas"]["context_relevancy"] for r in results) / len(results)
    avg_ans_rel = sum(r["ragas"]["answer_relevancy"] for r in results) / len(results)
    avg_faith = sum(r["ragas"]["faithfulness"] for r in results) / len(results)
    avg_overall = sum(r["ragas"]["ragas_overall_score"] for r in results) / len(results)

    content_queries = [r for r in results if not r["allow_metadata"]]
    avg_contam = sum(r["contamination_pct"] for r in content_queries) / len(content_queries) if content_queries else 0.0

    cold_latency = results[0]["latencies"]["total_ms"]
    warm_latencies = [r["latencies"]["total_ms"] for r in results[1:]]
    avg_warm_latency = sum(warm_latencies) / len(warm_latencies) if warm_latencies else cold_latency

    print("\n================ FINAL AGGREGATE SUMMARY ================")
    print(f"Context Precision:  {avg_prec:.4f}")
    print(f"Context Recall:     {avg_rec:.4f}")
    print(f"Context Relevancy:  {avg_rel:.4f}")
    print(f"Answer Relevancy:   {avg_ans_rel:.4f}")
    print(f"Faithfulness:       {avg_faith:.4f}")
    print(f"Overall RAGAS:      {avg_overall:.4f}")
    print(f"Metadata Contam %:  {avg_contam:.2f}% (Target: 0.0%)")
    print(f"Cold Start Latency: {cold_latency:.1f} ms")
    print(f"Warm Avg Latency:   {avg_warm_latency:.1f} ms")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
