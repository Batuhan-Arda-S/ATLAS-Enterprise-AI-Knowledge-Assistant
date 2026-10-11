import argparse

from app.database.session import get_session
from app.models.document import Document

from app.services.document_embedding import DocumentEmbeddingService, document_embedding_service


def main():

    parser=argparse.ArgumentParser()

    parser.add_argument('document_id', type=int)

    args=parser.parse_args()

    session_generator=get_session()
    session=next(session_generator)

    try:
        count=document_embedding_service.embed_document(session=session,document_id=args.document_id)

        print(f"{count} embeddings saved.")

    finally:
        session_generator.close()


if __name__=="__main__":
    main()
