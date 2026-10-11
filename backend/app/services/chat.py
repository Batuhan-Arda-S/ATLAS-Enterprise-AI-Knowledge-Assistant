from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationNotFoundError(Exception):
    pass


class ChatService:
    def get_conversation(self,session: Session,conversation_id: int,user_id: int) -> Conversation:
        conversation = session.scalar(
            select(Conversation).where(Conversation.id == conversation_id,
                                       Conversation.user_id == user_id))

        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

        return conversation

    def create_conversation(self,session: Session,user_id: int,document_id: int,
                            title: str | None = None) -> Conversation:

        conversation = Conversation(user_id=user_id,document_id=document_id,title=title)

        session.add(conversation)
        session.flush()

        return conversation

    def add_message(self,session: Session,conversation_id: int,user_id: int,
                    role: str,content: str | None,answer_status: str | None = None,
                    cited_chunk_ids: list[int] | None = None) -> Message:

        conversation = self.get_conversation(session,conversation_id,user_id)

        if role not in ("user","assistant"):
            raise ValueError("Invalid message role")

        if role == "user":
            if not content or not content.strip() or answer_status is not None or cited_chunk_ids is not None:
                raise ValueError("Invalid user message")

        if role == "assistant":
            if answer_status not in ("answered","no_candidates","insufficient_evidence"):
                raise ValueError("Invalid assistant status")

            if answer_status == "answered" and (not content or not cited_chunk_ids):
                raise ValueError("Answered message requires content and citations")

            if answer_status != "answered" and (content is not None or cited_chunk_ids):
                raise ValueError("Abstained message cannot contain an answer")

        message = Message(conversation_id=conversation.id,role=role,content=content,
                          answer_status=answer_status,cited_chunk_ids=cited_chunk_ids)

        session.add(message)
        conversation.updated_at = func.now()

        return message

    def get_messages(self,session: Session,conversation_id: int,user_id: int,
                     limit: int = 20) -> list[Message]:

        self.get_conversation(session,conversation_id,user_id)

        if not 1 <= limit <= 50:
            raise ValueError("Limit must be between 1 and 50")

        messages = session.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id.desc()).limit(limit)).all()

        return list(reversed(messages))

    def list_conversations(self,session: Session,user_id: int,
                           limit: int = 20) -> list[Conversation]:

        if not 1 <= limit <= 50:
            raise ValueError("Limit must be between 1 and 50")

        return session.scalars(select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc(),
                            Conversation.id.desc()).limit(limit)).all()