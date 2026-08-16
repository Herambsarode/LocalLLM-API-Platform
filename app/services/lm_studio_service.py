import asyncio
import time
import json
import httpx
from typing import Optional, AsyncGenerator
from app.core.config import get_settings
from app.services.inference_queue import inference_queue, InferenceQueueFull

settings = get_settings()


class LMStudioError(RuntimeError):
    """An error returned by, or connecting to, LM Studio."""

    def __init__(self, message: str, status_code: int = 503,
                 source: str = "lm_studio", retry_after: int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.source = source
        self.retry_after = retry_after


class LMStudioService:
    def __init__(self):
        self.base_url = settings.lm_studio_base_url_str
        self.management_url = self.base_url.removesuffix("/v1")
        read_timeout = settings.lm_studio_read_timeout or None
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=settings.lm_studio_connect_timeout,
                read=read_timeout,
                write=settings.lm_studio_write_timeout,
                pool=settings.lm_studio_pool_timeout,
            ),
            follow_redirects=True,
        )

    async def close(self):
        await self.client.aclose()

    async def list_models(self) -> list[dict]:
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            raise LMStudioError(f"Failed to fetch models from LM Studio: {e}")

    async def ensure_model_loaded(self, model: str, *, force_reload: bool = False) -> None:
        """Load the requested model if needed while holding the inference slot."""
        try:
            response = await self.client.get(f"{self.management_url}/api/v1/models")
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models") or payload.get("data") or []
            selected = next((
                item for item in models
                if item.get("key") == model or item.get("id") == model
            ), None)
            if selected is None:
                raise LMStudioError(f"Unknown model: {model}", 400)
            if force_reload:
                for instance in selected.get("loaded_instances", []):
                    unload = await self.client.post(
                        f"{self.management_url}/api/v1/models/unload",
                        json={"instance_id": instance["id"]},
                    )
                    unload.raise_for_status()
                selected["loaded_instances"] = []
            if settings.lm_studio_auto_evict_other_models:
                for item in models:
                    if item.get("key") == model:
                        continue
                    for instance in item.get("loaded_instances", []):
                        unload = await self.client.post(
                            f"{self.management_url}/api/v1/models/unload",
                            json={"instance_id": instance["id"]},
                        )
                        unload.raise_for_status()

            if selected.get("loaded_instances") or selected.get("state") == "loaded":
                return

            context_length = min(
                settings.lm_studio_context_length,
                selected.get("max_context_length", settings.lm_studio_context_length),
            )
            response = await self.client.post(
                f"{self.management_url}/api/v1/models/load",
                json={
                    "model": model,
                    "context_length": context_length,
                    "flash_attention": True,
                    "offload_kv_cache_to_gpu": settings.lm_studio_offload_kv_cache_to_gpu,
                    "parallel": settings.lm_studio_parallel,
                    "echo_load_config": True,
                },
            )
            response.raise_for_status()
        except LMStudioError:
            raise
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = str(e)
            raise LMStudioError(f"Could not load model {model}: {detail}", 429)
        except httpx.RequestError as e:
            raise LMStudioError(f"LM Studio model manager unavailable: {e}", 503)

    async def chat_completion(self, body: dict) -> dict:
        try:
            async with inference_queue.slot():
                await self.ensure_model_loaded(body["model"])
                # LM Studio can evict a worker while a long request is running
                # (for example when another local client switches models). A
                # single transparent cold reload is safer than leaking a 503 to
                # a multi-step client. Keep the queue slot during recovery so a
                # second gateway request cannot race the reload.
                attempts = max(1, settings.lm_studio_transient_retries + 1)
                for attempt in range(attempts):
                    try:
                        response = await self.client.post("/chat/completions", json=body)
                    except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                        if attempt + 1 >= attempts:
                            raise LMStudioError(
                                f"LM Studio connection failed after {attempts} attempts: {exc}",
                                503, "lm_studio_connection", 5,
                            ) from exc
                        await asyncio.sleep(settings.lm_studio_retry_backoff_seconds * (attempt + 1))
                        continue
                    if response.is_success:
                        data = response.json()
                        if not isinstance(data, dict) or not isinstance(data.get("choices"), list):
                            raise LMStudioError("LM Studio returned invalid OpenAI-compatible JSON", 502,
                                                "lm_studio_protocol", 2)
                        return data
                    response_text = response.text.lower()
                    if "unloaded" in response_text and attempt + 1 < attempts:
                        await self.ensure_model_loaded(body["model"], force_reload=True)
                        continue
                    if response.status_code in {502, 503, 504} and attempt + 1 < attempts:
                        await asyncio.sleep(settings.lm_studio_retry_backoff_seconds * (attempt + 1))
                        continue
                    response.raise_for_status()
                raise LMStudioError("Model worker recovery failed", 503)
        except InferenceQueueFull as e:
            raise LMStudioError(str(e), 429, "gateway_queue", 5)
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"message": str(e)}
            message = error_detail.get("error") or error_detail.get("message") or str(error_detail)
            # Preserve client-input failures instead of mislabelling them 502.
            status_code = e.response.status_code
            if "unloaded" in str(message).lower():
                status_code = 503
            retry_after = 5 if status_code in {429, 502, 503, 504} else None
            raise LMStudioError(str(message), status_code, "lm_studio", retry_after)
        except httpx.RequestError as e:
            raise LMStudioError(f"Failed to connect to LM Studio: {e}", 503,
                                "lm_studio_connection", 5)

    async def chat_completion_stream(self, body: dict) -> AsyncGenerator[str, None]:
        body["stream"] = True
        try:
            async with inference_queue.slot():
                await self.ensure_model_loaded(body["model"])
                attempts = max(1, settings.lm_studio_transient_retries + 1)
                for attempt in range(attempts):
                    async with self.client.stream("POST", "/chat/completions", json=body) as response:
                        if response.status_code in {502, 503, 504} and attempt + 1 < attempts:
                            await response.aread()
                            await asyncio.sleep(settings.lm_studio_retry_backoff_seconds * (attempt + 1))
                            continue
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data:"):
                                # Never retry after emitting a partial stream;
                                # doing so would duplicate tokens at the client.
                                yield f"{line}\n\n"
                        return
                raise LMStudioError("Streaming model worker recovery failed", 503,
                                    "lm_studio_worker", 5)
        except InferenceQueueFull as e:
            error = {"error": {"message": str(e), "type": "rate_limit_error", "source": "gateway_queue"}}
            yield f"data: {json.dumps(error)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            source = getattr(e, "source", "lm_studio")
            error = {"error": {"message": str(e), "type": "server_error", "source": source}}
            yield f"data: {json.dumps(error)}\n\n"
            yield "data: [DONE]\n\n"

    async def completion(self, body: dict) -> dict:
        try:
            async with inference_queue.slot():
                await self.ensure_model_loaded(body["model"])
                response = await self.client.post(
                    "/completions",
                    json=body,
                )
                response.raise_for_status()
                return response.json()
        except InferenceQueueFull as e:
            raise LMStudioError(str(e), 429)
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"message": str(e)}
            message = error_detail.get("error") or error_detail.get("message") or str(error_detail)
            status_code = e.response.status_code
            if "unloaded" in str(message).lower():
                status_code = 503
            raise LMStudioError(str(message), status_code)
        except httpx.RequestError as e:
            raise LMStudioError(f"Failed to connect to LM Studio: {e}", 503)

    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


_shared_service: LMStudioService | None = None


def get_lm_studio_service() -> LMStudioService:
    """Return the process-wide pooled upstream client."""
    global _shared_service
    if _shared_service is None or _shared_service.client.is_closed:
        _shared_service = LMStudioService()
    return _shared_service


async def close_lm_studio_service() -> None:
    global _shared_service
    if _shared_service is not None:
        await _shared_service.close()
        _shared_service = None
