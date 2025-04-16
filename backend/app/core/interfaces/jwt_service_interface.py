# backend/app/core/interfaces/jwt_service_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
from datetime import timedelta
from uuid import UUID

# Update import to use the new core location
from app.core.models.token_models import TokenPayload


class JWTServiceInterface(ABC):
    """Interface for JWT token creation and validation services."""

    @abstractmethod
    async def create_access_token(
        self,
        subject: Union[str, UUID],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
        scopes: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Creates a JWT access token."""
        pass

    @abstractmethod
    async def create_refresh_token(
        self,
        subject: Union[str, UUID],
        expires_delta: Optional[timedelta] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Creates a JWT refresh token."""
        pass

    @abstractmethod
    async def decode_token(self, token: str) -> TokenPayload:
        """Decodes a JWT token and validates it."""
        pass

    # Potentially add other methods if JWTService has more public methods
    # intended to be part of the interface.
