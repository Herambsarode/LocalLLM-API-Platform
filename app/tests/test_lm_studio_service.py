from unittest.mock import AsyncMock

import httpx
import pytest

from app.services.lm_studio_service import LMStudioService, LMStudioError


@pytest.mark.asyncio
async def test_chat_recovers_once_when_model_is_unloaded():
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": {"message": "Model unloaded."}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    service = LMStudioService()
    await service.client.aclose()
    service.client = httpx.AsyncClient(
        base_url="http://lm-studio.test/v1",
        transport=httpx.MockTransport(handler),
    )
    service.ensure_model_loaded = AsyncMock()

    result = await service.chat_completion({"model": "coder-14b", "messages": []})

    assert result["choices"][0]["message"]["content"] == "ok"
    assert service.ensure_model_loaded.await_count == 2
    service.ensure_model_loaded.assert_awaited_with("coder-14b", force_reload=True)
    await service.close()


@pytest.mark.asyncio
async def test_chat_retries_then_classifies_persistent_503():
    calls = 0
    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"error": {"message": "worker died"}})

    service = LMStudioService()
    await service.client.aclose()
    service.client = httpx.AsyncClient(
        base_url="http://lm-studio.test/v1",
        transport=httpx.MockTransport(handler),
    )
    service.ensure_model_loaded = AsyncMock()

    with pytest.raises(LMStudioError) as captured:
        await service.chat_completion({"model": "coder-14b", "messages": []})
    assert captured.value.status_code == 503
    assert captured.value.source == "lm_studio"
    assert service.ensure_model_loaded.await_count == 1
    assert calls == 3
    await service.close()


@pytest.mark.asyncio
async def test_chat_retries_transient_worker_failure_then_succeeds():
    calls = 0
    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(502, json={"error": {"message": "worker restarting"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "recovered"}}]})

    service = LMStudioService()
    await service.client.aclose()
    service.client = httpx.AsyncClient(base_url="http://lm-studio.test/v1",
                                       transport=httpx.MockTransport(handler))
    service.ensure_model_loaded = AsyncMock()
    result = await service.chat_completion({"model": "coder-14b", "messages": []})
    assert result["choices"][0]["message"]["content"] == "recovered"
    assert calls == 3
    await service.close()
