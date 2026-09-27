import uuid
import pytest
from app.models.document import Document, ProcessedStatus, SourceType
from app.models.organisation import Organisation
from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token


def test_unauthenticated_request_returns_401(client):
    """An unauthenticated request to protected document endpoints returns 401."""
    random_id = uuid.uuid4()
    response = client.get(f"/documents/{random_id}")
    assert response.status_code == 401
    assert "token required" in response.json()["detail"].lower()


def test_malformed_token_returns_401(client):
    """Request with a malformed or forged JWT returns 401."""
    headers = {"Authorization": "Bearer this-is-not-a-valid-jwt-token"}
    random_id = uuid.uuid4()
    response = client.get(f"/documents/{random_id}", headers=headers)
    assert response.status_code == 401


def test_cross_tenant_document_isolation(client, test_user, auth_headers, db_session):
    """Operators cannot access documents belonging to a different organisation."""
    # Create another organisation and a document belonging to it
    other_org = Organisation(id=uuid.uuid4(), name="Competitor Corp")
    db_session.add(other_org)
    db_session.flush()

    foreign_doc = Document(
        id=uuid.uuid4(),
        org_id=other_org.id,
        file_path=f"{other_org.id}/secret.pdf",
        file_name="secret.pdf",
        source_type=SourceType.PDF,
        processed_status=ProcessedStatus.PROCESSED,
    )
    db_session.add(foreign_doc)
    db_session.commit()

    # Current user tries to access foreign document
    response = client.get(f"/documents/{foreign_doc.id}", headers=auth_headers)
    assert response.status_code == 404
