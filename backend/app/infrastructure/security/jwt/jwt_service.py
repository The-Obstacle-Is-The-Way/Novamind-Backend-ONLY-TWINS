# -*- coding: utf-8 -*-
"""
JWT Service.

This module provides functionality for JSON Web Token generation,
validation, and management for secure authentication.
"""

import jwt
from jwt.exceptions import PyJWTError
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ValidationError
import logging

from app.config.settings import get_settings
from app.domain.exceptions import InvalidTokenError, TokenExpiredError
from app.infrastructure.security.jwt.jwt_models import TokenData


logger = logging.getLogger(__name__)

class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: Union[str, UUID]  # User ID
    exp: int  # Expiration timestamp (required)
    iat: int  # Issued at timestamp (required)
    jti: str  # JWT ID (required for uniqueness/revocation)
    scope: str = "access_token"  # Token scope (access_token or refresh_token)
    roles: Optional[List[str]] = None  # User roles
    permissions: Optional[List[str]] = None  # User permissions
    session_id: Optional[str] = None # Optional session identifier


class JWTService:
    """
    Core JWT Service for creating and validating tokens.
    
    Handles both access and refresh tokens using PyJWT and standardized exceptions.
    """
    def __init__(self):
        """Initialize JWTService, loading settings."""
        self.settings = get_settings()
        if not self.settings.SECRET_KEY or len(self.settings.SECRET_KEY) < 32:
            raise ValueError("JWT secret key is missing or too short (min 32 chars)")

    def _create_token(
        self,
        subject: Union[str, UUID],
        expires_delta: timedelta,
        scope: str,
        jti: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Internal helper to create a token."""
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode: Dict[str, Any] = {
            "sub": str(subject),
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": jti,
            "scope": scope,
        }
        if additional_claims:
            to_encode.update(additional_claims)

        # Validate payload before encoding
        try:
            TokenPayload(**to_encode) # Validate against the model
        except ValidationError as e:
             # In a real scenario, you might log this or handle it differently
             raise ValueError(f"Invalid payload data for JWT: {e}") from e

        return jwt.encode(
            to_encode, 
            self.settings.SECRET_KEY, 
            algorithm=self.settings.ALGORITHM
        )

    def create_access_token(
        self,
        subject: Union[str, UUID],
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Create an access token."""
        expires_delta = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = str(uuid4())
        additional_claims = {}
        if roles:
            additional_claims["roles"] = roles
        if permissions:
            additional_claims["permissions"] = permissions
        if session_id:
            additional_claims["session_id"] = session_id
            
        return self._create_token(
            subject=subject, 
            expires_delta=expires_delta, 
            scope="access_token", 
            jti=jti,
            additional_claims=additional_claims
        )

    def create_refresh_token(self, subject: Union[str, UUID], jti: str) -> str:
        """Create a refresh token."""
        expires_delta = timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        # Refresh tokens typically have minimal additional claims
        return self._create_token(
            subject=subject, 
            expires_delta=expires_delta, 
            scope="refresh_token",
            jti=jti
        )

    def decode_token(self, token: str) -> TokenPayload:
        """
        Decode and validate a JWT token.

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is invalid or cannot be decoded.
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM]
            )
            # Pydantic validation occurs here
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e
        except (jwt.InvalidTokenError, PyJWTError, ValidationError) as e:
            # Catch PyJWT errors and Pydantic validation errors
            raise InvalidTokenError(f"Token validation failed: {e}") from e
