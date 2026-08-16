from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    lm_studio: str
    uptime_seconds: float


class GPUStatus(BaseModel):
    available: bool
    name: Optional[str] = None
    utilization: Optional[float] = None
    memory_total_mb: Optional[float] = None
    memory_used_mb: Optional[float] = None
    temperature: Optional[float] = None


class SystemStatus(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    gpu: GPUStatus


class MetricsResponse(BaseModel):
    total_requests: int
    active_keys: int
    active_users: int
    models_available: int
    uptime_seconds: float
    system: SystemStatus
