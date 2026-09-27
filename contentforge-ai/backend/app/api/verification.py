import hashlib
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.approval_signature import ApprovalSignature
from app.models.trust_record import TrustRecord, TrustRecordType
from app.models.user import User, UserRole
from app.services.trust_chain_service import compute_content_hash, verify_chain

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Public Verification"])


class ContentVerifyPayload(BaseModel):
    text: Optional[str] = None


def _format_verification_response(db: Session, record: TrustRecord) -> dict:
    """Format verification metadata ensuring ZERO confidential text is ever returned."""
    chain_res = verify_chain(db, record.organisation_id)
    if not chain_res["intact"]:
        chain_integrity = f"broken_at_index_{chain_res['broken_at_index']}"
        status_val = "chain_broken"
    else:
        chain_integrity = "intact"
        status_val = "verified"

    # Source document verification check
    source_document_verified = False
    if record.record_type == TrustRecordType.GENERATED_OUTPUT and record.document_id:
        doc_trust = (
            db.query(TrustRecord)
            .filter(
                TrustRecord.document_id == record.document_id,
                TrustRecord.record_type == TrustRecordType.SOURCE_DOCUMENT,
            )
            .first()
        )
        source_document_verified = doc_trust is not None
    elif record.record_type == TrustRecordType.SOURCE_DOCUMENT:
        source_document_verified = True

    # Reviewer digital signature & approver info
    approved_by = None
    approved_at = None
    if record.output_id:
        sig = (
            db.query(ApprovalSignature)
            .filter(ApprovalSignature.output_id == record.output_id)
            .order_by(ApprovalSignature.signed_at.desc())
            .first()
        )
        if sig:
            if sig.reviewer:
                approved_by = getattr(sig.reviewer, "full_name", None) or sig.reviewer.email
            else:
                approved_by = "Authorized Security Reviewer"
            approved_at = sig.signed_at.isoformat() if sig.signed_at else None


    org_name = record.organisation.name if record.organisation else "Verified Organisation"
    output_type = None
    if record.output:
        output_type = record.output.output_type
    elif record.record_type == TrustRecordType.SOURCE_DOCUMENT:
        output_type = "source_document"

    type_val = record.record_type.value if hasattr(record.record_type, "value") else str(record.record_type)

    return {
        "status": status_val,
        "record_id": str(record.id),
        "record_type": type_val,
        "organisation_name": org_name,
        "output_type": output_type,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "source_document_verified": source_document_verified,
        "chain_integrity": chain_integrity,
        "chain_index": record.chain_index,
        "record_hash": record.record_hash,
        "content_hash": record.content_hash,
        "public_anchor_tx_hash": record.public_anchor_tx_hash,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.get("/verify/{record_id}")
def verify_record_public(
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Public verification endpoint (NO authentication required).
    Returns cryptographic integrity and provenance metadata for a trust record.
    Never returns raw document or output content.
    """
    record = db.query(TrustRecord).filter(TrustRecord.id == record_id).first()
    if not record:
        return {
            "status": "not_found",
            "record_id": str(record_id),
            "message": "No matching verified trust record found for this identifier.",
        }

    return _format_verification_response(db, record)


@router.post("/verify/by-content")
async def verify_by_content_public(
    request: Request,
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Public verification endpoint by content hash (NO authentication required).
    Accepts raw text or uploaded file, computes its SHA-256 hash, and verifies
    whether it exactly matches an officially anchored trust record.
    """
    content_bytes = b""
    content_str = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            content_str = body.get("text", "")
            content_bytes = content_str.encode("utf-8")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    elif file:
        content_bytes = await file.read()
    elif raw_text is not None:
        content_bytes = raw_text.encode("utf-8")
        content_str = raw_text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'file', 'raw_text', or JSON body {'text': '...'} must be provided.",
        )

    # 1. Compute hash of raw bytes
    raw_hash = hashlib.sha256(content_bytes).hexdigest()

    # 2. Also test if content_str is JSON or normal text
    parsed_json_hash = None
    if content_str:
        try:
            parsed = json.loads(content_str)
            parsed_json_hash = compute_content_hash(parsed)
        except Exception:
            pass

    # Search for matching trust record
    record = (
        db.query(TrustRecord)
        .filter(
            (TrustRecord.content_hash == raw_hash)
            | (TrustRecord.content_hash == parsed_json_hash if parsed_json_hash else False)
        )
        .order_by(TrustRecord.created_at.desc())
        .first()
    )

    if not record:
        return {
            "status": "not_found",
            "computed_hash": raw_hash,
            "message": "No matching verified record found. This content is either altered, unofficial, or unanchored.",
        }

    return _format_verification_response(db, record)


@router.get("/admin/trust-chain/verify")
def admin_verify_trust_chain(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin-only live audit check: walks and cryptographically recalculates
    every hash link in the organization's hash chain.
    """
    if current_user.role not in (UserRole.ORG_ADMIN, UserRole.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can run full trust-chain audits",
        )


    org_id = current_user.org_id
    result = verify_chain(db, org_id)

    org_name = current_user.organisation.name if current_user.organisation else "Organisation"
    return {
        "organisation_id": str(org_id),
        "organisation_name": org_name,
        "intact": result["intact"],
        "total_records": result["total_records"],
        "broken_at_index": result["broken_at_index"],
        "latest_record_hash": result["latest_record_hash"],
        "message": result["message"],
    }
