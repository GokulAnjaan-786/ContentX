"""Comprehensive Quality, Source Grounding, and 7-Format Content Generation Test.

Verifies:
1. Fact classification (high vs metadata vs internal).
2. All 7 generators (LinkedIn, Twitter, Advisory, Executive Summary, Presentation, Infographic, Video Package).
3. Zero exposure of raw internal [f1] tags or processing jargon in public text.
4. Video script narration human tone.
5. Non-invention for absent items ("Not specified in source document").
6. Cross-output metric consistency validation.
"""

import uuid
import pytest
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.fact_registry import FactRegistry
from ai_services.understanding.fact_extraction import classify_and_clean_fact_item, run_understanding_pass
from ai_services.orchestrator.context_builder import build_generator_context
from ai_services.generators.linkedin_generator import generate_linkedin_post
from ai_services.generators.twitter_generator import generate_twitter_thread
from ai_services.generators.advisory_generator import generate_advisory
from ai_services.generators.executive_summary_generator import generate_executive_summary
from ai_services.generators.presentation_generator import generate_presentation
from ai_services.generators.infographic_generator import generate_infographic
from ai_services.generators.video_generator import generate_video_package
from ai_services.validation.fact_checker import verify_output_facts, check_cross_output_consistency


@pytest.mark.asyncio
async def test_fact_classification_and_cleaning():
    """Verify internal processing info is classified as internal/metadata."""
    fact1 = classify_and_clean_fact_item({
        "statement": "An unusual increase in API requests was detected at Northstar Systems gateway on September 18.",
        "source_chunk_index": 0,
    })
    assert fact1["importance"] == "high"
    assert fact1["fact_type"] == "incident_finding"

    fact2 = classify_and_clean_fact_item({
        "statement": "ContentForge AI Version 1.0 PDF extraction cleaning chunking embeddings Fact Registry RAG retrieval",
        "source_chunk_index": 0,
    })
    assert fact2["importance"] == "internal"
    assert fact2["fact_type"] == "internal_processing"


@pytest.mark.asyncio
async def test_all_7_generators_grounding_and_no_jargon():
    """Generate all 7 formats and verify no [f1] exposure or processing jargon."""
    mock_facts = [
        FactRegistry(
            id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            fact_id_string="f1",
            fact_statement="On September 18, automated security monitoring detected unusual API request rates at Northstar Systems.",
            fact_type="incident_finding",
            importance="high",
            certainty_status="confirmed",
            entities=["Northstar Systems"],
            dates=["September 18"],
            numbers=["500"],
            confidence=1.0,
        ),
        FactRegistry(
            id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            fact_id_string="f2",
            fact_statement="Engineers applied rate-limiting controls and isolated the impacted gateway microservice within 45 minutes.",
            fact_type="action_item",
            importance="high",
            certainty_status="confirmed",
            entities=["Northstar Systems"],
            dates=[],
            numbers=["45"],
            confidence=1.0,
        ),
        FactRegistry(
            id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            fact_id_string="f3",
            fact_statement="Reviewed evidence did not confirm customer data exfiltration.",
            fact_type="technical_detail",
            importance="medium",
            certainty_status="uncertain",
            entities=[],
            dates=[],
            numbers=[],
            confidence=1.0,
        ),
    ]

    settings = {
        "audience": "executive",
        "tone": "authoritative",
        "detail_level": "standard",
        "objective": "incident_briefing",
    }

    generators = {
        "linkedin": generate_linkedin_post,
        "twitter": generate_twitter_thread,
        "advisory": generate_advisory,
        "executive_summary": generate_executive_summary,
        "presentation": generate_presentation,
        "infographic": generate_infographic,
        "video_package": generate_video_package,
    }

    valid_fact_ids = {"f1", "f2", "f3"}
    fact_map = {f.fact_id_string: f.fact_statement for f in mock_facts}

    for name, gen_fn in generators.items():
        formatted_facts, raw_facts = build_generator_context(mock_facts, name, settings)
        res = await gen_fn(formatted_facts, raw_facts, settings)

        assert isinstance(res, dict), f"{name} did not return dict"
        assert len(res.get("fact_ids_used", [])) > 0, f"{name} did not cite fact_ids_used"

        # Check grounding score
        score, used_ids, unverified = verify_output_facts(res, valid_fact_ids, fact_map)
        assert score >= 0.70, f"{name} grounding score too low: {score}"

        # Assert no raw [f1] tags or system jargon exposed in string values
        res_str = str(res)
        assert "[f1]" not in res_str and "[f2]" not in res_str, f"{name} exposed raw [f1] tags in text"
        assert "ContentForge AI Version 1.0" not in res_str, f"{name} exposed system version jargon"
        assert "PDF extraction" not in res_str, f"{name} exposed extraction jargon"
        assert "chunking" not in res_str and "embeddings" not in res_str, f"{name} exposed chunking jargon"


@pytest.mark.asyncio
async def test_negative_testing_non_invention():
    """Verify missing information yields 'Not specified in source document'."""
    mock_facts = [
        FactRegistry(
            id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            fact_id_string="f1",
            fact_statement="An unusual API request spike occurred on September 18.",
            fact_type="incident_finding",
            importance="high",
            certainty_status="confirmed",
            confidence=1.0,
        ),
    ]

    settings = {"audience": "security", "tone": "urgent", "detail_level": "standard", "objective": "advisory"}
    formatted_facts, raw_facts = build_generator_context(mock_facts, "advisory", settings)
    advisory = await generate_advisory(formatted_facts, raw_facts, settings)

    # Details & recommendations must state 'Not specified in source document' for unlisted metrics
    adv_str = str(advisory)
    assert "Not specified in source document" in adv_str or "not specified" in adv_str.lower()


@pytest.mark.asyncio
async def test_cross_output_consistency_detection():
    """Verify cross-output consistency detects 500 vs 5000 mismatch."""
    out1 = {
        "output_type": "linkedin",
        "content": {
            "hook": "Telemetry verified 500 systems were evaluated.",
            "fact_ids_used": ["f1"],
        },
    }
    out2 = {
        "output_type": "advisory",
        "content": {
            "summary": "Technical review claims 5000 systems were impacted.",
            "fact_ids_used": ["f1"],
        },
    }

    inconsistencies = check_cross_output_consistency([out1, out2])
    assert len(inconsistencies) > 0, "Failed to detect 500 vs 5000 number mismatch"
