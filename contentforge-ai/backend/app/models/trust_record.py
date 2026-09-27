import enum
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrustRecordType(str, enum.Enum):
    SOURCE_DOCUMENT = "source_document"
    GENERATED_OUTPUT = "generated_output"


class TrustRecord(Base):
    __tablename__ = "trust_records"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    organisation_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_type = sa.Column(
        sa.Enum(TrustRecordType, name="trust_record_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    document_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    output_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("generated_outputs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chain_index = sa.Column(sa.Integer, nullable=False)
    content_hash = sa.Column(sa.String(64), nullable=False, index=True)
    previous_record_hash = sa.Column(sa.String(64), nullable=False)
    record_hash = sa.Column(sa.String(64), nullable=False, index=True)
    public_anchor_tx_hash = sa.Column(sa.String(128), nullable=True)
    public_anchor_chain_id = sa.Column(sa.Integer, nullable=True)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint("organisation_id", "chain_index", name="uq_trust_record_org_chain_index"),
    )

    # Relationships
    organisation = relationship("Organisation")
    document = relationship("Document")
    output = relationship("GeneratedOutput")

    def __repr__(self) -> str:
        return f"<TrustRecord(id='{self.id}', idx={self.chain_index}, type='{self.record_type}', hash='{self.record_hash[:10]}...')>"
