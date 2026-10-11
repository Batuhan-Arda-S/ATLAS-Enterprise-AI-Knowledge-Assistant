from collections.abc import Iterator
from sqlalchemy.orm import Session, sessionmaker
from app.database.connection import engine

SessionFactory = sessionmaker(bind=engine)

def get_session() -> Iterator[Session]:
    session = SessionFactory()

    try:
        yield session
    finally:
        session.close()


def check_session() -> None:
    with SessionFactory() as session:
        print(type(session))


if __name__ == "__main__":
    check_session()