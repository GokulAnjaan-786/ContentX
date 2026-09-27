import enum
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by = sa.Column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selected_outputs = sa.Column(JSONType, nullable=False, default=list)
    settings = sa.Column(JSONType, nullable=False, default=dict)
    status = sa.Column(
        sa.String(32),
        default=JobStatus.QUEUED.value,
        nullable=False,
        index=True,
    )
    error_message = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("Document", backref="generation_jobs")
    user = relationship("User", backref="generation_jobs")
    outputs = relationship("GeneratedOutput", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GenerationJob(id='{self.id}', doc='{self.document_id}', status='{self.status}')>"
