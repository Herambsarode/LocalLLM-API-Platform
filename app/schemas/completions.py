from pydantic import BaseModel, Field
from typing import Optional, Any


class CompletionRequest(BaseModel):
    model: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    suffix: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    n: Optional[int] = Field(None, ge=1, le=10)
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[list[str]] = None
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    best_of: Optional[int] = None
    logit_bias: Optional[dict[str, float]] = None
    user: Optional[str] = None
    seed: Optional[int] = None

    model_config = {"extra": "ignore"}


class CompletionChoice(BaseModel):
    index: int
    text: str
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: CompletionUsage
