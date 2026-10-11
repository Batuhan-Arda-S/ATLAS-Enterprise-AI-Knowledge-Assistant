import httpx

from app.services.llm import LLMService
from app.services.prompt_builder import RAG_SYSTEM_PROMPT


question = "How many days per week may our employees work remotely?"

plain_messages = [{"role": "user", "content": question}]

grounded_messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT},
                     {"role": "user", "content": question}]


messages = [{"role": "system", "content": "Answer briefly in English."},
            {"role": "user", "content": "Explain what a REST API is."}]

with httpx.Client(base_url="http://127.0.0.1:11434",timeout=120.0) as client:
    service = LLMService(client=client,model="qwen3:4b-instruct")

    for label, messages in [("Without system prompt", plain_messages),
                            ("With RAG system prompt", grounded_messages)]:
        print(f"\n{label}:")
        print(service.generate(messages))