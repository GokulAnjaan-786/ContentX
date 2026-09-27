import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = sa.Column(sa.Integer, nullable=False)
    text = sa.Column(sa.Text, nullable=False)
    page_number = sa.Column(sa.Integer, nullable=True)
    section_reference = sa.Column(sa.String(128), nullable=True)
    word_count = sa.Column(sa.Integer, nullable=True)
    # 1536-dim vector for embeddings (e.g. OpenAI text-embedding-3-small or similar), left nullable for Part 1
    embedding = sa.Column(Vector(1536), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk(id='{self.id}', doc_id='{self.document_id}', index={self.chunk_index}, words={self.word_count})>"
