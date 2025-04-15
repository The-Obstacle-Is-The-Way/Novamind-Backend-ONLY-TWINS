# -*- coding: utf-8 -*-
"""
Redis Cache Implementation.

This module provides a Redis-based implementation of the CacheService
interface for efficient caching in a distributed environment.
"""

import json
from typing import Any, Dict, Optional
import time

import redis.asyncio as aioredis # Use redis.asyncio instead of aioredis

from app.application.interfaces.services.cache_service import CacheService
from app.core.utils.logging import get_logger
from app.config.settings import get_settings
settings = get_settings()

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
        self._settings = settings # Use the imported settings object
        
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
            
            # Prepare connection options
            redis_connection_options = {
                "encoding": "utf-8",
                "decode_responses": True
            }
            # Only add the 'ssl' argument if redis_ssl is explicitly True
            if redis_ssl:
                 redis_connection_options["ssl"] = True

            # Connect to Redis using the prepared options
            self._client = await aioredis.from_url(
                redis_url,
                **redis_connection_options
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
        self._cache: Dict[str, Any] = {}
        self._expirations: Dict[str, float] = {} # Store expiration timestamps

    async def _check_expired(self, key: str):
        """Check if a key has expired and remove it if so."""
        if key in self._expirations and self._expirations[key] < time.time():
            if key in self._cache:
                del self._cache[key]
            del self._expirations[key]
            return True
        return False

    async def get(self, key: str) -> Any:
        if self._check_expired(key):
            return None
        return self._cache.get(key)
        
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a value in the cache."""
        self._cache[key] = value
        if ex is not None:
            self._expirations[key] = time.time() + ex
        elif key in self._expirations: # Remove expiration if ex is None
             del self._expirations[key]
        return True
        
    async def delete(self, key: str) -> int:
        """Delete a value from the cache."""
        deleted = 0
        if key in self._cache:
            del self._cache[key]
            deleted = 1
        if key in self._expirations:
            del self._expirations[key]
        return deleted
        
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        if self._check_expired(key):
            return False
        return key in self._cache
        
    async def incr(self, key: str) -> int:
        """Increment a counter in the cache."""
        if self._check_expired(key):
             self._cache[key] = 0 # Initialize if expired and accessed by incr
        
        current_value = self._cache.get(key, 0)
        if not isinstance(current_value, int):
             # Attempt conversion or handle error
             try:
                 current_value = int(current_value)
             except (ValueError, TypeError):
                 # Cannot increment non-integer value that isn't convertible
                 # Redis behavior is to raise an error. We'll simulate by returning 0
                 # and logging an error. A more strict simulation could raise ValueError.
                 logger.error(f"InMemoryFallback: Cannot increment non-integer value for key '{key}'")
                 return 0 # Or raise ValueError("value is not an integer or out of range")

        new_value = current_value + 1
        self._cache[key] = new_value
        # Incrementing removes TTL in Redis, simulate this
        if key in self._expirations:
            del self._expirations[key]
        return new_value
        
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        if not await self.exists(key): # Check existence and expiration
            return False
        self._expirations[key] = time.time() + seconds
        return True
        
    async def ttl(self, key: str) -> int:
        """Get the TTL for a key."""
        if self._check_expired(key):
            return -2 # Key doesn't exist (because it expired)
        if key not in self._cache:
            return -2 # Key doesn't exist
        if key not in self._expirations:
            return -1 # Key exists but has no associated expiration
        
        remaining_ttl = int(self._expirations[key] - time.time())
        return max(0, remaining_ttl) # Return 0 if expired but not yet cleaned up
        
    async def close(self) -> None:
        """Close the cache connection."""
        self._cache = {}
        self._expirations = {}
        logger.debug("InMemoryFallback closed (cleared).")

# Optional: Add a utility function to get the cache instance if needed elsewhere
_cache_instance: Optional[RedisCache] = None

def get_cache_service() -> CacheService:
    """
    Get the global cache service instance.
    
    Initializes the service if it hasn't been already.
    
    Returns:
        CacheService: The initialized cache service instance (Redis or fallback).
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
        # Note: Initialization (connection) happens lazily on first operation
    return _cache_instance