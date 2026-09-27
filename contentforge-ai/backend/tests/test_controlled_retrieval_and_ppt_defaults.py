import pytest
import uuid
import asyncio
from app.models.fact_registry import FactRegistry
from app.models.document import Document, SourceType
from app.models.document_chunk import DocumentChunk
from ai_services.orchestrator.context_builder import build_generator_context
from ai_services.generators.presentation_generator import generate_presentation, extract_requested_slide_count
from ai_services.generators.executive_summary_generator import generate_executive_summary
from ai_services.generators.advisory_generator import generate_advisory
from ai_services.generators.linkedin_generator import generate_linkedin_post
from ai_services.understanding.embeddings import generate_and_store_chunk_embeddings, search_relevant_chunks
from ai_services.validation.fact_checker import verify_output_facts, check_cross_output_consistency


@pytest.mark.asyncio
async def test_1_presentation_default_5_slides():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="System telemetry verified 500 nodes active.", importance="high", fact_type="finding"),
        FactRegistry(fact_id_string="f2", fact_statement="Performance improved by 15%.", importance="high", fact_type="statistic")
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "presentation", {})
    ppt = await generate_presentation(formatted_facts, raw_facts, {})

    assert ppt.get("requested_slide_count") == 5
    assert ppt.get("actual_slide_count") == 5
    assert len(ppt.get("slides", [])) == 5


@pytest.mark.asyncio
async def test_2_presentation_custom_8_slides():
    facts = [FactRegistry(fact_id_string="f1", fact_statement="Fact 1", importance="high")]
    formatted_facts, raw_facts = build_generator_context(facts, "presentation", {"slide_count": 8})
    ppt = await generate_presentation(formatted_facts, raw_facts, {"slide_count": 8})

    assert ppt.get("requested_slide_count") == 8
    assert ppt.get("actual_slide_count") == 8
    assert len(ppt.get("slides", [])) == 8


@pytest.mark.asyncio
async def test_3_presentation_natural_language_10_slides():
    facts = [FactRegistry(fact_id_string="f1", fact_statement="Fact 1", importance="high")]
    settings = {"prompt": "Please generate a 10-slide presentation deck."}
    formatted_facts, raw_facts = build_generator_context(facts, "presentation", settings)
    ppt = await generate_presentation(formatted_facts, raw_facts, settings)

    assert ppt.get("requested_slide_count") == 10
    assert ppt.get("actual_slide_count") == 10
    assert len(ppt.get("slides", [])) == 10


@pytest.mark.asyncio
async def test_4_executive_summary_important_facts_only():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="Quarterly revenue reached $10 million with 20% year-over-year growth.", importance="high", fact_type="statistic"),
        FactRegistry(fact_id_string="f2", fact_statement="page 3 of 12 predictions.csv submission instructions", importance="metadata", fact_type="document_metadata")
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "executive_summary", {})
    summary = await generate_executive_summary(formatted_facts, raw_facts, {})
    sum_str = str(summary).lower()

    assert "page 3 of 12" not in sum_str
    assert "predictions.csv" not in sum_str


@pytest.mark.asyncio
async def test_5_advisory_cybersecurity_source_only():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="CVE-2026-9999 allows unauthenticated remote execution in API Gateway.", importance="high", fact_type="incident_finding")
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "advisory", {})
    advisory = await generate_advisory(formatted_facts, raw_facts, {})

    assert "cve-2026-9999" in str(advisory).lower() or "cve" in str(advisory).lower()


@pytest.mark.asyncio
async def test_6_executive_summary_non_cybersecurity():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="Clinical trials evaluated drug sentiment from patient comments across 5,000 samples.", importance="high", fact_type="finding")
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "executive_summary", {})
    summary = await generate_executive_summary(formatted_facts, raw_facts, {})
    sum_str = str(summary).lower()

    assert "cybersecurity" not in sum_str
    assert "operational advisory" not in sum_str


def test_7_bge_m3_and_pgvector_retrieval(db_session, test_user):
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, org_id=test_user.org_id, file_name="test_report.pdf", file_path="/tmp/test.pdf", source_type=SourceType.PDF)
    chunk = DocumentChunk(id=uuid.uuid4(), document_id=doc_id, chunk_index=0, text="Security vulnerabilities were identified in the API Gateway patch 2.4.1.")
    db_session.add(doc)
    db_session.add(chunk)
    db_session.commit()

    count = generate_and_store_chunk_embeddings(db_session, doc_id)
    assert count == 1

    chunks = search_relevant_chunks(db_session, doc_id, query="security vulnerabilities and patches", top_k=3)
    assert len(chunks) == 1
    assert chunks[0].id == chunk.id


def test_8_short_document_embeddings_reuse(db_session, test_user):
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, org_id=test_user.org_id, file_name="test_short.pdf", file_path="/tmp/short.pdf", source_type=SourceType.PDF)
    chunk = DocumentChunk(id=uuid.uuid4(), document_id=doc_id, chunk_index=0, text="Short summary document text.")
    db_session.add(doc)
    db_session.add(chunk)
    db_session.commit()

    count1 = generate_and_store_chunk_embeddings(db_session, doc_id)
    assert count1 == 1

    count2 = generate_and_store_chunk_embeddings(db_session, doc_id)
    assert count2 == 0  # Reused existing embeddings without regenerating


@pytest.mark.asyncio
async def test_9_extraction_noise_protection():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="total marks: 100 submission: code + presentation page 2 of 11", importance="metadata", fact_type="document_metadata"),
        FactRegistry(fact_id_string="f2", fact_statement="Sentiment classification model achieved 94% accuracy.", importance="high", fact_type="statistic")
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    assert "total marks: 100" not in formatted_facts
    assert "page 2 of 11" not in formatted_facts


@pytest.mark.asyncio
async def test_10_certainty_preservation():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="The system update may impact 200 servers.", importance="high", certainty_status="uncertain")
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})
    post_str = (post.get("hook", "") + " " + post.get("body", "")).lower()

    assert "may impact" in post_str or "could impact" in post_str or "unconfirmed" in post_str or "potential" in post_str


@pytest.mark.asyncio
async def test_11_number_preservation():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="Evaluated 10,000 patient records.", importance="high", numbers=["10000"])
    ]
    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})

    assert "10,000" in str(post) or "10000" in str(post)


@pytest.mark.asyncio
async def test_12_cross_output_consistency():
    facts = [
        FactRegistry(fact_id_string="f1", fact_statement="On 2026-04-10, system version 5.0 was released to 300 users.", importance="high", dates=["2026-04-10"], numbers=["5.0", "300"])
    ]

    fmt_ppt, raw_ppt = build_generator_context(facts, "presentation", {})
    fmt_exec, raw_exec = build_generator_context(facts, "executive_summary", {})

    ppt = await generate_presentation(fmt_ppt, raw_ppt, {})
    exec_sum = await generate_executive_summary(fmt_exec, raw_exec, {})

    assert "300" in str(ppt) and "300" in str(exec_sum)
