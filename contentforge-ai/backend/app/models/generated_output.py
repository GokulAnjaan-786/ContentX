import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    job_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    output_type = sa.Column(sa.String(32), nullable=False, index=True)
    content = sa.Column(JSONType, nullable=False, default=dict)
    validation_score = sa.Column(sa.Float, default=1.0, nullable=False)
    status = sa.Column(sa.String(32), default="completed", nullable=False)
    fact_ids_used = sa.Column(JSONType, nullable=False, default=list)
    unverified_claims = sa.Column(JSONType, nullable=False, default=list)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job = relationship("GenerationJob", back_populates="outputs")

    def __repr__(self) -> str:
        return f"<GeneratedOutput(id='{self.id}', type='{self.output_type}', score={self.validation_score})>"
