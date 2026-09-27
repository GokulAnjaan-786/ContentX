"""Add pii_detected, pii_types, injection_flagged, and injection_details to documents.

Revision ID: 0003_add_pii_and_security_flags
Revises: 0002_fact_registry_and_generation
Create Date: 2026-09-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0003_add_pii_and_security_flags"
down_revision: Union[str, None] = "0002_fact_registry_generation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("pii_detected", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("pii_types", JSONType, server_default="[]", nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("injection_flagged", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("injection_details", JSONType, server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("documents", "injection_details")
    op.drop_column("documents", "injection_flagged")
    op.drop_column("documents", "pii_types")
    op.drop_column("documents", "pii_detected")
