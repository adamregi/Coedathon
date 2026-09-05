from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import AppException
from app.core.logging import logger, setup_logging
from app.core.middleware import (
    CorrelationIdMiddleware,
    ProcessTimeMiddleware,
    RateLimitMiddleware,
)
from app.schemas.envelope import error_envelope

# Initialize structured logging
setup_logging()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "Auth", "description": "Authentication, JWT tokens, and user credentials"},
            {"name": "Students", "description": "Student profiles and skill proficiency records"},
            {"name": "Skills", "description": "Global skill catalog management and categorization"},
            {"name": "Jobs", "description": "Job listings and proficiency requirement specifications"},
            {"name": "Analysis", "description": "Matching Engine v1.0, gap analysis, and candidate discovery"},
            {"name": "Recommendations", "description": "Prioritized learning and skill acquisition recommendations"},
            {"name": "Applications", "description": "Candidate application lifecycle and state transitions"},
            {"name": "Dashboard", "description": "Role-specific analytical aggregates and metrics"},
            {"name": "Health", "description": "System availability and health probes"},
        ],
    )

    # Middleware Pipeline
    # 1. Rate Limiter
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )

    # 2. Process Timer
    app.add_middleware(ProcessTimeMiddleware)

    # 3. Correlation ID
    app.add_middleware(CorrelationIdMiddleware)

    # 4. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers - Mapping to Standard Envelope
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            f"AppException: {exc.code} - {exc.message}",
            extra={"details": exc.details, "status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            details.append({"location": loc, "message": err.get("msg"), "type": err.get("type")})

        logger.info(f"Validation error on {request.url.path}: {details}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_envelope(
                code="VALIDATION_ERROR",
                message="Request input validation failed. Check 'details' for field-level errors.",
                details=details,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        code_map = {
            401: "UNAUTHENTICATED",
            403: "PERMISSION_DENIED",
            404: "RESOURCE_NOT_FOUND",
            409: "RESOURCE_CONFLICT",
            429: "RATE_LIMIT_EXCEEDED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(
                code=code,
                message=str(exc.detail),
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope(
                code="INTERNAL_SERVER_ERROR",
                message="An internal server error occurred. Please contact system support.",
            ),
        )

    # Route Registration
    app.include_router(health_router)  # /health at root
    app.include_router(health_router, prefix="/api")  # /api/health
    from app.api.canonical import canonical_api_router
    app.include_router(canonical_api_router, prefix="/api")
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.on_event("startup")
    def on_startup():
        try:
            from app.db.base import Base
            from app.db.session import engine
            import app.db.models  # noqa
            Base.metadata.create_all(bind=engine)
            logger.info("MySQL tables verified/created successfully.")
        except Exception as e:
            logger.warning(f"Database table verification deferred: {e}")

    return app


app = create_app()
