import time
import uuid
from collections import defaultdict
from typing import Callable, Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette import status

from app.core.config import settings
from app.core.logging import correlation_id_ctx, logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:12]}"
        token = correlation_id_ctx.set(corr_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000.0  # in ms
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limit on docs, openapi, or health check
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json", "/redoc") or path.startswith("/docs"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization", "")
        identifier = f"{client_ip}:{auth_header[-16:]}" if auth_header else client_ip

        now = time.time()
        window_start = now - self.window_seconds

        # Prune old timestamps
        timestamps = [t for t in self.clients[identifier] if t > window_start]
        self.clients[identifier] = timestamps

        if len(timestamps) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client: {identifier}")
            corr_id = correlation_id_ctx.get() or "unknown"
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "data": None,
                    "meta": {
                        "timestamp": now,
                        "correlation_id": corr_id,
                    },
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                        "details": [],
                    },
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self.clients[identifier].append(now)
        return await call_next(request)
