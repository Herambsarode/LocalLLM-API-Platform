from pydantic import BaseModel, Field
from typing import Optional, Any, Literal


class ChatMessage(BaseModel):
    role: Literal["system", "developer", "user", "assistant", "tool", "function"] = "user"
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[Any] = None
    tool_call_id: Optional[str] = None
    reasoning_content: Optional[str] = None

    model_config = {"extra": "allow"}


class ChatCompletionRequest(BaseModel):
    model: str = "deepseek-coder-v2-lite-instruct"
    messages: list[ChatMessage] = Field(
        default_factory=lambda: [ChatMessage(role="user", content="hi")]
    )
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    n: Optional[int] = None
    stream: Optional[bool] = False
    stop: Optional[Any] = None
    max_tokens: Optional[int] = Field(None, ge=1)
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[dict[str, float]] = None
    user: Optional[str] = None
    seed: Optional[int] = None
    tools: Optional[Any] = None
    tool_choice: Optional[Any] = None
    response_format: Optional[Any] = None
    stream_options: Optional[Any] = None
    parallel_tool_calls: Optional[bool] = None

    model_config = {"extra": "allow"}


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage
    system_fingerprint: Optional[str] = None


class ChatCompletionStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict]
