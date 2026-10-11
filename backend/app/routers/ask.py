from dataclasses import asdict
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import LLM_MODEL, OLLAMA_BASE_URL
from app.database.session import SessionFactory
from app.dependencies.auth import get_current_user
from app.models.document import Document
from app.models.user import User, ROLE_ADMIN
from app.schemas.ask import AskRequest, AskResponse
from app.services.citation_validation import InvalidCitationError
from app.services.llm import LLMService, LLMServiceError
from app.services.rag import RAGService
from app.services.semantic_search import semantic_search_service

router = APIRouter(tags=["rag"])
logger = logging.getLogger(__name__)


@router.post("/ask",response_model=AskResponse)
def ask(payload: AskRequest,current_user: User = Depends(get_current_user)) -> AskResponse:
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403,detail="Document access is not permitted")

    with SessionFactory() as session:
        document = session.get(Document,payload.document_id)

        if document is None:
            raise HTTPException(status_code=404,detail="Document not found")

    try:
        with httpx.Client(base_url=OLLAMA_BASE_URL,timeout=120.0) as client:
            llm_service = LLMService(client=client,model=LLM_MODEL)

            rag_service = RAGService(session_factory=SessionFactory,
                                     search_service=semantic_search_service,
                                     llm_service=llm_service)

            result = rag_service.answer(document_id=payload.document_id,
                                        question=payload.question,
                                        limit=payload.limit)

    except (LLMServiceError,InvalidCitationError) as exc:
        logger.warning("RAG answer failed: error_type=%s", type(exc).__name__)
        raise HTTPException(status_code=502,detail="Answer generation failed") from exc

    return AskResponse(**asdict(result))
