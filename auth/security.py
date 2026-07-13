from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(
    plain_password: str, 
    hashed_password: str,
):
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    to_encode.update({
        "exp": expire,
    })

    return jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM,
    )

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    print("=" * 50)
    print("TOKEN:", token)
    print("SECRET:", SECRET_KEY)

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        print("PAYLOAD:", payload)

        user_id = payload.get("sub")
        print("USER ID:", user_id)

        if user_id is None:
            print("USER ID IS NONE")
            raise credentials_exception

    except JWTError as e:
        print("JWT ERROR:", e)
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    print("USER:", user)

    if user is None:
        print("USER NOT FOUND")
        raise credentials_exception

    print("=" * 50)

    return user