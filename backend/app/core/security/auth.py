"""
Authentication and authorization utilities for the Novamind Digital Twin Platform.

This module provides functions for user authentication, authorization,
and access control throughout the application.
"""
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config.settings import settings
from app.core.security.roles import Role

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")


class TokenData(BaseModel):
    """Data extracted from authentication token."""
    user_id: str
    roles: List[Role] = [Role.USER]
    expires: Optional[int] = None


# ====================================================================
# Authentication Functions
# ====================================================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        
    Returns:
        User data extracted from the token
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Extract roles from token (default to USER if not present)
        roles = payload.get("roles", [Role.USER])
        
        # Extract token expiration time
        expires = payload.get("exp")
        
        token_data = TokenData(user_id=user_id, roles=roles, expires=expires)
    except JWTError:
        raise credentials_exception
    
    # Return user data (in a real implementation, we would fetch this from the database)
    return {
        "id": token_data.user_id,
        "roles": token_data.roles,
        "username": f"user_{token_data.user_id[:8]}",  # Just for testing
        "email": f"user_{token_data.user_id[:8]}@example.com"  # Just for testing
    }


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Get the ID of the current authenticated user.
    
    This is a convenience function that extracts just the user ID from the token.
    
    Args:
        token: JWT token from the Authorization header
        
    Returns:
        User ID extracted from the token
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract and return user ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ====================================================================
# Authorization Functions
# ====================================================================

def has_role(required_role: Role, token: str = Depends(oauth2_scheme)) -> bool:
    """
    Check if the current user has the required role.
    
    Args:
        required_role: The role required for access
        token: JWT token from the Authorization header
        
    Returns:
        True if the user has the required role, False otherwise
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract roles from token
        roles = payload.get("roles", [])
        
        # Check if the required role is in the user's roles
        return required_role in roles
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def has_permission(permission: str, token: str = Depends(oauth2_scheme)) -> bool:
    """
    Check if the current user has the required permission.
    
    This function checks the user's roles and determines if any of those
    roles grant the required permission.
    
    Args:
        permission: The permission required for access
        token: JWT token from the Authorization header
        
    Returns:
        True if the user has the required permission, False otherwise
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        # Get the current user from the token
        user = get_current_user(token)
        
        # Get the user's roles
        roles = user.get("roles", [])
        
        # Check if any of the user's roles grant the required permission
        from app.core.security.roles import has_permission as role_has_permission
        return role_has_permission(roles, permission)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )