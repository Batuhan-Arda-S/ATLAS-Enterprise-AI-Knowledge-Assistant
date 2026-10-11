import json


def encode_sse(event: str,data: dict) -> str:
    if event not in ("token","done","error"):
        raise ValueError("Invalid SSE event")

    return f"event: {event}\ndata: {json.dumps(data,ensure_ascii=False)}\n\n"

