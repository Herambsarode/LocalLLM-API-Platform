from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import hash_api_key
from app.services.api_key_service import APIKeyService
from app.core.database import async_session_factory


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = [
            "/health", "/status", "/metrics", "/docs", "/openapi.json", "/redoc",
            "/auth/login", "/auth/register",
        ]
        if request.url.path in public_paths:
            return await call_next(request)

        if request.url.path.startswith("/v1/models") and request.method == "GET":
            return await call_next(request)

        if request.url.path.startswith("/auth/") or request.url.path.startswith("/dashboard") or request.url.path.startswith("/admin/") or request.url.path == "/":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": {"message": "Missing or invalid authorization header", "type": "auth_error"}},
                headers={"WWW-Authenticate": "Bearer"},
            )

        api_key = auth_header[7:]

        async with async_session_factory() as db:
            service = APIKeyService(db)
            key_obj = await service.validate_api_key(api_key)
            if not key_obj:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": {"message": "Invalid or expired API key", "type": "auth_error"}},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            request.state.api_key_id = key_obj.id
            request.state.user_id = key_obj.user_id

        return await call_next(request)
