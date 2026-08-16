from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class UsageRecordCreate(BaseModel):
    user_id: uuid.UUID
    api_key_id: Optional[uuid.UUID] = None
    model: str
    request_count: int = 1
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    response_time_ms: float = 0.0
    ip_address: Optional[str] = None
    country: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None


class UsageRecordResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    api_key_id: Optional[uuid.UUID]
    model: str
    request_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time_ms: float
    ip_address: Optional[str]
    country: Optional[str]
    endpoint: Optional[str]
    status_code: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageSummary(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    avg_response_time_ms: float


class UsageAnalytics(BaseModel):
    daily_requests: list[dict]
    monthly_requests: list[dict]
    model_breakdown: list[dict]
