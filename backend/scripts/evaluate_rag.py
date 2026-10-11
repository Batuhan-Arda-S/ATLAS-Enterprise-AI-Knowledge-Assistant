import json
from pathlib import Path

import httpx

from app.database.session import SessionFactory
from app.services.citation_validation import InvalidCitationError
from app.services.llm import LLMService, LLMServiceError
from app.services.rag import RAGService
from app.services.semantic_search import semantic_search_service


data_path = Path(__file__).resolve().parents[1] / "evaluation_data" / "rag_cases.json"
data = json.loads(data_path.read_text(encoding="utf-8"))

status_matches = 0
citation_matches = 0
execution_errors = 0

answerable_cases = sum(
    case["expected_status"] == "answered"
    for case in data["cases"]
)

with httpx.Client(base_url="http://127.0.0.1:11434",timeout=120.0) as client:
    llm_service = LLMService(client=client,model="qwen3:4b-instruct")

    rag_service = RAGService(session_factory=SessionFactory,
                             search_service=semantic_search_service,
                             llm_service=llm_service)

    for index, case in enumerate(data["cases"],start=1):
        try:
            result = rag_service.answer(
                document_id=data["document_id"],
                question=case["question"],
                limit=3
            )
        except (LLMServiceError,InvalidCitationError) as exc:
            execution_errors += 1
            print(f"\nCase {index} failed: {type(exc).__name__}")
            continue

        cited_ids = {source.chunk_id for source in result.cited_sources}
        expected_ids = set(case["expected_cited_chunk_ids"])

        status_ok = result.answer_status == case["expected_status"]
        citation_ok = cited_ids == expected_ids

        status_matches += status_ok

        if case["expected_status"] == "answered":
            citation_matches += citation_ok

        print(f"\nCase {index}: {case['question']}")
        print("Answer:",result.answer)
        print("Expected fact:",case["expected_fact"])
        print("Answer status:",result.answer_status)
        print("Status correct:",status_ok)
        print("Retrieved IDs:",[s.chunk_id for s in result.retrieved_sources])
        print("Cited IDs:",sorted(cited_ids))
        print("Expected citations:",sorted(expected_ids))
        print("Citations correct:",citation_ok)



total = len(data["cases"])

print("\nEvaluation summary")
print(f"Status matches: {status_matches}/{total}")
print(f"Exact citation matches: {citation_matches}/{answerable_cases}")
print(f"Execution errors: {execution_errors}/{total}")

