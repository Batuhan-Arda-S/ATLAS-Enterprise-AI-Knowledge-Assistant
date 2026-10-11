from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.rag import RAGService
from app.services.citation_validation import InvalidCitationError


def test_stream_answer_returns_completed_result():
    chunk = SimpleNamespace(id=1,document_id=12,chunk_index=0,
                            content="Remote work requires manager approval.")

    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = [(chunk,0.2)]
    llm_service.stream.return_value = iter(["Remote work ","requires approval [[chunk:1]]."])

    rag_service = RAGService(session_factory=lambda:nullcontext(object()),
                             search_service=search_service,llm_service=llm_service)

    events = list(rag_service.stream_answer(document_id=12,question="Is approval required?"))

    assert events[0] == ("token","Remote work ")
    assert events[1] == ("token","requires approval [[chunk:1]].")

    event_type,result = events[-1]

    assert event_type == "done"
    assert result.answer_status == "answered"
    assert result.cited_sources[0].chunk_id == 1


def test_stream_answer_hides_no_evidence_marker():
    chunk = SimpleNamespace(id=2,document_id=12,chunk_index=1,
                            content="Employees receive 20 days of annual leave.")

    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = [(chunk,0.2)]
    llm_service.stream.return_value = iter(["NO_","EVI","DENCE"])

    rag_service = RAGService(session_factory=lambda:nullcontext(object()),
                             search_service=search_service,llm_service=llm_service)

    events = list(rag_service.stream_answer(document_id=12,
                                            question="What is the maternity leave policy?"))

    assert len(events) == 1
    assert events[0][0] == "done"
    assert events[0][1].answer is None
    assert events[0][1].answer_status == "insufficient_evidence"


def test_stream_answer_rejects_invalid_citation():
    chunk = SimpleNamespace(id=1,document_id=12,chunk_index=0,
                            content="Remote work requires manager approval.")

    search_service = Mock()
    llm_service = Mock()

    search_service.search.return_value = [(chunk,0.2)]
    llm_service.stream.return_value = iter(["Approval required [[chunk:999]]."])

    rag_service = RAGService(session_factory=lambda:nullcontext(object()),
                             search_service=search_service,llm_service=llm_service)

    with pytest.raises(InvalidCitationError):
        list(rag_service.stream_answer(document_id=12,question="Is approval required?"))