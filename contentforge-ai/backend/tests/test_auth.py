import pytest
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog


def test_user_registration_success(client, db_session):
    """A new user can register successfully with an existing or new organisation."""
    payload = {
        "email": "newoperator@example.com",
        "password": "SecurePassword123!",
        "org_name": "Stark Industries",
        "role": "operator",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newoperator@example.com"
    assert data["user"]["role"] == "operator"
    assert "id" in data["user"]
    assert "org_id" in data["user"]

    # Verify password was hashed (never stored in plain text)
    user = db_session.query(User).filter(User.email == "newoperator@example.com").first()
    assert user is not None
    assert user.password_hash != "SecurePassword123!"
    assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")

    # Verify audit log was recorded
    audit = db_session.query(AuditLog).filter(AuditLog.action == "user_register").first()
    assert audit is not None
    assert audit.resource_id == str(user.id)


def test_user_registration_duplicate_email_rejected(client, test_user):
    """Attempting to register with an existing email returns 400."""
    payload = {
        "email": test_user.email,
        "password": "AnotherPassword123!",
        "org_name": "Duplicate Org",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_user_registration_weak_password_rejected(client):
    """Passwords shorter than 8 characters are rejected by schema validation."""
    payload = {
        "email": "shortpw@example.com",
        "password": "short",
        "org_name": "Test Org",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_user_login_success(client, test_user):
    """User can log in with valid credentials and receive a JWT access token."""
    payload = {
        "email": test_user.email,
        "password": "ValidPass123!",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email
    assert data["user"]["role"] == test_user.role.value


def test_user_login_invalid_password_rejected(client, test_user, db_session):
    """Logging in with an incorrect password returns 401."""
    payload = {
        "email": test_user.email,
        "password": "WrongPassword999!",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

    # Verify failed login is recorded in audit logs
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "user_login_failed")
        .first()
    )
    assert audit is not None


def test_user_login_nonexistent_email_rejected(client):
    """Logging in with an unregistered email returns 401."""
    payload = {
        "email": "ghost@doesnotexist.com",
        "password": "SomePassword123!",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
