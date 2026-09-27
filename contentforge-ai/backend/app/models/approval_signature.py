import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApprovalSignature(Base):
    __tablename__ = "approval_signatures"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    output_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("generated_outputs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_hash_signed = sa.Column(sa.String(64), nullable=False)
    signature = sa.Column(sa.String(256), nullable=False)
    signed_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    output = relationship("GeneratedOutput")
    reviewer = relationship("User")

    def __repr__(self) -> str:
        return f"<ApprovalSignature(output_id='{self.output_id}', reviewer_id='{self.reviewer_id}')>"
