from typing import Any, Dict, List, Optional
from fastapi import status


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class ValidationException(AppException):
    def __init__(self, message: str = "Input validation failed", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication credentials were not provided or are invalid"):
        super().__init__(
            code="UNAUTHENTICATED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenExpiredException(AppException):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            code="TOKEN_EXPIRED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class PermissionDeniedException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ResourceNotFoundException(AppException):
    def __init__(self, message: str = "Requested resource was not found"):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ResourceConflictException(AppException):
    def __init__(self, message: str = "Resource conflict detected"):
        super().__init__(
            code="RESOURCE_CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidStateTransitionException(AppException):
    def __init__(self, message: str = "The requested state transition is not allowed"):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class RateLimitExceededException(AppException):
    def __init__(self, message: str = "Too many requests. Please try again later"):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class InternalServerException(AppException):
    def __init__(self, message: str = "An unexpected internal server error occurred"):
        super().__init__(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
