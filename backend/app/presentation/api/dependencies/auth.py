# -*- coding: utf-8 -*-
"""
Auth Dependencies.

This module provides authentication and authorization dependencies
for FastAPI routes, including JWT validation and user resolution.
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.infrastructure.security.jwt_service import JWTService
from app.core.utils.logging import get_logger


logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


async def get_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        JWT token if present, None otherwise
    """
    if credentials is None:
        return None
        
    return credentials.credentials


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_header)
) -> Dict[str, Any]:
    """
    Authenticate and get current user from JWT token.
    
    This function validates the JWT token and extracts the user information.
    It enforces authentication by raising an exception if the token is invalid.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User data extracted from token
        
    Raises:
        HTTPException: If authentication fails
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    try:
        # Initialize JWT service
        jwt_service = JWTService(settings.JWT_SECRET_KEY)
        
        # Validate and decode token
        payload = await jwt_service.verify_token(token)
        
        if not payload:
            raise ValueError("Invalid token payload")
            
        return payload
        
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_optional_user(
    token: Optional[str] = Depends(get_token_from_header)
) -> Optional[Dict[str, Any]]:
    """
    Get user from JWT token without requiring authentication.
    
    This function attempts to validate and extract user information
    from the JWT token, but does not raise an exception if no token
    is provided or if validation fails.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User data extracted from token if valid, None otherwise
    """
    if token is None:
        return None
        
    try:
        # Initialize JWT service
        jwt_service = JWTService(settings.JWT_SECRET_KEY)
        
        # Validate and decode token
        payload = await jwt_service.verify_token(token)
        
        return payload
        
    except Exception as e:
        logger.debug(f"Optional authentication failed: {str(e)}")
        return None