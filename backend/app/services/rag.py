from dataclasses import dataclass
from collections.abc import Callable,Sequence,Iterator

from sqlalchemy.orm import Session

from app.evaluation.retrieval_assessment import assess_retrieval
from app.services.llm import LLMService
from app.services.prompt_builder import build_context, build_rag_messages
from app.services.semantic_search import SemanticSearchService
from app.services.citation_validation import validate_citations,InvalidCitationError
from typing import Literal

from app.services.prompt_builder import NO_EVIDENCE_MARKER

AnswerStatus = Literal["answered","no_candidates","insufficient_evidence"]

@dataclass(frozen=True)
class RetrievedSource:
    chunk_id: int
    document_id: int
    chunk_index: int


@dataclass(frozen=True)
class RAGResult:
    answer: str | None
    retrieval_status: str
    retrieved_sources: tuple[RetrievedSource, ...]
    cited_sources: tuple[RetrievedSource, ...] = ()
    answer_status: AnswerStatus = "answered"



class RAGService:
    def __init__(self,session_factory: Callable[[], Session],search_service: SemanticSearchService,llm_service: LLMService):
        self.session_factory = session_factory
        self.search_service = search_service
        self.llm_service = llm_service



    def answer(self, document_id: int, question: str, limit: int = 3,
                history: Sequence[dict[str, str]] = ()) -> RAGResult:

        if not question.strip():
            raise ValueError("Question cannot be blank")

        previous_question = next((message["content"] for message in reversed(history) if message["role"] == "user"),None)

        search_question = f"{previous_question}\n{question}" if previous_question else question

        with self.session_factory() as session:
            matches = self.search_service.search(session=session,
                                                 document_id=document_id,
                                                 question=search_question,
                                                 limit=limit)

            context = build_context(matches)

            sources = tuple(
                RetrievedSource(chunk_id=chunk.id,document_id=chunk.document_id,chunk_index=chunk.chunk_index)
                for chunk, _ in matches)

            distances=[distance for _, distance in matches]

            assessment = assess_retrieval(distances)

            if assessment.status == "no_candidates":
                return RAGResult(answer=None,
                                 retrieval_status=assessment.status,
                                 retrieved_sources=sources,
                                 answer_status="no_candidates")

            messages = build_rag_messages(question=question,context=context,history=history)

            answer = self.llm_service.generate(messages)

            sources_by_id = {source.chunk_id: source for source in sources}

            if answer.strip() == NO_EVIDENCE_MARKER:
                return RAGResult(answer=None,
                                 retrieval_status=assessment.status,
                                 retrieved_sources=sources,cited_sources=(),
                                 answer_status="insufficient_evidence")

            cited_ids = validate_citations(answer=answer,allowed_ids=set(sources_by_id))

            if not cited_ids:
                raise InvalidCitationError("LLM answer did not cite retrieved evidence")

            cited_sources = tuple(sources_by_id[chunk_id]for chunk_id in cited_ids)

            return RAGResult(answer=answer,
                             retrieval_status=assessment.status,
                             retrieved_sources=sources,
                             cited_sources=cited_sources)


    def stream_answer(self,document_id: int,question: str,limit: int = 3,
                      history: Sequence[dict[str,str]] = ()) -> Iterator[tuple[str,str | RAGResult]]:

        if not question.strip():
            raise ValueError("Question cannot be blank")

        previous_question = next(
            (message["content"] for message in reversed(history) if message["role"] == "user"),None)

        search_question = f"{previous_question}\n{question}" if previous_question else question

        with self.session_factory() as session:
            matches = self.search_service.search(session=session,document_id=document_id,
                                                 question=search_question,limit=limit)

            context = build_context(matches)

            sources = tuple(
                RetrievedSource(chunk_id=chunk.id,document_id=chunk.document_id,chunk_index=chunk.chunk_index)
                for chunk,_ in matches)

            distances = [distance for _,distance in matches]

        assessment = assess_retrieval(distances)

        if assessment.status == "no_candidates":
            yield "done",RAGResult(answer=None,retrieval_status=assessment.status,
                                   retrieved_sources=sources,answer_status="no_candidates")
            return

        messages = build_rag_messages(question=question,context=context,history=history)

        parts = []
        pending = ""
        possible_abstention = True

        for chunk in self.llm_service.stream(messages):
            parts.append(chunk)

            if possible_abstention:
                pending += chunk

                if NO_EVIDENCE_MARKER.startswith(pending.strip()):
                    continue

                possible_abstention = False
                yield "token",pending
            else:
                yield "token",chunk

        answer = "".join(parts).strip()

        if answer == NO_EVIDENCE_MARKER:
            yield "done",RAGResult(answer=None,retrieval_status=assessment.status,
                                   retrieved_sources=sources,answer_status="insufficient_evidence")
            return

        sources_by_id = {source.chunk_id:source for source in sources}
        cited_ids = validate_citations(answer=answer,allowed_ids=set(sources_by_id))

        if not cited_ids:
            raise InvalidCitationError("LLM answer did not cite retrieved evidence")

        cited_sources = tuple(sources_by_id[chunk_id] for chunk_id in cited_ids)

        result = RAGResult(answer=answer,retrieval_status=assessment.status,
                           retrieved_sources=sources,cited_sources=cited_sources,
                           answer_status="answered")

        yield "done",result