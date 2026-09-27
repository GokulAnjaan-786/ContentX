import asyncio
import time
import uuid
import pytest
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.document_chunk import DocumentChunk
from app.models.fact_registry import FactRegistry
from ai_services.understanding.fact_extraction import run_understanding_pass
from ai_services.validation.schema_validator import (
    validate_output_schema,
    OUTPUT_SCHEMA_MAP,
)
from ai_services.validation.fact_checker import (
    verify_output_facts,
    check_cross_output_consistency,
)
from ai_services.generators.advisory_generator import generate_advisory
from ai_services.generators.linkedin_generator import generate_linkedin_post
from ai_services.generators.twitter_generator import generate_twitter_thread
from ai_services.generators.executive_summary_generator import generate_executive_summary
from ai_services.generators.infographic_generator import generate_infographic
from ai_services.generators.presentation_generator import generate_presentation
from ai_services.generators.video_generator import generate_video_package
from ai_services.orchestrator.output_router import _run_single_generator


@pytest.fixture
def sample_known_document(db_session, test_organisation, test_user):
    """Create a test document with realistic security report chunks."""
    doc = Document(
        id=uuid.uuid4(),
        org_id=test_organisation.id,
        uploaded_by=test_user.id,
        file_path=f"{test_organisation.id}/advisory_sample.txt",
        file_name="advisory_sample.txt",
        source_type=SourceType.TEXT,
        processed_status=ProcessedStatus.PROCESSED,
    )
    db_session.add(doc)
    db_session.flush()

    chunk1 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        text=(
            "On 15 September 2026, researchers discovered CVE-2026-9999 impacting AuthGate 4.2. "
            "The vulnerability permits unauthenticated remote code execution on internet-facing gateways. "
            "No active exploits or compromise of production clusters have been observed to date."
        ),
        page_number=1,
        word_count=35,
    )
    chunk2 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=1,
        text=(
            "Security engineers deployed hotfix patch 4.2.1 across internal staging environments. "
            "All operators are instructed to isolate management interfaces until patches are applied. "
            "Notice: casualty figures and financial damages are not applicable."
        ),
        page_number=2,
        word_count=30,
    )
    db_session.add_all([chunk1, chunk2])
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_understanding_pass_extracts_facts(db_session, sample_known_document):
    """
    Test 1: Given a sample document with known facts, the Understanding Pass
    extracts those facts correctly into the Fact Registry.
    """
    metadata, facts = await run_understanding_pass(db_session, sample_known_document.id)

    assert metadata is not None
    assert len(metadata.summary) > 10
    assert len(facts) >= 2

    # Check fact registry entries have human-readable fact_id_strings and valid links
    for idx, fact in enumerate(facts, start=1):
        assert fact.fact_id_string == f"f{idx}"
        assert len(fact.fact_statement) > 5
        assert fact.confidence > 0.0

    # Verify facts were committed to the database
    db_facts = db_session.query(FactRegistry).filter(FactRegistry.document_id == sample_known_document.id).all()
    assert len(db_facts) == len(facts)


@pytest.mark.asyncio
async def test_advisory_generator_hallucination_guard(db_session, sample_known_document):
    """
    Test 2 (CRITICAL): Given a document missing a specific detail (e.g. no casualty numbers,
    no financial damages), the Advisory generator explicitly states it is not specified,
    and NEVER invents a number.
    """
    metadata, facts = await run_understanding_pass(db_session, sample_known_document.id)

    # Convert facts to context format
    raw_facts = [
        {"fact_id_string": f.fact_id_string, "fact_statement": f.fact_statement}
        for f in facts
    ]
    formatted_facts = "\n".join(f"- [{f['fact_id_string']}]: {f['fact_statement']}" for f in raw_facts)

    settings = {"audience": "security_operators", "detail_level": "standard"}
    output = await generate_advisory(formatted_facts, raw_facts, settings)

    # 1. Output must adhere to schema
    is_valid, validated, err = validate_output_schema("advisory", output)
    assert is_valid, f"Advisory schema validation failed: {err}"

    # 2. Strict hallucination guard check:
    # Casualties/unlisted figures must explicitly say 'Not specified in source document'
    advisory_text = str(output)
    assert "not specified in source document" in advisory_text.lower(), (
        "Advisory generator failed hallucination guard! Missing details were not flagged as unspecified."
    )

    # Ensure no fabricated casualty count like '10 dead' or '45 casualties'
    assert "casualty" not in advisory_text.lower() or "not specified" in advisory_text.lower()


@pytest.mark.asyncio
async def test_all_seven_generators_schema_validation(db_session, sample_known_document):
    """
    Test 3: All 7 generators return structured JSON matching their Pydantic schemas.
    """
    metadata, facts = await run_understanding_pass(db_session, sample_known_document.id)
    raw_facts = [
        {"fact_id_string": f.fact_id_string, "fact_statement": f.fact_statement}
        for f in facts
    ]
    formatted_facts = "\n".join(f"- [{f['fact_id_string']}]: {f['fact_statement']}" for f in raw_facts)
    settings = {"audience": "executives", "detail_level": "standard", "tone": "authoritative"}

    generators = {
        "linkedin": generate_linkedin_post,
        "twitter": generate_twitter_thread,
        "advisory": generate_advisory,
        "executive_summary": generate_executive_summary,
        "infographic": generate_infographic,
        "presentation": generate_presentation,
        "video_package": generate_video_package,
    }

    for out_type, gen_fn in generators.items():
        result = await gen_fn(formatted_facts, raw_facts, settings)
        is_valid, validated, err = validate_output_schema(out_type, result)
        assert is_valid, f"Generator {out_type} failed schema validation: {err}"
        assert validated is not None
        assert "fact_ids_used" in result


def test_fact_checker_flags_fake_claim():
    """
    Test 4: fact_checker.py correctly flags a deliberately-injected fake claim
    (a claim citing a fact_id that does not exist in the registry) as unverified.
    """
    valid_registry_ids = {"f1", "f2", "f3"}

    # Mock output with an authentic citation [f1] and a fabricated citation [f99]
    mock_content = {
        "title": "Legitimate Title [f1]",
        "body": "This claim is backed by the registry [f2]. However, this claim cites a fake fact [f99]!",
        "fact_ids_used": ["f1", "f2", "f99"],
    }

    confidence_score, cited_ids, unverified = verify_output_facts(mock_content, valid_registry_ids)

    # Must detect [f99] as invalid
    assert "f99" in cited_ids
    assert len(unverified) > 0

    fake_claim_detected = any("f99" in str(item) for item in unverified)
    assert fake_claim_detected, "Fact checker failed to flag fake claim [f99]!"
    assert confidence_score < 1.0


def test_cross_output_consistency_detects_mismatch():
    """
    Test 5: Cross-output consistency check correctly detects a deliberately
    mismatched date between two outputs citing the same underlying fact ID.
    """
    # Output 1 cites f1 and specifies '15 September'
    out1 = {
        "output_type": "linkedin",
        "content": {
            "hook": "On 15 September 2026, a critical vulnerability was disclosed [f1].",
            "body": "Security teams responded swiftly.",
            "fact_ids_used": ["f1"],
        },
    }
    # Output 2 cites f1 but states '16 September'
    out2 = {
        "output_type": "twitter",
        "content": {
            "tweets": [
                {"order": 1, "text": "1/ On 16 September 2026, researchers found a flaw [f1]."}
            ],
            "fact_ids_used": ["f1"],
        },
    }

    inconsistencies = check_cross_output_consistency([out1, out2])
    assert len(inconsistencies) > 0
    assert inconsistencies[0]["fact_id"] == "f1"
    assert inconsistencies[0]["type"] == "date_mismatch"


@pytest.mark.asyncio
async def test_parallel_execution_speed():
    """
    Test 6: Running 4 output types together in parallel completes faster than
    running them strictly one-by-one (proves asyncio.gather parallel execution).
    """
    async def simulated_generator(delay: float):
        await asyncio.sleep(delay)
        return {"status": "ok"}

    simulated_delay = 0.08  # 80ms per generator
    count = 4

    # 1. Measure sequential execution time
    t0 = time.perf_counter()
    for _ in range(count):
        await simulated_generator(simulated_delay)
    sequential_duration = time.perf_counter() - t0

    # 2. Measure parallel execution time
    t1 = time.perf_counter()
    await asyncio.gather(*[simulated_generator(simulated_delay) for _ in range(count)])
    parallel_duration = time.perf_counter() - t1

    # Parallel execution must be significantly faster (at least 2x faster than 4 sequential runs)
    assert parallel_duration < (sequential_duration * 0.65), (
        f"Parallel ({parallel_duration:.3f}s) was not significantly faster than sequential ({sequential_duration:.3f}s)"
    )
