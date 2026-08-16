import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.events import startup_event, shutdown_event
from app.api.middleware.auth import APIKeyAuthMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.api.routers import chat, completions, models, auth, admin, dashboard, monitoring

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield
    await shutdown_event()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Starlette executes middleware in reverse registration order. Register the
# limiter first so authentication runs before it and limits are per API key.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyAuthMiddleware)
app.add_middleware(LoggingMiddleware)

app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="dashboard")

app.include_router(chat.router)
app.include_router(completions.router)
app.include_router(models.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(monitoring.router)


@app.get("/")
async def root():
    return FileResponse(Path("app/static/index.html"))
