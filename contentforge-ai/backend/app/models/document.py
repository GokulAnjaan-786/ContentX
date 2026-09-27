import enum
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProcessedStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class SourceType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"


class Document(Base):
    __tablename__ = "documents"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    org_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by = sa.Column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_path = sa.Column(sa.String(1024), nullable=True)
    file_name = sa.Column(sa.String(255), nullable=True)
    file_size_bytes = sa.Column(sa.BigInteger, nullable=True)
    mime_type = sa.Column(sa.String(128), nullable=True)
    source_type = sa.Column(
        sa.Enum(SourceType, name="source_type_enum", native_enum=False),
        nullable=False,
    )
    sensitivity_flag = sa.Column(sa.String(64), default="internal", nullable=False)
    processed_status = sa.Column(
        sa.Enum(ProcessedStatus, name="processed_status_enum", native_enum=False),
        default=ProcessedStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    error_message = sa.Column(sa.Text, nullable=True)
    pii_detected = sa.Column(sa.Boolean, default=False, nullable=False)
    pii_types = sa.Column(sa.JSON, default=list, nullable=False)
    injection_flagged = sa.Column(sa.Boolean, default=False, nullable=False)
    injection_details = sa.Column(sa.JSON, default=dict, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organisation = relationship("Organisation", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )

    def __repr__(self) -> str:
        return f"<Document(id='{self.id}', status='{self.processed_status}', type='{self.source_type}')>"
