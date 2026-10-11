import time
import httpx

from app.services.llm import LLMService


messages = [{"role":"system","content":"Answer in English using one short paragraph."},
            {"role":"user","content":"Explain how Server-Sent Events work."}]

with httpx.Client(base_url="http://127.0.0.1:11434",timeout=120.0) as client:
    llm_service = LLMService(client=client,model="qwen3:4b-instruct")

    start = time.perf_counter()
    first_chunk_time = None

    print("Answer: ",end="",flush=True)

    for chunk in llm_service.stream(messages):
        if first_chunk_time is None:
            first_chunk_time = time.perf_counter() - start

        print(chunk,end="",flush=True)

    total_time = time.perf_counter() - start

    print()
    print(f"Time to first chunk: {first_chunk_time:.2f}s")
    print(f"Total time: {total_time:.2f}s")