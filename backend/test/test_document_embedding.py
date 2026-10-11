import numpy as np
import pytest
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk import document_chunk_repository
from app.services.document_embedding import document_embedding_service

def test_document_embeddings_are_saved_once(db_session,monkeypatch):

    document=Document(title="HR Policy",department="HR",content="Remote work and annual leave")

    document.chunks=[DocumentChunk(chunk_index=0,content="Remote work is allowed."),
                     DocumentChunk(chunk_index=1,content="Annual leave is 20 days.")]

    db_session.add(document)
    db_session.commit()

    document_id=document.id

    class FakeEmbeddingService:
        calls=0

        def embed_passages(self,texts):
            self.calls+=1

            assert texts==["Remote work is allowed.","Annual leave is 20 days."]

            return np.array([[0.1]*384,
                                    [0.2]*384],dtype=np.float32)

    fake_service=FakeEmbeddingService()

    monkeypatch.setattr("app.services.document_embedding.get_embedding_service",
                        lambda:fake_service)

    first_count=document_embedding_service.embed_document(db_session,document_id)

    assert first_count==2

    db_session.expire_all()

    stored_chunks=document_chunk_repository.get_by_document(db_session,document_id)

    assert len(stored_chunks)==2

    assert stored_chunks[0].embedding[0] == pytest.approx(0.1)
    assert stored_chunks[1].embedding[0] == pytest.approx(0.2)


    second_count=document_embedding_service.embed_document(db_session,document_id)

    assert second_count==0
    assert fake_service.calls==1



def test_wrong_embedding_shape_is_rejected(db_session,monkeypatch):

    document=Document(title="Security Policy",
                      department="IT",
                      content="Full security text")

    document.chunks = [DocumentChunk(chunk_index=0,content="First security rule."),
                       DocumentChunk(chunk_index=1,content="Second security rule.")]


    db_session.add(document)
    db_session.commit()

    class WrongEmbeddingService:
        def embed_passages(self,texts):
            return np.zeros((1,384),dtype=np.float32)


    monkeypatch.setattr("app.services.document_embedding.get_embedding_service",lambda: WrongEmbeddingService())

    with pytest.raises(ValueError):
        document_embedding_service.embed_document(db_session,document.id)

    db_session.expire_all()

    stored_chunks=document_chunk_repository.get_by_document(db_session,document.id)

    assert all(chunk.embedding is None for chunk in stored_chunks)