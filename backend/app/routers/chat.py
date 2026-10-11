from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.dependencies.auth import require_admin
from app.models.document import Document
from app.models.user import User
from app.schemas.chat import ConversationCreate,ConversationResponse,ConversationDetail
from app.services.chat import ChatService,ConversationNotFoundError


router = APIRouter(prefix="/chat",tags=["Chat"])
chat_service = ChatService()


@router.get("/",response_model=list[ConversationResponse])
def list_conversations(current_user: Annotated[User,Depends(require_admin)],
                       session: Annotated[Session,Depends(get_session)]):
    return chat_service.list_conversations(session,current_user.id,limit=50)


@router.post("/",response_model=ConversationResponse,status_code=201)
def create_conversation(payload: ConversationCreate,
                        current_user: Annotated[User,Depends(require_admin)],
                        session: Annotated[Session,Depends(get_session)]):
    if session.get(Document,payload.document_id) is None:
        raise HTTPException(status_code=404,detail="Document not found")
    conversation = chat_service.create_conversation(
        session,current_user.id,payload.document_id,payload.title)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get("/{conversation_id}",response_model=ConversationDetail)
def get_conversation(conversation_id: int,
                     current_user: Annotated[User,Depends(require_admin)],
                     session: Annotated[Session,Depends(get_session)]):
    try:
        conversation = chat_service.get_conversation(session,conversation_id,current_user.id)
        messages = chat_service.get_messages(session,conversation_id,current_user.id,limit=50)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404,detail="Conversation not found")
    return {"id":conversation.id,"document_id":conversation.document_id,
            "title":conversation.title,"created_at":conversation.created_at,
            "updated_at":conversation.updated_at,"messages":messages}
