from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

Base = declarative_base()


# ===== SQLAlchemy Models (Database Tables) =====

class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)  # Store hashed password, never plain text
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ===== Pydantic Schemas (Request/Response) =====

class UserCreate(BaseModel):
    """Schema for creating new user"""
    username: str
    email: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

class UserResponse(BaseModel):
    """Schema for returning user data (no password)"""
    user_id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    """Schema for internal DB operations"""
    hashed_password: str

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
