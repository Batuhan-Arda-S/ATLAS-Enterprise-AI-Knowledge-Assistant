from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Enterprise AI Knowledge Assistant API is running"}


def test_local_development_login_preflight():
    for origin in ("http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5174"):
        response = client.options("/users/login", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_unrelated_origin_cannot_preflight_login():
    response = client.options("/users/login", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
