# -*- coding: utf-8 -*-
"""
Rate Limiting Middleware

This module provides middleware for rate limiting requests to the NOVAMIND API.
It uses a Redis-backed distributed rate limiter to enforce limits across multiple instances.
"""

import json
import logging
from typing import Callable, Optional

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.infrastructure.security.rate_limiter import (
    DistributedRateLimiter,
    RateLimitType,
    get_rate_limiter,
)

# Configure logger
logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests based on client IP and user ID.
    
    This middleware applies rate limits to all incoming requests, with
    different limits based on the request path and user role.
    """
    
    def __init__(self, app, rate_limiter: Optional[DistributedRateLimiter] = None):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            rate_limiter: Optional rate limiter instance for dependency injection
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()
        
        # Paths that are exempt from rate limiting
        self.exempt_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request through the middleware.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware/endpoint
            
        Returns:
            Response: The processed response
        """
        # Skip rate limiting for exempt paths
        path = request.url.path
        if any(path.startswith(exempt_path) for exempt_path in self.exempt_paths):
            return await call_next(request)
        
        # Determine rate limit type based on path
        limit_type = self._get_rate_limit_type(path)
        
        # Get user ID if available in request state
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("sub") or request.state.user.get("id")
        
        # Check if rate limited
        is_limited, rate_limit_info = await self.rate_limiter.process_request(
            request=request,
            limit_type=limit_type,
            user_id=user_id,
        )
        
        if is_limited:
            # Create rate limited response
            content = {
                "detail": "Rate limit exceeded",
                "retry_after": rate_limit_info.get("retry_after", 1),
            }
            response = Response(
                content=json.dumps(content),
                media_type="application/json",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            
            # Add rate limit headers
            await self.rate_limiter.apply_rate_limit_headers(response, rate_limit_info)
            
            # Log rate limit event
            logger.warning(
                f"Rate limit exceeded for {request.client.host} on {path}"
            )
            
            return response
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to response
        await self.rate_limiter.apply_rate_limit_headers(response, rate_limit_info)
        
        return response
    
    def _get_rate_limit_type(self, path: str) -> RateLimitType:
        """
        Determine the rate limit type based on the request path.
        
        Args:
            path: The request path
            
        Returns:
            RateLimitType: The appropriate rate limit type
        """
        # Login endpoints
        if path.startswith("/api/v1/auth/") and "login" in path.lower():
            return RateLimitType.LOGIN
        
        # Analytics endpoints
        if path.startswith("/api/v1/analytics"):
            return RateLimitType.ANALYTICS
        
        # Patient data endpoints
        if path.startswith("/api/v1/patients"):
            return RateLimitType.PATIENT_DATA
        
        # Default rate limit
        return RateLimitType.DEFAULT


def setup_rate_limiting(app) -> None:
    """
    Configure rate limiting middleware for the application.
    
    Args:
        app: The FastAPI application
    """
    app.add_middleware(RateLimitingMiddleware)