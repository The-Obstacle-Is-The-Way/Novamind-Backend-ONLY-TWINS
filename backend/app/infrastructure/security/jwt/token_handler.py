# -*- coding: utf-8 -*-
"""
NOVAMIND JWT Token Handler
========================
Handles secure JWT token generation and validation for the NOVAMIND platform.
Implements HIPAA-compliant authentication with proper security measures.
"""

import time
from datetime import datetime, UTC, UTC, timedelta
from typing import Any, Dict, List, Optional, Union

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.utils.logging import get_logger
from app.domain.exceptions import AuthenticationError # Corrected exception name

# Initialize logger
logger = get_logger(__name__)


class TokenPayload(BaseModel):
    """Pydantic model for JWT token payload."""

    sub: str
    exp: int
    iat: int
    role: str
    permissions: List[str]
    session_id: str


class JWTHandler:
    """
    Handles JWT token generation and validation for authentication.
    Implements HIPAA-compliant security practices.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None,
    ):
        """
        Initialize JWT handler with security settings.

        Args:
            secret_key: Secret key for JWT encoding/decoding
            algorithm: JWT algorithm to use
            access_token_expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key or settings.security.JWT_SECRET_KEY
        if not self.secret_key or len(self.secret_key) < 32:
            raise ValueError("JWT secret key is missing or too short (min 32 chars)")

        self.algorithm = algorithm or settings.security.JWT_ALGORITHM
        self.access_token_expire_minutes = (
            access_token_expire_minutes
            or settings.security.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

        logger.debug(f"JWTHandler initialized with algorithm: {self.algorithm}")

    def create_access_token(
        self,
        user_id: Union[str, int],
        role: str,
        permissions: List[str],
        session_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new JWT access token.

        Args:
            user_id: User identifier
            role: User role
            permissions: List of user permissions
            session_id: Unique session identifier
            expires_delta: Custom expiration time

        Returns:
            JWT token string
        """
        expire_minutes = (
            expires_delta.total_seconds() / 60
            if expires_delta
            else self.access_token_expire_minutes
        )

        expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(UTC),
            "role": role,
            "permissions": permissions,
            "session_id": session_id,
        }

        # Log token creation with user ID and expiration (no secrets)
        logger.info(
            f"Created access token for user: {user_id}, expires: {expire.isoformat()}"
        )

        # Create token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload object with decoded token data

        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Convert to Pydantic model for validation
            token_data = TokenPayload(**payload)

            # Check if token is expired
            if datetime.fromtimestamp(token_data.exp) < datetime.now(UTC):
                logger.warning(f"Expired token attempt for user: {token_data.sub}")
                raise AuthenticationException("Token has expired")

            logger.debug(f"Verified token for user: {token_data.sub}")
            return token_data

        except JWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            raise AuthenticationException("Invalid authentication token")
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {str(e)}")
            raise AuthenticationException("Authentication error")

    def refresh_token(self, token: str, extend_minutes: Optional[int] = None) -> str:
        """
        Refresh an existing token with a new expiration.

        Args:
            token: Existing valid JWT token
            extend_minutes: New expiration time in minutes

        Returns:
            New JWT token string

        Raises:
            AuthenticationException: If token is invalid
        """
        # Verify the existing token
        token_data = self.verify_token(token)

        # Create new token with same data but extended expiration
        return self.create_access_token(
            user_id=token_data.sub,
            role=token_data.role,
            permissions=token_data.permissions,
            session_id=token_data.session_id,
            expires_delta=timedelta(
                minutes=extend_minutes or self.access_token_expire_minutes
            ),
        )

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user ID from token without full validation.

        Args:
            token: JWT token string

        Returns:
            User ID string

        Raises:
            AuthenticationException: If token is invalid
        """
        token_data = self.verify_token(token)
        return token_data.sub

    def get_permissions_from_token(self, token: str) -> List[str]:
        """
        Extract permissions from token.

        Args:
            token: JWT token string

        Returns:
            List of permission strings

        Raises:
            AuthenticationException: If token is invalid
        """
        token_data = self.verify_token(token)
        return token_data.permissions

    def get_role_from_token(self, token: str) -> str:
        """
        Extract role from token.

        Args:
            token: JWT token string

        Returns:
            Role string

        Raises:
            AuthenticationException: If token is invalid
        """
        token_data = self.verify_token(token)
        return token_data.role
