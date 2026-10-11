"""Minimal public probes for the local deployment."""

import logging
from functools import lru_cache

import httpx
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.core.config import BACKEND_DIR, LLM_MODEL, OLLAMA_BASE_URL
from app.database.connection import engine


router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def migration_heads() -> frozenset[str]:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    return frozenset(ScriptDirectory.from_config(config).get_heads())


def ollama_client() -> httpx.Client:
    return httpx.Client(base_url=OLLAMA_BASE_URL, timeout=3.0)


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
def ready() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()
            revisions = frozenset(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())
        expected = migration_heads()
    except Exception as exc:
        logger.warning("Readiness probe failed: error_type=%s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Service not ready") from None

    if not expected or revisions != expected:
        logger.warning("Readiness probe failed: schema migration incomplete")
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


@router.get("/ollama")
def ollama() -> dict[str, str]:
    try:
        with ollama_client() as client:
            response = client.get("/api/tags")
            response.raise_for_status()
            models = response.json()["models"]
            available = any(isinstance(model, dict) and model.get("name") == LLM_MODEL for model in models)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.warning("Ollama probe failed: error_type=%s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Model unavailable") from None

    if not available:
        logger.warning("Ollama probe failed: configured model unavailable")
        raise HTTPException(status_code=503, detail="Model unavailable")

    return {"status": "available"}
