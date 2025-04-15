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

from app.config.settings import get_settings
settings = get_settings()
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session as get_session
# Remove incorrect import of oauth2_scheme
# from app.core.auth import (
#     validate_jwt,
#     get_current_user_id,
#     get_has_patient_access,
#     get_admin_access
# )
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.domain.exceptions import InvalidTokenError, TokenExpiredError

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.repositories.user_repository import get_user_repository

# Instantiate oauth2_scheme here
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Assuming tokenUrl is correct

# Dependency to get JWTService instance (could use a more robust DI approach later)
async def get_jwt_service() -> JWTService:
    return JWTService()

async def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> TokenPayload:
    """
    Validate and decode the JWT token using JWTService.
    
    Args:
        token: JWT token from the Authorization header
        jwt_service: JWTService instance for decoding the token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt_service.decode_token(token)
        return payload
    except TokenExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token from the Authorization header
        session: Database session
        jwt_service: JWTService instance for decoding the token
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If user not found or inactive
    """
    payload = await get_current_token_payload(token, jwt_service)
    user_id = payload.sub # Access user ID from payload subject
    
    # Fetch user from repository
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
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> User:
    """
    Get the current authenticated clinician user.
    
    Args:
        token: JWT token from the Authorization header
        session: Database session
        jwt_service: JWTService instance for decoding the token
        
    Returns:
        Current authenticated clinician user
        
    Raises:
        HTTPException: If user doesn't have clinician role
    """
    payload = await get_current_token_payload(token, jwt_service)
    
    # Check roles from payload
    if not payload.roles or "clinician" not in payload.roles: # Example role check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    # Get the user
    user = await get_current_user(token=token, session=session, jwt_service=jwt_service)
    return user


async def get_current_active_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> User:
    """
    Get the current authenticated admin user.
    
    Args:
        token: JWT token from the Authorization header
        session: Database session
        jwt_service: JWTService instance for decoding the token
        
    Returns:
        Current authenticated admin user
        
    Raises:
        HTTPException: If user doesn't have admin role
    """
    payload = await get_current_token_payload(token, jwt_service)
    
    # Check roles from payload
    if not payload.roles or "admin" not in payload.roles: # Example role check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    # Get the user
    user = await get_current_user(token=token, session=session, jwt_service=jwt_service)
    return user


async def get_current_user_dict(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> Dict[str, Any]:
    """
    Get the current authenticated user as a dictionary.
    
    This endpoint is more efficient for routes that only need basic user info.
    
    Args:
        token: JWT token from the Authorization header
        session: Database session
        jwt_service: JWTService instance for decoding the token
        
    Returns:
        User information as a dictionary
    """
    user = await get_current_user(token=token, session=session, jwt_service=jwt_service)
    
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
    jwt_service: JWTService = Depends(get_jwt_service)
) -> Optional[User]:
    """
    Get the current user if authenticated, or None if not.
    
    This is useful for endpoints that can work with or without authentication.
    
    Args:
        token: JWT token from the Authorization header (optional)
        session: Database session
        jwt_service: JWTService instance for decoding the token
        
    Returns:
        Current authenticated user, or None if not authenticated
    """
    if not token:
        return None
        
    try:
        # Use JWTService to decode
        payload = jwt_service.decode_token(token)
        user_id = payload.sub
        
        # Use get_user_repository directly to avoid circular dependencies
        user_repository = await get_user_repository(session=session)
        user = await user_repository.get_by_id(user_id)
        
        if user and user.is_active:
            return user
    except (TokenExpiredError, InvalidTokenError):
        # Silently return None on token errors for optional user
        return None
    except Exception:
        # Log other potential errors
        # logger.exception("Error fetching optional user") 
        pass
        
    return None