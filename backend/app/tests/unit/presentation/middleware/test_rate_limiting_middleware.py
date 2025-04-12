# -*- coding: utf-8 -*-
"""
Tests for Rate Limiting Middleware.

This module contains unit tests for the rate limiting functionality,
ensuring it correctly limits API requests according to configuration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from fastapi import HTTPException, Request
from fastapi.responses import Response

from app.core.constants import CacheNamespace
from app.presentation.api.dependencies.rate_limiter import (
    RateLimitDependency,
    RateLimiter, # Assuming RateLimiter exists here or in a related module
    get_client_id # Assuming get_client_id exists here or in a related module
)


@pytest.mark.db_required() # Assuming db_required is a valid marker
class MockCacheService:
    """Mock implementation of CacheService for testing."""

    def __init__(self):
        """Initialize the mock cache with an empty store."""
        self.store = {}
        self.ttls = {}
        self._client = self # For compatibility if RateLimiter expects _client

    async def get(self, key: str) -> Any:
        """Get a value from the mock cache."""
        
        return self.store.get(key)

    async def set(self, key: str, value: Any, expiration: int = None) -> bool:
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


@pytest.fixture
def mock_cache():
    """Fixture providing a mock cache service."""
    
        return MockCacheService()


@pytest.fixture
def rate_limiter(mock_cache):
    """Fixture providing a rate limiter with mock cache."""
    # Assuming RateLimiter takes cache service as input
        return RateLimiter(cache=mock_cache)


@pytest.mark.asyncio
async def test_rate_limiter_initial_request(rate_limiter):
    """Test that the first request within limits is allowed."""
    # Test initial request (should be allowed)
    allowed, count, reset = await rate_limiter.check_rate_limit(
        key="test_client",
        max_requests=10,
        window_seconds=60
    )

    assert allowed is True
    assert count == 1
    assert reset == 60  # Window size


@pytest.mark.asyncio
async def test_rate_limiter_multiple_requests(rate_limiter):
    """Test multiple requests within limits."""
    # Make multiple requests
    results = []
    for _ in range(5):
        result = await rate_limiter.check_rate_limit(
            key="test_client",
            max_requests=10,
            window_seconds=60
        )
        results.append(result)

    # All should be allowed, counts should increment
    for i, (allowed, count, _) in enumerate(results):
        assert allowed is True
        assert count == i + 1


@pytest.mark.asyncio
async def test_rate_limiter_exceeding_limit(rate_limiter):
    """Test that requests exceeding the limit are denied."""
    # Set up rate limit of 5 requests
    max_requests = 5

    # Make 5 requests (all should be allowed)
    for i in range(max_requests):
        allowed, count, _ = await rate_limiter.check_rate_limit(
            key="test_client",
            max_requests=max_requests,
            window_seconds=60
        )
        assert allowed is True
        assert count == i + 1 # Count should increment correctly

    # Make one more request (should be denied)
    allowed, count, _ = await rate_limiter.check_rate_limit(
        key="test_client",
        max_requests=max_requests,
        window_seconds=60
    )

    assert allowed is False
    assert count == max_requests + 1


@pytest.mark.asyncio
async def test_rate_limiter_different_keys(rate_limiter):
    """Test rate limiting for different clients."""
    # Make requests for different clients
    allowed1, count1, _ = await rate_limiter.check_rate_limit(
        key="client1",
        max_requests=5,
        window_seconds=60
    )

    allowed2, count2, _ = await rate_limiter.check_rate_limit(
        key="client2",
        max_requests=5,
        window_seconds=60
    )

    # Both should be allowed with count 1
    assert allowed1 is True and allowed2 is True
    assert count1 == 1 and count2 == 1

    # Verify keys in cache are namespaced
    assert await rate_limiter.cache.exists(f"{CacheNamespace.RATE_LIMIT}:client1")
    assert await rate_limiter.cache.exists(f"{CacheNamespace.RATE_LIMIT}:client2")


@pytest.mark.asyncio
async def test_get_client_id_with_authenticated_user():
    """Test getting client ID for authenticated user."""
    # Mock request and user
    request = MagicMock(spec=Request)
    request.scope = {"client": ("127.0.0.1", 8000)} # Add client scope
    user = {"sub": "user123"}

    client_id = get_client_id(request=request, user=user)

    # Should use user ID
    assert client_id == "user:user123"


@pytest.mark.asyncio
async def test_get_client_id_with_ip():
    """Test getting client ID from IP address."""
    # Mock request with client IP
    request = MagicMock(spec=Request)
    request.scope = {"client": ("192.168.1.1", 8000)} # Add client scope
    request.headers = {} # Ensure headers exist

    client_id = get_client_id(request=request, user=None)

    # Should use IP address
    assert client_id == "ip:192.168.1.1"


@pytest.mark.asyncio
async def test_get_client_id_with_forwarded_ip():
    """Test getting client ID from X-Forwarded-For header."""
    # Mock request with X-Forwarded-For
    request = MagicMock(spec=Request)
    request.scope = {"client": ("10.0.0.1", 8000)} # Internal IP
    request.headers = {"x-forwarded-for": "203.0.113.1, 192.168.1.1"} # Lowercase header

    client_id = get_client_id(request=request, user=None)

    # Should use first IP in X-Forwarded-For
    assert client_id == "ip:203.0.113.1"


@pytest.mark.asyncio
async def test_rate_limit_dependency(mock_cache): # Use mock_cache fixture
    """Test the RateLimitDependency class."""
    # Create dependency
    dependency = RateLimitDependency(max_requests=5, window_seconds=60)

    # Mock request, client_id, and rate_limiter
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    client_id = "test_client"
    # Use the rate_limiter fixture which uses mock_cache
    rate_limiter_instance = RateLimiter(cache=mock_cache)

    # Configure rate_limiter.check_rate_limit to return allowed
    with patch.object(rate_limiter_instance, 'check_rate_limit', return_value=(True, 1, 60)) as mock_check:

        # Call the dependency
        await dependency(request=request, client_id=client_id, rate_limiter=rate_limiter_instance)

        # Verify rate_limiter was called correctly
        mock_check.assert_called_once_with(
            key="default:test_client",
            max_requests=5,
            window_seconds=60
        )

        # Verify headers were set on request.state
        assert request.state.rate_limit_remaining == 4
        assert request.state.rate_limit_reset == 60
        assert request.state.rate_limit_limit == 5


@pytest.mark.asyncio
async def test_rate_limit_dependency_exceeded(mock_cache): # Use mock_cache fixture
    """Test the RateLimitDependency when limit is exceeded."""
    # Create dependency
    dependency = RateLimitDependency(max_requests=5, window_seconds=60)

    # Mock request, client_id, and rate_limiter
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    client_id = "test_client"
    # Use the rate_limiter fixture which uses mock_cache
    rate_limiter_instance = RateLimiter(cache=mock_cache)

    # Configure rate_limiter.check_rate_limit to return not allowed
    with patch.object(rate_limiter_instance, 'check_rate_limit', return_value=(False, 6, 30)) as mock_check:

        # Call the dependency (should raise HTTPException)
        with pytest.raises(HTTPException) as excinfo:
            await dependency(request=request, client_id=client_id, rate_limiter=rate_limiter_instance)

        # Verify exception details
        assert excinfo.value.status_code == 429
        assert "Rate limit exceeded" in excinfo.value.detail
        assert excinfo.value.headers["Retry-After"] == "30"
        assert excinfo.value.headers["X-RateLimit-Limit"] == "5"
        assert excinfo.value.headers["X-RateLimit-Remaining"] == "0"