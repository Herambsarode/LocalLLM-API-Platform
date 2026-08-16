import time
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.completions import CompletionRequest
from app.services.lm_studio_service import LMStudioError, get_lm_studio_service
from app.services.usage_service import UsageService, UsageRecordCreate
from app.services.quota_service import QuotaService
from app.core.config import get_settings

logger = logging.getLogger("api")
router = APIRouter(tags=["completions"])
settings = get_settings()


@router.post("/v1/completions")
async def completions(
    request: Request,
    body: CompletionRequest,
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    api_key_id = getattr(request.state, "api_key_id", None)

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    quota_service = QuotaService(db)
    allowed, msg = await quota_service.check_quota(user_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg,
            headers={"Retry-After": "60", "X-PiCode-Error-Source": "account_quota"},
        )

    lm_studio = get_lm_studio_service()
    start_time = time.time()

    try:
        lm_body = body.model_dump(exclude_none=True)
        lm_body["max_tokens"] = min(
            lm_body.get("max_tokens", settings.lm_studio_default_max_tokens),
            settings.lm_studio_default_max_tokens,
        )
        response_data = await lm_studio.completion(lm_body)
    except LMStudioError as e:
        logger.error(f"LM Studio error: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))

    response_time_ms = (time.time() - start_time) * 1000
    usage = response_data.get("usage", {})

    usage_service = UsageService(db)
    try:
        await usage_service.record_usage(
            UsageRecordCreate(
                user_id=user_id,
                api_key_id=api_key_id,
                model=body.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                response_time_ms=response_time_ms,
                ip_address=request.client.host if request.client else None,
                endpoint="/v1/completions",
                status_code=200,
            )
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
        await db.rollback()

    return response_data
