from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.dependencies.auth import get_current_user,require_admin
from app.main import app
from app.models.document_chunk import DocumentChunk
from app.services.chat import ChatService


def test_document_endpoints_require_authentication():
    with TestClient(app) as client:
        assert client.get("/documents/").status_code == 401
        assert client.get("/documents/1").status_code == 401
        assert client.get("/documents/1/chunks/1").status_code == 401
        assert client.post("/documents/upload").status_code == 401


def test_employee_cannot_read_documents(client):
    app.dependency_overrides.pop(require_admin)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2,role="employee")
    assert client.get("/documents/").status_code == 403
    assert client.get("/chat/").status_code == 403


def test_conversation_history_is_owned_and_chronological(client,db_session):
    document = client.post("/documents/",json={
        "title":"Rules","department":"HR","content":"Employees need approval."
    }).json()
    created = client.post("/chat/",json={"document_id":document["id"]})
    assert created.status_code == 201
    conversation_id = created.json()["id"]
    assert client.get("/chat/").json()[0]["id"] == conversation_id

    service = ChatService()
    service.add_message(db_session,conversation_id,1,"user","Is approval needed?")
    service.add_message(db_session,conversation_id,1,"assistant","Yes [[chunk:4]].",
                        answer_status="answered",cited_chunk_ids=[4])
    db_session.commit()
    detail = client.get(f"/chat/{conversation_id}")
    assert detail.status_code == 200
    assert [message["role"] for message in detail.json()["messages"]] == ["user","assistant"]
    assert client.delete(f"/documents/{document['id']}").status_code == 409

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id=2,role="admin")
    assert client.get(f"/chat/{conversation_id}").status_code == 404
    assert client.get("/chat/").json() == []


def test_source_returns_only_matching_document_chunk(client,db_session):
    document = client.post("/documents/upload",data={"title":"Policy","department":"HR"},
        files={"file":("policy.txt",b"Employees need manager approval.","text/plain")}).json()
    chunk = db_session.scalar(select(DocumentChunk).where(
        DocumentChunk.document_id == document["id"]))
    response = client.get(f"/documents/{document['id']}/chunks/{chunk.id}")
    assert response.status_code == 200
    assert response.json()["content"] == "Employees need manager approval."
    assert client.get(f"/documents/{document['id'] + 1}/chunks/{chunk.id}").status_code == 404
