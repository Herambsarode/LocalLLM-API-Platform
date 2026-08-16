import asyncio
from contextlib import asynccontextmanager

from app.core.config import get_settings


class InferenceQueueFull(RuntimeError):
    pass


class InferenceQueue:
    """Process-wide FIFO admission queue for the local model worker."""

    def __init__(self) -> None:
        settings = get_settings()
        self._semaphore = asyncio.Semaphore(settings.inference_concurrency)
        self._lock = asyncio.Lock()
        self._waiting = 0
        self._active = 0
        self._max_waiting = settings.inference_queue_size
        self._wait_timeout = settings.inference_queue_wait_timeout

    @property
    def waiting(self) -> int:
        return self._waiting

    @property
    def active(self) -> int:
        return self._active

    @asynccontextmanager
    async def slot(self):
        async with self._lock:
            if self._waiting >= self._max_waiting:
                raise InferenceQueueFull("Inference queue is full")
            self._waiting += 1

        try:
            try:
                await asyncio.wait_for(
                    self._semaphore.acquire(), timeout=self._wait_timeout
                )
            except TimeoutError as exc:
                raise InferenceQueueFull("Timed out waiting for the inference queue") from exc
        finally:
            async with self._lock:
                self._waiting -= 1

        async with self._lock:
            self._active += 1

        try:
            yield
        finally:
            async with self._lock:
                self._active -= 1
            self._semaphore.release()


inference_queue = InferenceQueue()
