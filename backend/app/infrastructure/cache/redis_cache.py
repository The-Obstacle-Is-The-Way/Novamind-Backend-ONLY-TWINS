# -*- coding: utf-8 -*-
"""
Redis Cache Implementation.

This module provides a Redis-based implementation of the CacheService
interface for efficient caching in a distributed environment.
"""

import json
from typing import Any, Dict, Optional

import redis.asyncio as aioredis # Use redis.asyncio instead of aioredis

from app.application.interfaces.services.cache_service import CacheService
from app.core.utils.logging import get_logger
from app.core.config import get_app_settings


logger = get_logger(__name__)


class RedisCache(CacheService):
    """
    Redis-based implementation of the cache service.
    
    This class provides a Redis-backed cache service implementation,
    suitable for production use in a distributed environment.
    """
    
    def __init__(self):
        """Initialize the Redis cache service."""
        self._client = None
        self._settings = get_app_settings()
        
    async def initialize(self) -> None:
        """
        Initialize the Redis client.
        
        This method establishes a connection to the Redis server
        according to application settings.
        """
        if self._client is not None:
            return
            
        try:
            # Get Redis connection settings
            redis_url = getattr(self._settings, "REDIS_URL", "redis://localhost:6379/0")
            redis_ssl = getattr(self._settings, "REDIS_SSL", False)
            
            # Connect to Redis
            self._client = await aioredis.from_url(
                redis_url,
                ssl=redis_ssl,
                encoding="utf-8",
                decode_responses=True
            )
            
            logger.info(f"Connected to Redis at {redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Fallback to an in-memory implementation for development
            self._client = InMemoryFallback()
            logger.warning("Using in-memory fallback for cache (not for production)")
            
    async def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if self._client is None:
            await self.initialize()
            
        try:
            value = await self._client.get(key)
            
            if value is None:
                return None
                
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as is if not JSON
                return value
                
        except Exception as e:
            logger.error(f"Error retrieving key {key} from cache: {str(e)}")
            return None
            
    async def set(
        self, 
        key: str, 
        value: Any, 
        expiration: Optional[int] = None
    ) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expiration: Optional TTL in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self._client is None:
            await self.initialize()
            
        try:
            # Serialize complex objects to JSON
            if not isinstance(value, (str, int, float, bool)) and value is not None:
                value = json.dumps(value)
                
            # Set with expiration if provided
            if expiration is not None:
                await self._client.set(key, value, ex=expiration)
            else:
                await self._client.set(key, value)
                
            return True
            
        except Exception as e:
            logger.error(f"Error setting key {key} in cache: {str(e)}")
            return False
            
    async def delete(self, key: str) -> int:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Number of keys deleted (0 or 1)
        """
        if self._client is None:
            await self.initialize()
            
        try:
            return await self._client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key} from cache: {str(e)}")
            return 0
            
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if self._client is None:
            await self.initialize()
            
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            logger.error(f"Error checking if key {key} exists in cache: {str(e)}")
            return False
            
    async def increment(self, key: str) -> int:
        """
        Increment a counter in the cache.
        
        If the key doesn't exist, it's initialized to 0 before incrementing.
        
        Args:
            key: Cache key
            
        Returns:
            New value after incrementing
        """
        if self._client is None:
            await self.initialize()
            
        try:
            return await self._client.incr(key)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in cache: {str(e)}")
            return 0
            
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.
        
        Args:
            key: Cache key
            seconds: TTL in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self._client is None:
            await self.initialize()
            
        try:
            return bool(await self._client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key} in cache: {str(e)}")
            return False
            
    async def ttl(self, key: str) -> int:
        """
        Get the TTL for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if key exists but has no TTL,
            -2 if key doesn't exist
        """
        if self._client is None:
            await self.initialize()
            
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} in cache: {str(e)}")
            return -2
            
    async def close(self) -> None:
        """
        Close the cache connection.
        
        This method releases any resources used by the cache service.
        """
        if self._client is None:
            return
            
        try:
            await self._client.close()
            self._client = None
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")


class InMemoryFallback:
    """
    In-memory fallback for Redis operations.
    
    This class provides an in-memory implementation of Redis commands
    for development and testing when Redis is unavailable.
    """
    
    def __init__(self):
        """Initialize the in-memory cache."""
        self.data = {}
        self.expiry = {}
        
    async def get(self, key: str) -> Any:
        """Get a value from the cache."""
        return self.data.get(key)
        
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a value in the cache."""
        self.data[key] = value
        if ex is not None:
            self.expiry[key] = ex
        return True
        
    async def delete(self, key: str) -> int:
        """Delete a value from the cache."""
        if key in self.data:
            del self.data[key]
            if key in self.expiry:
                del self.expiry[key]
            return 1
        return 0
        
    async def exists(self, key: str) -> int:
        """Check if a key exists in the cache."""
        return 1 if key in self.data else 0
        
    async def incr(self, key: str) -> int:
        """Increment a counter in the cache."""
        if key not in self.data:
            self.data[key] = 0
        self.data[key] = int(self.data[key]) + 1
        return self.data[key]
        
    async def expire(self, key: str, seconds: int) -> int:
        """Set expiration on a key."""
        if key in self.data:
            self.expiry[key] = seconds
            return 1
        return 0
        
    async def ttl(self, key: str) -> int:
        """Get the TTL for a key."""
        if key not in self.data:
            return -2
        return self.expiry.get(key, -1)
        
    async def close(self) -> None:
        """Close the cache connection."""
        self.data = {}
        self.expiry = {}