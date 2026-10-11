from pwdlib import PasswordHash
from datetime import datetime,timedelta,timezone
import jwt
from app.core.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES,JWT_ALGORITHM,JWT_SECRET_KEY

password_hash=PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(user_id:int)->str:
    now = datetime.now(timezone.utc)

    expires_at=now+timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload={
        "sub":str(user_id),
        "iat":now,
        "exp":expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

def decode_access_token(token:str)->str:
    payload=jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM],
                       options={"require": ["sub", "iat", "exp"]})

    subject=payload.get("sub")

    if subject is None:
        raise ValueError("Token subject is missing")

    return int(subject)
