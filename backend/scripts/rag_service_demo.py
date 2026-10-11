import httpx

from app.database.session import SessionFactory
from app.services.llm import LLMService
from app.services.rag import RAGService
from app.services.semantic_search import semantic_search_service

with httpx.Client(base_url="http://127.0.0.1:11434",timeout=120.0) as client:

    llm_service = LLMService(client=client,model="qwen3:4b-instruct")

    rag_service = RAGService(session_factory=SessionFactory,search_service=semantic_search_service,llm_service=llm_service)

    questions = ["How many days per week may full-time employees work remotely?",
                 "What is the company's maternity leave policy?"]

    for question in questions:
        result = rag_service.answer(document_id=12,question=question,limit=3)

        print("\nQuestion:", question)
        print("Answer:", result.answer)
        print("Answer status:", result.answer_status)
        print("Retrieval status:", result.retrieval_status)
        print("Retrieved IDs:",[source.chunk_id for source in result.retrieved_sources])
        print("Cited IDs:",[source.chunk_id for source in result.cited_sources])