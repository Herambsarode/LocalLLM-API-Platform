import pytest
from app.schemas.completions import CompletionRequest, CompletionResponse, CompletionChoice, CompletionUsage


class TestCompletionSchemas:
    def test_valid_completion_request(self):
        request = CompletionRequest(model="deepseek-coder-v2", prompt="Hello")
        assert request.model == "deepseek-coder-v2"
        assert request.prompt == "Hello"
        assert request.stream is False

    def test_completion_request_with_options(self):
        request = CompletionRequest(
            model="deepseek-coder-v2",
            prompt="Write a poem",
            max_tokens=200,
            temperature=0.8,
            top_p=0.95,
        )
        assert request.max_tokens == 200
        assert request.temperature == 0.8
        assert request.top_p == 0.95

    def test_completion_response_structure(self):
        response = CompletionResponse(
            id="cmpl-123",
            created=1234567890,
            model="deepseek-coder-v2",
            choices=[
                CompletionChoice(
                    index=0,
                    text="Once upon a time",
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
        )
        assert response.object == "text_completion"
        assert response.choices[0].text == "Once upon a time"
        assert response.usage.total_tokens == 15

    def test_invalid_temperature_range(self):
        with pytest.raises(ValueError):
            CompletionRequest(model="test", prompt="test", temperature=-1)
