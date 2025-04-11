"""
Authentication dependencies for API endpoints.

This module provides dependencies for securing API endpoints with JWT-based
authentication, ensuring HIPAA-compliant access control to protected resources.
"""
from datetime import datetime
from typing import Dict, Optional, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session # Import get_session for AsyncSession dependency
# Remove incorrect import of oauth2_scheme
from app.core.auth import (
    validate_jwt,
    get_current_user_id,
    get_has_patient_access,
    get_admin_access
)
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.repositories.user_repository import get_user_repository

# Instantiate oauth2_scheme here
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Assuming tokenUrl is correct

async def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validate and decode the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    return validate_jwt(token)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session), # Depend directly on the session
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token from the Authorization header
        user_repository: User repository for fetching user data
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If user not found or inactive
    """
    # Use our new JWT validation
    payload = validate_jwt(token)
    
    # Get user ID from payload
    user_id = get_current_user_id(payload)
    
    # Fetch user from repository
    # Manually get the repository using the injected session
    user_repository = await get_user_repository(session=session)
    user = await user_repository.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
        
    return user


async def get_current_active_clinician(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session), # Depend directly on the session
) -> User:
    """
    Get the current authenticated clinician user.
    
    Args:
        token: JWT token from the Authorization header
        user_repository: User repository for fetching user data
        
    Returns:
        Current authenticated clinician user
        
    Raises:
        HTTPException: If user doesn't have clinician role
    """
    payload = validate_jwt(token)
    
    # Check if user has clinician access
    if not get_has_patient_access(payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    # Get the user
    # Pass the session to get_current_user
    user = await get_current_user(token=token, session=session)
    return user


async def get_current_active_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session), # Depend directly on the session
) -> User:
    """
    Get the current authenticated admin user.
    
    Args:
        token: JWT token from the Authorization header
        user_repository: User repository for fetching user data
        
    Returns:
        Current authenticated admin user
        
    Raises:
        HTTPException: If user doesn't have admin role
    """
    payload = validate_jwt(token)
    
    # Check if user has admin access
    if not get_admin_access(payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    # Get the user
    # Pass the session to get_current_user
    user = await get_current_user(token=token, session=session)
    return user


async def get_current_user_dict(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session) # Depend directly on the session
) -> Dict[str, Any]:
    """
    Get the current authenticated user as a dictionary.
    
    This endpoint is more efficient for routes that only need basic user info.
    
    Args:
        token: JWT token from the Authorization header
        user_repository: User repository for fetching user data
        
    Returns:
        User information as a dictionary
    """
    # Get the user
    # Pass the session to get_current_user
    user = await get_current_user(token=token, session=session)
    
    # Return just the essential information as a dictionary
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "roles": user.roles,
        "is_active": user.is_active,
    }


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """
    Get the current user if authenticated, or None if not.
    
    This is useful for endpoints that can work with or without authentication.
    
    Args:
        token: JWT token from the Authorization header (optional)
        session: Database session
        
    Returns:
        Current authenticated user, or None if not authenticated
    """
    if not token:
        return None
        
    try:
        # Validate the token
        payload = validate_jwt(token, raise_exception=False)
        if not payload:
            return None
            
        # Get user ID from payload
        user_id = get_current_user_id(payload)
        if not user_id:
            return None
        
        # Use get_user_repository directly to avoid circular dependencies
        user_repository = await get_user_repository(session=session)
        user = await user_repository.get_by_id(user_id)
        
        if user and user.is_active:
            return user
    except Exception:
        # Silently return None on any error
        pass
        
    return None