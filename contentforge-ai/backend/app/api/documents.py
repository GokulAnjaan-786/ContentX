import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_client_ip, get_current_user
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User, UserRole
from app.schemas.document import (
    DocumentChunkOut,
    DocumentChunksListResponse,
    DocumentOut,
    DocumentUploadResponse,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.services.audit_service import create_audit_log
from app.services.document_service import handle_document_upload

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(lambda: settings.RATE_LIMIT_UPLOAD)
async def upload_document(
    request: Request,
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    sensitivity_flag: str = Form("internal"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF, DOCX file or raw text for extraction and chunking.
    Scans for viruses, validates real magic MIME type, stores in MinIO,
    and enqueues background processing task.
    """
    client_ip = get_client_ip(request)
    file_bytes = None
    filename = None

    if file:
        file_bytes = await file.read()
        filename = file.filename

    doc = handle_document_upload(
        db=db,
        current_user=current_user,
        file_bytes=file_bytes,
        filename=filename,
        raw_text=raw_text,
        sensitivity_flag=sensitivity_flag,
        ip_address=client_ip,
    )

    return DocumentUploadResponse(
        document_id=doc.id,
        status=doc.processed_status,
        message="Document uploaded successfully and queued for background processing",
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve document metadata and processing status.
    Tenancy check: users can only access documents in their own organisation
    (unless system_admin).
    """
    query = db.query(Document).filter(Document.id == document_id)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    doc = query.first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )

    return doc


@router.get("/{document_id}/chunks", response_model=DocumentChunksListResponse)
def get_document_chunks(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve all extracted text chunks for a document.
    """
    # Verify document access
    query = db.query(Document).filter(Document.id == document_id)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    doc = query.first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    return DocumentChunksListResponse(
        document_id=doc.id,
        total_chunks=len(chunks),
        chunks=[DocumentChunkOut.model_validate(c) for c in chunks],
    )


@router.post("/{document_id}/understand", status_code=status.HTTP_200_OK)
async def trigger_document_understanding(
    request: Request,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger the single Understanding Pass for a document.
    Extracts summary, entities, topics, document type, and constructs the Fact Registry.
    """
    query = db.query(Document).filter(Document.id == document_id)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    doc = query.first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )

    from ai_services.understanding.fact_extraction import run_understanding_pass
    metadata, facts = await run_understanding_pass(db, doc.id)

    # Record audit log
    create_audit_log(
        db=db,
        action="understanding_pass_triggered",
        resource_type="document",
        resource_id=str(doc.id),
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        details=f"Understanding pass completed for doc '{doc.file_name or doc.id}'. Facts extracted: {len(facts)}.",
    )

    return {
        "document_id": doc.id,
        "status": "understanding_completed",
        "document_type": metadata.document_type,
        "summary": metadata.summary,
        "total_facts": len(facts),
        "entities": metadata.entities,
        "topics": metadata.topics,
    }


@router.get("/{document_id}/facts")
def get_document_facts(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the extracted Fact Registry for a document.
    All downstream generation reads exclusively from these entries.
    """
    query = db.query(Document).filter(Document.id == document_id)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    doc = query.first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )

    from app.models.fact_registry import FactRegistry
    from app.schemas.generation import FactRegistryListResponse, FactRegistryOut

    facts = (
        db.query(FactRegistry)
        .filter(FactRegistry.document_id == document_id)
        .order_by(FactRegistry.fact_id_string.asc())
        .all()
    )

    return FactRegistryListResponse(
        document_id=doc.id,
        total_facts=len(facts),
        facts=[FactRegistryOut.model_validate(f) for f in facts],
    )


@router.get("/{document_id}/integrity")
def check_document_integrity(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check cryptographic integrity of a source document.
    Re-hashes file stored in MinIO and compares against anchored trust record.
    """
    query = db.query(Document).filter(Document.id == document_id)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        query = query.filter(Document.org_id == current_user.org_id)

    doc = query.first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )

    from app.models.trust_record import TrustRecord, TrustRecordType
    from app.services.trust_chain_service import compute_content_hash
    from app.services.storage_service import storage_service

    trust_rec = (
        db.query(TrustRecord)
        .filter(
            TrustRecord.document_id == document_id,
            TrustRecord.record_type == TrustRecordType.SOURCE_DOCUMENT,
        )
        .first()
    )

    current_storage_hash = None
    matches = False
    try:
        raw_bytes = storage_service.download_file(doc.file_path)
        current_storage_hash = compute_content_hash(raw_bytes)
        if trust_rec and trust_rec.content_hash == current_storage_hash:
            matches = True
    except Exception as exc:
        pass

    return {
        "document_id": doc.id,
        "trust_record_id": trust_rec.id if trust_rec else None,
        "chain_index": trust_rec.chain_index if trust_rec else None,
        "anchored_hash": trust_rec.content_hash if trust_rec else None,
        "current_storage_hash": current_storage_hash,
        "matches": matches,
        "record_hash": trust_rec.record_hash if trust_rec else None,
        "created_at": trust_rec.created_at.isoformat() if (trust_rec and trust_rec.created_at) else None,
    }

