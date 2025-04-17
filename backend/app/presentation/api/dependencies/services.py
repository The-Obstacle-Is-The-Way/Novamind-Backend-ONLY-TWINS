# -*- coding: utf-8 -*-
"""
API Service Dependencies.

This module provides FastAPI dependency functions for injecting 
services into API routes.
"""

from typing import Callable, AsyncGenerator

from fastapi import Depends

from app.application.interfaces.services.cache_service import CacheService
from app.infrastructure.cache.redis_cache import RedisCache


# Singleton cache instance
_redis_cache = None


async def get_cache_service() -> AsyncGenerator[CacheService, None]:
    """
    Provide a cache service instance.
    
    This dependency creates and initializes a Redis cache service
    for caching in API routes.
    
    Yields:
        Cache service instance
    """
    global _redis_cache
    
    if _redis_cache is None:
        _redis_cache = RedisCache()
        
    # Initialize if needed
    await _redis_cache.initialize()
    
    try:
        yield _redis_cache
    finally:
        # No cleanup needed since we're keeping the instance alive
        pass

# Singleton digital twin core service instance
_digital_twin_service = None  # type: MockDigitalTwinCoreService

async def get_digital_twin_service() -> AsyncGenerator['DigitalTwinCoreService', None]:
    """
    Provide a stub Digital Twin Core service instance for API endpoints.
    
    Yields:
        MockDigitalTwinCoreService instance implementing DigitalTwinCoreService
    """
    global _digital_twin_service
    # Import stub core service and mock repositories
    from app.infrastructure.services.mock_digital_twin_core_service import MockDigitalTwinCoreService
    from app.infrastructure.repositories.mock_digital_twin_repository import MockDigitalTwinRepository
    from app.infrastructure.repositories.mock_patient_repository import MockPatientRepository
    # Import domain interface for type annotation
    from app.domain.services.digital_twin_core_service import DigitalTwinCoreService

    if _digital_twin_service is None:
        # Instantiate mock repositories
        twin_repo = MockDigitalTwinRepository()
        patient_repo = MockPatientRepository()
        # Create stub core service with mock dependencies
        _digital_twin_service = MockDigitalTwinCoreService(
            digital_twin_repository=twin_repo,
            patient_repository=patient_repo
        )
    try:
        yield _digital_twin_service  # type: ignore
    finally:
        # Singleton stub; no cleanup required
        pass

# Singleton PAT service instance
_pat_service = None

async def get_pat_service() -> AsyncGenerator['PATService', None]:
    """
    Provide a PAT service instance.
    
    Yields:
        PATService instance
    """
    global _pat_service
    from app.core.services.ml.pat.service import PATService # Local import
    from app.core.services.ml.pat.factory import PATServiceFactory # Local import for factory
    
    if _pat_service is None:
        # Use factory to create the configured PAT service (e.g., mock or aws)
        factory = PATServiceFactory()
        _pat_service = factory.create_service() # Uses settings.PAT_SERVICE_TYPE
        await _pat_service.initialize() # Assuming an async init method
        
    try:
        yield _pat_service
    finally:
        # No cleanup needed for singleton
        pass