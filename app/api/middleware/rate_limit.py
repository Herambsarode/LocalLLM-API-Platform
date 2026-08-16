import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings

settings = get_settings()


class InMemoryRateLimiter:
    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > window_start]

        if len(self.requests[key]) >= max_requests:
            reset_time = int(self.requests[key][0] + window_seconds)
            return False, reset_time

        self.requests[key].append(now)
        return True, int(now + window_seconds)

    def cleanup(self):
        now = time.time()
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > now - 3600]
            if not self.requests[key]:
                del self.requests[key]


rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/status", "/metrics", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        api_key_id = getattr(request.state, "api_key_id", None)
        client_host = request.client.host if request.client else "unknown"
        rate_limit_key = f"key:{api_key_id}" if api_key_id else f"ip:{client_host}"

        allowed, reset_time = rate_limiter.check(
            rate_limit_key,
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        )

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "message": "Rate limit exceeded. Please wait before retrying.",
                        "type": "rate_limit_error",
                    }
                },
                headers={
                    "Retry-After": str(max(1, reset_time - int(time.time()))),
                    "X-PiCode-Error-Source": "gateway_rate_limit",
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, settings.rate_limit_requests - len(rate_limiter.requests.get(rate_limit_key, [])))
        )
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response
