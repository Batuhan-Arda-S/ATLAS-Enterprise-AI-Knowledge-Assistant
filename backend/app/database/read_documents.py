from sqlalchemy import select

from app.database.session import SessionFactory
from app.models.document import Document


def list_documents()->None:
    statement = select(Document).order_by(Document.id)

    with SessionFactory() as session:
        documents=session.scalars(statement).all()

        if not documents:
            print("No Documents Found")

        for document in documents:
            print(
                f"{document.id} | "
                f"{document.title} | "
                f"{document.department}"
            )

def get_document_by_id(document_id: int)->None:
    statement = select(Document).where(Document.id == document_id)

    with SessionFactory() as session:
        document=session.scalars(statement).one_or_none()

        if document is None:
            print(f"Document with id {document_id} not found")
            return

        print(f"ID: {document.id}")
        print(f"Title: {document.title}")
        print(f"Department: {document.department}")
        print(f"Content: {document.content}")

if __name__ == "__main__":
    list_documents()