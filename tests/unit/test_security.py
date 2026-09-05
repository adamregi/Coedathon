from datetime import timedelta
import pytest

from app.core.errors import AuthenticationException, TokenExpiredException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.models import Role, User
from app.repositories.in_memory import RepositoryContainer
from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.services.auth_service import AuthService


def test_argon2_hashing_and_verification():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_access_token_creation_and_decoding():
    token = create_access_token(user_id=42, role="employer")
    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["user_id"] == 42
    assert payload["role"] == "employer"
    assert payload["type"] == "access"


def test_jwt_expiration_handling():
    # Expired in past
    expired_token = create_access_token(
        user_id=1,
        role="student",
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(TokenExpiredException):
        decode_token(expired_token)


def test_refresh_token_rotation_and_revocation():
    repos = RepositoryContainer()
    auth_service = AuthService(repos.user_repo, repos.student_repo)

    # Register user
    user = auth_service.register_user(
        UserRegisterRequest(
            email="refresh@test.com",
            password="Password123!",
            full_name="Refresh Tester",
            role=Role.STUDENT,
        )
    )

    # Login to receive tokens
    login_resp = auth_service.login_user(
        UserLoginRequest(email="refresh@test.com", password="Password123!")
    )
    first_refresh = login_resp.refresh_token

    # Rotate refresh token
    rotated_resp = auth_service.rotate_refresh_token(first_refresh)
    second_refresh = rotated_resp.refresh_token
    assert first_refresh != second_refresh

    # Attempting to use the old refresh token triggers reuse detection and revokes the family
    with pytest.raises(AuthenticationException) as exc_info:
        auth_service.rotate_refresh_token(first_refresh)
    assert "reuse detected" in str(exc_info.value).lower()
