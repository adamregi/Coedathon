from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

from app.core.logging import correlation_id_ctx

T = TypeVar("T")


class Meta(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str = Field(default_factory=lambda: correlation_id_ctx.get() or "unknown")
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = Field(default_factory=list)
    request_id: str = Field(default_factory=lambda: correlation_id_ctx.get() or "unknown")


class ResponseEnvelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    meta: Meta = Field(default_factory=Meta)
    error: Optional[ErrorDetail] = None


def success_envelope(
    data: Any,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    total: Optional[int] = None,
) -> dict[str, Any]:
    """Helper to construct standardized success envelope dictionaries."""
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id_ctx.get() or "unknown",
    }
    if page is not None:
        meta["page"] = page
    if per_page is not None:
        meta["per_page"] = per_page
    if total is not None:
        meta["total"] = total

    return {
        "data": data,
        "meta": meta,
        "error": None,
    }


def error_envelope(
    code: str,
    message: str,
    details: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """Helper to construct standardized error envelope dictionaries."""
    req_id = request_id or correlation_id_ctx.get() or "unknown"
    return {
        "data": None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": req_id,
        },
        "error": {
            "code": code,
            "message": message,
            "details": details if details is not None else [],
            "request_id": req_id,
        },
    }
