from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from app.core.config import get_settings

settings = get_settings()

if settings.metrics_enabled:
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )

    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    )

    api_requests_total = Counter(
        "api_requests_total",
        "Total API requests",
        ["model", "endpoint"],
    )

    tokens_total = Counter(
        "tokens_total",
        "Total tokens processed",
        ["model", "type"],
    )

    active_api_keys = Gauge(
        "active_api_keys",
        "Number of active API keys",
    )

    lm_studio_health = Gauge(
        "lm_studio_health",
        "LM Studio health status (1=up, 0=down)",
    )

    gpu_utilization = Gauge(
        "gpu_utilization",
        "GPU utilization percentage",
    )

    gpu_memory_used = Gauge(
        "gpu_memory_used_mb",
        "GPU memory used in MB",
    )
else:
    class NoopMetric:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass

    http_requests_total = NoopMetric()
    http_request_duration_seconds = NoopMetric()
    api_requests_total = NoopMetric()
    tokens_total = NoopMetric()
    active_api_keys = NoopMetric()
    lm_studio_health = NoopMetric()
    gpu_utilization = NoopMetric()
    gpu_memory_used = NoopMetric()


def get_metrics():
    if settings.metrics_enabled:
        return generate_latest(REGISTRY)
    return b""
