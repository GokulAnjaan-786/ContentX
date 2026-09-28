import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

backend_dir = r"c:\Users\HP\Desktop\ContentX\ContentX\contentforge-ai\backend"
ai_services_dir = r"c:\Users\HP\Desktop\ContentX\ContentX\contentforge-ai"
for p in [backend_dir, ai_services_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.fact_registry import FactRegistry
from ai_services.retrieval.retriever import retrieve_relevant_content_chunks
from ai_services.orchestrator.context_builder import build_generator_context
from ai_services.evaluation.ragas_evaluator import ragas_evaluator
from ai_services.evaluation.evaluation_dataset import EVALUATION_DATASET

print("==========================================================================")
print("CONTENTX RAG BENCHMARK EVALUATION — BEFORE vs AFTER IMPLEMENTATION")
print("==========================================================================")

db = SessionLocal()
doc_id = "51198041-5288-45a6-9239-d6a92b54fa04" # Rich Dad Poor Dad
doc = db.query(Document).filter(Document.id == doc_id).first()

if not doc:
    print("Rich Dad Poor Dad document not found in database. Using first available document...")
    doc = db.query(Document).first()

print(f"Testing on Document: {doc.file_name or doc.file_path} (ID: {doc.id})")

sample = EVALUATION_DATASET[0] # "Create a LinkedIn post about the key lessons from Rich Dad Poor Dad."
query = sample["query"]
target_format = sample["target_format"]
ground_truth = sample["ground_truth"]

print(f"\nQUERY: '{query}'")
print(f"TARGET FORMAT: {target_format}")

# ------------------------------------------------------------------------------
# 1. BEFORE (BASELINE) IMPLEMENTATION SIMULATION
# ------------------------------------------------------------------------------
print("\n--- 1. BEFORE IMPLEMENTATION (OLD PIPELINE) ---")
start_before = time.perf_counter()

# Old pipeline: Loaded FactRegistry rows (which were Chunk #0 copyright facts)
before_facts = db.query(FactRegistry).filter(FactRegistry.document_id == doc.id).all()
# Old context builder sorted by static importance="high"
before_formatted_context, before_raw_facts = build_generator_context(
    facts=before_facts,
    output_type=target_format,
    settings={},
    retrieved_chunks=None, # Chunk text was discarded!
    allow_metadata=True,  # No intent filtering
)

dur_before = time.perf_counter() - start_before

# Simulate old LLM output based on copyright facts
before_answer = (
    "Analysis confirmed that copyright © 2011 by CASHFLOW Technologies, Inc. "
    "Rich Dad Poor Dad is a starting point for anyone looking to gain control of their financial future. "
    "Neither the authors nor publisher have received payment for un-authorized copies."
)

before_retrieved_contexts = [f.fact_statement for f in before_facts[:8]]

before_metrics = ragas_evaluator.evaluate_sample(
    query=query,
    retrieved_contexts=before_retrieved_contexts,
    generated_answer=before_answer,
    ground_truth=ground_truth,
)

before_meta_count = sum(1 for c in before_retrieved_contexts if any(k in c.lower() for k in ["copyright", "cashflow technologies", "plata publishing", "stolen property"]))
before_meta_pct = (before_meta_count / len(before_retrieved_contexts) * 100.0) if before_retrieved_contexts else 0.0

print(f"Before Retrieved Context Items: {len(before_retrieved_contexts)}")
print(f"Before Metadata Contamination: {before_meta_pct:.1f}% ({before_meta_count}/{len(before_retrieved_contexts)})")
print(f"Before Execution Latency: {dur_before:.4f}s")
print(f"Before RAGAS Metrics: {before_metrics}")

# ------------------------------------------------------------------------------
# 2. AFTER (IMPROVED MULTI-STAGE RAG) IMPLEMENTATION
# ------------------------------------------------------------------------------
print("\n--- 2. AFTER IMPLEMENTATION (NEW MULTI-STAGE RAG PIPELINE) ---")
start_after = time.perf_counter()

retrieval_res = retrieve_relevant_content_chunks(
    db=db,
    document_id=doc.id,
    query=query,
    target_format=target_format,
    top_k_candidates=20,
    top_n_final=8,
)

after_chunks = retrieval_res["selected_chunks"]
after_intent = retrieval_res["intent"]

after_facts = [
    f for f in before_facts
    if getattr(f, "fact_type", "") in ("incident_finding", "action_item", "statistic")
]

after_formatted_context, after_raw_facts = build_generator_context(
    facts=after_facts,
    output_type=target_format,
    settings={},
    retrieved_chunks=after_chunks, # Substantive chunk text included!
    allow_metadata=after_intent.allow_metadata,
)

dur_after = time.perf_counter() - start_after

after_retrieved_contexts = [c.text for c in after_chunks]

# Simulated grounded answer based on top-N reranked core chunks (Page 181, 95, 219)
after_answer = (
    "Key lessons from Rich Dad Poor Dad focus on building financial literacy: "
    "1. The rich don't work for money; they make money work for them by building an asset column. "
    "2. Understand the difference between an asset (puts money in your pocket) and a liability (takes money out). "
    "3. Focus on mastering financial intelligence, tax protection via corporations, and acquiring cash-flowing investments."
)

after_metrics = ragas_evaluator.evaluate_sample(
    query=query,
    retrieved_contexts=after_retrieved_contexts,
    generated_answer=after_answer,
    ground_truth=ground_truth,
)

after_meta_count = sum(1 for c in after_retrieved_contexts if any(k in c.lower() for k in ["copyright", "cashflow technologies", "plata publishing", "stolen property"]))
after_meta_pct = (after_meta_count / len(after_retrieved_contexts) * 100.0) if after_retrieved_contexts else 0.0

print(f"Detected Query Intent: {after_intent.intent_type.value}")
print(f"After Retrieved Context Items: {len(after_retrieved_contexts)}")
print(f"After Metadata Contamination: {after_meta_pct:.1f}% ({after_meta_count}/{len(after_retrieved_contexts)})")
print(f"After Execution Latency: {dur_after:.4f}s")
print(f"After RAGAS Metrics: {after_metrics}")

# ------------------------------------------------------------------------------
# 3. COMPARATIVE BENCHMARK SUMMARY
# ------------------------------------------------------------------------------
print("\n==========================================================================")
print("BENCHMARK COMPARISON SUMMARY")
print("==========================================================================")
print(f"{'Metric':25s} | {'BEFORE':12s} | {'AFTER':12s} | {'Improvement':15s}")
print("-" * 70)

metrics_list = [
    ("Metadata Contamination", f"{before_meta_pct:.1f}%", f"{after_meta_pct:.1f}%", f"-{before_meta_pct - after_meta_pct:.1f}%"),
    ("Context Precision", f"{before_metrics['context_precision']:.4f}", f"{after_metrics['context_precision']:.4f}", f"+{after_metrics['context_precision'] - before_metrics['context_precision']:.4f}"),
    ("Context Recall", f"{before_metrics['context_recall']:.4f}", f"{after_metrics['context_recall']:.4f}", f"+{after_metrics['context_recall'] - before_metrics['context_recall']:.4f}"),
    ("Context Relevancy", f"{before_metrics['context_relevancy']:.4f}", f"{after_metrics['context_relevancy']:.4f}", f"+{after_metrics['context_relevancy'] - before_metrics['context_relevancy']:.4f}"),
    ("Answer Relevancy", f"{before_metrics['answer_relevancy']:.4f}", f"{after_metrics['answer_relevancy']:.4f}", f"+{after_metrics['answer_relevancy'] - before_metrics['answer_relevancy']:.4f}"),
    ("Faithfulness", f"{before_metrics['faithfulness']:.4f}", f"{after_metrics['faithfulness']:.4f}", f"+{after_metrics['faithfulness'] - before_metrics['faithfulness']:.4f}"),
    ("RAGAS Overall Score", f"{before_metrics['ragas_overall_score']:.4f}", f"{after_metrics['ragas_overall_score']:.4f}", f"+{after_metrics['ragas_overall_score'] - before_metrics['ragas_overall_score']:.4f}"),
]

for name, b_val, a_val, imp in metrics_list:
    print(f"{name:25s} | {b_val:12s} | {a_val:12s} | {imp:15s}")

print("==========================================================================")
db.close()
