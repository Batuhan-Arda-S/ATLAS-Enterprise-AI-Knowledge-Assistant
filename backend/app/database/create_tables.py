from app.database.base import Base
from app.database.connection import engine
from app.models.document import Document

def create_tables() -> None:
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    create_tables()
    print('Tables created')
