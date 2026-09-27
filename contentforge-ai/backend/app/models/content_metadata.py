import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


class ContentMetadata(Base):
    __tablename__ = "content_metadata"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary = sa.Column(sa.Text, nullable=False)
    document_type = sa.Column(sa.String(64), nullable=False)
    entities = sa.Column(JSONType, nullable=False, default=dict)
    topics = sa.Column(JSONType, nullable=False, default=list)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship back to document
    document = relationship("Document", backref=sa.orm.backref("content_metadata", uselist=False))

    def __repr__(self) -> str:
        return f"<ContentMetadata(id='{self.id}', doc_id='{self.document_id}', type='{self.document_type}')>"
