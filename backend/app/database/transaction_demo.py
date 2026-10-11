from sqlalchemy.exc import IntegrityError

from app.database.session import SessionFactory
from app.models.document import Document


def test_transaction_rollback() -> None:
    valid_document = Document(
        title="Sample 2",
        department="IT",
        content="Sample 2"
    )

    invalid_document = Document(
        title=None,
        department="Finance",
        content="this document is invalid"
    )

    with SessionFactory() as session:
        try:
            session.add_all([
                valid_document,
                invalid_document
            ])

            session.commit()

            print("Documents Successfully Saved")

        except IntegrityError:
            session.rollback()

            print("One Of The Documents Is Invalid")
            print("Transaction Taken Back:None Of The Documents Is Saved")


if __name__ == "__main__":
    test_transaction_rollback()