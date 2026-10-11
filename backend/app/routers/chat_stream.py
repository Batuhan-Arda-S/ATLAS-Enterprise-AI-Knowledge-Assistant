import logging
from dataclasses import asdict
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import LLM_MODEL, OLLAMA_BASE_URL
from app.database.session import SessionFactory
from app.dependencies.auth import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.chat_stream import ChatStreamRequest
from app.services.chat import ChatService, ConversationNotFoundError
from app.services.llm import LLMService
from app.services.rag import RAGService
from app.services.semantic_search import semantic_search_service
from app.services.sse import encode_sse


router = APIRouter(tags=["Chat"])
chat_service = ChatService()
logger = logging.getLogger(__name__)


@router.post("/chat/{conversation_id}/stream")
def stream_chat(conversation_id: int,payload: ChatStreamRequest,
                current_user: Annotated[User,Depends(get_current_user)]):

    if current_user.role != "admin":
        raise HTTPException(status_code=403,detail="Document access is not permitted")

    with SessionFactory() as session:
        try:
            conversation = chat_service.get_conversation(session,conversation_id,current_user.id)
        except ConversationNotFoundError:
            raise HTTPException(status_code=404,detail="Conversation not found")

        document_id = conversation.document_id

        if session.get(Document,document_id) is None:
            raise HTTPException(status_code=404,detail="Document not found")

        saved_messages = chat_service.get_messages(session,conversation_id,current_user.id,limit=10)

        history = [{"role":message.role,"content":message.content} for message in saved_messages if message.content]

    user_id = current_user.id

    def events():
        try:
            with httpx.Client(base_url=OLLAMA_BASE_URL,timeout=120.0) as client:
                llm_service = LLMService(client=client,model=LLM_MODEL)

                rag_service = RAGService(session_factory=SessionFactory,
                                         search_service=semantic_search_service,
                                         llm_service=llm_service)

                for event_type,data in rag_service.stream_answer(document_id=document_id,
                                                                 question=payload.question,
                                                                 limit=payload.limit,
                                                                 history=history):

                    if event_type == "token":
                        yield encode_sse("token",{"text":data})
                        continue

                    result = data

                    with SessionFactory() as session:
                        with session.begin():
                            chat_service.add_message(session,conversation_id,user_id,
                                                     role="user",content=payload.question)

                            chat_service.add_message(session,
                                                     conversation_id,
                                                     user_id,
                                                     role="assistant",
                                                     content=result.answer,
                                                     answer_status=result.answer_status,
                                                     cited_chunk_ids=[source.chunk_id for source in result.cited_sources])

                    yield encode_sse("done",{"answer":result.answer,
                                             "answer_status":result.answer_status,
                                             "retrieval_status":result.retrieval_status,
                                             "cited_sources":[asdict(source) for source in result.cited_sources]})

        except Exception as exc:
            logger.error("Chat streaming failed: error_type=%s", type(exc).__name__)
            yield encode_sse("error",{"message":"Chat streaming failed"})

    return StreamingResponse(events(),media_type="text/event-stream",
                             headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
