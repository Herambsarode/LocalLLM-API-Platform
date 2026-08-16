from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class APIKeyCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    key_prefix: str
    name: Optional[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyResponse):
    raw_key: str


class APIKeyListResponse(BaseModel):
    items: list[APIKeyResponse]
    total: int
    page: int
    size: int
