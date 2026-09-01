"""
backend/app/middleware/rate_limit.py

Sliding window rate limiting middleware protecting against abuse and DoS.
"""

from collections import defaultdict
import time
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.
    Limits requests per IP address per 60-second window.
    """

    def __init__(self, app, max_requests_per_minute: int = 120):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exempt health check endpoints and preflight OPTIONS from rate limiting
        if request.url.path in ["/health", "/api/v1/ping", "/docs", "/openapi.json"] or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

        # Purge timestamps older than 60 seconds
        timestamps = [t for t in self.request_history[client_ip] if t > window_start]
        self.request_history[client_ip] = timestamps

        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a moment before sending more requests.",
                headers={"Retry-After": "60"},
            )

        self.request_history[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(self.request_history[client_ip])))
        return response
