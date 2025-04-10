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

# Singleton digital twin service instance
_digital_twin_service = None

async def get_digital_twin_service() -> AsyncGenerator['DigitalTwinIntegrationService', None]:
    """
    Provide a Digital Twin Integration service instance.
    
    Yields:
        DigitalTwinIntegrationService instance
    """
    global _digital_twin_service
    from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService # Local import
    
    if _digital_twin_service is None:
        # In a real app, config would come from settings
        _digital_twin_service = DigitalTwinIntegrationService(config={})
        await _digital_twin_service.initialize() # Assuming an async init method
        
    try:
        yield _digital_twin_service
    finally:
        # No cleanup needed for singleton
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