import pytest

from app.exceptions.document import DocumentNotFoundError
from app.repositories.document_database import (document_database_repository)


def test_create_document_rolls_back_when_error_occurs(client,monkeypatch):

    original_create=document_database_repository.create

    def create_then_fail(*,session,document_data):
        original_create(session=session,document_data=document_data)

        raise RuntimeError("Forced transaction failure")

    monkeypatch.setattr(document_database_repository,'create',create_then_fail)

    with pytest.raises(RuntimeError,match="Forced transaction failure"):

        client.post("/documents",json={
            "title":"Rollback Test",
            "department":"Testing",
            "content":"This must not remain in the database."
        })

    response=client.get("/documents/")

    assert response.status_code == 200
    assert response.json()["total"]==0
    assert response.json()["items"]==[]
