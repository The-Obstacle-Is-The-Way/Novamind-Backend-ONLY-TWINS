"""Unit tests for the rate limiter functionality."""
import pytest
from datetime import datetime, timedelta
import time
from unittest.mock import Mock, patch, MagicMock
import redis

from app.infrastructure.security.rate_limiter_enhanced import (
    RateLimiter,
    RateLimitConfig,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimiterFactory
)


@pytest.fixture
def in_memory_rate_limiter():
    """Create an in-memory rate limiter for testing."""
    return InMemoryRateLimiter()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.zcard.return_value = 0
    mock.zadd.return_value = True
    mock.zremrangebyscore.return_value = 0
    mock.exists.return_value = False
    return mock


@pytest.fixture
def redis_rate_limiter(mock_redis):
    """Create a Redis rate limiter with mocked Redis client."""
    return RedisRateLimiter(redis_client=mock_redis)


class TestRateLimitConfig:
    """Tests for the RateLimitConfig class."""

    def test_init(self):
        """Test initialization of RateLimitConfig."""
        config = RateLimitConfig(requests=100, window_seconds=60, block_seconds=300)
        
        assert config.requests == 100
        assert config.window_seconds == 60
        assert config.block_seconds == 300

    def test_init_no_block(self):
        """Test initialization without block_seconds."""
        config = RateLimitConfig(requests=100, window_seconds=60)
        
        assert config.requests == 100
        assert config.window_seconds == 60
        assert config.block_seconds is None


class TestInMemoryRateLimiter:
    """Tests for the InMemoryRateLimiter implementation."""

    def test_check_rate_limit_under_limit(self, in_memory_rate_limiter):
        """Test that requests under the limit are allowed."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        
        # Should allow 5 requests
        for _ in range(5):
            assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True
        
        # 6th request should be limited
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is False

    def test_check_rate_limit_window_expiry(self, in_memory_rate_limiter):
        """Test that requests are allowed after the window expires."""
        config = RateLimitConfig(requests=1, window_seconds=1)
        
        # First request should be allowed
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True
        
        # Second request in the same window should be limited
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is False
        
        # Wait for the window to expire
        time.sleep(1.1)
        
        # Request should now be allowed again
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True

    def test_check_rate_limit_with_blocking(self, in_memory_rate_limiter):
        """Test that blocking prevents requests for the specified duration."""
        config = RateLimitConfig(requests=1, window_seconds=1, block_seconds=2)
        
        # First request should be allowed
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True
        
        # Second request exceeds limit and triggers blocking
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is False
        
        # Even after window expires, should still be blocked
        time.sleep(1.1)
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is False
        
        # After block expires, should be allowed again
        time.sleep(1.1)
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True

    def test_reset_limits(self, in_memory_rate_limiter):
        """Test resetting rate limits for a key."""
        config = RateLimitConfig(requests=1, window_seconds=60, block_seconds=300)
        
        # Use up the limit
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is False
        
        # Reset the limits
        in_memory_rate_limiter.reset_limits("test-key")
        
        # Should be allowed again
        assert in_memory_rate_limiter.check_rate_limit("test-key", config) is True

    def test_different_keys(self, in_memory_rate_limiter):
        """Test that different keys have separate rate limits."""
        config = RateLimitConfig(requests=1, window_seconds=60)
        
        # Use up limit for first key
        assert in_memory_rate_limiter.check_rate_limit("key1", config) is True
        assert in_memory_rate_limiter.check_rate_limit("key1", config) is False
        
        # Second key should still be allowed
        assert in_memory_rate_limiter.check_rate_limit("key2", config) is True
        assert in_memory_rate_limiter.check_rate_limit("key2", config) is False


class TestRedisRateLimiter:
    """Tests for the RedisRateLimiter implementation."""

    def test_check_rate_limit_under_limit(self, redis_rate_limiter, mock_redis):
        """Test that requests under the limit are allowed."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        
        # Mock zcard to return increasing counts
        mock_redis.zcard.side_effect = [0, 1, 2, 3, 4, 5]
        
        # Should allow 5 requests
        for i in range(5):
            assert redis_rate_limiter.check_rate_limit("test-key", config) is True
            
        # 6th request should be limited
        assert redis_rate_limiter.check_rate_limit("test-key", config) is False

    def test_check_rate_limit_with_blocking(self, redis_rate_limiter, mock_redis):
        """Test that blocking prevents requests for the specified duration."""
        config = RateLimitConfig(requests=1, window_seconds=1, block_seconds=2)
        
        # First request should be allowed
        mock_redis.zcard.return_value = 0
        assert redis_rate_limiter.check_rate_limit("test-key", config) is True
        
        # Second request exceeds limit and triggers blocking
        mock_redis.zcard.return_value = 1
        assert redis_rate_limiter.check_rate_limit("test-key", config) is False
        
        # Check that setex was called to set the block
        mock_redis.setex.assert_called_once()

    def test_blocked_key(self, redis_rate_limiter, mock_redis):
        """Test that blocked keys are rejected."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        
        # Mock exists to indicate key is blocked
        mock_redis.exists.return_value = True
        
        assert redis_rate_limiter.check_rate_limit("test-key", config) is False
        
        # Should not check the counter when blocked
        mock_redis.zcard.assert_not_called()

    def test_reset_limits(self, redis_rate_limiter, mock_redis):
        """Test resetting rate limits for a key."""
        redis_rate_limiter.reset_limits("test-key")
        
        # Should delete both the counter and blocked keys
        mock_redis.delete.assert_called_once()

    def test_redis_error_handling(self, redis_rate_limiter, mock_redis):
        """Test that Redis errors result in allowing requests (fail open)."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        
        # Mock Redis to raise an exception
        mock_redis.zcard.side_effect = redis.RedisError("Connection error")
        
        # Should allow the request despite Redis error
        assert redis_rate_limiter.check_rate_limit("test-key", config) is True


class TestRateLimiterFactory:
    """Tests for the RateLimiterFactory."""

    @patch('app.core.config.get_settings')
    def test_create_in_memory_limiter(self, mock_get_settings):
        """Test creating an in-memory rate limiter."""
        mock_settings = MagicMock()
        mock_settings.USE_REDIS_RATE_LIMITER = False
        mock_get_settings.return_value = mock_settings
        
        limiter = RateLimiterFactory.create_rate_limiter()
        
        assert isinstance(limiter, InMemoryRateLimiter)

    @patch('app.core.config.get_settings')
    @patch('app.infrastructure.security.rate_limiter_enhanced.redis.Redis')
    def test_create_redis_limiter(self, mock_redis, mock_get_settings):
        """Test creating a Redis rate limiter."""
        # Setup mock settings
        mock_settings = MagicMock()
        mock_settings.USE_REDIS_RATE_LIMITER = True
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_PASSWORD = ""
        mock_settings.REDIS_DB = 0
        mock_get_settings.return_value = mock_settings
        
        # Setup mock Redis client to succeed ping
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        # Create limiter
        limiter = RateLimiterFactory.create_rate_limiter()
        
        # Verify
        assert isinstance(limiter, RedisRateLimiter)

    @patch('app.core.config.get_settings')
    @patch('app.infrastructure.security.rate_limiter_enhanced.redis.Redis')
    def test_fallback_on_redis_error(self, mock_redis, mock_get_settings):
        """Test fallback to in-memory limiter on Redis error."""
        mock_settings = MagicMock()
        mock_settings.USE_REDIS_RATE_LIMITER = True
        mock_get_settings.return_value = mock_settings
        
        # Mock Redis to raise an exception
        mock_redis.side_effect = Exception("Redis connection error")
        
        limiter = RateLimiterFactory.create_rate_limiter()
        
        # Should fall back to in-memory implementation
        assert isinstance(limiter, InMemoryRateLimiter)