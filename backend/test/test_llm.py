import json
import httpx

from app.services.llm import LLMService

import pytest

from app.services.llm import LLMServiceError

def fake_ollama(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)

    assert request.method == "POST"
    assert request.url.path == "/api/chat"
    assert payload["model"] == "qwen3:4b-instruct"
    assert payload["stream"] is False

    return httpx.Response(200,json={"message": {"content": "  Test answer.  "}})


def test_generate_reads_ollama_response():
    transport = httpx.MockTransport(fake_ollama)

    with httpx.Client(base_url="http://127.0.0.1:11434",transport=transport) as client:
        service = LLMService(client=client,model="qwen3:4b-instruct")

        result = service.generate([{"role": "user", "content": "Hello"}])

    assert result == "Test answer."


def test_generate_handles_http_error():
    def fake_server(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503,json={"error": "Service temporarily unavailable"})

    transport = httpx.MockTransport(fake_server)

    with httpx.Client(base_url="http://127.0.0.1:11434",transport=transport) as client:
        service = LLMService(client=client,model="qwen3:4b-instruct")

        with pytest.raises(LLMServiceError,match="LLM request failed") as error:
            service.generate([{"role": "user", "content": "Hello"}])

    assert isinstance(error.value.__cause__ , httpx.HTTPStatusError)


def test_generate_rejects_empty_response():
    def fake_server(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200,json={"message": {"content": "   "}})

    transport = httpx.MockTransport(fake_server)

    with httpx.Client(base_url="http://127.0.0.1:11434",transport=transport) as client:
        service = LLMService(client=client,model="qwen3:4b-instruct")

        with pytest.raises(LLMServiceError,match="LLM returned empty content"):
            service.generate([{"role": "user", "content": "Hello"}])