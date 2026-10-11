from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False,index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"),nullable=False,index=True)
    title: Mapped[str | None] = mapped_column(String(200),nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),onupdate=func.now())

    messages: Mapped[list["Message"]] = relationship("Message",back_populates="conversation",
                                                     cascade="all, delete-orphan",order_by="Message.id")