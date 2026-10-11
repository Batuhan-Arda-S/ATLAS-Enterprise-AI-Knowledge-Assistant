from contextlib import nullcontext
from unittest.mock import Mock

from app.services.rag import RAGService
from types import SimpleNamespace


def test_rag_skips_llm_when_no_candidates():
    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = []

    rag_service = RAGService(session_factory=lambda: nullcontext(object()),
                             search_service=search_service,
                             llm_service=llm_service)

    result = rag_service.answer(document_id=12,question="What is the maternity leave policy?")

    assert result.answer is None
    assert result.retrieval_status == "no_candidates"
    assert result.retrieved_sources == ()
    assert result.answer_status == "no_candidates"

    llm_service.generate.assert_not_called()


def test_rag_returns_answer_and_sources():
    chunk = SimpleNamespace(id=1,document_id=12,chunk_index=0,content="Employees may work remotely up to two days per week.")

    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = [(chunk, 0.2)]
    llm_service.generate.return_value = "Up to two days per week. [[chunk:1]]"

    rag_service = RAGService(session_factory=lambda: nullcontext(object()),
                             search_service=search_service,
                             llm_service=llm_service)

    result = rag_service.answer(document_id=12,question="How many remote work days are allowed?")

    assert result.answer == "Up to two days per week. [[chunk:1]]"
    assert result.retrieval_status == "not_evaluated"
    assert result.retrieved_sources[0].chunk_id == 1
    assert result.cited_sources[0].chunk_id == 1
    assert len(result.cited_sources) == 1
    assert result.retrieved_sources[0].chunk_id == 1
    assert result.answer_status == "answered"

    llm_service.generate.assert_called_once()


def test_rag_abstains_when_evidence_is_insufficient():
    chunk = SimpleNamespace(id=2,document_id=12,chunk_index=1,content="Employees receive 20 days of annual leave.")

    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = [(chunk, 0.2)]
    llm_service.generate.return_value = "NO_EVIDENCE"

    rag_service = RAGService(session_factory=lambda: nullcontext(object()),
                             search_service=search_service,
                             llm_service=llm_service)

    result = rag_service.answer(document_id=12,question="What is the maternity leave policy?")

    assert result.answer is None
    assert result.answer_status == "insufficient_evidence"
    assert result.retrieval_status == "not_evaluated"

    assert result.retrieved_sources[0].chunk_id == 2
    assert result.cited_sources == ()

    llm_service.generate.assert_called_once()

def test_followup_uses_chat_history():
    chunk = SimpleNamespace(id=1,document_id=12,chunk_index=0,content="Remote work requires direct manager approval.")

    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = [(chunk,0.2)]
    llm_service.generate.return_value = "Yes, manager approval is required. [[chunk:1]]"

    history = [{"role":"user","content":"How many days may I work remotely?"},
               {"role":"assistant","content":"Up to two days per week. [[chunk:1]]"}]

    rag_service = RAGService(session_factory=lambda: nullcontext(object()),
                             search_service=search_service,llm_service=llm_service)

    result = rag_service.answer(document_id=12,question="Does my manager need to approve it?",history=history)

    search_question = search_service.search.call_args.kwargs["question"]
    messages = llm_service.generate.call_args.args[0]

    assert "How many days may I work remotely?" in search_question
    assert "Does my manager need to approve it?" in search_question

    assert messages[1] == history[0]
    assert messages[2] == history[1]
    assert "Does my manager need to approve it?" in messages[-1]["content"]

    assert result.answer_status == "answered"
    assert result.cited_sources[0].chunk_id == 1