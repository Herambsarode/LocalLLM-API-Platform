from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_admin_user, get_current_user
from app.services.usage_service import UsageService
from app.services.monitoring_service import MonitoringService
from app.services.model_service import ModelService
from app.database.models.user import User
from app.schemas.dashboard import MetricsResponse, SystemStatus, GPUStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
monitoring = MonitoringService()


@router.get("/analytics/daily")
async def daily_analytics(
    days: int = Query(30, ge=1, le=365),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsageService(db)
    return await service.get_all_daily_usage(days)


@router.get("/analytics/monthly")
async def monthly_analytics(
    months: int = Query(12, ge=1, le=24),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsageService(db)
    return await service.get_all_monthly_usage(months)


@router.get("/analytics/models")
async def model_analytics(
    days: int = Query(30, ge=1, le=365),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsageService(db)
    return await service.get_model_breakdown(days=days)


@router.get("/analytics/my-usage")
async def my_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsageService(db)
    daily = await service.get_user_daily_usage(current_user.id, days)
    summary = await service.get_user_summary(current_user.id)
    models = await service.get_model_breakdown(current_user.id, days)
    return {
        "daily": daily,
        "summary": summary,
        "models": models,
    }


@router.get("/system", response_model=SystemStatus)
async def system_status(
    _: User = Depends(get_admin_user),
):
    return monitoring.get_system_status()


@router.get("/gpu", response_model=GPUStatus)
async def gpu_status(
    _: User = Depends(get_admin_user),
):
    return monitoring.get_gpu_status()


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    usage_service = UsageService(db)
    model_service = ModelService(db)
    stats = await usage_service.get_global_stats()
    models, _ = await model_service.get_all()
    sys_status = monitoring.get_system_status()

    return MetricsResponse(
        total_requests=stats.get("total_requests", 0),
        active_keys=0,
        active_users=0,
        models_available=len(models),
        uptime_seconds=monitoring.get_uptime(),
        system=sys_status,
    )
