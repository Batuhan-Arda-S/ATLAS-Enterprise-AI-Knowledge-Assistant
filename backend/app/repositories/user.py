from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

class UserRepository:

    def get_by_email(self,session:Session,email: str) -> User|None:

        statement=select(User).where(User.email==email)

        return session.scalars(statement).one_or_none()

    def create(self,session:Session,user_data:dict) -> User:
        user=User(**user_data)

        session.add(user)
        session.flush()
        session.refresh(user)

        return user

    def get_by_id(self,session:Session,user_id:int) -> User|None:

        return session.get(User,user_id)

user_repository=UserRepository()