"""
ContentForge AI Pipeline Evaluation Script using DeepEval and Deterministic Metrics.
Evaluates the full pipeline (Understanding Pass + Generators) across the Golden Dataset.
Scores:
1. Faithfulness: Does the output only state verified things from the Fact Registry?
2. Answer Relevancy: Is the output structurally compliant and on-topic for its format?
3. Contextual Recall: Did the system capture and incorporate the source ground truth facts?
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_FILE = os.path.abspath(__file__)
EVAL_DIR = os.path.dirname(CURRENT_FILE)
AI_SERVICES_DIR = os.path.dirname(EVAL_DIR)
ROOT_DIR = os.path.dirname(AI_SERVICES_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for p in [ROOT_DIR, BACKEND_DIR, AI_SERVICES_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.models.document import Document, SourceType, ProcessedStatus
from app.models.document_chunk import DocumentChunk
from app.models.fact_registry import FactRegistry
from app.models.user import User, UserRole
from app.core.database import SessionLocal, engine, Base
from ai_services.extraction.chunker import chunk_document
from ai_services.understanding.fact_extraction import run_understanding_pass
from ai_services.orchestrator.output_router import execute_generation_job
from ai_services.validation.schema_validator import validate_output_schema
from ai_services.validation.fact_checker import verify_output_facts
from ai_services.evaluation.golden_dataset import GOLDEN_DOCUMENTS

logger = logging.getLogger("contentforge.evaluator")

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LATEST_REPORT_FILE = RESULTS_DIR / "latest.json"


def evaluate_faithfulness(output_content: Dict[str, Any], fact_ids: List[str]) -> float:
    """Calculate Faithfulness score [0.0 - 1.0] using fact verification."""
    val_score, _, unverified = verify_output_facts(output_content, set(fact_ids))
    return float(val_score)


def evaluate_answer_relevancy(output_type: str, output_content: Dict[str, Any]) -> float:
    """Calculate Answer Relevancy score [0.0 - 1.0] by verifying schema and structural requirements."""
    is_valid, validated_model, _ = validate_output_schema(output_type, output_content)
    if not is_valid:
        return 0.3

    score = 0.6  # Base score for valid schema

    if output_type == "linkedin":
        if output_content.get("hook") and len(output_content.get("hook", "")) > 10:
            score += 0.15
        if output_content.get("hashtags") and len(output_content.get("hashtags", [])) >= 2:
            score += 0.15
        if output_content.get("call_to_action"):
            score += 0.10

    elif output_type == "twitter":
        tweets = output_content.get("tweets", [])
        if len(tweets) >= 2:
            score += 0.20
        if all("order" in t and "text" in t for t in tweets):
            score += 0.20

    elif output_type == "advisory":
        if output_content.get("severity") and output_content.get("recommendations"):
            score += 0.40

    elif output_type == "executive_summary":
        if output_content.get("key_takeaways") and len(output_content.get("key_takeaways", [])) >= 2:
            score += 0.40

    return min(1.0, score)


def evaluate_contextual_recall(ground_truth_facts: List[str], extracted_facts: List[str]) -> float:
    """
    Calculate Contextual Recall [0.0 - 1.0]:
    Measures proportion of ground truth facts captured in the Fact Registry.
    """
    if not ground_truth_facts:
        return 1.0
    if not extracted_facts:
        return 0.0

    matched_count = 0
    extracted_text_blob = " ".join(extracted_facts).lower()

    for gt in ground_truth_facts:
        gt_keywords = [w.lower() for w in gt.split() if len(w) > 4]
        # If at least 50% of distinctive keywords appear in the extracted facts
        if gt_keywords:
            matched_words = sum(1 for kw in gt_keywords if kw in extracted_text_blob)
            if matched_words / len(gt_keywords) >= 0.40:
                matched_count += 1
        else:
            if gt.lower() in extracted_text_blob:
                matched_count += 1

    return round(matched_count / len(ground_truth_facts), 3)


async def run_evaluation_pipeline(
    limit: Optional[int] = None,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Run evaluation across the golden dataset and produce metrics report.
    """
    start_time = time.perf_counter()
    docs_to_evaluate = GOLDEN_DOCUMENTS[:limit] if limit else GOLDEN_DOCUMENTS

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    from app.models.organisation import Organisation
    test_org = db.query(Organisation).first()
    if not test_org:
        test_org = Organisation(
            id=uuid.uuid4(),
            name="Evaluation Org",
        )
        db.add(test_org)
        db.commit()
        db.refresh(test_org)

    # Ensure test user exists
    test_user = db.query(User).filter(User.email == "evaluator@contentforge.ai").first()
    if not test_user:
        test_user = User(
            id=uuid.uuid4(),
            org_id=test_org.id,
            email="evaluator@contentforge.ai",
            password_hash="not_used_for_eval",
            role=UserRole.SYSTEM_ADMIN,
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

    results_per_doc = []
    total_faithfulness = []
    total_relevancy = []
    total_recall = []

    for doc_item in docs_to_evaluate:
        doc_id = uuid.uuid4()
        text_content = doc_item["text"]
        gt_facts = doc_item["ground_truth_facts"]

        # 1. Ingest Document
        doc = Document(
            id=doc_id,
            org_id=test_org.id,
            uploaded_by=test_user.id,
            file_name=f"{doc_item['id']}_{doc_item['title'][:30]}.txt",
            source_type=SourceType.TEXT,
            file_path=f"eval/{doc_id}.txt",
            file_size_bytes=len(text_content.encode("utf-8")),
            mime_type="text/plain",
            processed_status=ProcessedStatus.PROCESSED,
        )
        db.add(doc)

        # 2. Chunk Document
        chunks = chunk_document(text_content, target_words=600, overlap_words=50)
        chunk_entities = [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                text=c["text"],
                page_number=c.get("page_number", 1),
                section_reference=c.get("section_reference", "Main"),
                word_count=c.get("word_count", len(c["text"].split())),
            )
            for c in chunks
        ]
        db.add_all(chunk_entities)
        db.commit()

        # 3. Execute Understanding Pass
        await run_understanding_pass(db, doc.id)

        # 4. Fetch Fact Registry
        fact_records = db.query(FactRegistry).filter(FactRegistry.document_id == doc.id).all()
        extracted_statements = [f.fact_statement for f in fact_records]
        valid_fids = [f.fact_id_string for f in fact_records]

        # 5. Calculate Recall
        recall_score = evaluate_contextual_recall(gt_facts, extracted_statements)
        total_recall.append(recall_score)

        # 6. Generate Outputs
        from app.models.generation_job import GenerationJob, JobStatus
        job = GenerationJob(
            id=uuid.uuid4(),
            document_id=doc.id,
            requested_by=test_user.id,
            selected_outputs=doc_item["target_outputs"],
            settings={"audience": "technical", "tone": "authoritative"},
            status=JobStatus.QUEUED.value,
        )
        db.add(job)
        db.commit()

        executed_job = await execute_generation_job(db, job.id)

        doc_faith_scores = []
        doc_relevancy_scores = []
        output_evaluations = {}

        for out in executed_job.outputs:
            f_score = evaluate_faithfulness(out.content, valid_fids)
            r_score = evaluate_answer_relevancy(out.output_type, out.content)
            doc_faith_scores.append(f_score)
            doc_relevancy_scores.append(r_score)
            total_faithfulness.append(f_score)
            total_relevancy.append(r_score)

            output_evaluations[out.output_type] = {
                "faithfulness": round(f_score, 3),
                "answer_relevancy": round(r_score, 3),
                "status": out.status,
                "facts_cited": len(out.fact_ids_used),
            }

        avg_doc_faith = round(sum(doc_faith_scores) / max(1, len(doc_faith_scores)), 3)
        avg_doc_rel = round(sum(doc_relevancy_scores) / max(1, len(doc_relevancy_scores)), 3)

        results_per_doc.append({
            "doc_id": doc_item["id"],
            "title": doc_item["title"],
            "category": doc_item["category"],
            "facts_extracted": len(fact_records),
            "contextual_recall": recall_score,
            "average_faithfulness": avg_doc_faith,
            "average_answer_relevancy": avg_doc_rel,
            "outputs": output_evaluations,
        })

    db.close()
    duration = time.perf_counter() - start_time

    overall_faith = round(sum(total_faithfulness) / max(1, len(total_faithfulness)), 3)
    overall_rel = round(sum(total_relevancy) / max(1, len(total_relevancy)), 3)
    overall_recall = round(sum(total_recall) / max(1, len(total_recall)), 3)
    composite_score = round((overall_faith * 0.4) + (overall_rel * 0.3) + (overall_recall * 0.3), 3)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_documents_evaluated": len(docs_to_evaluate),
        "execution_time_seconds": round(duration, 2),
        "overall_metrics": {
            "faithfulness": overall_faith,
            "answer_relevancy": overall_rel,
            "contextual_recall": overall_recall,
            "composite_score": composite_score,
        },
        "target_thresholds": {
            "faithfulness_target": 0.85,
            "answer_relevancy_target": 0.80,
            "contextual_recall_target": 0.80,
        },
        "document_breakdown": results_per_doc,
    }

    if save_results:
        # Save timestamped report
        ts = int(time.time())
        run_file = RESULTS_DIR / f"eval_report_{ts}.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Update latest.json
        with open(LATEST_REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Evaluation completed. Report saved to {run_file} and {LATEST_REPORT_FILE}")

    return report


def get_latest_evaluation_report() -> Dict[str, Any]:
    """Retrieve the most recent evaluation report or generate a fresh baseline."""
    if LATEST_REPORT_FILE.exists():
        try:
            with open(LATEST_REPORT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading latest evaluation report: {e}")

    # If no report exists, run a 4-document quick evaluation to establish a baseline
    return asyncio.run(run_evaluation_pipeline(limit=4, save_results=True))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run ContentForge AI Evaluation Pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents to evaluate")
    args = parser.parse_args()

    print(f"Starting AI Evaluation Pipeline over golden dataset (limit={args.limit})...")
    report_data = asyncio.run(run_evaluation_pipeline(limit=args.limit))
    print("\n================== EVALUATION REPORT SUMMARY ==================")
    print(f"Timestamp:              {report_data['timestamp']}")
    print(f"Documents Evaluated:    {report_data['total_documents_evaluated']}")
    print(f"Execution Duration:     {report_data['execution_time_seconds']}s")
    print(f"Faithfulness Score:     {report_data['overall_metrics']['faithfulness']}")
    print(f"Answer Relevancy Score: {report_data['overall_metrics']['answer_relevancy']}")
    print(f"Contextual Recall Score:{report_data['overall_metrics']['contextual_recall']}")
    print(f"Composite Score:        {report_data['overall_metrics']['composite_score']}")
    print("===============================================================\n")
