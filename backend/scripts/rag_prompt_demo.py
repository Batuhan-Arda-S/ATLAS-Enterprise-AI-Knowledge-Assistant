import httpx

from app.database.session import SessionFactory
from app.services.semantic_search import semantic_search_service
from app.services.prompt_builder import (build_context,build_rag_messages)
from app.services.llm import LLMService

question = (
    "How many days per week may full-time employees "
    "work remotely?")

with SessionFactory() as session:
    matches = semantic_search_service.search(session=session,document_id=12,question=question,limit=3)

    retrieved_ids = [chunk.id for chunk, _ in matches]
    context = build_context(matches)

    messages = build_rag_messages(question=question,context=context)

with httpx.Client(base_url="http://127.0.0.1:11434",timeout=120.0) as client:

    service = LLMService(client=client,model="qwen3:4b-instruct")

    answer = service.generate(messages)

print("Retrieved chunk IDs:", retrieved_ids)
print("LLM answer:", answer)