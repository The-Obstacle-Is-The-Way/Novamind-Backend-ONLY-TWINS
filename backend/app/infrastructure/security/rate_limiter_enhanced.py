"""
Enhanced rate limiter implementation with multiple backend options.

This module provides rate limiting capabilities with both in-memory and Redis
backends for high availability and scalability.
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple, Any

import redis

from app.core.config.settings import get_settings

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limit behavior."""
    
    requests: int
    """Maximum number of requests allowed within the window."""
    
    window_seconds: int
    """Duration of the rate limit window in seconds."""
    
    block_seconds: Optional[int] = None
    """Duration to block if limit is exceeded (optional)."""


class RateLimiter(ABC):
    """Abstract base class for rate limiting implementations."""
    
    @abstractmethod
    def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """
        Check if a request should be allowed or limited.
        
        Args:
            key: Unique identifier for the client/endpoint
            config: Rate limit configuration
            
        Returns:
            bool: True if request is allowed, False if limited
        """
        pass
    
    @abstractmethod
    def reset_limits(self, key: str) -> None:
        """
        Reset rate limits for a specific key.
        
        Args:
            key: Unique identifier to reset
        """
        pass


class InMemoryRateLimiter(RateLimiter):
    """
    In-memory implementation of rate limiting.
    
    Useful for single-instance deployments or testing.
    """
    
    def __init__(self):
        """Initialize the in-memory rate limiter."""
        # Map of key -> list of request timestamps
        self._requests: Dict[str, List[float]] = {}
        
        # Map of key -> block expiry timestamp
        self._blocked: Dict[str, float] = {}
    
    def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """
        Check if a request should be allowed or limited.
        
        Args:
            key: Unique identifier for the client/endpoint
            config: Rate limit configuration
            
        Returns:
            bool: True if request is allowed, False if limited
        """
        now = time.time()
        
        # Check if key is blocked
        if key in self._blocked:
            if now < self._blocked[key]:
                return False
            else:
                # Block expired, remove it
                del self._blocked[key]
        
        # Initialize request list if not exists
        if key not in self._requests:
            self._requests[key] = []
        
        # Remove expired timestamps
        window_start = now - config.window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]
        
        # Check request count
        if len(self._requests[key]) >= config.requests:
            # Apply block if configured
            if config.block_seconds:
                self._blocked[key] = now + config.block_seconds
            
            return False
        
        # Add new request timestamp
        self._requests[key].append(now)
        return True
    
    def reset_limits(self, key: str) -> None:
        """
        Reset rate limits for a specific key.
        
        Args:
            key: Unique identifier to reset
        """
        if key in self._requests:
            del self._requests[key]
        
        if key in self._blocked:
            del self._blocked[key]


class RedisRateLimiter(RateLimiter):
    """
    Redis-based implementation of rate limiting.
    
    Provides distributed rate limiting for multi-instance deployments.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the Redis rate limiter.
        
        Args:
            redis_client: Optional Redis client, will create one if not provided
        """
        self.redis = redis_client
        
        if not self.redis:
            settings = get_settings()
            try:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    socket_timeout=3,
                    socket_connect_timeout=3,
                    health_check_interval=30
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Will fail at runtime if redis is needed but not connected
    
    def _get_counter_key(self, key: str) -> str:
        """Get the Redis key for request counting."""
        return f"ratelimit:count:{key}"
    
    def _get_block_key(self, key: str) -> str:
        """Get the Redis key for blocking."""
        return f"ratelimit:block:{key}"
    
    def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """
        Check if a request should be allowed or limited.
        
        Args:
            key: Unique identifier for the client/endpoint
            config: Rate limit configuration
            
        Returns:
            bool: True if request is allowed, False if limited
        """
        if not self.redis:
            # Fail open if Redis is not available
            logger.warning("Redis not available, allowing request")
            return True
        
        try:
            block_key = self._get_block_key(key)
            
            # Check if key is blocked
            if self.redis.exists(block_key):
                return False
            
            counter_key = self._get_counter_key(key)
            now = time.time()
            window_start = now - config.window_seconds
            
            # Clean up old entries
            self.redis.zremrangebyscore(counter_key, 0, window_start)
            
            # Count requests in current window
            request_count = self.redis.zcard(counter_key)
            
            if request_count >= config.requests:
                # Apply block if configured
                if config.block_seconds:
                    self.redis.setex(block_key, config.block_seconds, 1)
                
                return False
            
            # Add new request timestamp
            self.redis.zadd(counter_key, {str(now): now})
            
            # Set expiry on the counter to avoid leaking memory
            self.redis.expire(counter_key, config.window_seconds + 60)
            
            return True
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiter: {e}")
            # Fail open rather than blocking legitimate requests
            return True
    
    def reset_limits(self, key: str) -> None:
        """
        Reset rate limits for a specific key.
        
        Args:
            key: Unique identifier to reset
        """
        if not self.redis:
            return
        
        try:
            # Delete both counter and block keys
            self.redis.delete(self._get_counter_key(key), self._get_block_key(key))
        except redis.RedisError as e:
            logger.error(f"Redis error in reset_limits: {e}")


class RateLimiterFactory:
    """Factory for creating rate limiter instances."""
    
    @staticmethod
    def create_rate_limiter() -> RateLimiter:
        """
        Create a rate limiter instance based on configuration.
        
        Returns:
            RateLimiter: Either a Redis or in-memory rate limiter
        """
        settings = get_settings()
        
        if settings.USE_REDIS_RATE_LIMITER:
            try:
                logger.info("Creating Redis rate limiter")
                return RedisRateLimiter()
            except Exception as e:
                logger.error(f"Failed to create Redis rate limiter: {e}")
                logger.warning("Falling back to in-memory rate limiter")
        
        logger.info("Creating in-memory rate limiter")
        return InMemoryRateLimiter()


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.
    
    Returns:
        RateLimiter: The rate limiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiterFactory.create_rate_limiter()
    
    return _rate_limiter