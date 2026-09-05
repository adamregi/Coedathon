import hashlib
from typing import Optional
from app.core.audit import emit_audit_event
from app.core.errors import (
    AuthenticationException,
    PermissionDeniedException,
    ResourceConflictException,
    ResourceNotFoundException,
    TokenExpiredException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.models import RefreshToken, Role, StudentProfile, User
from app.domain.protocols import StudentRepositoryProtocol, UserRepositoryProtocol
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRead,
    UserRegisterRequest,
)


class AuthService:
    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        student_repo: Optional[StudentRepositoryProtocol] = None,
    ):
        self.user_repo = user_repo
        self.student_repo = student_repo

    def register_user(self, req: UserRegisterRequest) -> UserRead:
        # Check email uniqueness
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            emit_audit_event(
                action="USER_REGISTRATION_FAILED",
                actor_role=req.role.value,
                target_type="user",
                target_id=req.email,
                details={"reason": "email_already_exists"},
                status="FAILURE",
            )
            raise ResourceConflictException(f"User with email '{req.email}' already exists")

        # Prevent public registration of admin accounts
        role = req.role
        if role == Role.ADMIN:
            raise PermissionDeniedException("Public registration cannot create administrative accounts")

        hashed_pw = hash_password(req.password)
        user = User(
            id=0,
            email=req.email.lower(),
            hashed_password=hashed_pw,
            full_name=req.full_name,
            role=role,
        )
        created_user = self.user_repo.create(user)

        # Automatically provision student profile if student
        if role == Role.STUDENT and self.student_repo:
            self.student_repo.create_student(
                StudentProfile(
                    student_id=0,
                    name=created_user.full_name,
                    email=created_user.email,
                    user_id=created_user.id,
                )
            )

        emit_audit_event(
            action="USER_REGISTERED",
            actor_id=created_user.id,
            actor_role=created_user.role.value,
            target_type="user",
            target_id=str(created_user.id),
            details={"email": created_user.email, "role": created_user.role.value},
            status="SUCCESS",
        )

        return UserRead(
            id=created_user.id,
            email=created_user.email,
            full_name=created_user.full_name,
            role=created_user.role,
            is_active=created_user.is_active,
            created_at=created_user.created_at,
        )

    def login_user(self, req: UserLoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            emit_audit_event(
                action="USER_LOGIN_FAILED",
                target_type="user",
                target_id=req.email,
                details={"reason": "invalid_credentials"},
                status="FAILURE",
            )
            raise AuthenticationException("Invalid email or password")

        if not user.is_active:
            emit_audit_event(
                action="USER_LOGIN_BLOCKED",
                actor_id=user.id,
                actor_role=user.role.value,
                target_type="user",
                target_id=str(user.id),
                details={"reason": "account_disabled"},
                status="FAILURE",
            )
            raise AuthenticationException("Account is inactive")

        # Create access and refresh tokens
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        raw_refresh_token, family_id, expires_at = create_refresh_token(
            user_id=user.id, role=user.role.value
        )

        token_hash = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()
        self.user_repo.save_refresh_token(
            RefreshToken(
                id=0,
                user_id=user.id,
                token_hash=token_hash,
                family_id=family_id,
                is_revoked=False,
                expires_at=expires_at,
            )
        )

        emit_audit_event(
            action="USER_LOGIN_SUCCESS",
            actor_id=user.id,
            actor_role=user.role.value,
            target_type="user",
            target_id=str(user.id),
            status="SUCCESS",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=15 * 60,
        )

    def rotate_refresh_token(self, raw_refresh_token: str) -> TokenResponse:
        payload = decode_token(raw_refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationException("Provided token is not a refresh token")

        token_hash = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()
        stored_token = self.user_repo.get_refresh_token(token_hash)

        if not stored_token:
            raise AuthenticationException("Refresh token is unrecognized")

        # If token was revoked, revoke the whole family (potential token reuse attack)
        if stored_token.is_revoked:
            self.user_repo.revoke_family_tokens(stored_token.family_id)
            emit_audit_event(
                action="TOKEN_REUSE_DETECTED",
                actor_id=stored_token.user_id,
                target_type="refresh_token_family",
                target_id=stored_token.family_id,
                details={"reason": "revoked_token_reused"},
                status="ALERT",
            )
            raise AuthenticationException("Token reuse detected; all sessions revoked")

        # Revoke the current refresh token (single use)
        self.user_repo.revoke_refresh_token(token_hash)

        user_id = int(payload["sub"])
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationException("User not found or inactive")

        # Issue new access token and rotated refresh token in the same family
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        new_raw_token, family_id, expires_at = create_refresh_token(
            user_id=user.id, role=user.role.value, family_id=stored_token.family_id
        )

        new_token_hash = hashlib.sha256(new_raw_token.encode("utf-8")).hexdigest()
        self.user_repo.save_refresh_token(
            RefreshToken(
                id=0,
                user_id=user.id,
                token_hash=new_token_hash,
                family_id=family_id,
                is_revoked=False,
                expires_at=expires_at,
            )
        )

        emit_audit_event(
            action="TOKEN_REFRESH_SUCCESS",
            actor_id=user.id,
            actor_role=user.role.value,
            target_type="user",
            target_id=str(user.id),
            status="SUCCESS",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_token,
            token_type="bearer",
            expires_in=15 * 60,
        )

    def revoke_refresh_token(self, raw_refresh_token: str) -> bool:
        token_hash = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()
        revoked = self.user_repo.revoke_refresh_token(token_hash)
        emit_audit_event(
            action="TOKEN_REVOKED",
            target_type="refresh_token",
            target_id=token_hash[:16],
            status="SUCCESS" if revoked else "NOT_FOUND",
        )
        return revoked
