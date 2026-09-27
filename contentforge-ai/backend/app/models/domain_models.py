import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(64), unique=True, nullable=False)
    description = sa.Column(sa.String(255), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Permission(Base):
    __tablename__ = "permissions"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    code = sa.Column(sa.String(64), unique=True, nullable=False)
    description = sa.Column(sa.String(255), nullable=True)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = sa.Column(sa.Integer, default=1, nullable=False)
    file_path = sa.Column(sa.String(1024), nullable=False)
    sha256_hash = sa.Column(sa.String(64), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DocumentSource(Base):
    __tablename__ = "document_sources"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    source_uri = sa.Column(sa.String(1024), nullable=False)
    source_type = sa.Column(sa.String(64), nullable=False)
    ingested_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FactEvidence(Base):
    __tablename__ = "fact_evidence"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    fact_id = sa.Column(sa.Uuid, sa.ForeignKey("fact_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    snippet = sa.Column(sa.Text, nullable=False)
    page_number = sa.Column(sa.Integer, nullable=True)
    confidence_score = sa.Column(sa.Float, default=1.0)


class Entity(Base):
    __tablename__ = "entities"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = sa.Column(sa.String(255), nullable=False)
    entity_type = sa.Column(sa.String(64), nullable=False)
    attributes = sa.Column(sa.JSON, default=dict)


class FactEntity(Base):
    __tablename__ = "fact_entities"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    fact_id = sa.Column(sa.Uuid, sa.ForeignKey("fact_registry.id", ondelete="CASCADE"), nullable=False)
    entity_id = sa.Column(sa.Uuid, sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)


class FactRelationship(Base):
    __tablename__ = "fact_relationships"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    source_fact_id = sa.Column(sa.Uuid, sa.ForeignKey("fact_registry.id", ondelete="CASCADE"), nullable=False)
    target_fact_id = sa.Column(sa.Uuid, sa.ForeignKey("fact_registry.id", ondelete="CASCADE"), nullable=False)
    relationship_type = sa.Column(sa.String(64), nullable=False)


class Topic(Base):
    __tablename__ = "topics"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    topic_name = sa.Column(sa.String(255), nullable=False)
    relevance = sa.Column(sa.Float, default=1.0)


class Conflict(Base):
    __tablename__ = "conflicts"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    conflict_description = sa.Column(sa.Text, nullable=False)
    severity = sa.Column(sa.String(32), default="medium")


class OutputClaim(Base):
    __tablename__ = "output_claims"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    output_id = sa.Column(sa.Uuid, sa.ForeignKey("generated_outputs.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = sa.Column(sa.Text, nullable=False)
    grounded_status = sa.Column(sa.String(32), default="grounded")
    certainty = sa.Column(sa.String(32), default="confirmed")


class ClaimFactLink(Base):
    __tablename__ = "claim_fact_links"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    claim_id = sa.Column(sa.Uuid, sa.ForeignKey("output_claims.id", ondelete="CASCADE"), nullable=False)
    fact_id = sa.Column(sa.Uuid, sa.ForeignKey("fact_registry.id", ondelete="CASCADE"), nullable=False)


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    job_id = sa.Column(sa.Uuid, sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False)
    status = sa.Column(sa.String(32), default="completed")
    overall_confidence = sa.Column(sa.Float, default=1.0)
    ran_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    validation_run_id = sa.Column(sa.Uuid, sa.ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=False)
    issue_type = sa.Column(sa.String(64), nullable=False)
    severity = sa.Column(sa.String(32), default="warning")
    description = sa.Column(sa.Text, nullable=False)
    target_output = sa.Column(sa.String(64), nullable=True)


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    verification_id = sa.Column(sa.String(64), unique=True, nullable=False, index=True)
    document_id = sa.Column(sa.Uuid, sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    output_id = sa.Column(sa.Uuid, sa.ForeignKey("generated_outputs.id", ondelete="SET NULL"), nullable=True)
    source_hash = sa.Column(sa.String(64), nullable=False)
    output_hash = sa.Column(sa.String(64), nullable=False)
    verification_status = sa.Column(sa.String(32), default="verified")
    issuer = sa.Column(sa.String(255), default="ContentX Trust Engine")
    qr_code_svg = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DomainProfile(Base):
    __tablename__ = "domain_profiles"

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    domain_key = sa.Column(sa.String(64), unique=True, nullable=False)
    domain_name = sa.Column(sa.String(128), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    validation_rules = sa.Column(sa.JSON, default=dict)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
