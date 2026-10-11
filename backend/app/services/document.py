from app.exceptions import document
from app.models.document import Document,DOCUMENT_STATUS_PENDING,DOCUMENT_STATUS_PROCESSED,DOCUMENT_STATUS_FAILED
from sqlalchemy.orm import Session
from app.repositories.document_database import (
    document_database_repository as document_repository, document_database_repository
)
from app.exceptions.document import DocumentNotFoundError

from app.models.document import DOCUMENT_STATUS_PENDING,Document
from app.services.file_storage import file_storage
from app.services.document_parser import DocumentParser, document_parser
from app.services.chunking import chunking_service
from app.repositories.document_chunk import document_chunk_repository
from app.services.embedding import get_embedding_service
import logging

logger = logging.getLogger(__name__)

class DocumentService:

    def create_document(self,session:Session,document_data: dict) -> Document:

        try:
            document=document_repository.create(session=session,document_data=document_data)

            session.commit()
            return document

        except Exception:
            session.rollback()
            raise


    def get_documents(self,
                      session: Session,
                      offset:int=10,
                      limit:int=10)->dict:
        documents = document_repository.get_all(session=session,offset=offset, limit=limit)

        total=document_repository.count_all(session=session)
        return{
            "items":documents,
            "total":total,
            "offset":offset,
            "limit":limit
        }

    def get_document(self,session:Session,document_id:int)->Document:

        document=document_repository.get_by_id(session=session,document_id=document_id)

        if document is None:
            raise DocumentNotFoundError()

        return document



    def update_document(self,session:Session,document_id:int,update_data:dict)->Document:

        try:
            document = document_repository.update(session=session,document_id=document_id,update_data=update_data)

            if document is None:
                raise DocumentNotFoundError()

            session.commit()

            return document

        except Exception:
            session.rollback()
            raise




    def delete_document(self,session:Session,document_id:int)-> dict:

        try:
            document=session.get(Document,document_id)
            if document is None:
                raise DocumentNotFoundError()
            storage_key=document.storage_key
            deleted_document=document_repository.delete(session=session,document_id=document_id)
            session.commit()
            if storage_key:
                try:
                    file_storage.delete(storage_key)
                except OSError:
                    logger.exception("Document file cleanup failed for document %s",document_id)
            return deleted_document

        except Exception:
            session.rollback()
            raise


    def create_uploaded_document(self,session:Session,title:str,department:str,filename:str|None,content_type:str|None,contents:bytes)->Document:

        storage_key=file_storage.save(contents=contents,original_filename=filename)

        database_data={
            "title":title,
            "department":department,
            "content":"",
            "filename":filename,
            "storage_key":storage_key,
            "content_type":content_type,
            "file_size":len(contents),
            "processing_status":DOCUMENT_STATUS_PENDING
        }
        try:
            document=document_repository.create(session=session,document_data=database_data)
            session.commit()

        except Exception:
            session.rollback()

            file_storage.delete(storage_key)

            raise


        try:

            extracted_text=(document_parser.extract_text(contents=contents,
                                                         content_type=content_type))

            if not extracted_text.strip():
                raise ValueError("No extractable text")


        except Exception:
            document.processing_status=(DOCUMENT_STATUS_FAILED)

            try:
                session.commit()

            except Exception:
                session.rollback()

            return document

        document_id=document.id
        try:
            chunk_texts=chunking_service.split_text_smart(text=extracted_text,
                                                          chunk_size=500)
            vectors=get_embedding_service().embed_passages(chunk_texts)
            if vectors.shape != (len(chunk_texts),384):
                raise ValueError("Unexpected passage embedding shape")

            document_chunk_repository.create_many(session=session,
                                                  document_id=document.id,
                                                  chunk_texts=chunk_texts)
            chunks=document_chunk_repository.get_by_document(session=session,document_id=document.id)
            for chunk,vector in zip(chunks,vectors):
                chunk.embedding=vector.tolist()

            document.content=extracted_text
            document.processing_status=DOCUMENT_STATUS_PROCESSED

            session.commit()

        except Exception:
            session.rollback()
            document=session.get(Document,document_id)
            document.processing_status=DOCUMENT_STATUS_FAILED
            session.commit()

        return document


document_service = DocumentService()


