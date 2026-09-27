import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReviewerKey(Base):
    __tablename__ = "reviewer_keys"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    public_key = sa.Column(sa.String(256), nullable=False)
    encrypted_private_key = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ReviewerKey(user_id='{self.user_id}', public_key='{self.public_key[:16]}...')>"
