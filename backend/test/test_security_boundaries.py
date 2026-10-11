from datetime import datetime, timedelta, timezone
import secrets

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import security
from app.core.security import hash_password
from app.database.base import Base
from app.database.session import get_session
from app.main import app
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.message import Message
from app.models.user import User


@pytest.fixture
def isolated_app(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    secret = secrets.token_hex(32)
    monkeypatch.setattr(security, "JWT_SECRET_KEY", secret)

    def get_test_session():
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    monkeypatch.setattr("app.routers.chat_stream.SessionFactory", factory)
    monkeypatch.setattr("app.routers.ask.SessionFactory", factory)

    with factory.begin() as session:
        users = [
            User(email=f"{name}@example.com", hashed_password=hash_password("test-password"), role=role)
            for name, role in (
                ("employee-a", "employee"), ("employee-b", "employee"),
                ("admin-a", "admin"), ("admin-b", "admin"),
                ("inactive", "employee"),
            )
        ]
        users[4].is_active = False
        session.add_all(users)
        session.flush()
        document = Document(title="Policy", department="HR", content="Manager approval is required.")
        session.add(document)
        session.flush()
        chunk = DocumentChunk(document_id=document.id, chunk_index=0, content=document.content)
        session.add(chunk)
        session.flush()
        conversation = Conversation(user_id=users[2].id, document_id=document.id)
        session.add(conversation)
        session.flush()
        session.add(Message(conversation_id=conversation.id, role="assistant",
                            content=f"Approval is required [[chunk:{chunk.id}]].",
                            answer_status="answered", cited_chunk_ids=[chunk.id]))
        ids = {"employees": [users[0].id, users[1].id],
               "admins": [users[2].id, users[3].id], "inactive": users[4].id,
               "document": document.id, "chunk": chunk.id, "conversation": conversation.id}

    with TestClient(app) as client:
        yield client, ids, secret

    app.dependency_overrides.clear()
    engine.dispose()


def auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {security.create_access_token(user_id)}"}


def test_missing_invalid_modified_and_expired_tokens_are_rejected(isolated_app):
    client, ids, secret = isolated_app
    valid = security.create_access_token(ids["admins"][0])
    expired = jwt.encode({"sub": str(ids["admins"][0]),
                          "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, secret, algorithm="HS256")
    head, body, signature = valid.split(".")
    modified = f"{head}.{body}.{'A' if signature[0] != 'A' else 'B'}{signature[1:]}"
    no_expiry = jwt.encode({"sub": str(ids["admins"][0]),
                            "iat": datetime.now(timezone.utc)}, secret, algorithm="HS256")
    for token in (None, "invalid", modified, expired, no_expiry):
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        for path in ("/users/me", "/documents/", f"/chat/{ids['conversation']}"):
            assert client.get(path, headers=headers).status_code == 401
    assert client.get("/users/me", headers=auth(ids["admins"][0])).status_code == 200


def test_inactive_user_cannot_login(isolated_app):
    client, ids, _ = isolated_app
    response = client.post("/users/login", json={
        "email": "inactive@example.com", "password": "test-password",
    })
    assert response.status_code == 401
    assert client.get("/users/me", headers=auth(ids["inactive"])).status_code == 401


def test_employees_cannot_use_admin_document_and_chat_routes(isolated_app):
    client, ids, _ = isolated_app
    for user_id in ids["employees"]:
        headers = auth(user_id)
        assert client.get("/documents/", headers=headers).status_code == 403
        assert client.get(f"/documents/{ids['document']}", headers=headers).status_code == 403
        assert client.get(f"/documents/{ids['document']}/chunks/{ids['chunk']}", headers=headers).status_code == 403
        assert client.post(f"/documents/{ids['document']}/search", headers=headers,
                           json={"question": "Approval?"}).status_code == 403
        assert client.post("/ask", headers=headers,
                           json={"document_id": ids["document"], "question": "Approval?"}).status_code == 403
        assert client.get("/chat/", headers=headers).status_code == 403
        assert client.post(f"/chat/{ids['conversation']}/stream", headers=headers,
                           json={"question": "Approval?"}).status_code == 403
        assert client.post("/documents/upload", headers=headers).status_code == 403
        assert client.delete(f"/documents/{ids['document']}", headers=headers).status_code == 403


def test_other_admin_cannot_read_or_stream_conversation(isolated_app):
    client, ids, _ = isolated_app
    owner = auth(ids["admins"][0])
    other = auth(ids["admins"][1])
    conversation_id = ids["conversation"]
    assert client.get(f"/chat/{conversation_id}", headers=owner).status_code == 200
    assert client.get(f"/chat/{conversation_id}", headers=other).status_code == 404
    assert client.get("/chat/", headers=other).json() == []
    response = client.post(f"/chat/{conversation_id}/stream", headers=other,
                           json={"question": "Approval?"})
    assert response.status_code == 404


def test_citation_respects_document_and_global_admin_policy(isolated_app):
    client, ids, _ = isolated_app
    path = f"/documents/{ids['document']}/chunks/{ids['chunk']}"
    assert client.get(path, headers=auth(ids["admins"][1])).status_code == 200
    assert client.get(path, headers=auth(ids["employees"][0])).status_code == 403
    assert client.get(f"/documents/{ids['document'] + 1}/chunks/{ids['chunk']}",
                      headers=auth(ids["admins"][0])).status_code == 404


def test_chat_stream_rejects_oversized_question(isolated_app):
    client, ids, _ = isolated_app
    response = client.post(f"/chat/{ids['conversation']}/stream",
                           headers=auth(ids["admins"][0]), json={"question": "x" * 1001})
    assert response.status_code == 422


def test_cors_does_not_trust_arbitrary_loopback_port(isolated_app):
    client, _, _ = isolated_app
    response = client.options("/users/me", headers={
        "Origin": "http://localhost:9999",
        "Access-Control-Request-Method": "GET",
    })
    assert response.headers.get("access-control-allow-origin") is None
    allowed = client.options("/users/me", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    })
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_document_json_inputs_have_database_and_resource_limits(isolated_app):
    client, ids, _ = isolated_app
    headers = auth(ids["admins"][0])
    for title, content in (("x" * 226, "Policy"), ("Policy", "x" * 200_001)):
        response = client.post("/documents/", headers=headers,
                               json={"title": title, "department": "HR", "content": content})
        assert response.status_code == 422
