"""Enhance fact_registry with classification, importance, certainty_status, entities, dates, numbers.

Revision ID: 0005_enhance_fact_registry
Revises: 0004_add_trust_layer_tables
Create Date: 2026-09-27 12:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0005_enhance_fact_registry"
down_revision: Union[str, None] = "0004_add_trust_layer_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    op.add_column("fact_registry", sa.Column("fact_type", sa.String(length=32), nullable=False, server_default="finding"))
    op.add_column("fact_registry", sa.Column("importance", sa.String(length=32), nullable=False, server_default="high"))
    op.add_column("fact_registry", sa.Column("certainty_status", sa.String(length=32), nullable=False, server_default="confirmed"))
    op.add_column("fact_registry", sa.Column("entities", JSONType, nullable=True))
    op.add_column("fact_registry", sa.Column("dates", JSONType, nullable=True))
    op.add_column("fact_registry", sa.Column("numbers", JSONType, nullable=True))


def downgrade() -> None:
    op.drop_column("fact_registry", "numbers")
    op.drop_column("fact_registry", "dates")
    op.drop_column("fact_registry", "entities")
    op.drop_column("fact_registry", "certainty_status")
    op.drop_column("fact_registry", "importance")
    op.drop_column("fact_registry", "fact_type")
