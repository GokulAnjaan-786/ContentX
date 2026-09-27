import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = sa.Column(sa.String(128), nullable=False, index=True)
    resource_type = sa.Column(sa.String(64), nullable=False)
    resource_id = sa.Column(sa.String(128), nullable=True)
    timestamp = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    ip_address = sa.Column(sa.String(64), nullable=True)
    details = sa.Column(sa.Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(action='{self.action}', resource='{self.resource_type}:{self.resource_id}', user='{self.user_id}')>"
