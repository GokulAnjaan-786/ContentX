import enum
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    ORG_ADMIN = "org_admin"
    SYSTEM_ADMIN = "system_admin"


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    org_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = sa.Column(sa.String(255), unique=True, index=True, nullable=False)
    password_hash = sa.Column(sa.String(255), nullable=False)
    role = sa.Column(
        sa.Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.OPERATOR,
        nullable=False,
    )
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organisation = relationship("Organisation", back_populates="users")
    uploaded_documents = relationship("Document", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"
