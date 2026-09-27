import io
import uuid
import pytest
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.document_chunk import DocumentChunk
from app.models.audit_log import AuditLog
from worker.tasks import process_document_task


def test_upload_valid_pdf_and_process_to_chunks(client, auth_headers, sample_pdf_bytes, db_session):
    """
    Uploading a valid PDF creates a Document with status 'uploaded'.
    Executing the worker task extracts, cleans, chunks, and updates status to 'processed'.
    """
    files = {
        "file": ("quarterly_report.pdf", sample_pdf_bytes, "application/pdf")
    }
    data = {"sensitivity_flag": "confidential"}

    response = client.post("/documents/upload", headers=auth_headers, files=files, data=data)
    assert response.status_code == 202
    resp_data = response.json()
    assert "document_id" in resp_data
    assert resp_data["status"] == "uploaded"

    doc_id = resp_data["document_id"]

    # Verify document exists in DB with status 'uploaded'
    doc = db_session.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
    assert doc is not None
    assert doc.file_name == "quarterly_report.pdf"
    assert doc.source_type == SourceType.PDF

    # Verify audit log was written for upload
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.resource_id == doc_id, AuditLog.action == "document_upload")
        .first()
    )
    assert audit is not None

    # Execute worker processing task
    task_result = process_document_task(doc_id)
    assert task_result["status"] == "success"
    assert task_result["chunks_count"] > 0

    # Refresh document state
    db_session.refresh(doc)
    assert doc.processed_status == ProcessedStatus.PROCESSED
    assert doc.error_message is None

    # Verify document_chunks rows were created
    chunks = (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.document_id == uuid.UUID(doc_id))
        .all()
    )
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.text) > 0
        assert chunk.word_count is not None
        assert chunk.word_count > 0
        assert chunk.embedding is None  # Left nullable for Part 2

    # Verify GET /documents/{id} returns metadata and processed status
    get_doc_resp = client.get(f"/documents/{doc_id}", headers=auth_headers)
    assert get_doc_resp.status_code == 200
    doc_meta = get_doc_resp.json()
    assert doc_meta["id"] == doc_id
    assert doc_meta["processed_status"] == "processed"
    assert doc_meta["source_type"] == "pdf"

    # Verify GET /documents/{id}/chunks returns the chunks
    get_chunks_resp = client.get(f"/documents/{doc_id}/chunks", headers=auth_headers)
    assert get_chunks_resp.status_code == 200
    chunks_data = get_chunks_resp.json()
    assert chunks_data["document_id"] == doc_id
    assert chunks_data["total_chunks"] == len(chunks)
    assert len(chunks_data["chunks"]) == len(chunks)


def test_upload_fake_extension_rejected_by_magic(client, auth_headers, fake_pdf_bytes):
    """
    Uploading a disguised file (an executable renamed to .pdf) must be rejected
    by python-magic file validation with HTTP 400.
    """
    files = {
        "file": ("malicious_payload.pdf", fake_pdf_bytes, "application/pdf")
    }
    response = client.post("/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "rejected" in detail.lower() or "executable" in detail.lower() or "actual content type" in detail.lower()


def test_upload_oversized_file_rejected(client, auth_headers):
    """
    Uploading a file exceeding the 20MB limit is rejected with HTTP 413.
    """
    # 21 MB payload
    oversized_data = b"0" * (21 * 1024 * 1024)
    files = {
        "file": ("huge_file.pdf", oversized_data, "application/pdf")
    }
    response = client.post("/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"]


def test_upload_virus_signature_rejected_by_clamav(client, auth_headers, eicar_virus_bytes, db_session):
    """
    Uploading a file containing an infected virus signature (EICAR) is detected and rejected.
    """
    files = {
        "file": ("eicar_test.txt", eicar_virus_bytes, "text/plain")
    }
    response = client.post("/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 400
    assert "threat" in response.json()["detail"].lower() or "malware" in response.json()["detail"].lower()


def test_upload_raw_text_and_process(client, auth_headers, db_session):
    """
    Uploading pasted raw text creates a document and chunks accurately.
    """
    raw_content = (
        "ContentForge AI transforms unstructured reports into synchronized executive summaries, "
        "LinkedIn posts, and infographics. Every assertion is referenced to its original context."
    )
    data = {
        "raw_text": raw_content,
        "sensitivity_flag": "internal",
    }
    response = client.post("/documents/upload", headers=auth_headers, data=data)
    assert response.status_code == 202
    doc_id = response.json()["document_id"]

    # Process task
    task_res = process_document_task(doc_id)
    assert task_res["status"] == "success"

    # Verify chunks
    chunks = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == uuid.UUID(doc_id)).all()
    assert len(chunks) == 1
    assert "ContentForge AI transforms" in chunks[0].text
