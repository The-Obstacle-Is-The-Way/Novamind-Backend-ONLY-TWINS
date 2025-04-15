# -*- coding: utf-8 -*-
"""
FastAPI dependency injection functions.

This module provides a collection of dependency injection functions for use with
FastAPI's dependency injection system. These functions create and provide
various services and dependencies to API endpoints.
"""

from typing import Any, Dict, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status

from app.config.settings import get_settings
from app.infrastructure.persistence.sqlalchemy.database import get_session
from app.core.exceptions import InvalidConfigurationError
from app.core.services.ml.pat.factory import PATFactory
from app.core.services.ml.pat.interface import PATInterface


def get_pat_service() -> PATInterface:
    """
    Dependency injection function for the PAT service.
    
    Creates and initializes a PAT service instance using the factory pattern
    based on configuration in settings. This ensures that the correct implementation
    (mock or production) is provided to the API endpoints.
    
    Returns:
        Initialized PAT service instance
        
    Raises:
        HTTPException: If service initialization fails
    """
    try:
        # Get PAT configuration from settings
        pat_config = get_settings().ml_config.get("pat", {})
        
        # Create PAT service using factory
        service = PATFactory.create_pat_service(pat_config)
        
        return service
        
    except InvalidConfigurationError as e:
        # Handle configuration errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PAT service configuration error: {str(e)}"
        )
        
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize PAT service: {str(e)}"
        )