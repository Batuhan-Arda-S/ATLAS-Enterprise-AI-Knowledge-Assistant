from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.routers.ask import ask
from app.schemas.ask import AskRequest


def test_ask_requires_jwt():
    with TestClient(app) as client:
        response = client.post("/ask",json={"document_id": 12,
                                                "question": "What is the remote work policy?"})

    assert response.status_code == 401


def test_employee_cannot_ask(monkeypatch):
    def forbidden_session():
        pytest.fail("Unauthorized request reached the database")

    monkeypatch.setattr("app.routers.ask.SessionFactory",forbidden_session)

    with pytest.raises(HTTPException) as error:
        ask(payload=AskRequest(document_id=12,question="Remote work policy?"),
            current_user=SimpleNamespace(role="employee"))

    assert error.value.status_code == 403