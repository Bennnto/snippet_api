"""
Authentication module - handles user authentication and JWT tokens.
No hardcoded credentials - all users stored in database with hashed passwords.
"""

from .models import User, UserCreate, UserLogin, UserResponse, Token
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    authenticate_user,
    get_user_from_token,
)

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "authenticate_user",
    "get_user_from_token",
]
