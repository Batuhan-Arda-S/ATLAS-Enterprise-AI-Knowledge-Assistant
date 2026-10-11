from datetime import datetime
from typing import Annotated

from pydantic import(BaseModel,ConfigDict,EmailStr,StringConstraints)

PasswordText=Annotated[str,StringConstraints(min_length=8,max_length=128)]


class UserCreate(BaseModel):
    email: EmailStr
    password: PasswordText


class UserLogin(BaseModel):
    email: EmailStr
    password: PasswordText


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    email:EmailStr
    role:str
    is_active:bool
    created_at:datetime
    updated_at:datetime

class TokenReponse(BaseModel):
    access_token:str
    token_type:str

