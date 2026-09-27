import os
import sys
import uuid
from typing import List, Optional

# Ensure ROOT_DIR (contentforge-ai) is on sys.path for ai_services imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
for p in [BASE_DIR, ROOT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.api.deps import get_client_ip, get_current_user
from app.models.document import Document
from app.models.fact_registry import FactRegistry
from app.models.generation_job import GenerationJob, JobStatus
from app.models.generated_output import GeneratedOutput
from app.models.user import User, UserRole
from app.schemas.generation import (
    GeneratedOutputOut,
    GenerationJobResponse,
    GenerationJobStatusResponse,
    GenerationOutputsListResponse,
    GenerationRequest,
    OutputUpdateRequest,
    HistoryItemOut,
)
from app.services.audit_service import create_audit_log

router = APIRouter(tags=["Generation"])


@router.post("/generate", response_model=GenerationJobResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERATE)
async def create_generation_job(
    request: Request,
    payload: GenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enqueue a multi-format content generation job.
    Reads exclusively from the document's Fact Registry.
    """
    client_ip = get_client_ip(request)

    # 1. Verify document access
    query = db.query(Document).filter(Document.id == payload.document_id)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    doc = query.first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{payload.document_id}' not found",
        )

    # 2. Check if Fact Registry exists, else trigger Understanding Pass
    fact_count = db.query(FactRegistry).filter(FactRegistry.document_id == doc.id).count()
    if fact_count == 0:
        from ai_services.understanding.fact_extraction import run_understanding_pass
        await run_understanding_pass(db, doc.id)

    # 3. Create GenerationJob entity
    job_id = uuid.uuid4()
    job_settings = payload.settings or {}
    if payload.selected_audiences:
        job_settings["selected_audiences"] = payload.selected_audiences

    job = GenerationJob(
        id=job_id,
        document_id=doc.id,
        requested_by=current_user.id,
        selected_outputs=payload.selected_outputs,
        settings=job_settings,
        status=JobStatus.QUEUED.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Record audit log
    create_audit_log(
        db=db,
        action="generation_job_created",
        resource_type="generation_job",
        resource_id=str(job.id),
        user_id=current_user.id,
        ip_address=client_ip,
        details=f"Job queued for outputs: {payload.selected_outputs}",
    )

    # Dispatch Celery background task if Redis is available, else execute inline
    if settings.ENVIRONMENT != "testing":
        from worker.celery_app import is_redis_available
        task_dispatched = False
        if is_redis_available():
            try:
                from worker.tasks import generate_job_task
                generate_job_task.delay(str(job.id))
                task_dispatched = True
            except Exception as e:
                logger.warning(f"Celery dispatch failed for job {job.id} ({e}). Executing inline.")
        if not task_dispatched:
            from ai_services.orchestrator.output_router import execute_generation_job
            await execute_generation_job(db, job.id)
    else:
        # In testing environment, run synchronously for instant verification
        from ai_services.orchestrator.output_router import execute_generation_job
        await execute_generation_job(db, job.id)

    return GenerationJobResponse(
        job_id=job.id,
        document_id=job.document_id,
        status=job.status,
        selected_outputs=job.selected_outputs,
        message="Generation job created successfully and queued for parallel processing",
    )


@router.get("/generation/{job_id}", response_model=GenerationJobStatusResponse)
def get_generation_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve status and metadata of a generation job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job '{job_id}' not found",
        )

    # Tenancy check
    if current_user.role != UserRole.SYSTEM_ADMIN and job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found")

    return job


@router.get("/generation/{job_id}/outputs", response_model=GenerationOutputsListResponse)
def get_generation_job_outputs(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all generated outputs and their validation scores for a job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job '{job_id}' not found",
        )

    if current_user.role != UserRole.SYSTEM_ADMIN and job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found")

    outputs = (
        db.query(GeneratedOutput)
        .filter(GeneratedOutput.job_id == job_id)
        .order_by(GeneratedOutput.created_at.asc())
        .all()
    )

    return GenerationOutputsListResponse(
        job_id=job.id,
        total_outputs=len(outputs),
        outputs=[GeneratedOutputOut.model_validate(o) for o in outputs],
    )


@router.get("/outputs/{output_id}", response_model=GeneratedOutputOut)
def get_single_output(
    output_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve single generated output detail, including which fact_ids
    were used for end-to-end traceability back to the source document.
    """
    output = db.query(GeneratedOutput).filter(GeneratedOutput.id == output_id).first()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated output '{output_id}' not found",
        )

    if current_user.role != UserRole.SYSTEM_ADMIN and output.job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated output not found")

    return output


@router.put("/outputs/{output_id}", response_model=GeneratedOutputOut)
def update_generated_output(
    request: Request,
    output_id: uuid.UUID,
    payload: OutputUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update generated output content (operator inline edit before review/export)."""
    output = db.query(GeneratedOutput).filter(GeneratedOutput.id == output_id).first()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated output '{output_id}' not found",
        )

    if current_user.role != UserRole.SYSTEM_ADMIN and output.job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated output not found")

    # Update content
    output.content = payload.content
    db.commit()
    db.refresh(output)

    # Record audit log
    create_audit_log(
        db=db,
        action="output_edited",
        resource_type="output",
        resource_id=str(output.id),
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        details=f"Output {output.output_type} edited for job {output.job_id}.",
    )

    return output


@router.post("/outputs/{output_id}/approve")
def approve_generated_output(
    request: Request,
    output_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Approve an output: marks status as approved, cryptographically hashes final content,
    creates a chained trust record linking to the source document, and generates
    an Ed25519 digital signature from the approving reviewer.
    """
    output = db.query(GeneratedOutput).filter(GeneratedOutput.id == output_id).first()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated output '{output_id}' not found",
        )

    if current_user.role != UserRole.SYSTEM_ADMIN and output.job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated output not found")

    output.status = "approved"
    db.commit()
    db.refresh(output)

    from app.models.trust_record import TrustRecord, TrustRecordType
    from app.services.trust_chain_service import create_trust_record, compute_content_hash
    from app.services.signing_service import sign_content_hash

    content_hash = compute_content_hash(output.content)

    trust_rec = (
        db.query(TrustRecord)
        .filter(TrustRecord.output_id == output.id)
        .first()
    )
    if not trust_rec:
        trust_rec = create_trust_record(
            db=db,
            organisation_id=output.job.document.org_id,
            record_type=TrustRecordType.GENERATED_OUTPUT,
            content=output.content,
            document_id=output.job.document_id,
            output_id=output.id,
        )

    approval_sig = sign_content_hash(
        db=db,
        reviewer_id=current_user.id,
        output_id=output.id,
        content_hash=content_hash,
    )

    create_audit_log(
        db=db,
        action="output_approved",
        resource_type="output",
        resource_id=str(output.id),
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        details=f"Output {output.output_type} approved by {current_user.email}. Signed hash: {content_hash[:12]}...",
    )

    return {
        "output_id": str(output.id),
        "status": output.status,
        "trust_record_id": str(trust_rec.id),
        "chain_index": trust_rec.chain_index,
        "content_hash": trust_rec.content_hash,
        "record_hash": trust_rec.record_hash,
        "reviewer_id": str(current_user.id),
        "reviewer_name": getattr(current_user, "full_name", None) or current_user.email,
        "signature": approval_sig.signature,
        "signed_at": approval_sig.signed_at.isoformat(),
        "message": "Output approved, cryptographically anchored, and digitally signed.",
    }


@router.get("/outputs/{output_id}/signature")
def get_output_signature(
    output_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve digital signature, signer's public key, and timestamp for an output,
    allowing independent cryptographic verification.
    """
    output = db.query(GeneratedOutput).filter(GeneratedOutput.id == output_id).first()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated output '{output_id}' not found",
        )

    if current_user.role != UserRole.SYSTEM_ADMIN and output.job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated output not found")

    from app.models.approval_signature import ApprovalSignature
    from app.models.reviewer_key import ReviewerKey
    from app.services.trust_chain_service import compute_content_hash
    from app.services.signing_service import verify_signature

    sig = (
        db.query(ApprovalSignature)
        .filter(ApprovalSignature.output_id == output_id)
        .order_by(ApprovalSignature.signed_at.desc())
        .first()
    )

    if not sig:
        return {
            "output_id": str(output.id),
            "has_signature": False,
            "signature": None,
            "signer_public_key": None,
            "signer_name": None,
            "signed_at": None,
            "content_hash_signed": None,
            "signature_valid": False,
        }

    rev_key = db.query(ReviewerKey).filter(ReviewerKey.user_id == sig.reviewer_id).first()
    public_key = rev_key.public_key if rev_key else None
    current_content_hash = compute_content_hash(output.content)
    is_valid = False
    if public_key:
        is_valid = verify_signature(public_key, sig.content_hash_signed, sig.signature)

    reviewer_display = "Reviewer"
    if sig.reviewer:
        reviewer_display = getattr(sig.reviewer, "full_name", None) or sig.reviewer.email

    return {
        "output_id": str(output.id),
        "has_signature": True,
        "signature": sig.signature,
        "signer_public_key": public_key,
        "signer_name": reviewer_display,
        "signed_at": sig.signed_at.isoformat(),
        "content_hash_signed": sig.content_hash_signed,
        "current_content_hash": current_content_hash,
        "content_matches_signed_hash": (sig.content_hash_signed == current_content_hash),
        "signature_valid": is_valid,
    }



@router.get("/outputs/{output_id}/export")
def export_generated_output(
    request: Request,
    output_id: uuid.UUID,
    format: str = "text",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export single output payload with embedded verification QR code and audit event."""
    output = db.query(GeneratedOutput).filter(GeneratedOutput.id == output_id).first()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated output '{output_id}' not found",
        )

    if current_user.role != UserRole.SYSTEM_ADMIN and output.job.document.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated output not found")

    from app.models.trust_record import TrustRecord, TrustRecordType
    from app.services.trust_chain_service import create_trust_record
    from app.services.qr_service import generate_qr_code_base64

    # Ensure output has a trust record
    trust_rec = (
        db.query(TrustRecord)
        .filter(TrustRecord.output_id == output.id)
        .first()
    )
    if not trust_rec:
        trust_rec = create_trust_record(
            db=db,
            organisation_id=output.job.document.org_id,
            record_type=TrustRecordType.GENERATED_OUTPUT,
            content=output.content,
            document_id=output.job.document_id,
            output_id=output.id,
        )

    verification_url = f"{settings.FRONTEND_URL}/verify/{trust_rec.id}"
    short_id = str(trust_rec.id)[:8]
    verification_notice = f"Scan to verify authenticity — contentforge.ai/verify/{short_id}"
    qr_code_b64 = generate_qr_code_base64(verification_url)

    create_audit_log(
        db=db,
        action="output_exported",
        resource_type="output",
        resource_id=str(output.id),
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        details=f"Output {output.output_type} exported as format: {format}. TrustRecord: {trust_rec.id}",
    )

    return {
        "output_id": str(output.id),
        "output_type": output.output_type,
        "format": format,
        "content": output.content,
        "exported_at": output.created_at.isoformat(),
        "trust_record_id": str(trust_rec.id),
        "chain_index": trust_rec.chain_index,
        "verification_url": verification_url,
        "verification_notice": verification_notice,
        "qr_code_base64": qr_code_b64,
    }



@router.get("/history", response_model=List[HistoryItemOut])
def get_transformation_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve transformation history for the user's organization."""
    query = (
        db.query(GenerationJob)
        .join(Document, GenerationJob.document_id == Document.id)
        .order_by(GenerationJob.created_at.desc())
    )

    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    jobs = query.limit(limit).all()

    return [
        HistoryItemOut(
            id=j.id,
            job_id=j.id,
            document_id=j.document_id,
            document_title=j.document.file_name or f"Document {j.document_id.hex[:8]}",
            status=j.status,
            selected_outputs=j.selected_outputs,
            created_at=j.created_at,
        )
        for j in jobs
    ]

