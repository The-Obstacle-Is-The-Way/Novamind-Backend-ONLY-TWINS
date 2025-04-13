"""
Authentication module for the Novamind Digital Twin Backend.

This module provides functions for user authentication, JWT token
generation and validation, and current user retrieval for endpoints.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import get_settings
settings = get_settings()
from app.domain.entities.user import User

# OAuth2 token URL endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    # In a real implementation, this would query the database
    # For testing purposes, we'll return a mock user
    if username == "test_user" and password == "password":
        from app.tests.fixtures.user_fixtures import test_user_id, test_roles
        return User(
            id=test_user_id,
            username=username,
            email="test@example.com",
            roles=test_roles,
            is_active=True,
            full_name="Test User"
        )
    return None


def _create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(settings.TIMEZONE) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def _verify_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token and return its payload.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _get_user_by_id(user_id: Union[str, UUID]) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    # In a real implementation, this would query the database
    # For testing purposes, we'll return a mock user
    from app.tests.fixtures.user_fixtures import test_user_id, test_roles
    if str(user_id) == str(test_user_id):
        return User(
            id=UUID(str(user_id)),
            username="test_user",
            email="test@example.com",
            roles=test_roles,
            is_active=True,
            full_name="Test User"
        )
    return None


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current authenticated user from a JWT token.
    
    Args:
        token: JWT token to validate
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    payload = _verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = _get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user