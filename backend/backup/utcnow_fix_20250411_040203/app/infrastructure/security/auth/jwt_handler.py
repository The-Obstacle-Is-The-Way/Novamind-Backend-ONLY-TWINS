# -*- coding: utf-8 -*-
"""
HIPAA-Compliant JWT Authentication Handler

This module provides functions to create and verify JSON Web Tokens (JWTs)
for secure authentication and authorization in compliance with HIPAA requirements.

Features:
- Secure token creation with industry-standard algorithms
- Cryptographic signature verification
- Role and permission claims for authorization
- Token expiration and revocation support
- Refresh token functionality

Usage:
    # Create a token for a user
    token = create_access_token({"user_id": "123", "role": "doctor"})

    # Verify and decode a token
    payload = verify_token(token)

    # Get current user from a token
    user = get_current_user(token)
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.config import settings
from app.domain.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
)

# OAuth2 scheme for FastAPI to extract the token from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    scope: str = "access_token",
) -> str:
    """
    Create a JWT access token with a given payload and expiration time.

    Args:
        data: The payload to include in the token
        expires_delta: Optional override for token expiration time
        scope: Token scope (access_token or refresh_token)

    Returns:
        str: JWT token as string
    """
    # Get settings
    # settings object is imported directly

    # Create a copy of the data
    payload = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    payload.update(
        {
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "sub": str(data.get("user_id", "")),
            "jti": str(uuid.uuid4()),  # Unique token ID for potential revocation
            "scope": scope,
        }
    )

    # Encode the token
    encoded_jwt = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with a given payload and longer expiration time.

    Args:
        data: The payload to include in the token

    Returns:
        str: JWT refresh token as string
    """
    # Get settings
    # settings object is imported directly

    # Create refresh token with longer expiration (default to 7 days if not specified)
    refresh_expire_days = getattr(settings, "JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7)
    refresh_expire = timedelta(days=refresh_expire_days)

    # Create minimal payload for refresh token
    minimal_payload = {"user_id": data.get("user_id"), "role": data.get("role")}

    return create_access_token(
        data=minimal_payload, expires_delta=refresh_expire, scope="refresh_token"
    )


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token and return its payload if valid.

    Args:
        token: The JWT token to verify

    Returns:
        Dict[str, Any]: The decoded token payload

    Raises:
        InvalidTokenError: If the token is invalid
        TokenExpiredError: If the token has expired
    """
    # Get settings
    # settings object is imported directly

    try:
        # Decode and verify the token
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except (jwt.InvalidTokenError, jwt.PyJWTError, ValidationError):
        raise InvalidTokenError("Invalid authentication token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current authenticated user from a token.

    This is a FastAPI dependency that can be used in route handlers.

    Args:
        token: The JWT token from the request

    Returns:
        Dict[str, Any]: User information from the token

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify the token
        payload = verify_token(token)

        # Check if it's an access token
        if payload.get("scope") != "access_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token scope",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user_id from token
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("User identifier missing from token")

        # Return user information from the token
        return {
            "user_id": user_id,
            "role": payload.get("role"),
            "permissions": payload.get("permissions", []),
            # Add any other user fields you need from the token
        }
    except (InvalidTokenError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_tokens_for_user(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.

    Args:
        user_data: User information to include in the tokens

    Returns:
        Dict[str, str]: Dictionary with access_token and refresh_token
    """
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
