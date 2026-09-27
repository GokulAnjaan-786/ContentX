"""Add content_metadata, fact_registry, generation_jobs, and generated_outputs.

Revision ID: 0002_fact_registry_and_generation
Revises: 0001_initial_schema
Create Date: 2026-09-26 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0002_fact_registry_generation"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # 1. content_metadata table
    op.create_table(
        "content_metadata",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("entities", JSONType, nullable=False),
        sa.Column("topics", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", name="uq_content_metadata_document_id"),
    )
    op.create_index(op.f("ix_content_metadata_document_id"), "content_metadata", ["document_id"], unique=True)

    # 2. fact_registry table
    op.create_table(
        "fact_registry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("fact_id_string", sa.String(length=32), nullable=False),
        sa.Column("fact_statement", sa.Text(), nullable=False),
        sa.Column("source_chunk_id", sa.Uuid(), nullable=True),
        sa.Column("source_snippet", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_chunk_id"], ["document_chunks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "fact_id_string", name="uq_doc_fact_id"),
    )
    op.create_index(op.f("ix_fact_registry_document_id"), "fact_registry", ["document_id"], unique=False)
    op.create_index(op.f("ix_fact_registry_source_chunk_id"), "fact_registry", ["source_chunk_id"], unique=False)

    # 3. generation_jobs table
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by", sa.Uuid(), nullable=True),
        sa.Column("selected_outputs", JSONType, nullable=False),
        sa.Column("settings", JSONType, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generation_jobs_document_id"), "generation_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_generation_jobs_status"), "generation_jobs", ["status"], unique=False)

    # 4. generated_outputs table
    op.create_table(
        "generated_outputs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("output_type", sa.String(length=32), nullable=False),
        sa.Column("content", JSONType, nullable=False),
        sa.Column("validation_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("fact_ids_used", JSONType, nullable=False),
        sa.Column("unverified_claims", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["generation_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_outputs_job_id"), "generated_outputs", ["job_id"], unique=False)
    op.create_index(op.f("ix_generated_outputs_output_type"), "generated_outputs", ["output_type"], unique=False)


def downgrade() -> None:
    op.drop_table("generated_outputs")
    op.drop_table("generation_jobs")
    op.drop_table("fact_registry")
    op.drop_table("content_metadata")
