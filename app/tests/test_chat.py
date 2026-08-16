import pytest
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatMessage,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
)


class TestChatSchemas:
    def test_valid_chat_request(self):
        request = ChatCompletionRequest(
            model="deepseek-coder-v2",
            messages=[
                ChatMessage(role="system", content="You are helpful"),
                ChatMessage(role="user", content="Hello"),
            ],
        )
        assert request.model == "deepseek-coder-v2"
        assert len(request.messages) == 2
        assert request.stream is False

    def test_chat_request_with_all_fields(self):
        request = ChatCompletionRequest(
            model="deepseek-coder-v2",
            messages=[ChatMessage(role="user", content="Hi")],
            temperature=0.7,
            top_p=0.9,
            max_tokens=100,
            stream=False,
        )
        assert request.temperature == 0.7
        assert request.top_p == 0.9
        assert request.max_tokens == 100

    def test_invalid_temperature(self):
        with pytest.raises(ValueError):
            ChatCompletionRequest(
                model="test",
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=3.0,
            )

    def test_chat_response_structure(self):
        response = ChatCompletionResponse(
            id="chatcmpl-123",
            created=1234567890,
            model="deepseek-coder-v2",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="Hello!"),
                    finish_reason="stop",
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            ),
        )
        assert response.object == "chat.completion"
        assert len(response.choices) == 1
        assert response.usage.prompt_tokens == 10
        assert response.usage.total_tokens == 15

    def test_message_roles(self):
        for role in ["system", "user", "assistant", "function", "tool"]:
            msg = ChatMessage(role=role, content="test")
            assert msg.role == role

    def test_invalid_role(self):
        with pytest.raises(ValueError):
            ChatMessage(role="invalid_role", content="test")
