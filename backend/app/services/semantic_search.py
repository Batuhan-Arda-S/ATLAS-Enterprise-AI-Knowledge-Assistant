from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk import document_chunk_repository

from app.services.embedding import get_embedding_service


class SemanticSearchService:

    def search(self,session:Session,document_id:int,question:str,limit:int=3)->list[tuple[DocumentChunk,float]]:

        if not question.strip():
            raise ValueError("Question cannot be blank")

        if document_id<=0:
            raise ValueError("Document ID must be positive")

        if not 1<=limit<=10:
            raise ValueError("Limit must be between 1 and 10")

        query_vector=get_embedding_service().embed_query(question)

        if query_vector.shape!=(384,):
            raise ValueError("Unexpected query embedding shape")

        return document_chunk_repository.search_similar(session=session,
                                                        document_id=document_id,
                                                        query_vector=query_vector.tolist(),
                                                        limit=limit)


semantic_search_service=SemanticSearchService()