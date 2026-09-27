import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    action: str,
    resource_type: str,
    user_id: Optional[uuid.UUID] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[str] = None,
) -> AuditLog:
    """Create an audit log record within the current database session."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            details=details,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        db.rollback()
        # Return transient object without crashing the business action
        return AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
        )
