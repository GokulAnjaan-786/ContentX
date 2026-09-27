import logging
import uuid
import zipfile
import io
from typing import Optional, Tuple
try:
    import magic
except Exception:
    magic = None
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.user import User
from app.services.storage_service import storage_service
from app.services.clamav_service import clamav_service
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)

ALLOWED_PDF_MIMES = {"application/pdf"}
ALLOWED_DOCX_MIMES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "application/x-zip-compressed",
}
ALLOWED_TEXT_MIMES = {"text/plain", "text/csv", "application/json"}


def validate_file_content(file_bytes: bytes, filename: str) -> Tuple[SourceType, str]:
    """
    Validate file size, inspect actual magic bytes, and check against virus signatures.

    Returns:
        (SourceType, detected_mime_type)
    """
    # 1. Size limit validation
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB",
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # 2. ClamAV malware scan
    is_clean, virus_name = clamav_service.scan_bytes(file_bytes)
    if not is_clean:
        logger.warning(f"Malware detected in upload '{filename}': {virus_name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload rejected: Potential security threat detected ({virus_name})",
        )

    # 3. Magic MIME type sniffing
    try:
        mime_detector = magic.Magic(mime=True)
        detected_mime = mime_detector.from_buffer(file_bytes)
    except Exception as e:
        logger.error(f"Error detecting MIME type with python-magic: {e}")
        # Fallback to pure header inspection
        if file_bytes.startswith(b"%PDF"):
            detected_mime = "application/pdf"
        elif file_bytes.startswith(b"PK\x03\x04"):
            detected_mime = "application/zip"
        else:
            detected_mime = "application/octet-stream"

    lower_name = filename.lower()

    # Reject dangerous executable types immediately
    dangerous_mimes = {
        "application/x-dosexec",
        "application/x-executable",
        "application/x-sharedlib",
        "application/x-pie-executable",
        "application/x-mach-binary",
        "application/x-msdos-program",
    }
    if detected_mime in dangerous_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File rejected: Executable or binary payload detected ({detected_mime})",
        )

    # Match claimed extension against detected magic
    if lower_name.endswith(".pdf"):
        if detected_mime not in ALLOWED_PDF_MIMES and not file_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension is .pdf but actual content type is '{detected_mime}'. Upload rejected.",
            )
        return SourceType.PDF, detected_mime

    elif lower_name.endswith(".docx"):
        if detected_mime not in ALLOWED_DOCX_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension is .docx but actual content type is '{detected_mime}'. Upload rejected.",
            )
        # Verify internal DOCX structure (word/document.xml inside zip)
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Corrupted or invalid DOCX archive structure.",
                    )
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid zip file for DOCX.",
            )
        return SourceType.DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif lower_name.endswith(".txt"):
        if detected_mime not in ALLOWED_TEXT_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension is .txt but actual content type is '{detected_mime}'.",
            )
        return SourceType.TEXT, detected_mime

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF, DOCX, and TXT are supported.",
        )


def handle_document_upload(
    db: Session,
    current_user: User,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    raw_text: Optional[str] = None,
    sensitivity_flag: str = "internal",
    ip_address: Optional[str] = None,
) -> Document:
    """
    Validate, store in MinIO, record Document entity, write audit log,
    and dispatch Celery background processing task.
    """
    doc_id = uuid.uuid4()

    if raw_text and raw_text.strip():
        # Raw text upload
        content_bytes = raw_text.encode("utf-8")
        if len(content_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Pasted text exceeds maximum allowed size.",
            )

        # ClamAV scan on text bytes
        is_clean, virus_name = clamav_service.scan_bytes(content_bytes)
        if not is_clean:
            create_audit_log(
                db=db,
                action="document_upload_rejected",
                resource_type="document",
                user_id=current_user.id,
                ip_address=ip_address,
                details=f"Infected text rejected: {virus_name}",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Text content rejected: Malicious content detected ({virus_name})",
            )

        source_type = SourceType.TEXT
        mime_type = "text/plain"
        file_name = filename or f"pasted_text_{doc_id.hex[:8]}.txt"
        file_path = f"{current_user.org_id}/{doc_id}/{file_name}"
        storage_service.upload_file(content_bytes, file_path, content_type=mime_type)
        file_size = len(content_bytes)

    elif file_bytes and filename:
        source_type, mime_type = validate_file_content(file_bytes, filename)
        file_name = filename
        file_path = f"{current_user.org_id}/{doc_id}/{file_name}"
        storage_service.upload_file(file_bytes, file_path, content_type=mime_type)
        file_size = len(file_bytes)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file upload or raw_text must be provided.",
        )

    # PII and Prompt Injection scanning
    pii_detected = False
    pii_types = []
    injection_flagged = False
    injection_details = {}

    if raw_text:
        try:
            from app.services.pii_service import scan_text_for_pii
            from ai_services.security.injection_scanner import scan_for_prompt_injection

            pii_res = scan_text_for_pii(raw_text)
            pii_detected = pii_res.pii_detected
            pii_types = pii_res.pii_types

            inj_res = scan_for_prompt_injection(raw_text)
            injection_flagged = inj_res.is_flagged
            injection_details = inj_res.to_dict()
            if injection_flagged:
                logger.warning(f"Uploaded text flagged for prompt injection: {inj_res.detected_patterns}")
        except Exception as scan_err:
            logger.error(f"Error during pre-upload security scan: {scan_err}")

    # Persist document metadata
    doc = Document(
        id=doc_id,
        org_id=current_user.org_id,
        uploaded_by=current_user.id,
        file_path=file_path,
        file_name=file_name,
        file_size_bytes=file_size,
        mime_type=mime_type,
        source_type=source_type,
        sensitivity_flag=sensitivity_flag,
        processed_status=ProcessedStatus.UPLOADED,
        pii_detected=pii_detected,
        pii_types=pii_types,
        injection_flagged=injection_flagged,
        injection_details=injection_details,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Source Document Integrity Anchoring (Part 5)
    try:
        from app.services.trust_chain_service import create_trust_record
        from app.models.trust_record import TrustRecordType

        raw_payload = content_bytes if (raw_text and raw_text.strip()) else file_bytes
        if raw_payload:
            create_trust_record(
                db=db,
                organisation_id=current_user.org_id,
                record_type=TrustRecordType.SOURCE_DOCUMENT,
                content=raw_payload,
                document_id=doc.id,
            )
            logger.info(f"Source document {doc.id} anchored to trust chain")
    except Exception as trust_err:
        logger.error(f"Failed to anchor source document {doc.id} to trust chain: {trust_err}")

    # Record audit log
    create_audit_log(

        db=db,
        action="document_upload",
        resource_type="document",
        resource_id=str(doc.id),
        user_id=current_user.id,
        ip_address=ip_address,
        details=f"File '{file_name}' uploaded. Source type: {source_type}. Status: uploaded",
    )

    # Dispatch background processing task (Celery if Redis is available, or background thread)
    if settings.ENVIRONMENT != "testing":
        from worker.celery_app import is_redis_available
        task_dispatched = False
        if is_redis_available():
            try:
                from worker.tasks import process_document_task
                process_document_task.apply_async(args=[str(doc.id)], retry=False)
                task_dispatched = True
                logger.info(f"Dispatched process_document_task for doc {doc.id} to Celery queue")
            except Exception as e:
                logger.warning(f"Celery task dispatch failed ({e}). Using background thread executor.")

        if not task_dispatched:
            import threading
            from worker.tasks import process_document_task
            logger.info(f"Running process_document_task for doc {doc.id} via background thread executor")
            thread = threading.Thread(target=process_document_task, args=(str(doc.id),), daemon=True)
            thread.start()

    return doc
