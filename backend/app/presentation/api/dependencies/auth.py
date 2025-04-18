# -*- coding: utf-8 -*-
"""
Auth Dependencies.

This module provides authentication and authorization dependencies
for FastAPI routes, including JWT validation and user resolution.
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
settings = get_settings()
from app.infrastructure.security.jwt.jwt_service import JWTService, get_jwt_service
from app.core.utils.logging import get_logger
from app.infrastructure.security.auth.authentication_service import AuthenticationService

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
    token: Optional[str] = Depends(get_token_from_header),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> Dict[str, Any]:
    """
    Authenticate and get current user from JWT token.
    
    This function validates the JWT token and extracts the user information.
    It enforces authentication by raising an exception if the token is invalid.
    
    Args:
        token: JWT token from Authorization header
        jwt_service: Injected JWTService instance
        
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
        # Validate and decode token using the *injected* service
        payload = await jwt_service.verify_token(token)
        
        if not payload:
            raise ValueError("Invalid token payload")
            
        return payload
        
    except Exception as e:
        logger.warning(f"Authentication failed ({type(e).__name__}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_optional_user(
    token: Optional[str] = Depends(get_token_from_header),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> Optional[Dict[str, Any]]:
    """
    Get user from JWT token without requiring authentication.
    
    This function attempts to validate and extract user information
    from the JWT token, but does not raise an exception if no token
    is provided or if validation fails.
    
    Args:
        token: JWT token from Authorization header
        jwt_service: Injected JWTService instance
        
    Returns:
        User data extracted from token if valid, None otherwise
    """
    if token is None:
        return None
        
    try:
        # Validate and decode token using the *injected* service
        payload = await jwt_service.verify_token(token)
        
        return payload
        
    except Exception as e:
        logger.debug(f"Optional authentication failed ({type(e).__name__}): {str(e)}")
        return None


async def verify_provider_access(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify that the user has provider access level.
    
    Args:
        user: User data from JWT token
        
    Returns:
        User data if the user has provider or admin access
        
    Raises:
        HTTPException: If the user does not have required access level
    """
    # Support both dict-based payloads (production) and simple objects used in unit‑tests
    role = (
        user.get("role", "").lower()
        if isinstance(user, dict)
        else getattr(user, "role", "").lower()
    )
    # Allow providers, administrators, and clinicians access to protected routes
    if role not in ["provider", "admin", "clinician"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider or Admin access required",
        )
    return user


async def verify_admin_access(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify that the user has admin access level.
    
    Args:
        user: User data from JWT token
        
    Returns:
        User data if the user has admin access
        
    Raises:
        HTTPException: If the user does not have admin access
    """
    # Support both dict payloads and object-based mocks
    role = (
        user.get("role", "").lower()
        if isinstance(user, dict)
        else getattr(user, "role", "").lower()
    )
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
