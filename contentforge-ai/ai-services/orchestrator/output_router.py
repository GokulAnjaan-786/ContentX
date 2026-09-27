import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List
from sqlalchemy.orm import Session

from app.models.generation_job import GenerationJob, JobStatus
from app.models.generated_output import GeneratedOutput
from app.models.fact_registry import FactRegistry
from ai_services.orchestrator.context_builder import build_generator_context
from ai_services.generators.linkedin_generator import generate_linkedin_post
from ai_services.generators.twitter_generator import generate_twitter_thread
from ai_services.generators.advisory_generator import generate_advisory
from ai_services.generators.executive_summary_generator import generate_executive_summary
from ai_services.generators.infographic_generator import generate_infographic
from ai_services.generators.presentation_generator import generate_presentation
from ai_services.generators.video_generator import generate_video_package
from ai_services.validation.schema_validator import validate_output_schema
from ai_services.validation.fact_checker import verify_output_facts, check_cross_output_consistency

from ai_services.understanding.embeddings import (
    generate_and_store_chunk_embeddings,
    search_relevant_chunks,
    get_active_embedding_model_name,
)

logger = logging.getLogger(__name__)

GENERATOR_ROUTER: Dict[str, Callable] = {
    "linkedin": generate_linkedin_post,
    "twitter": generate_twitter_thread,
    "advisory": generate_advisory,
    "executive_summary": generate_executive_summary,
    "infographic": generate_infographic,
    "presentation": generate_presentation,
    "video_package": generate_video_package,
}

OUTPUT_RETRIEVAL_OBJECTIVES: Dict[str, str] = {
    "presentation": "Retrieve key topic, background, major findings, data statistics, strategic impact, and conclusion takeaways for presentation slides.",
    "executive_summary": "Retrieve major findings, strategic impact, important numbers, dates, status, key actions, and unresolved issues.",
    "advisory": "Retrieve threat or issue, affected systems, products, technical identifiers, severity, attack vectors, impact, mitigation, and detection actions.",
    "linkedin": "Retrieve core narrative, major technical/business findings, key statistics, and main takeaways for professional publishing.",
    "twitter": "Retrieve key takeaways, concise findings, and major statistics for summary thread.",
    "infographic": "Retrieve core statistics, key data points, metrics, and structured milestones for visual breakdown.",
    "video_package": "Retrieve major narrative events, key findings, and visualizable telemetry/data for broadcast script.",
}


from ai_services.orchestrator.audience_profile import resolve_audiences

async def _run_single_generator(
    output_type: str,
    generator_fn: Callable,
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
    audience: str = "professional",
) -> Dict[str, Any]:
    """Execute a single generator asynchronously with metric tracking."""
    import time
    start_t = time.perf_counter()
    try:
        res = await generator_fn(
            formatted_facts=formatted_facts,
            raw_facts=raw_facts,
            settings=settings,
        )
        if isinstance(res, dict):
            res["audience"] = audience
        duration = time.perf_counter() - start_t
        try:
            from app.core.metrics import AI_GENERATION_DURATION
            AI_GENERATION_DURATION.labels(output_type=output_type, status="success").observe(duration)
        except Exception:
            pass
        return res
    except Exception as e:
        duration = time.perf_counter() - start_t
        try:
            from app.core.metrics import AI_GENERATION_DURATION, AI_GENERATION_FAILURES
            AI_GENERATION_DURATION.labels(output_type=output_type, status="error").observe(duration)
            AI_GENERATION_FAILURES.labels(output_type=output_type, reason=type(e).__name__).inc()
        except Exception:
            pass
        raise e


async def execute_generation_job(
    db: Session,
    job_id: uuid.UUID,
) -> GenerationJob:
    """
    Orchestrate multi-format generation job with Truth Compression support:
    1. Retrieve job settings and Fact Registry.
    2. Resolve (output_type, audience) combinations.
    3. Route each (format, audience) pair to its generator.
    4. Execute all generators in parallel using asyncio.gather.
    5. Validate each output schema and verify claims against Fact Registry.
    6. Perform cross-output & audience consistency check across generated artifacts.
    7. Persist generated outputs and update job status.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise ValueError(f"Generation job {job_id} not found")

    job.status = JobStatus.PROCESSING.value
    db.commit()

    # Load Fact Registry for the document
    facts = (
        db.query(FactRegistry)
        .filter(FactRegistry.document_id == job.document_id)
        .order_by(FactRegistry.fact_id_string.asc())
        .all()
    )

    if not facts:
        job.status = JobStatus.FAILED.value
        job.error_message = "No facts found in Fact Registry. Run Understanding Pass first."
        db.commit()
        return job

    valid_fact_ids = {f.fact_id_string for f in facts}
    fact_statements_map = {f.fact_id_string: f.fact_statement for f in facts}
    selected_outputs = job.selected_outputs or []
    settings = job.settings or {}
    selected_audiences = settings.get("selected_audiences") or settings.get("audience") or ["automatic"]
    if isinstance(selected_audiences, str):
        selected_audiences = [selected_audiences]

    # Resolve output + audience pairs
    generation_pairs = resolve_audiences(selected_outputs, selected_audiences)

    # Build tasks for parallel execution
    tasks = []
    output_pairs_ordered = []

    for pair in generation_pairs:
        out_type = pair["output_type"]
        aud_type = pair["audience"]
        key = out_type.lower().strip()
        generator_fn = GENERATOR_ROUTER.get(key)
        if not generator_fn:
            logger.warning(f"Unknown generator requested: {key}")
            continue

        # 1. Output-Specific RAG Retrieval using BGE-M3 + pgvector
        retrieval_objective = OUTPUT_RETRIEVAL_OBJECTIVES.get(key, "Retrieve relevant source facts and key findings.")
        try:
            generate_and_store_chunk_embeddings(db, job.document_id)
            relevant_chunks = search_relevant_chunks(db, job.document_id, query=retrieval_objective, top_k=8)
            retrieved_chunk_ids = {c.id for c in relevant_chunks}
        except Exception as rag_err:
            logger.warning(f"RAG retrieval warning for {key}: {rag_err}")
            relevant_chunks = []
            retrieved_chunk_ids = set()

        # 2. Filter FactRegistry facts linked to retrieved chunks or high/medium importance
        if retrieved_chunk_ids:
            relevant_facts = [
                f for f in facts 
                if f.source_chunk_id in retrieved_chunk_ids or getattr(f, "importance", "high") in ("high", "medium")
            ]
            if not relevant_facts:
                relevant_facts = facts
        else:
            relevant_facts = facts

        formatted_facts, raw_facts = build_generator_context(relevant_facts, key, settings, audience=aud_type)

        # Logging development debug visibility
        active_model = get_active_embedding_model_name()
        logger.info(
            f"RAG PIPELINE | OUTPUT: {key} | EMBEDDING_MODEL: {active_model} | VECTOR_STORE: PostgreSQL pgvector | "
            f"RETRIEVED_CHUNKS: {len(relevant_chunks)} | SELECTED_FACTS: {len(relevant_facts)} | FINAL_CONTEXT_FACTS: {len(raw_facts)}"
        )

        tasks.append(_run_single_generator(key, generator_fn, formatted_facts, raw_facts, settings, audience=aud_type))
        output_pairs_ordered.append((key, aud_type))

    # Execute all generators in parallel
    logger.info(f"Executing {len(tasks)} generators in parallel for job {job.id}...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    generated_entities: List[GeneratedOutput] = []
    has_warnings = False
    completed_outputs_for_consistency: List[Dict[str, Any]] = []

    for (out_type, aud_type), result in zip(output_pairs_ordered, results):
        output_id = uuid.uuid4()

        if isinstance(result, Exception):
            logger.error(f"Generator {out_type} ({aud_type}) failed with exception: {result}")
            gen_out = GeneratedOutput(
                id=output_id,
                job_id=job.id,
                output_type=out_type,
                content={"error": str(result)},
                validation_score=0.0,
                status="failed",
                fact_ids_used=[],
                unverified_claims=[{"error": str(result)}],
            )
            has_warnings = True
        else:
            # 1. Validate Schema
            is_valid, validated_model, schema_err = validate_output_schema(out_type, result)
            if not is_valid:
                gen_out = GeneratedOutput(
                    id=output_id,
                    job_id=job.id,
                    output_type=out_type,
                    content=result if isinstance(result, dict) else {"raw": str(result)},
                    validation_score=0.0,
                    status="failed",
                    fact_ids_used=[],
                    unverified_claims=[{"schema_error": schema_err}],
                )
                has_warnings = True
            else:
                content_dict = validated_model.model_dump()
                # 2. Fact Check against Fact Registry
                val_score, used_ids, unverified = verify_output_facts(content_dict, valid_fact_ids, fact_statements_map)
                out_status = "completed_with_warnings" if unverified or val_score < 0.70 else "completed"
                if unverified or val_score < 0.70:
                    has_warnings = True

                gen_out = GeneratedOutput(
                    id=output_id,
                    job_id=job.id,
                    output_type=out_type,
                    content=content_dict,
                    validation_score=val_score,
                    status=out_status,
                    fact_ids_used=used_ids,
                    unverified_claims=unverified,
                )
                completed_outputs_for_consistency.append({
                    "output_type": out_type,
                    "content": content_dict,
                })

        db.add(gen_out)
        generated_entities.append(gen_out)

    # 3. Cross-Output Consistency Check
    inconsistencies = check_cross_output_consistency(completed_outputs_for_consistency)
    if inconsistencies:
        has_warnings = True
        job.error_message = f"Cross-output consistency warnings detected: {len(inconsistencies)} conflict(s)"
        logger.warning(f"Job {job.id} detected cross-output inconsistencies: {inconsistencies}")

    job.status = (
        JobStatus.COMPLETED_WITH_WARNINGS.value
        if has_warnings
        else JobStatus.COMPLETED.value
    )
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)

    logger.info(f"Finished generation job {job.id} with status: {job.status}")
    return job
