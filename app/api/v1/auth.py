from fastapi import APIRouter, Depends, status
from app.api.deps import get_auth_service, get_current_user
from app.domain.models import User
from app.schemas.auth import (
    RefreshTokenRequest,
    RevokeTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRead,
    UserRegisterRequest,
)
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ResponseEnvelope[UserRead], status_code=status.HTTP_201_CREATED)
def register(
    req: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account with role (student, employer, admin)."""
    user_read = auth_service.register_user(req)
    return success_envelope(data=user_read.model_dump())


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
def login(
    req: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password to receive JWT access and rotating refresh tokens."""
    tokens = auth_service.login_user(req)
    return success_envelope(data=tokens.model_dump())


@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
def refresh_token(
    req: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Exchange a valid refresh token for a new access token and a rotated refresh token."""
    tokens = auth_service.rotate_refresh_token(req.refresh_token)
    return success_envelope(data=tokens.model_dump())


@router.post("/revoke", response_model=ResponseEnvelope[dict])
def revoke_token(
    req: RevokeTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Explicitly revoke a refresh token."""
    revoked = auth_service.revoke_refresh_token(req.refresh_token)
    return success_envelope(data={"revoked": revoked})


@router.get("/me", response_model=ResponseEnvelope[UserRead])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve profile information for the currently authenticated user."""
    return success_envelope(
        data=UserRead(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
        ).model_dump()
    )
