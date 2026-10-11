from sqlalchemy import inspect
from app.database.session import SessionFactory
from app.models.document import Document

def insert_sample_document()->None:
    document = Document(
        title='Sample Document',
        department='Sample Department',
        content='Sample Content'
    )

    print(f"First ID Value: {document.id}")
    document_state=inspect(document)
    print(f"Is Transient?: {document_state.transient}")

    with SessionFactory() as session:
        session.add(document)

        document_state = inspect(document)

        print(f"Is Pending?: {document_state.pending}")
        print(f"ID After Added To Session: {document.id}")

        session.commit()
        session.refresh(document)

        document_state = inspect(document)
        print(f"Is Persistent?: {document_state.persistent}")
        print(f"ID Of The Saved Document: {document.id}")
        print(f"Create Time: {document.created_at}")

if __name__ == "__main__":
    insert_sample_document()


