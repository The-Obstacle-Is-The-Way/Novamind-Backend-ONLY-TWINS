"""
Security utilities for authentication and authorization.

This module provides security utilities for JWT token handling, password hashing,
and other security-related functionality required for HIPAA compliance.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from uuid import UUID

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: Union[str, UUID]  # User ID
    exp: Optional[int] = None  # Expiration timestamp
    roles: Optional[list[str]] = None  # User roles


# Set up password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(subject: Union[str, UUID], expires_delta: Optional[timedelta] = None, roles: Optional[list[str]] = None) -> str:
    """
    Create a JWT token with the specified subject (user ID) and expiration.
    
    Args:
        subject: Subject of the token (typically user ID)
        expires_delta: Token expiration time delta (optional)
        roles: User roles to include in the token
    
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
    }
    
    if roles:
        to_encode["roles"] = roles
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    Decode a JWT token and validate its signature.
    
    Args:
        token: JWT token to decode
        
    Returns:
        TokenPayload with decoded information
        
    Raises:
        jwt.PyJWTError: If token is invalid or verification fails
    """
    payload = jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    return TokenPayload(
        sub=payload.get("sub"),
        exp=payload.get("exp"),
        roles=payload.get("roles")
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.
    
    Args:
        plain_password: Plaintext password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password.
    
    Args:
        password: Plaintext password to hash
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)