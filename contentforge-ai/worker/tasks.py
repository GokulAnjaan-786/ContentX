import logging
import uuid
from typing import Any, Dict, List

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.document_chunk import DocumentChunk
from app.services.storage_service import storage_service
from ai_services.extraction.pdf_extractor import extract_text_from_pdf
from ai_services.extraction.docx_extractor import extract_text_from_docx
from ai_services.extraction.cleaner import clean_extracted_pages, clean_text
from ai_services.extraction.chunker import chunk_document
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="worker.tasks.process_document_task", max_retries=2)
def process_document_task(self, document_id: str) -> Dict[str, Any]:
    """
    Background worker task to extract, clean, and chunk uploaded documents.
    """
    db = SessionLocal()
    try:
        doc_uuid = uuid.UUID(document_id)
        doc = db.query(Document).filter(Document.id == doc_uuid).first()

        if not doc:
            logger.error(f"Document {document_id} not found in database.")
            return {"status": "error", "message": "Document not found"}

        logger.info(f"Starting background processing for document {doc.id} ({doc.source_type})")
        doc.processed_status = ProcessedStatus.PROCESSING
        db.commit()

        # Retrieve file bytes from storage
        file_bytes = storage_service.download_file(doc.file_path)
        logger.info(f"[1/8] File retrieved from storage for doc {doc.id}")
        chunks_data: List[Dict[str, Any]] = []

        if doc.source_type == SourceType.PDF:
            logger.info(f"[2/8] PDF extraction started for doc {doc.id}")
            raw_pages = extract_text_from_pdf(file_bytes)
            logger.info(f"[3/8] PDF extraction completed ({len(raw_pages)} pages) for doc {doc.id}")
            cleaned_pages = clean_extracted_pages(raw_pages)
            logger.info(f"[4/8] Text cleaning completed for doc {doc.id}")
            chunks_data = chunk_document(
                content=cleaned_pages,
                target_words=settings.CHUNK_SIZE_TARGET,
                overlap_words=settings.CHUNK_OVERLAP,
            )
            logger.info(f"[5/8] Chunking completed ({len(chunks_data)} chunks) for doc {doc.id}")

        elif doc.source_type == SourceType.DOCX:
            logger.info(f"[2/8] DOCX extraction started for doc {doc.id}")
            raw_elements = extract_text_from_docx(file_bytes)
            logger.info(f"[3/8] DOCX extraction completed for doc {doc.id}")
            cleaned_elements = []
            for elem in raw_elements:
                cleaned_val = clean_text(elem["text"])
                if cleaned_val:
                    cleaned_elements.append({
                        **elem,
                        "text": cleaned_val,
                    })
            logger.info(f"[4/8] Text cleaning completed for doc {doc.id}")
            chunks_data = chunk_document(
                content=cleaned_elements,
                target_words=settings.CHUNK_SIZE_TARGET,
                overlap_words=settings.CHUNK_OVERLAP,
            )
            logger.info(f"[5/8] Chunking completed ({len(chunks_data)} chunks) for doc {doc.id}")

        elif doc.source_type == SourceType.TEXT:
            logger.info(f"[2/8] Text ingestion started for doc {doc.id}")
            raw_text = file_bytes.decode("utf-8", errors="replace")
            cleaned_text = clean_text(raw_text)
            logger.info(f"[4/8] Text cleaning completed for doc {doc.id}")
            chunks_data = chunk_document(
                content=cleaned_text,
                target_words=settings.CHUNK_SIZE_TARGET,
                overlap_words=settings.CHUNK_OVERLAP,
            )
            logger.info(f"[5/8] Chunking completed ({len(chunks_data)} chunks) for doc {doc.id}")

        else:
            raise ValueError(f"Unsupported source type: {doc.source_type}")

        # Delete any pre-existing chunks for idempotency / re-runs
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

        # Batch insert chunks
        chunk_entities = [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                text=c["text"],
                page_number=c.get("page_number"),
                section_reference=c.get("section_reference"),
                word_count=c.get("word_count"),
                embedding=None,  # Handled during understanding pass
            )
            for c in chunks_data
        ]
        db.add_all(chunk_entities)

        # Security & Privacy Scans (PII + Prompt Injection)
        try:
            from app.services.pii_service import scan_text_for_pii
            from ai_services.security.injection_scanner import scan_for_prompt_injection

            assembled_text = " ".join([c["text"] for c in chunks_data])
            pii_res = scan_text_for_pii(assembled_text)
            doc.pii_detected = pii_res.pii_detected
            doc.pii_types = pii_res.pii_types

            inj_res = scan_for_prompt_injection(assembled_text)
            doc.injection_flagged = inj_res.is_flagged
            doc.injection_details = inj_res.to_dict()

            if doc.injection_flagged:
                logger.warning(
                    f"Document {doc.id} flagged for prompt injection: "
                    f"{inj_res.detected_patterns} (risk={inj_res.risk_level})"
                )
                try:
                    from app.core.metrics import SECURITY_DETECTIONS
                    SECURITY_DETECTIONS.labels(category="prompt_injection").inc()
                except Exception:
                    pass
            if doc.pii_detected:
                logger.info(f"Document {doc.id} detected with PII types: {doc.pii_types}")
                try:
                    from app.core.metrics import SECURITY_DETECTIONS
                    SECURITY_DETECTIONS.labels(category="pii").inc()
                except Exception:
                    pass

        except Exception as scan_err:
            logger.error(f"Error during post-extraction security scans for doc {doc.id}: {scan_err}")

        # Mark document as processed
        doc.processed_status = ProcessedStatus.PROCESSED
        doc.error_message = None
        db.commit()

        logger.info(
            f"[6/8] Successfully processed document {doc.id}. "
            f"Created {len(chunk_entities)} chunks."
        )

        # Trigger automatic Understanding Pass in non-testing environments
        if settings.ENVIRONMENT != "testing":
            from worker.celery_app import is_redis_available
            task_dispatched = False
            if is_redis_available():
                try:
                    from worker.tasks import understand_document_task
                    understand_document_task.apply_async(args=[str(doc.id)], retry=False)
                    task_dispatched = True
                    logger.info(f"[7/8] Dispatched understanding pass task for doc {doc.id} to Celery")
                except Exception as auto_err:
                    logger.warning(f"Could not auto-trigger understanding pass via Celery ({auto_err}). Running inline.")

            if not task_dispatched:
                try:
                    from worker.tasks import understand_document_task
                    understand_document_task(str(doc.id))
                    logger.info(f"[7/8] Completed inline understanding pass for doc {doc.id}")
                except Exception as sync_err:
                    logger.error(f"Inline understanding pass failed: {sync_err}")

        return {
            "status": "success",
            "document_id": str(doc.id),
            "chunks_count": len(chunk_entities),
            "pii_detected": doc.pii_detected,
            "injection_flagged": doc.injection_flagged,
        }

    except Exception as exc:
        db.rollback()
        logger.exception(f"Error processing document {document_id}: {exc}")
        try:
            # Re-fetch document to mark as failed
            doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
            if doc:
                doc.processed_status = ProcessedStatus.FAILED
                doc.error_message = str(exc)[:1000]
                db.commit()
        except Exception as update_err:
            logger.error(f"Failed to update document error status: {update_err}")

        # Re-raise for Celery task failure tracking
        raise exc

    finally:
        db.close()


@celery_app.task(bind=True, name="worker.tasks.understand_document_task", max_retries=1)
def understand_document_task(self, document_id: str) -> Dict[str, Any]:
    """Celery task to run the single Understanding Pass on a document."""
    import asyncio
    from ai_services.understanding.fact_extraction import run_understanding_pass

    db = SessionLocal()
    try:
        doc_uuid = uuid.UUID(document_id)
        metadata, facts = asyncio.run(run_understanding_pass(db, doc_uuid))
        return {
            "status": "success",
            "document_id": str(doc_uuid),
            "facts_count": len(facts),
            "summary": metadata.summary,
        }
    except Exception as exc:
        logger.exception(f"Understanding pass task failed for document {document_id}: {exc}")
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.tasks.generate_job_task", max_retries=1)
def generate_job_task(self, job_id: str) -> Dict[str, Any]:
    """Celery task to execute parallel generation across requested formats."""
    import asyncio
    from ai_services.orchestrator.output_router import execute_generation_job

    db = SessionLocal()
    try:
        job_uuid = uuid.UUID(job_id)
        job = asyncio.run(execute_generation_job(db, job_uuid))
        return {
            "status": job.status,
            "job_id": str(job.id),
            "outputs_count": len(job.outputs),
        }
    except Exception as exc:
        logger.exception(f"Generation task failed for job {job_id}: {exc}")
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.tasks.enforce_data_retention_task")
def enforce_data_retention_task(self, retention_days: int = None) -> Dict[str, Any]:
    """Scheduled task to purge raw files from MinIO for documents older than threshold."""
    from datetime import datetime, timezone, timedelta
    from app.services.audit_service import create_audit_log

    db = SessionLocal()
    try:
        days = retention_days or getattr(settings, "DATA_RETENTION_DAYS", 90)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        old_docs = (
            db.query(Document)
            .filter(
                Document.created_at < cutoff,
                Document.file_path.isnot(None),
            )
            .all()
        )

        purged_count = 0
        for doc in old_docs:
            try:
                if doc.file_path:
                    storage_service.delete_file(doc.file_path)
                doc.file_path = None
                doc.file_size_bytes = 0

                create_audit_log(
                    db=db,
                    action="data_retention_purge",
                    resource_type="document",
                    resource_id=str(doc.id),
                    details=f"Raw document storage purged after exceeding {days}-day retention policy.",
                )
                purged_count += 1
            except Exception as file_err:
                logger.error(f"Failed to purge raw file for doc {doc.id}: {file_err}")

        db.commit()
        logger.info(f"Data retention policy enforced: purged {purged_count} files older than {cutoff}.")
        return {
            "status": "success",
            "purged_count": purged_count,
            "retention_days": days,
            "cutoff_date": cutoff.isoformat(),
        }
    except Exception as exc:
        db.rollback()
        logger.exception(f"Data retention task failed: {exc}")
        raise exc
    finally:
        db.close()


