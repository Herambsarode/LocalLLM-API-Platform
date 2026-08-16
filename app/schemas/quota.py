from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class QuotaResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    daily_requests_limit: int
    monthly_requests_limit: int
    daily_tokens_limit: int
    monthly_tokens_limit: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuotaUpdate(BaseModel):
    daily_requests_limit: Optional[int] = Field(None, ge=0)
    monthly_requests_limit: Optional[int] = Field(None, ge=0)
    daily_tokens_limit: Optional[int] = Field(None, ge=0)
    monthly_tokens_limit: Optional[int] = Field(None, ge=0)
