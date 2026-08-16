import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, engine
from app.services.lm_studio_service import get_lm_studio_service
from app.services.monitoring_service import MonitoringService
from app.core.config import get_settings
from app.services.inference_queue import inference_queue

router = APIRouter(tags=["monitoring"])
monitoring = MonitoringService()
settings = get_settings()
start_time = time.time()


@router.get("/health")
async def health_check():
    db_healthy = False
    lm_healthy = False

    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            db_healthy = True
    except Exception:
        db_healthy = False

    try:
        lm = get_lm_studio_service()
        lm_healthy = await lm.health_check()
    except Exception:
        lm_healthy = False

    status = "healthy" if (db_healthy and lm_healthy) else "degraded"

    return {
        "status": status,
        "version": settings.app_version,
        "database": "connected" if db_healthy else "disconnected",
        "lm_studio": "connected" if lm_healthy else "disconnected",
        "inference_queue": {
            "active": inference_queue.active,
            "waiting": inference_queue.waiting,
            "capacity": settings.inference_queue_size,
        },
        "uptime_seconds": time.time() - start_time,
    }


@router.get("/status")
async def system_status():
    sys_status = monitoring.get_system_status()
    return {
        "status": "running",
        "version": settings.app_version,
        "uptime_seconds": monitoring.get_uptime(),
        "system": sys_status,
        "inference_queue": {
            "active": inference_queue.active,
            "waiting": inference_queue.waiting,
            "capacity": settings.inference_queue_size,
        },
    }


@router.get("/metrics")
async def prometheus_metrics():
    from app.utils.metrics import get_metrics
    from starlette.responses import Response
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")
