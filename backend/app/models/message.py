from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')",name="ck_messages_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"),
                                                nullable=False,index=True)

    role: Mapped[str] = mapped_column(String(20),nullable=False)
    content: Mapped[str | None] = mapped_column(Text,nullable=True)
    answer_status: Mapped[str | None] = mapped_column(String(30),nullable=True)
    cited_chunk_ids: Mapped[list[int] | None] = mapped_column(JSON,nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())

    conversation: Mapped["Conversation"] = relationship("Conversation",back_populates="messages")