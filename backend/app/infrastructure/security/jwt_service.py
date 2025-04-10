# -*- coding: utf-8 -*-
"""
JWT Service.

This module provides functionality for JSON Web Token generation,
validation, and management for secure authentication.
"""

import time
from typing import Dict, Any, Optional
import jwt
from jwt.exceptions import PyJWTError

from app.core.utils.logging import get_logger


logger = get_logger(__name__)


class JWTService:
    """
    Service for JWT token operations.
    
    Handles creation, validation, and decoding of JSON Web Tokens
    for secure user authentication.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize the JWT service.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT signing algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        
    async def create_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[int] = None
    ) -> str:
        """
        Create a new JWT token.
        
        Args:
            data: Payload data to encode in the token
            expires_delta: Token expiration time in seconds
            
        Returns:
            Encoded JWT token string
        """
        payload = data.copy()
        
        # Set issued at time
        issued_at = int(time.time())
        payload.update({"iat": issued_at})
        
        # Set expiration time if provided
        if expires_delta:
            expires = issued_at + expires_delta
            payload.update({"exp": expires})
            
        # Encode token
        token = jwt.encode(
            payload, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return token
        
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            return payload
            
        except PyJWTError as e:
            # Log error without exposing sensitive details
            logger.warning(f"JWT verification failed: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
            
    async def refresh_token(
        self, 
        token: str, 
        expires_delta: Optional[int] = None
    ) -> str:
        """
        Refresh a valid JWT token.
        
        Args:
            token: Valid JWT token to refresh
            expires_delta: New expiration time in seconds
            
        Returns:
            New JWT token with updated expiration
            
        Raises:
            ValueError: If token is invalid or expired
        """
        # Verify current token
        payload = await self.verify_token(token)
        
        # Remove previous exp and iat claims
        if "exp" in payload:
            del payload["exp"]
        if "iat" in payload:
            del payload["iat"]
            
        # Create new token
        return await self.create_token(payload, expires_delta)
