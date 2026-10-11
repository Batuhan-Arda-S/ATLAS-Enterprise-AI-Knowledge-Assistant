from sqlalchemy.orm import Session

from app.core.security import hash_password,verify_password,create_access_token
from app.exceptions.user import UserAlreadyExistsError,InvalidCredentialsError
from app.models.user import User
from app.repositories.user import user_repository

class UserService:

    def register_user(self,session:Session,user_data:dict)->User:

        existing_user=user_repository.get_by_email(session=session,email=user_data['email'])

        if existing_user is not None:
            raise UserAlreadyExistsError()

        database_data={
            "email":user_data['email'],
            "hashed_password":hash_password(user_data['password']),
        }


        try:
            user=user_repository.create(session=session,user_data=database_data)

            session.commit()
            return user

        except Exception:
            session.rollback()
            raise

    def authenticate_user(self,session:Session,email:str,password:str)->User:

        user=user_repository.get_by_email(session=session,email=email)

        if user is None:
            raise InvalidCredentialsError()

        password_is_valid=verify_password(password,user.hashed_password)

        if not password_is_valid or not user.is_active:
            raise InvalidCredentialsError()

        return user

    def login_user(self,session:Session,email:str,password:str)->dict:

        user=self.authenticate_user(session=session,email=email,password=password)

        access_token=create_access_token(user_id=user.id)

        return {"access_token":access_token,"token_type":"bearer"}



user_service=UserService()

