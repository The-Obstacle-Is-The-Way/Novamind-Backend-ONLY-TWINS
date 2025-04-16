# backend/app/core/models/token_models.py

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class TokenPayload(BaseModel):
    """Schema for the data encoded within a JWT token."""
    sub: str | UUID  # Subject of the token (user ID)
    exp: datetime    # Expiration time claim
    iat: datetime    # Issued at time claim
    iss: Optional[str] = None # Issuer claim
    aud: Optional[str | List[str]] = None # Audience claim
    jti: Optional[str] = None # JWT ID claim
    scopes: Optional[List[str]] = Field(default_factory=list) # Custom scope claim
    session_id: Optional[str] = None # Optional session identifier

    class Config:
        # If needed for compatibility or specific settings
        # e.g., arbitrary_types_allowed = True # if UUID causes issues without it
        pass
