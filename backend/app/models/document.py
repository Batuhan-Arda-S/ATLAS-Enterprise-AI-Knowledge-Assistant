from datetime import datetime
from sqlalchemy import DateTime,String,Text,func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Relationship
from app.database.base import Base


DOCUMENT_STATUS_PENDING = "pending"
DOCUMENT_STATUS_PROCESSED = "processed"
DOCUMENT_STATUS_FAILED = "failed"

class Document(Base):
    __tablename__ = 'documents'

    id:Mapped[int]=mapped_column(primary_key=True)

    title:Mapped[str]=mapped_column(String(225),nullable=False)

    department:Mapped[str]=mapped_column(String(100),nullable=False)

    content:Mapped[str]=mapped_column(Text(),nullable=False)

    filename:Mapped[str|None] =mapped_column(String(255),nullable=True)

    storage_key:Mapped[str|None]=mapped_column(String(500),nullable=True)

    content_type: Mapped[str | None] = mapped_column(String(100),nullable=True)

    file_size: Mapped[int | None] = mapped_column(nullable=True)

    processing_status: Mapped[str] = mapped_column(
        String(20),
        default=DOCUMENT_STATUS_PROCESSED,
        server_default=DOCUMENT_STATUS_PROCESSED,
        nullable=False)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),
                                              server_default=func.now(),
                                              nullable=False)

    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),
                                              server_default=func.now(),
                                              onupdate=func.now(),
                                              nullable=False)

    chunks:Mapped[list["DocumentChunk"]]=Relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )
