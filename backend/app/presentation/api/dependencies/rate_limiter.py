# -*- coding: utf-8 -*-
"""
Rate Limiter Dependency Module.

This module provides FastAPI dependencies for rate limiting,
ensuring proper protection against abuse and API overload.
"""

from typing import Optional
from fastapi import Depends, Request, HTTPException, status

from app.core.utils.logging import get_logger
from app.presentation.api.dependencies.auth import get_current_user
from app.presentation.api.dependencies.services import get_cache_service
from app.application.interfaces.services.cache_service import CacheService
from app.core.constants import CacheNamespace


logger = get_logger(__name__)


class RateLimitDependency:
    """
    Rate limiting dependency for FastAPI endpoints.
    
    This class creates a callable dependency that can be injected into
    FastAPI endpoints to enforce rate limits.
    """
    
    def __init__(
        self, 
        api_tier: str, 
        max_requests: Optional[int] = None, 
        window_seconds: Optional[int] = None
    ):
        """
        Initialize the rate limiter.
        
        Args:
            api_tier: Rate limit tier to use (e.g., 'standard', 'analytics')
            max_requests: Maximum requests per window, or None to use config default
            window_seconds: Time window in seconds, or None to use config default
        """
        self.api_tier = api_tier
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
    async def __call__(
        self, 
        request: Request, 
        cache: CacheService = Depends(get_cache_service),
        user: Optional[dict] = Depends(get_current_user)
    ) -> None:
        """
        Check rate limit for current request.
        
        This method is called when the dependency is injected into an endpoint.
        It checks the rate limit and raises an exception if the limit is exceeded.
        
        Args:
            request: FastAPI request
            cache: Cache service for tracking request counts
            user: Authenticated user
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Get client identifier (IP or user ID)
        client_id = self._get_client_identifier(request, user)
        
        # Check rate limit
        if await self._is_rate_limited(client_id, cache):
            logger.warning(f"Rate limit exceeded for client {client_id} on {self.api_tier} tier")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
    
    def _get_client_identifier(self, request: Request, user: Optional[dict]) -> str:
        """
        Get a unique identifier for the client.
        
        Uses user ID if authenticated, or IP address if not.
        
        Args:
            request: FastAPI request
            user: Authenticated user
            
        Returns:
            Client identifier
        """
        # Use user ID if available
        if user and "sub" in user:
            return f"user:{user['sub']}"
            
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
        
    async def _is_rate_limited(self, client_id: str, cache: CacheService) -> bool:
        """
        Check if the client has exceeded their rate limit.
        
        Args:
            client_id: Client identifier
            cache: Cache service
            
        Returns:
            True if rate limited, False otherwise
        """
        # Set defaults if not specified
        max_requests = self.max_requests or 100  # Default: 100 requests
        window_seconds = self.window_seconds or 60  # Default: 60 seconds
        
        # Create cache key
        cache_key = f"{CacheNamespace.RATE_LIMIT}:{self.api_tier}:{client_id}"
        
        # Get current count
        count = await cache.get(cache_key) or 0
        
        # Check if limit exceeded
        if count >= max_requests:
            return True
            
        # Increment counter and set expiry
        await cache.increment(cache_key)
        await cache.expire(cache_key, window_seconds)
        
        return False

# --- Factory Functions --- (Likely missing definitions)

def rate_limit(
    api_tier: str = "standard", 
    max_requests: Optional[int] = None, 
    window_seconds: Optional[int] = None
) -> RateLimitDependency:
    """Factory for standard rate limit dependency."""
    return RateLimitDependency(api_tier, max_requests, window_seconds)

def sensitive_rate_limit(
    api_tier: str = "sensitive", 
    max_requests: Optional[int] = 5, # Example: Lower limit for sensitive ops
    window_seconds: Optional[int] = 60
) -> RateLimitDependency:
    """Factory for sensitive operation rate limit dependency."""
    return RateLimitDependency(api_tier, max_requests, window_seconds)

def admin_rate_limit(
    api_tier: str = "admin", 
    max_requests: Optional[int] = 1000, # Example: Higher limit for admin ops
    window_seconds: Optional[int] = 60 
) -> RateLimitDependency:
    """Factory for admin operation rate limit dependency."""
    return RateLimitDependency(api_tier, max_requests, window_seconds)