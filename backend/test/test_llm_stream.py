import json

import httpx
import pytest

from app.services.llm import LLMService, LLMServiceError
from app.services.sse import encode_sse


def test_llm_stream_returns_chunks():
    events = [{"message":{"content":"Hello"},"done":False},
              {"message":{"content":" world"},"done":False},
              {"done":True}]

    body = "\n".join(json.dumps(event) for event in events) + "\n"

    transport = httpx.MockTransport(lambda request: httpx.Response(200,text=body))

    with httpx.Client(base_url="http://test",transport=transport) as client:
        llm_service = LLMService(client=client,model="test-model")

        chunks = list(llm_service.stream([{"role":"user","content":"Say hello"}]))

    assert chunks == ["Hello"," world"]
    assert "".join(chunks) == "Hello world"


def test_llm_stream_rejects_incomplete_response():
    body = json.dumps({"message":{"content":"Hello"},"done":False}) + "\n"

    transport = httpx.MockTransport(lambda request: httpx.Response(200,text=body))

    with httpx.Client(base_url="http://test",transport=transport) as client:
        llm_service = LLMService(client=client,model="test-model")

        with pytest.raises(LLMServiceError):
            list(llm_service.stream([{"role":"user","content":"Hi"}]))


def test_sse_event_format():
    result = encode_sse("token",{"text":"Hello"})

    assert result == 'event: token\ndata: {"text": "Hello"}\n\n'