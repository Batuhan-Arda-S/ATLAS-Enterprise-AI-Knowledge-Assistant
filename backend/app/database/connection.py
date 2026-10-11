import os

from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import(
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER
    )

if os.getenv("DATABASE_URL"):
    DATABASE_URL = make_url(os.environ["DATABASE_URL"])
    if DB_PASSWORD:
        DATABASE_URL = DATABASE_URL.set(password=DB_PASSWORD)
else:
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

engine = create_engine(DATABASE_URL)


def check_database_connection() -> tuple[str,str]:
    with engine.connect() as connection:
        result=connection.execute(
            text(
                "SELECT current_database(),current_user"
            )
        )

        database_name,database_user=result.one()
        return database_name,database_user

if __name__ == "__main__":
    database_name,database_user=check_database_connection()

    print(f"Connected database: {database_name}")
    print(f"Connected user: {database_user}")
