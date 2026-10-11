from app.models.document import Document
from app.models.document_chunk import DocumentChunk

import pytest
from sqlalchemy.exc import IntegrityError

def test_document_chunks_are_linked_and_ordered(db_session):
    document=Document(
        title="Employee Handbook",
        department="Human Resources",
        content="Full document text"
    )

    document.chunks.append(DocumentChunk(chunk_index=1,content="Second chunk"))
    document.chunks.append(DocumentChunk(chunk_index=0,content="First chunk"))

    db_session.add(document)
    db_session.commit()

    db_session.expire_all()

    assert len(document.chunks)==2

    assert [chunk.chunk_index for chunk in document.chunks] == [0, 1]

def test_duplicate_chunk_index_is_rejected(db_session):

    document=Document(title="Security Policy",department="IT",content="Security policy text")

    db_session.add(document)
    db_session.flush()

    db_session.add_all([
        DocumentChunk(document_id=document.id,chunk_index=0,content="First"),
    DocumentChunk(document_id=document.id,chunk_index=0,content="Duplicate")])

    with pytest.raises(IntegrityError):db_session.commit()

    db_session.rollback()


def test_deleting_document_deletes_chunks(db_session):

    document=Document(title="Old Policy",department="HR",content="Old policy text")

    document.chunks.append(DocumentChunk(chunk_index=0,content="Old chunk"))

    db_session.add(document)
    db_session.commit()

    chunk_id=document.chunks[0].id

    db_session.delete(document)
    db_session.commit()

    deleted_chunk=db_session.get(DocumentChunk,chunk_id)

    assert deleted_chunk is None



def test_chunk_embedding_can_be_stored(db_session):
    document=Document(title="Remote Work Policy",
                      department="HR",
                      content="Full policy text")

    vector=[0.1]*384

    document.chunks.append(DocumentChunk(chunk_index=0,content="Remote work is allowed.",embedding=vector))

    db_session.add(document)
    db_session.commit()

    chunk_id=document.chunks[0].id

    db_session.expire_all()

    stored_chunk=db_session.get(DocumentChunk,chunk_id)

    assert stored_chunk is not None
    assert stored_chunk.embedding is not None
    assert len(stored_chunk.embedding) == 384
    assert stored_chunk.embedding[0] == 0.1