from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "AI API Platform"
    app_version: str = "1.0.0"
    app_description: str = "Production-ready OpenAI-compatible API for self-hosted LLMs"
    debug: bool = False
    secret_key: str = "change-this-to-a-random-secret-key-at-least-64-chars"

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/ai_api"
    database_sync_url: str = "postgresql://user:password@localhost:5432/ai_api"

    lm_studio_base_url: str = "http://localhost:1234/v1"
    # Model generation can legitimately take several minutes on local hardware.
    # A value of 0 disables only the response read timeout; connection and write
    # operations remain bounded so a genuinely unavailable server fails quickly.
    lm_studio_read_timeout: float = 0
    lm_studio_connect_timeout: float = 10
    lm_studio_write_timeout: float = 30
    lm_studio_pool_timeout: float = 10
    lm_studio_transient_retries: int = 2
    lm_studio_retry_backoff_seconds: float = 1
    lm_studio_default_max_tokens: int = 4096
    lm_studio_context_length: int = 8192
    lm_studio_auto_evict_other_models: bool = True
    lm_studio_parallel: int = 1
    lm_studio_offload_kv_cache_to_gpu: bool = True
    inference_concurrency: int = 1
    inference_queue_size: int = 20
    inference_queue_wait_timeout: float = 900
    # Accepted for compatibility with older deployments; no longer used for
    # inference reads because it caused valid long generations to become 502s.
    lm_studio_timeout: float | None = None

    api_key_prefix: str = "sk_live_"
    api_key_bytes: int = 32
    api_key_hash_algorithm: str = "sha256"

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    default_daily_requests: int = 10000
    default_monthly_requests: int = 300000
    default_daily_tokens: int = 10000000
    default_monthly_tokens: int = 300000000

    cors_origins: str = "*"

    log_level: str = "INFO"
    log_format: str = "json"

    metrics_enabled: bool = True
    prometheus_multiproc_dir: str = "/tmp/prometheus"

    bcrypt_rounds: int = 12
    access_token_expire_minutes: int = 60

    redis_url: str = ""

    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "changeme123"

    model_config = {"env_file": ".env", "case_sensitive": False}

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def database_url_str(self) -> str:
        return str(self.database_url)

    @property
    def database_sync_url_str(self) -> str:
        return str(self.database_sync_url)

    @property
    def lm_studio_base_url_str(self) -> str:
        return str(self.lm_studio_base_url).rstrip("/")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
