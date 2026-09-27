import hashlib
import json
import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trust_record import TrustRecord, TrustRecordType

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64


def compute_content_hash(content: Union[str, bytes, dict, list]) -> str:
    """Compute deterministic SHA-256 hash of content.

    - bytes: hashed directly
    - str: encoded as UTF-8 then hashed
    - dict/list: normalized into canonical sorted JSON (no extra whitespace) then hashed
    """
    if isinstance(content, bytes):
        raw_bytes = content
    elif isinstance(content, str):
        raw_bytes = content.encode("utf-8")
    elif isinstance(content, (dict, list)):
        raw_bytes = json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        raw_bytes = str(content).encode("utf-8")

    return hashlib.sha256(raw_bytes).hexdigest()


def compute_record_hash(
    chain_index: int,
    previous_record_hash: str,
    content_hash: str,
    record_type: Union[TrustRecordType, str],
    organisation_id: Union[UUID, str],
) -> str:
    """Compute the tamper-evident hash for a trust record.

    Cryptographically binds:
    (chain_index || previous_record_hash || content_hash || record_type || organisation_id)
    """
    type_str = record_type.value if hasattr(record_type, "value") else str(record_type)
    org_str = str(organisation_id)
    payload = f"{chain_index}:{previous_record_hash}:{content_hash}:{type_str}:{org_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_trust_record(
    db: Session,
    organisation_id: UUID,
    record_type: TrustRecordType,
    content: Union[str, bytes, dict, list],
    document_id: Optional[UUID] = None,
    output_id: Optional[UUID] = None,
) -> TrustRecord:
    """Append a new tamper-evident record to the organisation's hash-chain."""
    content_hash = compute_content_hash(content)

    # Get the latest record in the organisation's chain
    latest = (
        db.query(TrustRecord)
        .filter(TrustRecord.organisation_id == organisation_id)
        .order_by(TrustRecord.chain_index.desc())
        .first()
    )

    if latest is None:
        chain_index = 0
        previous_record_hash = GENESIS_HASH
    else:
        chain_index = latest.chain_index + 1
        previous_record_hash = latest.record_hash

    record_hash = compute_record_hash(
        chain_index=chain_index,
        previous_record_hash=previous_record_hash,
        content_hash=content_hash,
        record_type=record_type,
        organisation_id=organisation_id,
    )

    record = TrustRecord(
        organisation_id=organisation_id,
        record_type=record_type,
        document_id=document_id,
        output_id=output_id,
        chain_index=chain_index,
        content_hash=content_hash,
        previous_record_hash=previous_record_hash,
        record_hash=record_hash,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        f"Created TrustRecord #{chain_index} for org {organisation_id} "
        f"[type={record_type}, hash={record_hash[:12]}...]"
    )
    return record


def verify_chain(db: Session, organisation_id: UUID) -> Dict[str, Any]:
    """Walk and verify the cryptographic integrity of an organisation's entire hash-chain.

    Returns:
        {
            "intact": bool,
            "total_records": int,
            "broken_at_index": Optional[int],
            "message": str,
            "latest_record_hash": Optional[str]
        }
    """
    records = (
        db.query(TrustRecord)
        .filter(TrustRecord.organisation_id == organisation_id)
        .order_by(TrustRecord.chain_index.asc())
        .all()
    )

    if not records:
        return {
            "intact": True,
            "total_records": 0,
            "broken_at_index": None,
            "latest_record_hash": None,
            "message": "Chain is empty (no records anchored yet).",
        }

    for i, rec in enumerate(records):
        # 1. Verify sequential chain indexing
        if rec.chain_index != i:
            return {
                "intact": False,
                "total_records": len(records),
                "broken_at_index": rec.chain_index,
                "message": f"Broken chain index sequence: expected {i}, got {rec.chain_index}.",
            }

        # 2. Verify previous record hash link
        expected_prev = GENESIS_HASH if i == 0 else records[i - 1].record_hash
        if rec.previous_record_hash != expected_prev:
            return {
                "intact": False,
                "total_records": len(records),
                "broken_at_index": rec.chain_index,
                "message": (
                    f"Chain break at index {rec.chain_index}: previous_record_hash mismatch. "
                    f"Expected {expected_prev[:12]}..., got {rec.previous_record_hash[:12]}..."
                ),
            }

        # 3. Verify record hash integrity
        expected_record_hash = compute_record_hash(
            chain_index=rec.chain_index,
            previous_record_hash=rec.previous_record_hash,
            content_hash=rec.content_hash,
            record_type=rec.record_type,
            organisation_id=organisation_id,
        )

        if rec.record_hash != expected_record_hash:
            return {
                "intact": False,
                "total_records": len(records),
                "broken_at_index": rec.chain_index,
                "message": (
                    f"Tampered record at index {rec.chain_index}: record_hash recalculation mismatch. "
                    f"Expected {expected_record_hash[:12]}..., found {rec.record_hash[:12]}..."
                ),
            }

    return {
        "intact": True,
        "total_records": len(records),
        "broken_at_index": None,
        "latest_record_hash": records[-1].record_hash,
        "message": f"Hash-chain verified successfully: all {len(records)} blocks intact.",
    }
