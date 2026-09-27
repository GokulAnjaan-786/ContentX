import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import create_access_token, get_password_hash, verify_password
from app.api.deps import get_client_ip, get_current_user
from app.models.organisation import Organisation
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user account with hashed password, organization creation, audit logging,
    and immediate JWT authentication token issuance.
    """
    client_ip = get_client_ip(request)

    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        create_audit_log(
            db=db,
            action="user_register_failed",
            resource_type="user",
            ip_address=client_ip,
            details=f"Email collision for {payload.email}",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    # Resolve or create organisation
    org = None
    if payload.org_id:
        org = db.query(Organisation).filter(Organisation.id == payload.org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organisation with id '{payload.org_id}' not found",
            )
    else:
        org_name = payload.org_name or f"Org for {payload.email.split('@')[0]}"
        org = Organisation(name=org_name)
        db.add(org)
        db.flush()

    # Hash password and save user
    hashed_pw = get_password_hash(payload.password)
    user = User(
        org_id=org.id,
        email=payload.email.lower(),
        password_hash=hashed_pw,
        role=payload.role or UserRole.OPERATOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Record audit log
    create_audit_log(
        db=db,
        action="user_register",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
        ip_address=client_ip,
        details=f"Registered user with role '{user.role}' in organisation '{org.name}'",
    )

    # Issue JWT access token for immediate session creation
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=str(user.id),
        claims={
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "org_id": str(user.org_id),
        },
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials, enforce rate limits, write audit log, and return JWT token.
    """
    client_ip = get_client_ip(request)

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        create_audit_log(
            db=db,
            action="user_login_failed",
            resource_type="user",
            user_id=user.id if user else None,
            ip_address=client_ip,
            details=f"Failed login attempt for email {payload.email}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=str(user.id),
        claims={
            "email": user.email,
            "role": user.role.value,
            "org_id": str(user.org_id),
        },
        expires_delta=access_token_expires,
    )

    create_audit_log(
        db=db,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
        ip_address=client_ip,
        details="User authenticated successfully",
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log out current user and record audit log."""
    client_ip = get_client_ip(request)
    create_audit_log(
        db=db,
        action="user_logout",
        resource_type="user",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        ip_address=client_ip,
        details=f"User {current_user.email} logged out",
    )
    return {"message": "Logged out successfully"}

