from fastapi import APIRouter
from app.core.config import settings
from app.schemas.envelope import ResponseEnvelope, success_envelope

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ResponseEnvelope[dict])
def health_check():
    """System health check probe returning application status and version."""
    return success_envelope(
        data={
            "status": "ok",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "persistence_contracts": "active",
        }
    )
