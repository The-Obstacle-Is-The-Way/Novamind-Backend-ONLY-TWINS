"""Unit tests for the rate limiter functionality."""
import asyncio
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from redis.asyncio.client import Redis
from fastapi import Request, Response, HTTPException

from app.infrastructure.security.rate_limiter import (
    RateLimiter,
    RateLimitType,
    RateLimitExceededError,
    rate_limit_ip
)


class TestRateLimiter:
    """Test suite for RateLimiter class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock(spec=Redis)
        
        # Setup mock pipeline
        mock_pipeline = AsyncMock()
        mock.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [0, 1]  # Default values for first call
        
        # We can further customize the pipeline in individual tests
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.__aexit__.return_value = None
        
        return mock
#     return mock # FIXME: return outside function
    
    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create a RateLimiter instance with a mock Redis client."""
        return RateLimiter(
            redis=mock_redis,
            default_limit=100,
            default_window=timedelta(seconds=60)
        )
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI Request."""
        mock = MagicMock(spec=Request)
        mock.client.host = "127.0.0.1"
        mock.headers = {}
        return mock
    
    @pytest.mark.asyncio
    async def test_init(self, mock_redis):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(
            redis=mock_redis,
            default_limit=100,
            default_window=timedelta(seconds=60)
        )
        
        assert limiter.redis is mock_redis
        assert limiter.default_limit == 100
        assert limiter.default_window == timedelta(seconds=60)
    
    @pytest.mark.asyncio
    async def test_is_rate_limited_not_limited(self, rate_limiter, mock_redis):
        """Test is_rate_limited returns False when limit is not exceeded."""
        # Configure mock pipeline to return values indicating no rate limit exceeded
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.__aexit__.return_value = None
        
        # First value is incr result, second is ttl
        mock_pipeline.execute.return_value = [10, 50]
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test_key",
            limit=100,
            window=timedelta(seconds=60)
        )
        
        assert is_limited is False
        assert info["remaining"] == 90  # 100 - 10
        assert info["reset"] == 50  # TTL from Redis
        
        # Verify the correct Redis commands were called
        mock_pipeline.incr.assert_called_once_with("ratelimit:test_key")
        mock_pipeline.expire.assert_called_once_with("ratelimit:test_key", 60)
    
    @pytest.mark.asyncio
    async def test_is_rate_limited_exceeded(self, rate_limiter, mock_redis):
        """Test is_rate_limited returns True when limit is exceeded."""
        # Configure mock pipeline to return values indicating rate limit exceeded
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.__aexit__.return_value = None
        
        # First value (101) exceeds limit (100), second is TTL
        mock_pipeline.execute.return_value = [101, 45]
        
        is_limited, info = await rate_limiter.is_rate_limited(
            "test_key",
            limit=100,
            window=timedelta(seconds=60)
        )
        
        assert is_limited is True
        assert info["remaining"] == 0  # Since limit is exceeded
        assert info["reset"] == 45  # TTL from Redis
    
    @pytest.mark.asyncio
    async def test_is_rate_limited_default_values(self, rate_limiter, mock_redis):
        """Test is_rate_limited uses default values when not provided."""
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.__aexit__.return_value = None
        mock_pipeline.execute.return_value = [50, 30]
        
        is_limited, info = await rate_limiter.is_rate_limited("test_key")
        
        assert is_limited is False
        assert info["remaining"] == 50  # 100 - 50
        assert info["reset"] == 30  # TTL from Redis
        
        # Verify the expire used the default window (60 seconds)
        mock_pipeline.expire.assert_called_once_with("ratelimit:test_key", 60)
    
    @pytest.mark.asyncio
    async def test_is_rate_limited_redis_error(self, rate_limiter, mock_redis):
        """Test is_rate_limited handles Redis errors properly."""
        # Make Redis pipeline operations raise an exception
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.__aenter__.return_value = mock_pipeline
        mock_pipeline.__aexit__.return_value = None
        mock_pipeline.execute.side_effect = Exception("Redis connection error")
        
        # When Redis fails, should return not limited with appropriate message
        is_limited, info = await rate_limiter.is_rate_limited("test_key")
        
        assert is_limited is False
        assert "error" in info
        assert "Redis connection error" in info["error"]
    
    @pytest.mark.asyncio
    async def test_process_request(self, rate_limiter, mock_request):
        """Test processing a basic request."""
        with patch.object(
            rate_limiter,
            "is_rate_limited",
            AsyncMock(return_value=(False, {"remaining": 99}))
        ):
            is_limited, info = await rate_limiter.process_request(mock_request)
            
            assert is_limited is False
            assert info["remaining"] == 99
            
            # Verify is_rate_limited was called with the correct identifier
            rate_limiter.is_rate_limited.assert_called_once()
            call_args = rate_limiter.is_rate_limited.call_args
            assert call_args[0][0] == "ip:127.0.0.1"
            assert call_args[1]["limit_type"] == RateLimitType.DEFAULT
    
    @pytest.mark.asyncio
    async def test_process_request_with_token(self, rate_limiter, mock_request):
        """Test processing a request with an API token."""
        # Setup request with Authorization header
        mock_request.headers = {"Authorization": "Bearer test_token"}
        
        with patch.object(
            rate_limiter,
            "is_rate_limited",
            AsyncMock(return_value=(False, {"remaining": 99}))
        ):
            is_limited, info = await rate_limiter.process_request(
                mock_request,
                limit_type=RateLimitType.TOKEN
            )
            
            # Verify is_rate_limited was called with token-based identifier
            rate_limiter.is_rate_limited.assert_called_once()
            call_args = rate_limiter.is_rate_limited.call_args
            assert call_args[0][0] == "token:test_token"
            assert call_args[1]["limit_type"] == RateLimitType.TOKEN
    
    @pytest.mark.asyncio
    async def test_process_request_exceeded(self, rate_limiter, mock_request):
        """Test processing a request that exceeds rate limit."""
        with patch.object(
            rate_limiter,
            "is_rate_limited",
            AsyncMock(return_value=(True, {"remaining": 0, "reset": 30}))
        ):
            is_limited, info = await rate_limiter.process_request(mock_request)
            
            assert is_limited is True
            assert info["remaining"] == 0
            assert info["reset"] == 30
    
    @pytest.mark.asyncio
    async def test_rate_limit_ip_decorator(self, mock_redis):
        """Test the rate_limit_ip decorator."""
        # Create a limiter for testing the decorator
        limiter = RateLimiter(redis=mock_redis)
        
        # Setup mock response for the decorator
        mock_response = MagicMock(spec=Response)
        
        # Create a decorated async function
        @rate_limit_ip(limiter=limiter, limit=10)
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        
        # Configure rate limiter mock
        with patch.object(
            limiter,
            "is_rate_limited",
            AsyncMock(return_value=(False, {"remaining": 9, "reset": 60}))
        ):
            # Call decorated function
            result = await test_endpoint(mock_request)
            
            # Verify result
            assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_rate_limit_ip_decorator_exceeded(self, mock_redis):
        """Test the rate_limit_ip decorator when limit is exceeded."""
        # Create a limiter for testing the decorator
        limiter = RateLimiter(redis=mock_redis)
        
        # Create a decorated async function
        @rate_limit_ip(limiter=limiter, limit=10)
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        
        # Configure rate limiter mock to indicate limit exceeded
        with patch.object(
            limiter,
            "is_rate_limited",
            AsyncMock(return_value=(True, {"remaining": 0, "reset": 30}))
        ):
            # Call should raise RateLimitExceededError
            with pytest.raises(RateLimitExceededError):
                await test_endpoint(mock_request)