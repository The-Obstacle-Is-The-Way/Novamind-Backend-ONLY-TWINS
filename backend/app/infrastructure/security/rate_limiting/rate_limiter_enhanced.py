"""
Enhanced Rate Limiter module for API protection.

This module provides enhanced rate limiting capabilities for protecting APIs from abuse.
It supports both in-memory and Redis-based rate limiting with configurable thresholds.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, cast

import redis
from pydantic import BaseModel

from app.core.config import get_settings
settings = get_settings()

logger = logging.getLogger(__name__)


class RateLimitConfig(BaseModel):
    """
    Configuration for rate limiting.
    
    Attributes:
        requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        block_seconds: Optional blocking period after exceeding limit
    """
    
    requests: int
    window_seconds: int
    block_seconds: Optional[int] = None


class RateLimiter(ABC):
    """
    Abstract base class for rate limiters.
    
    This defines the interface that all rate limiter implementations must follow.
    """
    
    @abstractmethod
    def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """
        Check if a request should be rate limited.
        
        Args:
            key: Identifier for the rate limit (e.g., IP address, user ID)
            config: Rate limit configuration
            
        Returns:
            True if request is allowed, False if it should be rate limited
        """
        pass
    
    @abstractmethod
    def reset_limits(self, key: str) -> None:
        """
        Reset rate limits for a specific key.
        
        Args:
            key: Identifier to reset
        """
        pass


class InMemoryRateLimiter(RateLimiter):
    """
    In-memory implementation of rate limiting.
    
    Uses local memory to track request counts and blocked status.
    Suitable for single-instance deployments.
    """
    
    def __init__(self):
        """Initialize the in-memory rate limiter."""
        self._request_logs: Dict[str, List[datetime]] = {}
        self._blocked_until: Dict[str, datetime] = {}
    
    def _clean_old_requests(self, key: str, window_seconds: int) -> None:
        """
        Remove expired requests from the logs.
        
        Args:
            key: Identifier for the rate limit
            window_seconds: Time window in seconds
        """
        if key not in self._request_logs:
            return
            
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        self._request_logs[key] = [
            t for t in self._request_logs[key] if t >= cutoff
        ]
    
    def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """
        Check if a request should be rate limited.
        
        Args:
            key: Identifier for the rate limit (e.g., IP address, user ID)
            config: Rate limit configuration
            
        Returns:
            True if request is allowed, False if it should be rate limited
        """
        now = datetime.now()
        
        # Check if the key is blocked
        if key in self._blocked_until and self._blocked_until[key] > now:
            return False
        
        # Clean up old requests
        self._clean_old_requests(key, config.window_seconds)
        
        # Initialize request log if needed
        if key not in self._request_logs:
            self._request_logs[key] = []
        
        # Check if over the limit
        if len(self._request_logs[key]) >= config.requests:
            # Block the key if block_seconds is set
            if config.block_seconds:
                self._blocked_until[key] = now + timedelta(seconds=config.block_seconds)
            return False
        
        # Add this request to the log
        self._request_logs[key].append(now)
        return True
    
    def reset_limits(self, key: str) -> None:
        """
        Reset rate limits for a specific key.
        
        Args:
            key: Identifier to reset
        """
        if key in self._request_logs:
            del self._request_logs[key]
        
        if key in self._blocked_until:
            del self._blocked_until[key]


class RedisRateLimiter(RateLimiter):
    """
    Redis-based implementation of rate limiting.
    
    Uses Redis sorted sets for distributed rate limiting across multiple instances.
    Suitable for production, multi-instance deployments.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the Redis rate limiter.
        
        Args:
            redis_client: Optional Redis client to use
        """
        self._redis = redis_client
    
    def _get_counter_key(self, key: str) -> str:
        """
        Generate Redis key for request counter.
        
        Args:
            key: Identifier for the rate limit
            
        Returns:
            Redis key string
        """
        return f"ratelimit:counter:{key}"
    
    def _get_blocked_key(self, key: str) -> str:
        """
        Generate Redis key for blocked status.
        
        Args:
            key: Identifier for the rate limit
            
        Returns:
            Redis key string
        """
        return f"ratelimit:blocked:{key}"
    
    def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """
        Check if a request should be rate limited.
        
        Args:
            key: Identifier for the rate limit (e.g., IP address, user ID)
            config: Rate limit configuration
            
        Returns:
            True if request is allowed, False if it should be rate limited
        """
        try:
            if not self._redis:
                return True
                
            now = datetime.now().timestamp()
            blocked_key = self._get_blocked_key(key)
            counter_key = self._get_counter_key(key)
            
            # Check if the key is blocked
            if self._redis.exists(blocked_key):
                return False
            
            # Clean up old requests
            expired_cutoff = now - config.window_seconds
            self._redis.zremrangebyscore(counter_key, 0, expired_cutoff)
            
            # Check if over the limit
            request_count = self._redis.zcard(counter_key)
            if request_count >= config.requests:
                # Block the key if block_seconds is set
                if config.block_seconds:
                    self._redis.setex(blocked_key, config.block_seconds, 1)
                return False
            
            # Add this request to the log
            self._redis.zadd(counter_key, {str(now): now})
            # Set expiration on the sorted set
            self._redis.expire(counter_key, config.window_seconds * 2)
            
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiter: {e}")
            # Fail open - allow the request when Redis has an error
            return True
    
    def reset_limits(self, key: str) -> None:
        """
        Reset rate limits for a specific key.
        
        Args:
            key: Identifier to reset
        """
        try:
            if not self._redis:
                return
                
            blocked_key = self._get_blocked_key(key)
            counter_key = self._get_counter_key(key)
            
            # Delete both keys
            self._redis.delete(blocked_key, counter_key)
            
        except redis.RedisError as e:
            logger.error(f"Redis error in reset_limits: {e}")


class RateLimiterFactory:
    """
    Factory for creating rate limiters.
    
    This class uses the Factory Method pattern to create the appropriate
    rate limiter based on configuration settings.
    """
    
    @staticmethod
    def create_rate_limiter() -> RateLimiter:
        """
        Create a rate limiter based on configuration.
        
        Returns:
            An appropriate RateLimiter implementation
        """
        # Use Redis limiter if configured
        app_settings = get_settings()
        if app_settings.USE_REDIS_RATE_LIMITER:
            try:
                redis_client = redis.Redis(
                    host=app_settings.REDIS_HOST,
                    port=app_settings.REDIS_PORT,
                    password=app_settings.REDIS_PASSWORD,
                    db=app_settings.REDIS_DB,
                    socket_timeout=5,
                    decode_responses=True
                )
                # Test connection
                redis_client.ping()
                logger.info("Using Redis-based rate limiter")
                return RedisRateLimiter(redis_client)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, falling back to in-memory rate limiter: {e}")
        
        # Default to in-memory limiter
        logger.info("Using in-memory rate limiter")
        return InMemoryRateLimiter()