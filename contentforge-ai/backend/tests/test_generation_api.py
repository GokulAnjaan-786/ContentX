import uuid
import pytest
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.document_chunk import DocumentChunk
from app.models.fact_registry import FactRegistry
from app.models.generation_job import GenerationJob, JobStatus


@pytest.fixture
def document_with_chunks(db_session, test_organisation, test_user):
    doc = Document(
        id=uuid.uuid4(),
        org_id=test_organisation.id,
        uploaded_by=test_user.id,
        file_path=f"{test_organisation.id}/briefing.txt",
        file_name="briefing.txt",
        source_type=SourceType.TEXT,
        processed_status=ProcessedStatus.PROCESSED,
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        text="ContentForge AI enforces single understanding pass and shared Fact Registry for all downstream generators.",
        page_number=1,
        word_count=15,
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(doc)
    return doc


def test_understanding_pass_api_and_facts_retrieval(client, auth_headers, document_with_chunks):
    """
    Test POST /documents/{id}/understand triggers understanding pass,
    and GET /documents/{id}/facts returns the populated Fact Registry.
    """
    doc_id = str(document_with_chunks.id)

    # 1. Trigger Understanding Pass
    resp = client.post(f"/documents/{doc_id}/understand", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "understanding_completed"
    assert data["total_facts"] >= 1
    assert "summary" in data

    # 2. Retrieve Fact Registry via GET /documents/{id}/facts
    facts_resp = client.get(f"/documents/{doc_id}/facts", headers=auth_headers)
    assert facts_resp.status_code == 200
    facts_data = facts_resp.json()
    assert facts_data["document_id"] == doc_id
    assert facts_data["total_facts"] >= 1
    assert len(facts_data["facts"]) >= 1

    first_fact = facts_data["facts"][0]
    assert first_fact["fact_id_string"].startswith("f")
    assert len(first_fact["fact_statement"]) > 0


def test_generation_workflow_api(client, auth_headers, document_with_chunks):
    """
    End-to-end test of:
    - POST /generate
    - GET /generation/{job_id}
    - GET /generation/{job_id}/outputs
    - GET /outputs/{output_id}
    """
    doc_id = str(document_with_chunks.id)

    # 1. Enqueue generation job for 3 formats
    gen_payload = {
        "document_id": doc_id,
        "selected_outputs": ["linkedin", "advisory", "executive_summary"],
        "settings": {
            "audience": "executive",
            "tone": "authoritative",
            "detail_level": "standard",
        },
    }
    gen_resp = client.post("/generate", json=gen_payload, headers=auth_headers)
    assert gen_resp.status_code == 202
    gen_data = gen_resp.json()
    assert "job_id" in gen_data
    job_id = gen_data["job_id"]

    # 2. Check job status via GET /generation/{job_id}
    status_resp = client.get(f"/generation/{job_id}", headers=auth_headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["id"] == job_id
    assert status_data["status"] in ("completed", "completed_with_warnings", "queued", "processing")

    # 3. Retrieve all outputs via GET /generation/{job_id}/outputs
    outputs_resp = client.get(f"/generation/{job_id}/outputs", headers=auth_headers)
    assert outputs_resp.status_code == 200
    outputs_data = outputs_resp.json()
    assert outputs_data["total_outputs"] == 3
    assert len(outputs_data["outputs"]) == 3

    # Check validation scores and format types
    output_types = [o["output_type"] for o in outputs_data["outputs"]]
    assert "linkedin" in output_types
    assert "advisory" in output_types
    assert "executive_summary" in output_types

    first_output = outputs_data["outputs"][0]
    output_id = first_output["id"]
    assert first_output["validation_score"] >= 0.0
    assert len(first_output["fact_ids_used"]) > 0

    # 4. Fetch single output detail via GET /outputs/{output_id}
    single_resp = client.get(f"/outputs/{output_id}", headers=auth_headers)
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["id"] == output_id
    assert single_data["output_type"] == first_output["output_type"]
    assert "content" in single_data
    assert "fact_ids_used" in single_data
