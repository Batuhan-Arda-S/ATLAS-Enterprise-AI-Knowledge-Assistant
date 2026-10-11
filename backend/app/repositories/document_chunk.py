from sqlalchemy.orm import Session
from sqlalchemy import select,type_coerce

from pgvector.sqlalchemy import VECTOR

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

class DocumentChunkRepository:

    def create_many(self,session:Session,document_id:int,chunk_texts:list[str])->None:

        chunks=[]

        for index,text in enumerate(chunk_texts):
            chunk=DocumentChunk(document_id=document_id,chunk_index=index,content=text)

            chunks.append(chunk)

            session.add_all(chunks)

    def get_by_document(self,session:Session,document_id:int)->list[DocumentChunk]:

        statement=select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)

        return list(session.scalars(statement).all())


    def search_similar(self,session:Session,document_id:int,query_vector:list[float],limit:int=3)->list[tuple[DocumentChunk,float]]:

        if len(query_vector)!=384:
            raise ValueError("Query vector must have 384 dimensions")

        vector_column=type_coerce(DocumentChunk.embedding,VECTOR(384))

        distance=vector_column.cosine_distance(query_vector)

        statement=(select(DocumentChunk,distance.label("distance"))
                         .where(DocumentChunk.document_id==document_id,DocumentChunk.embedding.is_not(None))
                         .order_by(distance)
                         .limit(limit))

        rows=session.execute(statement).all()

        return [(chunk,float(distance)) for chunk,distance in rows]


document_chunk_repository=DocumentChunkRepository()
