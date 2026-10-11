from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.schemas.user import UserCreate, UserResponse,TokenReponse,UserLogin
from app.services.user import user_service

from app.dependencies.auth import get_current_user
from app.models.user import User

from app.dependencies.auth import get_current_user,require_admin

router=APIRouter(prefix="/users",tags=["users"])

@router.post("/register",status_code=201,response_model=UserResponse)
def register_user(user:UserCreate,session:Annotated[Session,Depends(get_session)]):

    user_data=user.model_dump()

    return user_service.register_user(session=session,user_data=user_data)

@router.post("/login",status_code=200,response_model=TokenReponse)
def login_user(credentials:UserLogin,session:Annotated[Session,Depends(get_session)]):

    return user_service.login_user(session=session,email=credentials.email,password=credentials.password)

@router.get("/me",response_model=UserResponse)
def get_me(current_user:Annotated[User,Depends(get_current_user)]):

    return current_user

@router.get("/admin-check")
def admin_check(current_user:Annotated[User,Depends(require_admin)]):

    return {"message":"Admin access granted",
            "user_id":current_user.id}
