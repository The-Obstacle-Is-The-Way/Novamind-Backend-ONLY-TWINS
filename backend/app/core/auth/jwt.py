"""
JWT authentication module for the Novamind Digital Twin system.

This module provides functions for JWT token validation, user authentication,
and related security operations following HIPAA compliant practices.
"""
import time
from datetime import datetime, UTC, UTC, timedelta
from typing import Dict, Optional, Any, Union

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# OAuth2 scheme for JWT handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

# JWT algorithms
ALGORITHM = "HS256"


def create_jwt_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT token.
    
    Args:
        data: Payload data to include in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encode the token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (DecodeError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_jwt(
    token: str = Depends(oauth2_scheme),
    raise_exception: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT token and return its payload.
    
    Args:
        token: JWT token from authorization header
        raise_exception: Whether to raise an HTTPException on validation failure
        
    Returns:
        Decoded token payload, or None if validation fails and raise_exception is False
        
    Raises:
        HTTPException: If token is invalid and raise_exception is True
    """
    try:
        return decode_jwt_token(token)
    except HTTPException as e:
        if raise_exception:
            raise e
        return None


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Extract the current user's ID from the JWT token.
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or missing user_id
    """
    payload = validate_jwt(token)
    
    # Extract user_id from payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_has_patient_access(token: str = Depends(oauth2_scheme)) -> bool:
    """
    Check if the current user has access to patient data.
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        True if user has patient access, False otherwise
    """
    payload = validate_jwt(token)
    
    # Check for patient access role
    roles = payload.get("roles", [])
    
    # Users with these roles have patient access
    patient_access_roles = [
        "admin", "provider", "clinician", "researcher", 
        "patient_coordinator", "medical_staff"
    ]
    
    return any(role in patient_access_roles for role in roles)


def get_admin_access(token: str = Depends(oauth2_scheme)) -> bool:
    """
    Check if the current user has admin access.
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        True if user has admin access, False otherwise
    """
    payload = validate_jwt(token)
    
    # Check for admin role
    roles = payload.get("roles", [])
    
    return "admin" in roles