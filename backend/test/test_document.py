def create_test_document(client):
    response=client.post("/documents/",json={
        "title":"Test Document",
        "department":"Testing",
        "content":"Test Content"
    })
    assert response.status_code == 201
    return response.json()


def test_documents_empty(client):
    response=client.get("/documents/")

    assert response.status_code == 200

    assert response.json() =={
        "items": [],
        "total":0,
        "offset":0,
        "limit":10
    }

def test_create_document(client):
    response=client.post("/documents/",
                         json={
                             "title":"Test Document",
                             "department":"Testing",
                             "content":"This document exists only during the test."
                         })

    assert response.status_code == 201

    data=response.json()
    assert data["title"] == "Test Document"
    assert data["department"] == "Testing"
    assert data["content"] == "This document exists only during the test."
    assert "id" in data


def test_get_document_by_id(client):
    created_document=create_test_document(client)

    document_id=created_document["id"]

    response=client.get(f"/documents/{document_id}")
    assert response.status_code == 200
    data=response.json()

    assert data["id"] == document_id
    assert data["title"] == "Test Document"
    assert data["department"] == "Testing"
    assert data["content"] == "Test Content"

def test_update_document(client):
    created_document=create_test_document(client)

    document_id=created_document["id"]

    response=client.patch(f"/documents/{document_id}",json={
        "title":"Updated Document",
    })

    assert response.status_code == 200

    data=response.json()

    assert data["id"] == document_id
    assert data["title"] == "Updated Document"
    assert data["department"] == "Testing"
    assert data["content"] == "Test Content"

    get_response=client.get(f"/documents/{document_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Updated Document"


def test_delete_document(client):
    created_document=create_test_document(client)
    document_id=created_document["id"]

    response=client.delete(f"/documents/{document_id}")
    assert response.status_code == 200
    data=response.json()

    assert data["message"] == "Document Deleted Successfully"
    assert data["document"]["id"]==document_id
    assert data["document"]["title"] == "Test Document"

    get_response=client.get(f"/documents/{document_id}")
    assert get_response.status_code == 404
    assert get_response.json()=={"detail":"File Not Found"}

def test_get_nonexistent_document(client):
    response=client.get("/documents/999999")

    assert response.status_code == 404
    assert response.json()=={"detail":"File Not Found"}


def test_document_cors(client):
    origin="http://localhost:5173"
    document=create_test_document(client)

    response=client.get(f"/documents/{document['id']}",headers={"Origin":origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin

    missing=client.get("/documents/999999",headers={"Origin":origin})
    assert missing.status_code == 404
    assert missing.headers["access-control-allow-origin"] == origin

    preflight=client.options(f"/documents/{document['id']}",headers={
        "Origin":origin,
        "Access-Control-Request-Method":"GET"
    })
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == origin
    assert "GET" in preflight.headers["access-control-allow-methods"]


def test_create_document_with_blank_title(client):
    response=client.post("/documents/",json={
        "title": "    ",
        "department": "Testing",
        "content": "Test Content"
    })

    assert response.status_code == 422
    assert "detail" in response.json()

def test_create_document_without_department(client):
    response=client.post("/documents/",json={
        "title": "Test Document",
        "content": "Test Content"
    })

    assert response.status_code == 422

def test_update_document_with_empty_body(client):
    created_document=create_test_document(client)

    document_id=created_document["id"]
    response=client.patch(f"/documents/{document_id}",json={})

    assert response.status_code == 422

def test_update_document_with_null_field(client):
    created_document=create_test_document(client)
    document_id=created_document["id"]

    response=client.patch(f"/documents/{document_id}",json={
        "title": None,
    })
    assert response.status_code == 422


def test_get_documents_with_negative_offset(client):
    response=client.get("/documents/?offset=-1")

    assert response.status_code == 422

def test_get_documents_with_zero_limit(client):
    response = client.get("/documents/?limit=0")

    assert response.status_code == 422

def test_get_documents_with_too_large_limit(client):
    response = client.get("/documents/?limit=101")

    assert response.status_code == 422

def test_get_documents_with_invalid_offset_type(client):
    response = client.get("/documents/?offset=hello")

    assert response.status_code == 422


