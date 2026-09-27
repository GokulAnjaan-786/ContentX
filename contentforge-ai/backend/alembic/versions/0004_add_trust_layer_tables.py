"""Add trust_records, reviewer_keys, and approval_signatures tables.

Revision ID: 0004_add_trust_layer_tables
Revises: 0003_add_pii_and_security_flags
Create Date: 2026-09-26 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_add_trust_layer_tables"
down_revision: Union[str, None] = "0003_add_pii_and_security_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. trust_records
    op.create_table(
        "trust_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("output_id", sa.Uuid(), nullable=True),
        sa.Column("chain_index", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_record_hash", sa.String(length=64), nullable=False),
        sa.Column("record_hash", sa.String(length=64), nullable=False),
        sa.Column("public_anchor_tx_hash", sa.String(length=128), nullable=True),
        sa.Column("public_anchor_chain_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["output_id"], ["generated_outputs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organisation_id", "chain_index", name="uq_trust_record_org_chain_index"),
    )
    op.create_index(op.f("ix_trust_records_organisation_id"), "trust_records", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_trust_records_record_type"), "trust_records", ["record_type"], unique=False)
    op.create_index(op.f("ix_trust_records_document_id"), "trust_records", ["document_id"], unique=False)
    op.create_index(op.f("ix_trust_records_output_id"), "trust_records", ["output_id"], unique=False)
    op.create_index(op.f("ix_trust_records_content_hash"), "trust_records", ["content_hash"], unique=False)
    op.create_index(op.f("ix_trust_records_record_hash"), "trust_records", ["record_hash"], unique=False)

    # 2. reviewer_keys
    op.create_table(
        "reviewer_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("public_key", sa.String(length=256), nullable=False),
        sa.Column("encrypted_private_key", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviewer_keys_user_id"), "reviewer_keys", ["user_id"], unique=True)

    # 3. approval_signatures
    op.create_table(
        "approval_signatures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("output_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("content_hash_signed", sa.String(length=64), nullable=False),
        sa.Column("signature", sa.String(length=256), nullable=False),
        sa.Column(
            "signed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["output_id"], ["generated_outputs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approval_signatures_output_id"), "approval_signatures", ["output_id"], unique=False)
    op.create_index(op.f("ix_approval_signatures_reviewer_id"), "approval_signatures", ["reviewer_id"], unique=False)


def downgrade() -> None:
    op.drop_table("approval_signatures")
    op.drop_table("reviewer_keys")
    op.drop_table("trust_records")
