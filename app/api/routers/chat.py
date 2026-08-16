import time
import uuid
import json
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse, JSONResponse

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, ChatCompletionUsage
from app.services.lm_studio_service import LMStudioService, LMStudioError, get_lm_studio_service
from app.services.usage_service import UsageService, UsageRecordCreate
from app.services.quota_service import QuotaService
from app.core.config import get_settings

logger = logging.getLogger("api")
router = APIRouter(tags=["chat"])
settings = get_settings()


def _sanitize_response(data: dict) -> dict:
    data.pop("stats", None)
    for choice in data.get("choices", []):
        msg = choice.get("message", {})
        msg.pop("reasoning_content", None)
        if msg.get("tool_calls") == []:
            msg.pop("tool_calls", None)
    return data


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
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

    if body.stream:
        return await _handle_stream(
            request, body, lm_studio, user_id, api_key_id, start_time
        )

    try:
        lm_body = body.model_dump(exclude_none=True, exclude={"stream"})
        lm_body["max_tokens"] = min(
            lm_body.get("max_tokens", settings.lm_studio_default_max_tokens),
            settings.lm_studio_default_max_tokens,
        )
        response_data = await lm_studio.chat_completion(lm_body)
    except LMStudioError as e:
        logger.error(f"LM Studio error: {e}")
        error_type = "invalid_request_error" if e.status_code == 400 else "server_error"
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"message": str(e), "type": error_type, "source": e.source}},
            headers={
                **({"Retry-After": str(e.retry_after)} if e.retry_after else {}),
                "X-PiCode-Error-Source": e.source,
            },
        )

    response_data = _sanitize_response(response_data)

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
                endpoint="/v1/chat/completions",
                status_code=200,
            )
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
        await db.rollback()

    return response_data


async def _handle_stream(
    request: Request,
    body: ChatCompletionRequest,
    lm_studio: LMStudioService,
    user_id: uuid.UUID,
    api_key_id: uuid.UUID,
    start_time: float,
):
    lm_body = body.model_dump(exclude_none=True)
    lm_body["stream"] = True
    lm_body["max_tokens"] = min(
        lm_body.get("max_tokens", settings.lm_studio_default_max_tokens),
        settings.lm_studio_default_max_tokens,
    )

    async def generate():
        from app.core.database import async_session_factory
        total_prompt_tokens = 0
        total_completion_tokens = 0
        try:
            async for chunk in lm_studio.chat_completion_stream(lm_body):
                yield chunk
                if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
                    try:
                        data = json.loads(chunk[6:])
                        if "usage" in data:
                            total_prompt_tokens = data["usage"].get("prompt_tokens", 0)
                            total_completion_tokens = data["usage"].get("completion_tokens", 0)
                    except (json.JSONDecodeError, KeyError):
                        pass
        finally:
            response_time_ms = (time.time() - start_time) * 1000
            async with async_session_factory() as stream_db:
                usage_service = UsageService(stream_db)
                try:
                    await usage_service.record_usage(
                        UsageRecordCreate(
                            user_id=user_id,
                            api_key_id=api_key_id,
                            model=body.model,
                            prompt_tokens=total_prompt_tokens,
                            completion_tokens=total_completion_tokens,
                            total_tokens=total_prompt_tokens + total_completion_tokens,
                            response_time_ms=response_time_ms,
                            ip_address=request.client.host if request.client else None,
                            endpoint="/v1/chat/completions",
                            status_code=200,
                        )
                    )
                    await stream_db.commit()
                except Exception as e:
                    logger.error(f"Failed to record streaming usage: {e}")
                    await stream_db.rollback()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
