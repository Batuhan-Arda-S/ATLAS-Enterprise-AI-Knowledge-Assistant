from jinja2.utils import missing
from sqlalchemy.orm import Session
from app.repositories.document_chunk import document_chunk_repository

from app.services.embedding import get_embedding_service

EMBEDDING_DIMENSIONS=384

class DocumentEmbeddingService:

    def embed_document(self,session:Session,document_id:int)->int:

        try:
            chunks=document_chunk_repository.get_by_document(session=session,document_id=document_id)

            missing_chunks=[chunk for chunk in chunks if chunk.embedding is None]

            if not missing_chunks:
                return 0

            texts=[chunk.content for chunk in missing_chunks]

            vectors=get_embedding_service().embed_passages(texts)

            expected_shape=(len(missing_chunks),EMBEDDING_DIMENSIONS)

            if vectors.shape != expected_shape:
                raise ValueError(f"Unexpected embedding shape: {vectors.shape}")

            for chunk,vector in zip(missing_chunks,vectors):
                chunk.embedding=vector.tolist()

            session.commit()

            return len(missing_chunks)

        except Exception:
            session.rollback()
            raise


document_embedding_service=DocumentEmbeddingService()