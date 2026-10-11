import numpy as np

from app.services.semantic_search import SemanticSearchService


def test_search_passes_query_vector_to_repository(monkeypatch):
    captured = {}

    class FakeEmbeddingService:
        def embed_query(self, question):
            assert question == "Can I work remotely?"
            return np.full(384, 0.1, dtype=np.float32)

    class FakeRepository:
        def search_similar(self,session,document_id,query_vector,limit):

            captured["document_id"] = document_id
            captured["query_vector"] = query_vector
            captured["limit"] = limit
            return []

    monkeypatch.setattr("app.services.semantic_search.get_embedding_service",lambda: FakeEmbeddingService())

    monkeypatch.setattr("app.services.semantic_search.document_chunk_repository",FakeRepository())

    service = SemanticSearchService()

    results = service.search(session=None,document_id=7,question="Can I work remotely?",limit=3)

    assert results == []
    assert captured["document_id"] == 7
    assert captured["limit"] == 3
    assert len(captured["query_vector"]) == 384