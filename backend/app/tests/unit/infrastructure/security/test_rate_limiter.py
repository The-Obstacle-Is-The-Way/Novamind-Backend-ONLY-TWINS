"""Unit tests for rate limiter implementation."""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import redis

from app.infrastructure.security.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimiterFactory
)


class TestRateLimitConfig:
    """Test suite for RateLimitConfig."""

    def test_init(self):
        """Test the initialization of RateLimitConfig."""
        config = RateLimitConfig(requests=10, window_seconds=60, block_seconds=120)
        assert config.requests == 10
        assert config.window_seconds == 60
        assert config.block_seconds == 120

    def test_init_without_block(self):
        """Test initialization without block_seconds."""
        config = RateLimitConfig(requests=10, window_seconds=60)
        assert config.requests == 10
        assert config.window_seconds == 60
        assert config.block_seconds is None


class TestInMemoryRateLimiter:
    """Test suite for in-memory rate limiter implementation."""

    @pytest.fixture
    def limiter(self):
        """Create a fresh rate limiter for each test."""
        return InMemoryRateLimiter()

    @pytest.fixture
    def basic_config(self):
        """Create a basic rate limit config."""
        return RateLimitConfig(requests=3, window_seconds=60)

    @pytest.fixture
    def blocking_config(self):
        """Create a config with blocking enabled."""
        return RateLimitConfig(requests=3, window_seconds=60, block_seconds=120)

    def test_basic_rate_limiting(self, limiter, basic_config):
        """Test that basic rate limiting works."""
        key = "test_ip"
        
        # First 3 requests should be allowed
        assert limiter.check_rate_limit(key, basic_config) is True
        assert limiter.check_rate_limit(key, basic_config) is True
        assert limiter.check_rate_limit(key, basic_config) is True
        
        # Fourth request should be blocked
        assert limiter.check_rate_limit(key, basic_config) is False
    
    def test_different_keys_counted_separately(self, limiter, basic_config):
        """Test that different keys are rate limited separately."""
        key1 = "ip1"
        key2 = "ip2"
        
        # Use up all requests for key1
        for _ in range(3):
            assert limiter.check_rate_limit(key1, basic_config) is True
        
        # Should be blocked now
        assert limiter.check_rate_limit(key1, basic_config) is False
        
        # But key2 should still be allowed
        assert limiter.check_rate_limit(key2, basic_config) is True
    
    def test_sliding_window(self, limiter):
        """Test that the sliding window works correctly."""
        key = "test_ip"
        
        # Short window config for testing
        config = RateLimitConfig(requests=2, window_seconds=1)
        
        # First 2 requests allowed
        assert limiter.check_rate_limit(key, config) is True
        assert limiter.check_rate_limit(key, config) is True
        
        # Third request blocked
        assert limiter.check_rate_limit(key, config) is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.check_rate_limit(key, config) is True
    
    def test_blocking(self, limiter, blocking_config):
        """Test that blocking works correctly."""
        key = "test_ip"
        
        # Use up all requests
        for _ in range(3):
            assert limiter.check_rate_limit(key, blocking_config) is True
        
        # Trigger blocking
        assert limiter.check_rate_limit(key, blocking_config) is False
        
        # Even after a clean window, should still be blocked
        limiter._request_history[key] = []
        assert limiter.check_rate_limit(key, blocking_config) is False
        
        # Simulate block time expiring
        limiter._blocked_until[key] = datetime.now() - timedelta(seconds=1)
        
        # Now should work again
        assert limiter.check_rate_limit(key, blocking_config) is True
    
    def test_reset_limits(self, limiter, basic_config):
        """Test that reset_limits works properly."""
        key = "test_ip"
        
        # Use up all requests
        for _ in range(3):
            assert limiter.check_rate_limit(key, basic_config) is True
        
        # Fourth request blocked
        assert limiter.check_rate_limit(key, basic_config) is False
        
        # Reset the limits
        limiter.reset_limits(key)
        
        # Should work again
        assert limiter.check_rate_limit(key, basic_config) is True


class TestRedisRateLimiter:
    """Test suite for Redis-based rate limiter."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mocked Redis client."""
        mock = MagicMock(spec=redis.Redis)
        # Default behavior for exists
        mock.exists.return_value = False
        # Default behavior for zcard (count)
        mock.zcard.return_value = 0
        return mock
    
    @pytest.fixture
    def limiter(self, mock_redis):
        """Create a Redis rate limiter with mocked Redis client."""
        return RedisRateLimiter(redis_client=mock_redis)
    
    @pytest.fixture
    def basic_config(self):
        """Create a basic rate limit config."""
        return RateLimitConfig(requests=3, window_seconds=60)
    
    @pytest.fixture
    def blocking_config(self):
        """Create a config with blocking enabled."""
        return RateLimitConfig(requests=3, window_seconds=60, block_seconds=120)
    
    def test_check_when_not_blocked_and_under_limit(self, limiter, mock_redis, basic_config):
        """Test normal flow when request is under the limit."""
        key = "test_ip"
        mock_redis.exists.return_value = False  # Not blocked
        mock_redis.zcard.return_value = 2  # Under limit
        
        result = limiter.check_rate_limit(key, basic_config)
        
        assert result is True
        # Check Redis operations
        mock_redis.zremrangebyscore.assert_called_once()
        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    def test_check_when_over_limit(self, limiter, mock_redis, basic_config):
        """Test when request exceeds the limit."""
        key = "test_ip"
        mock_redis.exists.return_value = False  # Not blocked
        mock_redis.zcard.return_value = 3  # At limit
        
        result = limiter.check_rate_limit(key, basic_config)
        
        assert result is False
        # Should not add request to window
        mock_redis.zadd.assert_not_called()
    
    def test_check_when_blocked(self, limiter, mock_redis, basic_config):
        """Test when key is blocked."""
        key = "test_ip"
        mock_redis.exists.return_value = True  # Blocked
        
        result = limiter.check_rate_limit(key, basic_config)
        
        assert result is False
        # Should not check window or add request
        mock_redis.zcard.assert_not_called()
        mock_redis.zadd.assert_not_called()
    
    def test_blocking_when_limit_exceeded(self, limiter, mock_redis, blocking_config):
        """Test blocking behavior when limit is exceeded."""
        key = "test_ip"
        mock_redis.exists.return_value = False  # Not blocked
        mock_redis.zcard.return_value = 3  # At limit
        
        result = limiter.check_rate_limit(key, blocking_config)
        
        assert result is False
        # Should block the key
        mock_redis.setex.assert_called_once_with(
            f"{limiter.blocked_prefix}{key}", 
            blocking_config.block_seconds, 
            "blocked"
        )
    
    def test_reset_limits(self, limiter, mock_redis):
        """Test that reset_limits deletes the correct Redis keys."""
        key = "test_ip"
        limiter.reset_limits(key)
        
        # Should delete both window and blocked keys
        mock_redis.delete.assert_called_once_with(
            f"{limiter.prefix}{key}",
            f"{limiter.blocked_prefix}{key}"
        )
    
    def test_redis_error_handling(self, limiter, mock_redis, basic_config):
        """Test that Redis errors are caught and fail open."""
        key = "test_ip"
        mock_redis.zremrangebyscore.side_effect = redis.RedisError("Connection error")
        
        # Should fail open (allow request) when Redis errors
        result = limiter.check_rate_limit(key, basic_config)
        
        assert result is True


@patch("app.infrastructure.security.rate_limiter.get_settings")
class TestRateLimiterFactory:
    """Test suite for RateLimiterFactory."""
    
    def test_create_in_memory_rate_limiter(self, mock_get_settings):
        """Test creating an in-memory rate limiter."""
        # Configure to use in-memory
        mock_settings = MagicMock()
        mock_settings.USE_REDIS_RATE_LIMITER = False
        mock_get_settings.return_value = mock_settings
        
        limiter = RateLimiterFactory.create_rate_limiter()
        
        assert isinstance(limiter, InMemoryRateLimiter)
    
    @patch("app.infrastructure.security.rate_limiter.RedisRateLimiter")
    def test_create_redis_rate_limiter(self, mock_redis_limiter, mock_get_settings):
        """Test creating a Redis rate limiter."""
        # Configure to use Redis
        mock_settings = MagicMock()
        mock_settings.USE_REDIS_RATE_LIMITER = True
        mock_get_settings.return_value = mock_settings
        
        # Set up mock return value
        mock_instance = MagicMock(spec=RedisRateLimiter)
        mock_redis_limiter.return_value = mock_instance
        
        limiter = RateLimiterFactory.create_rate_limiter()
        
        assert limiter == mock_instance
        mock_redis_limiter.assert_called_once()
    
    @patch("app.infrastructure.security.rate_limiter.RedisRateLimiter")
    def test_fallback_when_redis_fails(self, mock_redis_limiter, mock_get_settings):
        """Test fallback to in-memory when Redis creation fails."""
        # Configure to use Redis
        mock_settings = MagicMock()
        mock_settings.USE_REDIS_RATE_LIMITER = True
        mock_get_settings.return_value = mock_settings
        
        # Make Redis creation fail
        mock_redis_limiter.side_effect = Exception("Redis connection error")
        
        limiter = RateLimiterFactory.create_rate_limiter()
        
        # Should fall back to in-memory
        assert isinstance(limiter, InMemoryRateLimiter)