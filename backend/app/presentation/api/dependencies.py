# -*- coding: utf-8 -*-
"""
API Dependencies Module.

This module provides FastAPI dependency functions for injecting
services and repositories into API routes.
"""

from typing import AsyncGenerator, Dict, Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config.ml_settings import get_ml_settings
from app.core.config import get_settings
from app.infrastructure.ml.phi_detection import PHIDetectionService
from app.infrastructure.ml.mentallama import MentaLLaMAService
from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService
from app.infrastructure.security.jwt_service import JWTService
from app.core.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize security
security = HTTPBearer(auto_error=False)


# Get ML settings once for all dependencies
ml_settings = get_ml_settings()


# Dependency for PHI Detection Service
async def get_phi_detection_service() -> AsyncGenerator[PHIDetectionService, None]:
    """
    Provide a PHI detection service instance.
    
    This dependency creates and initializes a PHI detection service
    for use in routes that need to detect and anonymize PHI.
    
    Yields:
        PHI detection service instance
    """
    service = PHIDetectionService(
        pattern_file=ml_settings.phi_detection.pattern_file
    )
    
    # Ensure service is initialized
    service.ensure_initialized()
    
    yield service


# Dependency for MentaLLaMA Service
async def get_mentallama_service(
    phi_detection_service: PHIDetectionService = Depends(get_phi_detection_service)
) -> AsyncGenerator[MentaLLaMAService, None]:
    """
    Provide a MentaLLaMA service instance.
    
    This dependency creates and initializes a MentaLLaMA service
    for clinical text analysis, using PHI detection for HIPAA compliance.
    
    Args:
        phi_detection_service: PHI detection service for anonymizing PHI
        
    Yields:
        MentaLLaMA service instance
    """
    service = MentaLLaMAService(
        phi_detection_service=phi_detection_service,
        api_key=ml_settings.mentallama.api_key,
        api_endpoint=ml_settings.mentallama.api_endpoint,
        model_name=ml_settings.mentallama.default_model,
        temperature=ml_settings.mentallama.temperature
    )
    
    try:
        yield service
    finally:
        # Clean up resources
        await service.close()


# Dependency for Digital Twin Service
async def get_digital_twin_service() -> DigitalTwinIntegrationService:
    """
    Provide a Digital Twin Integration service instance.
    
    This dependency creates a new instance of the Digital Twin Integration service
    for use in routes that need to interact with the digital twin system.
    
    Returns:
        Digital Twin Integration service instance
    """
    return DigitalTwinIntegrationService(
        api_key=ml_settings.digital_twin.api_key,
        base_url=ml_settings.digital_twin.base_url,
        phi_detection_service=PHIDetectionService(
            pattern_file=ml_settings.phi_detection.pattern_file
        )
    )


# Authentication dependencies

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
    settings_obj = get_settings()
    
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    try:
        # Initialize JWT service
        jwt_service = JWTService(
            secret_key=settings_obj.security.jwt_secret,
            algorithm=settings_obj.security.jwt_algorithm
        )
        
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


async def get_current_user_id(
    user: Dict[str, Any] = Depends(get_current_user)
) -> UUID:
    """
    Extract user ID from the current authenticated user.
    
    Args:
        user: Current authenticated user data
        
    Returns:
        UUID of the current user
        
    Raises:
        HTTPException: If user ID is missing or invalid
    """
    try:
        user_id = user.get("sub")
        if not user_id:
            raise ValueError("User ID not found in token")
            
        return UUID(user_id)
        
    except Exception as e:
        logger.warning(f"Failed to extract user ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identification",
            headers={"WWW-Authenticate": "Bearer"}
        )