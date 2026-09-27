import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class FactRegistry(Base):
    __tablename__ = "fact_registry"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fact_id_string = sa.Column(sa.String(32), nullable=False)
    fact_statement = sa.Column(sa.Text, nullable=False)
    source_chunk_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_snippet = sa.Column(sa.Text, nullable=True)
    confidence = sa.Column(sa.Float, default=1.0, nullable=False)
    fact_type = sa.Column(sa.String(32), default="finding", nullable=False)
    importance = sa.Column(sa.String(32), default="high", nullable=False)
    certainty_status = sa.Column(sa.String(32), default="confirmed", nullable=False)
    entities = sa.Column(sa.JSON, nullable=True)
    dates = sa.Column(sa.JSON, nullable=True)
    numbers = sa.Column(sa.JSON, nullable=True)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint("document_id", "fact_id_string", name="uq_doc_fact_id"),
    )

    # Relationships
    document = relationship("Document", backref=sa.orm.backref("facts", cascade="all, delete-orphan"))
    source_chunk = relationship("DocumentChunk", backref="derived_facts")

    def __repr__(self) -> str:
        return f"<FactRegistry(id='{self.id}', fact_id='{self.fact_id_string}', doc='{self.document_id}')>"
