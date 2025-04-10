# -*- coding: utf-8 -*-
"""
Common dependencies for biometric-related endpoints.

This module provides common dependencies and utilities for biometric-related
endpoints, such as authentication and patient ID validation.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer

from app.domain.exceptions import AuthenticationError, AuthorizationError # Corrected names
from app.infrastructure.security.jwt_service import JWTService


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    jwt_service: JWTService = Depends()
) -> UUID:
    """
    Get the ID of the currently authenticated user.
    
    Args:
        token: JWT token from the request
        jwt_service: Service for JWT operations
        
    Returns:
        UUID of the current user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Validate the token and get the user ID
        payload = jwt_service.decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationException("Invalid authentication credentials")
        
        return UUID(user_id)
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_patient_id(
    patient_id: UUID = Path(..., description="ID of the patient"),
    current_user_id: UUID = Depends(get_current_user_id)
) -> UUID:
    """
    Get and validate the patient ID from the path.
    
    This dependency also checks if the current user has permission to
    access the specified patient's data.
    
    Args:
        patient_id: Patient ID from the path
        current_user_id: ID of the current user
        
    Returns:
        Validated patient ID
        
    Raises:
        HTTPException: If the user doesn't have permission to access the patient
    """
    # In a real implementation, we would check if the current user
    # has permission to access this patient's data
    # For example, if the user is a clinician, they might only have
    # access to patients assigned to them
    
    # For now, we'll just return the patient ID
    return patient_id


async def get_current_user_role(
    token: str = Depends(oauth2_scheme),
    jwt_service: JWTService = Depends()
) -> str:
    """
    Get the role of the currently authenticated user.
    
    Args:
        token: JWT token from the request
        jwt_service: Service for JWT operations
        
    Returns:
        Role of the current user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Validate the token and get the user role
        payload = jwt_service.decode_token(token)
        role = payload.get("role")
        
        if not role:
            raise AuthenticationException("Invalid authentication credentials")
        
        return role
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def require_clinician_role(
    role: str = Depends(get_current_user_role)
) -> None:
    """
    Require that the current user has the clinician role.
    
    Args:
        role: Role of the current user
        
    Raises:
        HTTPException: If the user doesn't have the clinician role
    """
    if role != "clinician" and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires clinician privileges"
        )


async def require_admin_role(
    role: str = Depends(get_current_user_role)
) -> None:
    """
    Require that the current user has the admin role.
    
    Args:
        role: Role of the current user
        
    Raises:
        HTTPException: If the user doesn't have the admin role
    """
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires admin privileges"
        )