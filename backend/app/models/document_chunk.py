from sqlalchemy import ForeignKey,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import JSON
from pgvector.sqlalchemy import VECTOR

from app.database.base import Base

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'

    __table_args__=(
        UniqueConstraint('document_id',"chunk_index",name="uq_document_chunks_document_index"),
    )

    id:Mapped[int]=mapped_column(primary_key=True)

    document_id :Mapped[int]=mapped_column(ForeignKey("documents.id",ondelete="CASCADE"),
                                           nullable=False,
                                           index=True)


    chunk_index:Mapped[int]=mapped_column(nullable=False)

    content:Mapped[str]=mapped_column(Text, nullable=False)

    document:Mapped["Document"]=relationship("Document",back_populates="chunks")

    embedding:Mapped[list[float]|None]=mapped_column(JSON().with_variant(VECTOR(384),"postgresql"),nullable=True)



