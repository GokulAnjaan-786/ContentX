import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(255), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    users = relationship("User", back_populates="organisation", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organisation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Organisation(id='{self.id}', name='{self.name}')>"
