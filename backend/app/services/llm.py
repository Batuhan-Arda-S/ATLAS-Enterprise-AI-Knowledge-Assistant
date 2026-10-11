import httpx
import json
from collections.abc import Iterator

class LLMServiceError(RuntimeError):
    pass


class LLMService:
    def __init__(self, client: httpx.Client, model: str):
        self.client = client
        self.model = model


    def generate(self,messages:list[dict[str,str]])->str:

        if not messages:
            raise ValueError("At least one message is required")

        try:
            response=self.client.post("/api/chat",json={"model":self.model,
                                                             "messages":messages,
                                                             "stream":False})

            response.raise_for_status()
            content=response.json()["message"]["content"]

        except (httpx.HTTPError,KeyError,TypeError,ValueError) as exc:
            raise LLMServiceError("LLM request failed") from exc

        if not isinstance(content,str) or not content.strip():
            raise LLMServiceError("LLM returned empty content")

        return content.strip()



    def stream(self,messages: list[dict[str,str]]) -> Iterator[str]:
        if not messages:
            raise ValueError("Messages cannot be empty")

        completed = False
        has_content = False

        try:
            with self.client.stream("POST","/api/chat",json={"model":self.model,
                                                             "messages":messages,
                                                             "stream":True}) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    event = json.loads(line)

                    if not isinstance(event,dict):
                        raise ValueError("Invalid streaming event")

                    if event.get("error"):
                        raise LLMServiceError("LLM streaming failed")

                    if event.get("done") is True:
                        completed = True
                        break

                    content = event["message"]["content"]

                    if not isinstance(content,str):
                        raise TypeError("Invalid LLM chunk")

                    if content:
                        has_content = True
                        yield content

        except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
            raise LLMServiceError("LLM streaming request failed") from exc

        if not completed:
            raise LLMServiceError("LLM stream ended before completion")

        if not has_content:
            raise LLMServiceError("LLM returned empty streamed content")