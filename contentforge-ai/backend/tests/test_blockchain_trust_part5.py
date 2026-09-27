import hashlib
import json
import uuid
import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.models.approval_signature import ApprovalSignature
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.generated_output import GeneratedOutput
from app.models.generation_job import GenerationJob, JobStatus
from app.models.reviewer_key import ReviewerKey
from app.models.trust_record import TrustRecord, TrustRecordType
from app.models.user import User, UserRole
from app.services.signing_service import verify_signature
from app.services.trust_chain_service import (
    GENESIS_HASH,
    compute_content_hash,
    compute_record_hash,
    create_trust_record,
    verify_chain,
)


def test_document_upload_anchors_trust_record(client, db_session, test_user, auth_headers, sample_pdf_bytes):
    """Uploading a document must automatically anchor a source_document trust record into the hash-chain."""
    response = client.post(
        "/documents/upload",
        files={"file": ("incident_briefing.pdf", sample_pdf_bytes, "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    doc_id = uuid.UUID(data["document_id"])

    # Query trust_records table
    trust_rec = (
        db_session.query(TrustRecord)
        .filter(TrustRecord.document_id == doc_id)
        .first()
    )
    assert trust_rec is not None
    assert trust_rec.record_type == TrustRecordType.SOURCE_DOCUMENT
    assert trust_rec.chain_index == 0
    assert trust_rec.previous_record_hash == GENESIS_HASH
    assert trust_rec.content_hash == hashlib.sha256(sample_pdf_bytes).hexdigest()

    # Recompute record hash and verify
    expected_record_hash = compute_record_hash(
        chain_index=0,
        previous_record_hash=GENESIS_HASH,
        content_hash=trust_rec.content_hash,
        record_type=TrustRecordType.SOURCE_DOCUMENT,
        organisation_id=test_user.org_id,
    )
    assert trust_rec.record_hash == expected_record_hash

    # Verify GET /documents/{id}/integrity
    integ_res = client.get(f"/documents/{doc_id}/integrity", headers=auth_headers)
    assert integ_res.status_code == 200
    integ_data = integ_res.json()
    assert integ_data["matches"] is True
    assert integ_data["anchored_hash"] == trust_rec.content_hash
    assert integ_data["chain_index"] == 0


def test_output_approval_creates_chained_record_and_signature(client, db_session, test_user, auth_headers):
    """Approving an output must anchor it chained to the document, and digitally sign it with Ed25519."""
    # 1. Create document and genesis trust record
    doc = Document(
        id=uuid.uuid4(),
        org_id=test_user.org_id,
        uploaded_by=test_user.id,
        file_path=f"{test_user.org_id}/doc.txt",
        file_name="incident_report.txt",
        file_size_bytes=256,
        mime_type="text/plain",
        source_type=SourceType.TEXT,
        processed_status=ProcessedStatus.PROCESSED,
    )
    db_session.add(doc)
    db_session.commit()

    doc_record = create_trust_record(
        db=db_session,
        organisation_id=test_user.org_id,
        record_type=TrustRecordType.SOURCE_DOCUMENT,
        content="Original source incident content",
        document_id=doc.id,
    )
    assert doc_record.chain_index == 0

    # 2. Create generation job and generated output
    job = GenerationJob(
        id=uuid.uuid4(),
        document_id=doc.id,
        requested_by=test_user.id,
        selected_outputs=["advisory"],
        status=JobStatus.COMPLETED.value,
    )
    db_session.add(job)
    db_session.commit()

    advisory_content = {
        "title": "CRITICAL: Zero-Day Infiltration Advisory",
        "severity": "CRITICAL",
        "scope": "Enterprise Perimeter Gateways",
        "recommended_actions": ["Block egress port 4444", "Rotate master credentials"],
    }
    output = GeneratedOutput(
        id=uuid.uuid4(),
        job_id=job.id,
        output_type="advisory",
        content=advisory_content,
        status="completed",
        validation_score=0.98,
    )
    db_session.add(output)
    db_session.commit()

    # 3. Call approve endpoint
    appr_res = client.post(f"/outputs/{output.id}/approve", headers=auth_headers)
    assert appr_res.status_code == 200
    appr_data = appr_res.json()

    assert appr_data["status"] == "approved"
    assert appr_data["chain_index"] == 1
    assert appr_data["signature"] is not None

    # Check trust record in DB
    output_record = (
        db_session.query(TrustRecord)
        .filter(TrustRecord.output_id == output.id)
        .first()
    )
    assert output_record is not None
    assert output_record.chain_index == 1
    assert output_record.previous_record_hash == doc_record.record_hash
    assert output_record.content_hash == compute_content_hash(advisory_content)

    # Check approval signature in DB
    sig = (
        db_session.query(ApprovalSignature)
        .filter(ApprovalSignature.output_id == output.id)
        .first()
    )
    assert sig is not None
    assert sig.content_hash_signed == output_record.content_hash

    # Check GET /outputs/{output.id}/signature
    sig_res = client.get(f"/outputs/{output.id}/signature", headers=auth_headers)
    assert sig_res.status_code == 200
    sig_data = sig_res.json()
    assert sig_data["has_signature"] is True
    assert sig_data["signature_valid"] is True
    assert sig_data["content_matches_signed_hash"] is True


def test_verify_chain_intact_on_untouched_chain(db_session, test_organisation):
    """verify_chain() must return intact=True and broken_at_index=None on an untouched sequence."""
    org_id = test_organisation.id

    rec0 = create_trust_record(
        db=db_session,
        organisation_id=org_id,
        record_type=TrustRecordType.SOURCE_DOCUMENT,
        content=b"Block 0 initial payload",
    )
    rec1 = create_trust_record(
        db=db_session,
        organisation_id=org_id,
        record_type=TrustRecordType.GENERATED_OUTPUT,
        content={"format": "advisory", "text": "Block 1 content"},
    )
    rec2 = create_trust_record(
        db=db_session,
        organisation_id=org_id,
        record_type=TrustRecordType.GENERATED_OUTPUT,
        content={"format": "exec_summary", "text": "Block 2 content"},
    )

    result = verify_chain(db_session, org_id)
    assert result["intact"] is True
    assert result["total_records"] == 3
    assert result["broken_at_index"] is None
    assert result["latest_record_hash"] == rec2.record_hash


def test_tamper_detection_on_corrupted_historical_record(db_session, test_organisation):
    """CRITICAL TEST: Manually corrupting a historical row in the DB must cause verify_chain()
    to immediately detect the tampering and report the exact break point."""
    org_id = test_organisation.id

    # 1. Build a valid 4-block chain
    for i in range(4):
        create_trust_record(
            db=db_session,
            organisation_id=org_id,
            record_type=TrustRecordType.GENERATED_OUTPUT if i > 0 else TrustRecordType.SOURCE_DOCUMENT,
            content=f"Immutable block data index {i}",
        )

    # Initial verification passes
    initial_check = verify_chain(db_session, org_id)
    assert initial_check["intact"] is True
    assert initial_check["total_records"] == 4

    # 2. Simulate attacker manually altering historical row #1 (e.g., editing database directly)
    tampered_record = (
        db_session.query(TrustRecord)
        .filter(TrustRecord.organisation_id == org_id, TrustRecord.chain_index == 1)
        .first()
    )
    assert tampered_record is not None

    # Attacker alters the content hash without being able to forge the valid chain
    tampered_record.content_hash = "f" * 64
    db_session.commit()

    # 3. Verify that verify_chain() catches the tampering precisely at index 1
    tamper_check = verify_chain(db_session, org_id)
    assert tamper_check["intact"] is False
    assert tamper_check["broken_at_index"] == 1
    assert "Tampered record at index 1" in tamper_check["message"]


def test_public_verification_endpoint_genuine_record_and_no_leakage(client, db_session, test_user):
    """GET /verify/{record_id} must work without authentication, return verification metadata,
    and NEVER leak confidential raw document/output text."""
    secret_internal_text = "CONFIDENTIAL INTERNAL CYBERSECURITY VULNERABILITY CVE-2026-9999 DETAILED EXPLOIT CODE"

    record = create_trust_record(
        db=db_session,
        organisation_id=test_user.org_id,
        record_type=TrustRecordType.SOURCE_DOCUMENT,
        content=secret_internal_text,
    )

    # Public unauthenticated request (no headers)
    response = client.get(f"/verify/{record.id}")
    assert response.status_code == 200
    data = response.json()

    # Verification assertions
    assert data["status"] == "verified"
    assert data["chain_integrity"] == "intact"
    assert data["source_document_verified"] is True
    assert data["chain_index"] == 0
    assert data["content_hash"] == hashlib.sha256(secret_internal_text.encode("utf-8")).hexdigest()

    # CONFIDENTIALITY ASSERTION: Verify raw content is NEVER present anywhere in response JSON
    raw_response_str = json.dumps(data)
    assert secret_internal_text not in raw_response_str
    assert "CONFIDENTIAL" not in raw_response_str
    assert "CVE-2026-9999" not in raw_response_str
    assert "content" not in data
    assert "raw_text" not in data


def test_public_verification_by_content_exact_and_tampered(client, db_session, test_user):
    """POST /verify/by-content must return 'verified' for exact match and 'not_found' for altered content."""
    original_advisory_text = "Threat Actor APT-42 actively targeting unpatched gateway servers."
    tampered_advisory_text = "Threat Actor APT-42 NOT targeting unpatched gateway servers."  # 1 word changed

    create_trust_record(
        db=db_session,
        organisation_id=test_user.org_id,
        record_type=TrustRecordType.SOURCE_DOCUMENT,
        content=original_advisory_text,
    )

    # 1. Exact match test
    exact_res = client.post(
        "/verify/by-content",
        json={"text": original_advisory_text},
    )
    assert exact_res.status_code == 200
    exact_data = exact_res.json()
    assert exact_data["status"] == "verified"
    assert exact_data["chain_integrity"] == "intact"

    # 2. Tampered content test (1 word modified)
    tampered_res = client.post(
        "/verify/by-content",
        json={"text": tampered_advisory_text},
    )
    assert tampered_res.status_code == 200
    tampered_data = tampered_res.json()
    assert tampered_data["status"] == "not_found"
    assert "No matching verified record found" in tampered_data["message"]


def test_independent_ed25519_signature_verification(client, db_session, test_user, auth_headers):
    """Reviewer signature can be independently verified using standard Ed25519 verification."""
    # Setup output and approve it
    doc = Document(
        id=uuid.uuid4(),
        org_id=test_user.org_id,
        uploaded_by=test_user.id,
        file_path="org/doc.txt",
        file_name="doc.txt",
        file_size_bytes=100,
        mime_type="text/plain",
        source_type=SourceType.TEXT,
        processed_status=ProcessedStatus.PROCESSED,
    )
    db_session.add(doc)
    job = GenerationJob(
        id=uuid.uuid4(),
        document_id=doc.id,
        requested_by=test_user.id,
        selected_outputs=["advisory"],
        status=JobStatus.COMPLETED.value,
    )
    db_session.add(job)
    output = GeneratedOutput(
        id=uuid.uuid4(),
        job_id=job.id,
        output_type="advisory",
        content={"bulletin": "Critical patch deployment scheduled."},
        status="completed",
        validation_score=1.0,
    )
    db_session.add(output)
    db_session.commit()

    # Approve
    client.post(f"/outputs/{output.id}/approve", headers=auth_headers)

    # Fetch signature payload
    sig_res = client.get(f"/outputs/{output.id}/signature", headers=auth_headers)
    assert sig_res.status_code == 200
    sig_data = sig_res.json()

    pub_key_hex = sig_data["signer_public_key"]
    signature_hex = sig_data["signature"]
    content_hash = sig_data["content_hash_signed"]

    # 1. Independent verification using python's cryptography library (mimicking third party auditor)
    pub_bytes = bytes.fromhex(pub_key_hex)
    sig_bytes = bytes.fromhex(signature_hex)
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)

    # Must verify successfully with correct data
    public_key.verify(sig_bytes, content_hash.encode("utf-8"))

    # 2. Corrupted data must fail verification
    altered_hash = "0" + content_hash[1:]
    with pytest.raises(InvalidSignature):
        public_key.verify(sig_bytes, altered_hash.encode("utf-8"))


def test_export_embeds_qr_code_and_verification_url(client, db_session, test_user, auth_headers):
    """Exporting an output must return a valid verification URL and base64 PNG QR code."""
    doc = Document(
        id=uuid.uuid4(),
        org_id=test_user.org_id,
        uploaded_by=test_user.id,
        file_path="org/doc.txt",
        file_name="doc.txt",
        file_size_bytes=100,
        mime_type="text/plain",
        source_type=SourceType.TEXT,
        processed_status=ProcessedStatus.PROCESSED,
    )
    db_session.add(doc)
    job = GenerationJob(
        id=uuid.uuid4(),
        document_id=doc.id,
        requested_by=test_user.id,
        selected_outputs=["advisory"],
        status=JobStatus.COMPLETED.value,
    )
    db_session.add(job)
    output = GeneratedOutput(
        id=uuid.uuid4(),
        job_id=job.id,
        output_type="advisory",
        content={"title": "Official Advisory"},
        status="completed",
        validation_score=1.0,
    )
    db_session.add(output)
    db_session.commit()

    export_res = client.get(f"/outputs/{output.id}/export", headers=auth_headers)
    assert export_res.status_code == 200
    export_data = export_res.json()

    assert "trust_record_id" in export_data
    assert "verification_url" in export_data
    assert export_data["verification_url"].endswith(f"/verify/{export_data['trust_record_id']}")
    assert export_data["verification_notice"].startswith("Scan to verify authenticity")
    assert export_data["qr_code_base64"].startswith("data:image/png;base64,")


def test_admin_trust_chain_verify_endpoint(client, test_admin_user, admin_auth_headers, test_user, auth_headers):
    """Admin endpoint /admin/trust-chain/verify must allow admins and reject non-admins."""
    # Admin request
    admin_res = client.get("/admin/trust-chain/verify", headers=admin_auth_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert "intact" in data
    assert data["intact"] is True

    # Operator request
    op_res = client.get("/admin/trust-chain/verify", headers=auth_headers)
    assert op_res.status_code == 403
