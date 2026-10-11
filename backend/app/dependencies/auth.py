from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.database.session import get_session
from app.exceptions.user import InvalidAccessTokenError, AdminRequiredError
from app.models.user import User,ROLE_ADMIN
from app.repositories.user import user_repository

bearer_scheme=HTTPBearer(auto_error=False)

def get_current_user(
        credentials:Annotated[HTTPAuthorizationCredentials | None,Depends(bearer_scheme)],
        session:Annotated[Session,Depends(get_session)]) -> User:

    if credentials is None:
        raise InvalidAccessTokenError()

    try:
        user_id=decode_access_token(credentials.credentials)
    except (InvalidTokenError,ValueError):
        raise InvalidAccessTokenError()

    user=user_repository.get_by_id(session=session,user_id=user_id)

    if user is None or not user.is_active:
        raise InvalidAccessTokenError()

    return user


def require_admin(current_user:Annotated[User,Depends(get_current_user)])->User:

    if current_user.role != ROLE_ADMIN:
        raise AdminRequiredError()

    return current_user

