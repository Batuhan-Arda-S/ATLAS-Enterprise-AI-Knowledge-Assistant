import pytest
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_session
from app.main import app
from app.dependencies.auth import require_admin
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(TEST_DATABASE_URL,connect_args={"check_same_thread":False} , poolclass=StaticPool)

TestSessionFactory = sessionmaker(bind=test_engine)

def override_get_session():
    session = TestSessionFactory()

    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(monkeypatch):
    Base.metadata.create_all(bind=test_engine)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[require_admin] = lambda: type("TestAdmin",(),{"id":1,"role":"admin"})()
    monkeypatch.setattr("app.services.document.get_embedding_service",
                        lambda: type("TestEmbedding",(),{
                            "embed_passages":lambda self,texts: np.ones((len(texts),384),dtype=np.float32)
                        })())

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(client):
    session = TestSessionFactory()

    try:
        yield session
    finally:
        session.close()
