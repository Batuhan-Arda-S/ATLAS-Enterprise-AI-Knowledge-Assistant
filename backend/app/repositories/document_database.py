from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.models.document import Document




class DocumentDatabaseRepository:

    def count_all(self,session:Session)->int:
        statement=select(func.count(Document.id))

        total=session.scalar(statement)
        return int(total)

    def create(self,session:Session,document_data:dict)->Document:
        document=Document(**document_data)

        session.add(document)
        session.flush()
        session.refresh(document)

        return document

    def get_all(self,
                session:Session,
                offset:int=0,
                limit:int=10)->list[Document]:
        statement=(
            select(Document)
            .order_by(Document.id)
            .offset(offset)
            .limit(limit)
        )

        documents=session.scalars(statement).all()

        return list(documents)


    def get_by_id(self,session:Session,document_id:int)->Document|None:
        statement=select(Document).where(Document.id == document_id)


        document=session.scalars(statement).one_or_none()

        return document


    def update(self,session:Session,document_id:int,update_data:dict)->Document|None:



            document=session.get(Document,document_id)

            if document is None:
                return None

            for field,value in update_data.items():
                setattr(document,field,value)

            session.flush()
            session.refresh(document)

            return document



    def delete(self,session:Session, document_id: int) -> dict | None:


        document = session.get(Document, document_id)

        if document is None:
            return None

        deleted_document = {
            "id": document.id,
            "title": document.title,
            "department": document.department,
            "content": document.content,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }

        session.delete(document)
        session.flush()

        return deleted_document




document_database_repository=DocumentDatabaseRepository()