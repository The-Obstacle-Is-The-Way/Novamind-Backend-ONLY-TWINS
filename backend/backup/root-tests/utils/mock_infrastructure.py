# -*- coding: utf-8 -*-
"""
Mock Infrastructure Components.

This module provides mock implementations of various infrastructure components
for use in testing, ensuring tests don't depend on real external services.
"""

from typing import Dict, List, Any, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.interfaces.services.cache_service import CacheService


class MockCacheService(CacheService):
    """Mock implementation of the cache service for testing."""
    
    def __init__(self):
        """Initialize the mock cache with an empty store."""
        self.store = {}
        self.ttls = {}
        self._client = self
        
    async def get(self, key: str) -> Any:
        """Get a value from the mock cache."""
        return self.store.get(key)
        
    async def set(
        self, 
        key: str, 
        value: Any, 
        expiration: Optional[int] = None
    ) -> bool:
        """Set a value in the mock cache."""
        self.store[key] = value
        if expiration:
            self.ttls[key] = expiration
        return True
        
    async def delete(self, key: str) -> int:
        """Delete a value from the mock cache."""
        if key in self.store:
            del self.store[key]
            if key in self.ttls:
                del self.ttls[key]
            return 1
        return 0
        
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the mock cache."""
        return key in self.store
        
    async def increment(self, key: str) -> int:
        """Increment a value in the mock cache."""
        if key not in self.store:
            self.store[key] = 0
        self.store[key] = int(self.store[key]) + 1
        return self.store[key]
        
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key in the mock cache."""
        if key in self.store:
            self.ttls[key] = seconds
            return True
        return False
        
    async def ttl(self, key: str) -> int:
        """Get TTL for a key in the mock cache."""
        return self.ttls.get(key, 0)
        
    async def close(self) -> None:
        """Close the mock cache."""
        self.store = {}
        self.ttls = {}


class MockDBSession:
    """Mock database session for testing."""
    
    def __init__(self):
        """Initialize the mock database session."""
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.queries = []
        self.added_objects = []
        self.deleted_objects = []
        
    async def commit(self):
        """Commit the session."""
        self.committed = True
        
    async def rollback(self):
        """Rollback the session."""
        self.rolled_back = True
        
    async def close(self):
        """Close the session."""
        self.closed = True
        
    async def execute(self, query, *args, **kwargs):
        """Execute a query."""
        self.queries.append((query, args, kwargs))
        return MagicMock()
        
    async def scalar(self, query, *args, **kwargs):
        """Execute a query and return the first column of the first row."""
        self.queries.append((query, args, kwargs))
        return None
        
    def add(self, obj):
        """Add an object to the session."""
        self.added_objects.append(obj)
        
    def delete(self, obj):
        """Delete an object from the session."""
        self.deleted_objects.append(obj)
        
    async def refresh(self, obj):
        """Refresh an object from the database."""
        pass


def patch_redis():
    """
    Patch the Redis cache implementation for testing.
    
    Returns:
        A patch context manager for Redis
    """
    return patch('app.infrastructure.cache.redis_cache.RedisCache', return_value=MockCacheService())


def patch_database():
    """
    Patch the database session for testing.
    
    Returns:
        A patch context manager for the database session
    """
    mock_session = MockDBSession()
    
    async def get_mock_session():
        yield mock_session
        
    return patch('app.infrastructure.persistence.sqlalchemy.config.database.get_db_session', get_mock_session)


def setup_test_infrastructure():
    """
    Set up all test infrastructure patches.
    
    Returns:
        A list of patch context managers
    """
    return [
        patch_redis(),
        patch_database()
    ]