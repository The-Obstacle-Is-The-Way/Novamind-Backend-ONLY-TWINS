# -*- coding: utf-8 -*-
"""
Unit tests for Redis-backed Rate Limiter.

Tests the rate limiting functionality with mock Redis to ensure proper
rate limiting, token bucket algorithm, and response headers.
"""

import json
import time
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Request, Response
from starlette.datastructures import Headers, MutableHeaders

from app.infrastructure.security.rate_limiter import (
    DistributedRateLimiter,  
    RateLimitConfig,  
    RateLimitType  
)
@pytest.fixture
def mock_cache_service():
        """Create a mock Redis cache service for testing."""
    mock_cache = AsyncMock()
mock_cache.exists = AsyncMock(return_value=False)
mock_cache.get = AsyncMock(return_value=None)
mock_cache.set = AsyncMock(return_value=True)
    # Ensure the Redis client exists for the rate limiter
    mock_cache.redis_client = AsyncMock()
return mock_cache
@pytest.fixture
def rate_limiter(mock_cache_service):
        """Create a DistributedRateLimiter instance with a mock cache service."""
    limiter = DistributedRateLimiter(cache_service=mock_cache_service)
return limiter
@pytest.fixture
def mock_request():
        """Create a mock FastAPI request for testing."""
    mock = MagicMock(spec=Request)
mock.client = MagicMock()
mock.client.host = "127.0.0.1"
    mock.headers = Headers({})
mock.state = MagicMock()
mock.state.user = None    return mock
@pytest.fixture
def mock_response():
        """Create a mock Response for testing."""
    mock = MagicMock(spec=Response)
mock.headers = MutableHeaders({})
return mock


@pytest.mark.db_required
class TestRateLimitConfig:
        """Tests for RateLimitConfig class."""
def test_init(self):
    """Test initialization of RateLimitConfig."""
        config = RateLimitConfig(
            requests_per_period=100,
            period_seconds=60,
            burst_capacity=10
        )
assert config.requests_per_period == 100
        assert config.period_seconds == 60
        assert config.burst_capacity == 10
def test_init_default_burst_capacity(self):
    """Test initialization of RateLimitConfig with default burst capacity."""
        config = RateLimitConfig(
            requests_per_period=100,
            period_seconds=60
        )
assert config.requests_per_period == 100
        assert config.period_seconds == 60
        assert config.burst_capacity == 0
class TestDistributedRateLimiter:
        """Tests for DistributedRateLimiter class."""
def test_init(self, mock_cache_service):
    """Test initialization of DistributedRateLimiter."""
        limiter = DistributedRateLimiter(cache_service=mock_cache_service)
assert limiter.cache == mock_cache_service
        assert limiter.configs
        assert limiter.configs[RateLimitType.DEFAULT].requests_per_period == 100
        assert limiter.configs[RateLimitType.LOGIN].requests_per_period == 5
def test_configure(self, rate_limiter):
    """Test configuring rate limits."""
        custom_config = RateLimitConfig(
            requests_per_period=200,
            period_seconds=30,
            burst_capacity=20
        )
rate_limiter.configure(RateLimitType.DEFAULT, custom_config)
assert rate_limiter.configs[RateLimitType.DEFAULT].requests_per_period == 200
        assert rate_limiter.configs[RateLimitType.DEFAULT].period_seconds == 30
        assert rate_limiter.configs[RateLimitType.DEFAULT].burst_capacity == 20

    @pytest.mark.asyncio
    async def test_is_rate_limited_redis_unavailable(self, rate_limiter):
    """Test behavior when Redis is unavailable."""
        rate_limiter.cache.redis_client = None
        is_limited, info = await rate_limiter.is_rate_limited("test-ip")
assert is_limited is False
        assert info["allowed"] is True
        assert "Redis unavailable" in info["reason"]

    @pytest.mark.asyncio
    async def test_is_rate_limited_new_bucket(self, rate_limiter, mock_cache_service):
    """Test first request creates a new bucket."""
        mock_cache_service.exists.return_value = False
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test-ip", RateLimitType.DEFAULT
        )
        
        assert is_limited is False
        assert "remaining" in info
        assert info["remaining"] == 109  # 100 + 10 burst - 1 current request
        
        # Verify cache interactions
        mock_cache_service.exists.assert_called_once()
mock_cache_service.set.assert_called_once()
        # Check contents of what was stored in cache
        call_args = mock_cache_service.set.call_args[1]
assert call_args["key"].startswith("rate_limit:default:test-ip")
assert "remaining" in call_args["value"]
assert call_args["value"]["remaining"] == 109

    @pytest.mark.asyncio
    async def test_is_rate_limited_existing_bucket(self, rate_limiter, mock_cache_service):
    """Test request with existing bucket."""
        mock_cache_service.exists.return_value = True
        current_time = time.time()
mock_cache_service.get.return_value = {
            "remaining": 50,
            "reset_at": current_time + 30,
            "last_request": current_time - 5,
        }
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test-ip", RateLimitType.DEFAULT
        )
        
        assert is_limited is False
        assert info["remaining"] == 49  # 50 - 1
        assert info["reset_at"] == current_time + 30
        
        # Verify cache interactions
        mock_cache_service.exists.assert_called_once()
mock_cache_service.get.assert_called_once()
mock_cache_service.set.assert_called_once()
        # Check contents of what was stored in cache
        call_args = mock_cache_service.set.call_args[1]
assert call_args["key"].startswith("rate_limit:default:test-ip")
assert call_args["value"]["remaining"] == 49

    @pytest.mark.asyncio
    async def test_is_rate_limited_bucket_expired(self, rate_limiter, mock_cache_service):
    """Test request when bucket has expired."""
        mock_cache_service.exists.return_value = True
        current_time = time.time()
mock_cache_service.get.return_value = {
            "remaining": 50,
            "reset_at": current_time - 10,  # Expired 10 seconds ago
            "last_request": current_time - 30,
        }
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test-ip", RateLimitType.DEFAULT
        )
        
        assert is_limited is False
        assert info["remaining"] == 109  # Bucket was reset
        
        # Verify cache interactions
        mock_cache_service.exists.assert_called_once()
mock_cache_service.get.assert_called_once()
mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_rate_limited_no_tokens_left(self, rate_limiter, mock_cache_service):
    """Test request when no tokens are left."""
        mock_cache_service.exists.return_value = True
        current_time = time.time()
mock_cache_service.get.return_value = {
            "remaining": 0,
            "reset_at": current_time + 30,
            "last_request": current_time - 1,
        }
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test-ip", RateLimitType.DEFAULT
        )
        
        assert is_limited is True
        assert info["remaining"] == 0
        assert info["retry_after"] >= 29  # At least 29 seconds left
        
        # Verify cache interactions
        mock_cache_service.exists.assert_called_once()
mock_cache_service.get.assert_called_once()
        # No set called since the bucket wasn't modified

    @pytest.mark.asyncio
    async def test_is_rate_limited_with_user_id(self, rate_limiter, mock_cache_service):
    """Test rate limiting with a user ID."""
        mock_cache_service.exists.return_value = False
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test-ip", RateLimitType.DEFAULT, user_id="user123"
        )
        
        assert is_limited is False
        assert "remaining" in info
        
        # Verify cache interactions
        mock_cache_service.exists.assert_called_once()
        # Check the key includes the user ID
        call_args = mock_cache_service.exists.call_args[0][0]
assert "user123" in call_args

    @pytest.mark.asyncio
    async def test_is_rate_limited_redis_error(self, rate_limiter, mock_cache_service):
    """Test behavior when Redis raises an error."""
        mock_cache_service.exists.side_effect = Exception("Redis error")
        
        is_limited, info = await rate_limiter.is_rate_limited("test-ip")
        
        assert is_limited is False
        assert "Error" in info["reason"]

    @pytest.mark.asyncio
    async def test_apply_rate_limit_headers(self, rate_limiter, mock_response):
    """Test applying rate limit headers to response."""
        rate_limit_info = {
            "limit": 100,
            "remaining": 99,
            "reset_at": time.time() + 60,
        }
        
        await rate_limiter.apply_rate_limit_headers(mock_response, rate_limit_info)
        
        assert mock_response.headers["X-RateLimit-Limit"] == "100"
        assert mock_response.headers["X-RateLimit-Remaining"] == "99"
        assert "X-RateLimit-Reset" in mock_response.headers

    @pytest.mark.asyncio
    async def test_apply_rate_limit_headers_with_retry(self, rate_limiter, mock_response):
    """Test applying rate limit headers with retry-after."""
        rate_limit_info = {
            "limit": 100,
            "remaining": 0,
            "reset_at": time.time() + 60,
            "retry_after": 60,
        }
        
        await rate_limiter.apply_rate_limit_headers(mock_response, rate_limit_info)
        
        assert mock_response.headers["X-RateLimit-Limit"] == "100"
        assert mock_response.headers["X-RateLimit-Remaining"] == "0"
        assert mock_response.headers["Retry-After"] == "60"

    @pytest.mark.asyncio
    async def test_process_request_default(self, rate_limiter, mock_request):
    """Test processing a basic request."""
        with patch.object(:
            rate_limiter, "is_rate_limited", AsyncMock(return_value=(False, {"remaining": 99})))
            is_limited, info = await rate_limiter.process_request(mock_request)
            
            assert is_limited is False
            assert info["remaining"] == 99
            
            # Verify is_rate_limited was called with the correct identifier
            rate_limiter.is_rate_limited.assert_called_once()
call_args = rate_limiter.is_rate_limited.call_args
            assert call_args[0][0] == "ip:127.0.0.1"
            assert call_args[1]["limit_type"] == RateLimitType.DEFAULT

    @pytest.mark.asyncio
    async def test_process_request_with_api_key(self, rate_limiter, mock_request):
    """Test processing a request with an API key."""
        mock_request.headers = Headers({"X-API-Key": "test-api-key"})
        
        with patch.object(:
            rate_limiter, "is_rate_limited", AsyncMock(return_value=(False, {"remaining": 99})))
            is_limited, info = await rate_limiter.process_request(mock_request)
            
            assert is_limited is False
            assert info["remaining"] == 99
            
            # Verify is_rate_limited was called with the correct identifier and type
            rate_limiter.is_rate_limited.assert_called_once()
call_args = rate_limiter.is_rate_limited.call_args
            assert call_args[0][0] == "api_key:test-api-key"
            assert call_args[1]["limit_type"] == RateLimitType.API_KEY

    @pytest.mark.asyncio
    async def test_process_request_with_user(self, rate_limiter, mock_request):
    """Test processing a request with a user."""
        mock_request.state.user = {"sub": "user123"}
        
        with patch.object(:
            rate_limiter, "is_rate_limited", AsyncMock(return_value=(False, {"remaining": 99})))
            is_limited, info = await rate_limiter.process_request(mock_request)
            
            assert is_limited is False
            assert info["remaining"] == 99
            
            # Verify is_rate_limited was called with the correct user_id
            rate_limiter.is_rate_limited.assert_called_once()
call_args = rate_limiter.is_rate_limited.call_args
            assert call_args[1]["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_process_request_custom_limit_type(self, rate_limiter, mock_request):
    """Test processing a request with a custom limit type."""
        with patch.object(:
            rate_limiter, "is_rate_limited", AsyncMock(return_value=(False, {"remaining": 99})))
            is_limited, info = await rate_limiter.process_request(
                mock_request, RateLimitType.LOGIN
            )
            
            assert is_limited is False
            assert info["remaining"] == 99
            
            # Verify is_rate_limited was called with the correct limit_type
            rate_limiter.is_rate_limited.assert_called_once()
call_args = rate_limiter.is_rate_limited.call_args
            assert call_args[1]["limit_type"] == RateLimitType.LOGIN