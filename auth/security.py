import secrets
from datetime import datetime, timedelta
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
import jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()


# ===== Password Functions =====

def hash_password(password: str) -> str:
    """Hash a plain text password for storage"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ===== JWT Token Functions =====

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ===== Database Dependency =====

def get_db():
    """Dependency to get database session"""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== Authentication Functions (Database-backed) =====

def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> dict:
    """
    Authenticate user from HTTP Basic Auth credentials against database.
    NO HARDCODING - checks database for user and validates password hash.
    """
    from .models import User
    
    username = credentials.username
    password = credentials.password
    
    # Query database for user
    user = db.query(User).filter(User.username == username).first()
    
    # Verify user exists and password matches
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"}
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return {"user_id": user.user_id, "username": user.username, "is_admin": user.is_admin}


def authenticate_user(username: str, password: str, db: Session):
    """
    Authenticate user with username and password.
    Returns User object if valid, None otherwise.
    """
    from .models import User
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_from_token(token: str, db: Session):
    """Extract and validate user from JWT token"""
    payload = decode_access_token(token)
    username = payload.get("username")
    
    from .models import User
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
