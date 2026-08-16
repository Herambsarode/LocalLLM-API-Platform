from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class ModelCreate(BaseModel):
    model_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    provider: str = "lm_studio"
    description: Optional[str] = None
    context_length: Optional[int] = None
    is_active: bool = True
    is_default: bool = False


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    provider: Optional[str] = None
    description: Optional[str] = None
    context_length: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ModelResponse(BaseModel):
    id: uuid.UUID
    model_id: str
    name: str
    provider: str
    description: Optional[str]
    context_length: Optional[int]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelListResponse(BaseModel):
    items: list[ModelResponse]
    total: int
