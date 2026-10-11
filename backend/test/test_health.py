import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.core.config import LLM_MODEL
from app.main import app
from app.routers import health


client = TestClient(app)


def test_liveness_does_not_depend_on_database_or_ollama(monkeypatch):
    class UnavailableEngine:
        def connect(self):
            raise RuntimeError("database password should stay private")

    monkeypatch.setattr(health, "engine", UnavailableEngine())
    assert client.get("/health/live").json() == {"status": "alive"}


def test_readiness_requires_database_and_current_migration(monkeypatch):
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with test_engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('current_head')"))

    monkeypatch.setattr(health, "engine", test_engine)
    monkeypatch.setattr(health, "migration_heads", lambda: frozenset({"current_head"}))

    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

    monkeypatch.setattr(health, "migration_heads", lambda: frozenset({"new_head"}))
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}


def test_readiness_failure_does_not_expose_database_details(monkeypatch, caplog):
    class UnavailableEngine:
        def connect(self):
            raise RuntimeError("password=private-value host=internal-db")

    monkeypatch.setattr(health, "engine", UnavailableEngine())
    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}
    assert "private-value" not in caplog.text
    assert "internal-db" not in caplog.text


def test_readiness_rejects_missing_schema(monkeypatch):
    monkeypatch.setattr(health, "engine", create_engine("sqlite://", poolclass=StaticPool))
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}


def test_ollama_model_probe_is_separate_from_readiness(monkeypatch):
    def available_client():
        return httpx.Client(
            base_url="http://ollama.invalid",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"models": [{"name": LLM_MODEL}]})
            ),
        )

    monkeypatch.setattr(health, "ollama_client", available_client)
    assert client.get("/health/ollama").json() == {"status": "available"}

    def missing_model_client():
        return httpx.Client(
            base_url="http://ollama.invalid",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"models": [{"name": "other-model"}]})
            ),
        )

    monkeypatch.setattr(health, "ollama_client", missing_model_client)
    assert client.get("/health/ollama").status_code == 503


def test_ollama_probe_hides_connection_error(monkeypatch, caplog):
    def unavailable_client():
        def fail(_: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("secret-in-ollama-url")

        return httpx.Client(base_url="http://ollama.invalid", transport=httpx.MockTransport(fail))

    monkeypatch.setattr(health, "ollama_client", unavailable_client)
    response = client.get("/health/ollama")
    assert response.status_code == 503
    assert response.json() == {"detail": "Model unavailable"}
    assert "secret-in-ollama-url" not in caplog.text
