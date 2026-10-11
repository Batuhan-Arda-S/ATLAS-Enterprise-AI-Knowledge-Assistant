from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers.semantic_search import search_document
from app.schemas.semantic_search import SemanticSearchRequest


def test_employee_cannot_search_document():
    class FakeSession:
        def get(self, model, document_id):
            pytest.fail("Database lookup must not occur")

    request = SemanticSearchRequest(question="What is the remote work policy?",limit=3)

    user = SimpleNamespace(role="employee")

    with pytest.raises(HTTPException) as error:
        search_document(payload=request,document_id=12,session=FakeSession(),current_user=user)

    assert error.value.status_code == 403

def test_admin_receives_search_results(monkeypatch):
    class FakeSession:
        def get(self, model, document_id):
            assert document_id == 12
            return SimpleNamespace(id=12)

    chunk = SimpleNamespace(id=1,chunk_index=0,content="Employees may work remotely two days per week.")

    def fake_search(session, document_id, question, limit):
        assert document_id == 12
        assert question == "How many days can employees work remotely?"
        assert limit == 3

        return [(chunk, 0.2)]

    monkeypatch.setattr("app.routers.semantic_search.semantic_search_service.search",fake_search)

    result = search_document(payload=SemanticSearchRequest
                            (question="How many days can employees work remotely?"),
                             document_id=12,
                             session=FakeSession(),
                             current_user=SimpleNamespace(role="admin"))

    assert result.document_id == 12
    assert result.retrieval_status == "not_evaluated"
    assert len(result.results) == 1

    assert result.results[0].chunk_id == 1
    assert result.results[0].cosine_similarity == pytest.approx(0.8)


def test_admin_cannot_search_missing_document():
    class FakeSession:
        def get(self, model, document_id):
            return None

    with pytest.raises(HTTPException) as error:
        search_document(payload=SemanticSearchRequest(question="What is the remote work policy?"),
                        document_id=999,
                        session=FakeSession(),
                        current_user=SimpleNamespace(role="admin"))

    assert error.value.status_code == 404