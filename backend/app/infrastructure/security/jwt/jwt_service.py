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
from pydantic import BaseModel, Field, ValidationError, SecretStr
import logging

from app.config.settings import get_settings, Settings
from app.core.exceptions.jwt_exceptions import JWTError, TokenExpiredError, InvalidTokenError, MissingTokenError
from fastapi import Depends
from app.core.interfaces.jwt_service_interface import JWTServiceInterface
from app.core.models.token_models import TokenPayload
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class JWTService(JWTServiceInterface):
    """
    Core JWT Service for creating and validating tokens.
    
    Handles both access and refresh tokens using PyJWT and standardized exceptions.
    """
    def __init__(self, settings: Settings = Depends(get_settings)):
        """Initialize JWTService with settings dependency."""
        # Store the injected settings object on the instance
        self.settings = settings
        logger.debug(f"JWTService initialized with settings ID: {id(self.settings)}, type: {type(self.settings)}")
        logger.debug(f"SECRET_KEY type: {type(self.settings.SECRET_KEY)}, value: {self.settings.SECRET_KEY.get_secret_value()[:5]}...")
        logger.debug(f"ALGORITHM: {self.settings.ALGORITHM}")
        logger.debug(f"ACCESS_TOKEN_EXPIRE_MINUTES: {self.settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        
        # Validate settings (optional but good practice)
        if not isinstance(self.settings.SECRET_KEY, SecretStr):
            raise TypeError("SECRET_KEY must be a SecretStr")
        if not self.settings.ALGORITHM:
            raise ValueError("ALGORITHM cannot be empty")
        if not isinstance(self.settings.ACCESS_TOKEN_EXPIRE_MINUTES, int):
            raise TypeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer")

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

        # Ensure secret key is a string for jwt.encode
        secret_key = self.settings.SECRET_KEY.get_secret_value()
        algorithm = self.settings.ALGORITHM
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt

    async def create_access_token(
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

    async def create_refresh_token(self, subject: Union[str, UUID], jti: str) -> str:
        """Create a refresh token."""
        expires_delta = timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        # Refresh tokens typically have minimal additional claims
        return self._create_token(
            subject=subject, 
            expires_delta=expires_delta, 
            scope="refresh_token",
            jti=jti
        )

    async def decode_token(self, token: str) -> TokenPayload:
        """
        Decode and validate a JWT token.

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is invalid or cannot be decoded.
        """
        logger.debug(f"Decoding token. Using Secret Key: {'*' * len(self.settings.SECRET_KEY.get_secret_value())} Algorithm: {self.settings.ALGORITHM}")
        try:
            secret_key = self.settings.SECRET_KEY.get_secret_value()
            algorithm = self.settings.ALGORITHM
            
            logger.debug(f"Decoding token with Algorithm: {algorithm}, Secret Key Used (start): {secret_key[:5]}...")


            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={"verify_aud": False} # Adjust based on audience requirements
            )
            # Pydantic validation occurs here
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e
        except (jwt.InvalidTokenError, PyJWTError, ValidationError) as e:
            # Catch PyJWT errors and Pydantic validation errors
            raise InvalidTokenError(f"Token validation failed: {e}") from e


# Dependency provider remains the same, but JWTService now resolves its own settings
def get_jwt_service() -> JWTService:
    """FastAPI dependency provider for JWTService."""
    # JWTService now resolves its own settings via get_settings() in __init__
    return JWTService()
