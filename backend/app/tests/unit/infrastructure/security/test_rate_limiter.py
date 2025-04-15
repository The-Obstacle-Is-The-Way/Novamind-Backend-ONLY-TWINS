"""Unit tests for the rate limiter functionality."""
import pytest
from datetime import datetime, timedelta, timezone # Added timezone
import time
from unittest.mock import Mock, patch, MagicMock, call, AsyncMock # Added call and AsyncMock
import redis # Import redis for mocking RedisRateLimiter if needed
import logging
import os # Import os if needed for env vars, though not used in this version
import asyncio

# Updated import path
# from app.infrastructure.security.rate_limiter_enhanced import (
from app.infrastructure.security.rate_limiting.rate_limiter import (
    RateLimiter,
    RateLimitExceeded,
    RateLimitConfig,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimiterFactory,
    DistributedRateLimiter,
    RateLimitType,
)
from app.infrastructure.cache.redis_cache import RedisCache # Import for mocking

# Define UTC if not imported elsewhere (Python 3.11+)
try:
    from datetime import UTC # Use standard UTC if available
except ImportError:
    UTC = timezone.utc # Fallback for older Python versions


@pytest.fixture
def in_memory_rate_limiter():
    """Create an in-memory rate limiter for testing."""
    return InMemoryRateLimiter()

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock(spec=redis.Redis) # Use spec for better mocking
    # Set default return values for common methods used by RedisRateLimiter
    mock.zcard.return_value = 0
    mock.zadd.return_value = 1 # Typically returns number of elements added
    mock.zremrangebyscore.return_value = 0 # Number of elements removed
    mock.exists.return_value = 0 # Redis returns 0 if key doesn't exist
    mock.setex.return_value = True
    mock.delete.return_value = 1 # Number of keys deleted
    mock.zcount.return_value = 0
    return mock

@pytest.fixture
def redis_rate_limiter(mock_redis):
    """Create a Redis rate limiter with mocked Redis client."""
    return RedisRateLimiter(redis_client=mock_redis)


class TestRateLimitConfig:
    """Tests for the RateLimitConfig class."""

    def test_init(self):
        """Test initialization of RateLimitConfig."""
        config = RateLimitConfig(
            requests=100,
            window_seconds=60,
            block_seconds=300
        )
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

    def test_init(self):
        """Test initialization of InMemoryRateLimiter."""
        rate_limiter = InMemoryRateLimiter()
        assert isinstance(rate_limiter, RateLimiter)
        assert rate_limiter._request_logs == {}
        assert rate_limiter._blocked_keys == {}

    def test_add_request(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test adding a request to the rate limiter."""
        key = "test-key-add"
        in_memory_rate_limiter._add_request(key)
        assert key in in_memory_rate_limiter._request_logs
        assert len(in_memory_rate_limiter._request_logs[key]) == 1
        in_memory_rate_limiter._add_request(key)
        assert len(in_memory_rate_limiter._request_logs[key]) == 2

    def test_clean_old_requests(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test cleaning old requests based on window size."""
        key = "test-key-clean"
        now = time.time()
        in_memory_rate_limiter._request_logs[key] = [
            now - 120, now - 90, now - 30, now,
        ]
        in_memory_rate_limiter._clean_old_requests(key, 60)
        assert len(in_memory_rate_limiter._request_logs[key]) == 2
        assert in_memory_rate_limiter._request_logs[key][0] >= now - 60
        assert in_memory_rate_limiter._request_logs[key][1] >= now - 60

    def test_is_blocked(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test checking if a key is blocked."""
        key = "test-key-block-check"
        assert in_memory_rate_limiter._is_blocked(key) is False
        now = time.time()
        in_memory_rate_limiter._blocked_keys[key] = now + 300
        assert in_memory_rate_limiter._is_blocked(key) is True
        in_memory_rate_limiter._blocked_keys[key] = now - 10
        assert in_memory_rate_limiter._is_blocked(key) is False
        assert key not in in_memory_rate_limiter._blocked_keys

    def test_block_key(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test blocking a key."""
        key = "test-key-block-action"
        block_duration = 300
        now = time.time()
        in_memory_rate_limiter._block_key(key, block_duration)
        assert key in in_memory_rate_limiter._blocked_keys
        assert now + block_duration - 10 < in_memory_rate_limiter._blocked_keys[key] < now + block_duration + 10

    def test_count_recent_requests(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test counting recent requests."""
        key = "test-key-count"
        now = time.time()
        in_memory_rate_limiter._request_logs[key] = [
            now - 120, now - 90, now - 30, now
        ]
        count = in_memory_rate_limiter._count_recent_requests(key, 60)
        assert count == 2

    def test_check_rate_limit_under_limit(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test check_rate_limit when under the limit."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        key = "test-key-under"
        for _ in range(4):
            assert in_memory_rate_limiter.check_rate_limit(key, config) is True
        assert len(in_memory_rate_limiter._request_logs[key]) == 4

    def test_check_rate_limit_at_limit(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test check_rate_limit when reaching the limit."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        key = "test-key-at"
        for _ in range(5):
            assert in_memory_rate_limiter.check_rate_limit(key, config) is True
        assert len(in_memory_rate_limiter._request_logs[key]) == 5

    def test_check_rate_limit_over_limit(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test check_rate_limit when over the limit."""
        config = RateLimitConfig(requests=5, window_seconds=60, block_seconds=300)
        key = "test-key-over"
        for _ in range(5):
            assert in_memory_rate_limiter.check_rate_limit(key, config) is True
        assert in_memory_rate_limiter.check_rate_limit(key, config) is False
        assert key in in_memory_rate_limiter._blocked_keys

    def test_check_rate_limit_blocked_key(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test check_rate_limit with a blocked key."""
        config = RateLimitConfig(requests=5, window_seconds=60, block_seconds=300)
        key = "test-key-blocked"
        in_memory_rate_limiter._block_key(key, 300)
        assert in_memory_rate_limiter.check_rate_limit(key, config) is False

    def test_reset_limits(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test resetting limits for a key."""
        key = "test-key-reset"
        in_memory_rate_limiter._request_logs[key] = [time.time()]
        in_memory_rate_limiter._blocked_keys[key] = time.time() + 300
        in_memory_rate_limiter.reset_limits(key)
        assert key not in in_memory_rate_limiter._request_logs
        assert key not in in_memory_rate_limiter._blocked_keys

    @patch("app.infrastructure.security.rate_limiter_enhanced.logging")
    def test_logging_on_rate_limit(self, mock_logging: MagicMock, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test logging when a request is rate limited."""
        config = RateLimitConfig(requests=1, window_seconds=60, block_seconds=300)
        key = "test-key-log"
        assert in_memory_rate_limiter.check_rate_limit(key, config) is True
        assert in_memory_rate_limiter.check_rate_limit(key, config) is False
        mock_logging.warning.assert_called_once()
        log_message = mock_logging.warning.call_args[0][0]
        assert key in log_message
        assert "rate limited" in log_message.lower()

    def test_rate_limit_per_endpoint(self, in_memory_rate_limiter: InMemoryRateLimiter):
        """Test different rate limits for different endpoints (keys)."""
        api_config = RateLimitConfig(requests=10, window_seconds=60)
        auth_config = RateLimitConfig(requests=3, window_seconds=60)
        api_key = "api-endpoint"
        auth_key = "auth-endpoint"

        for _ in range(10):
            assert in_memory_rate_limiter.check_rate_limit(api_key, api_config) is True
        assert in_memory_rate_limiter.check_rate_limit(api_key, api_config) is False

        for _ in range(3):
            assert in_memory_rate_limiter.check_rate_limit(auth_key, auth_config) is True
        assert in_memory_rate_limiter.check_rate_limit(auth_key, auth_config) is False


class TestRedisRateLimiter:
    """Tests for the RedisRateLimiter implementation."""

    def test_init_with_mock(self, mock_redis: MagicMock):
        """Test initialization with a mocked Redis client."""
        rate_limiter = RedisRateLimiter(redis_client=mock_redis)
        assert isinstance(rate_limiter, RateLimiter)
        assert rate_limiter._redis is mock_redis

    def test_init_without_redis(self):
        """Test initialization without providing a Redis client (creates its own)."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client
            rate_limiter = RedisRateLimiter(redis_url="redis://localhost:6379/0")
            assert rate_limiter._redis is mock_client
            mock_from_url.assert_called_once_with("redis://localhost:6379/0")

    def test_add_request(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test adding a request to Redis."""
        key = "test-key-redis-add"
        with patch('time.time', return_value=1000.0):
             redis_rate_limiter._add_request(key)
             mock_redis.zadd.assert_called_once()
             call_args = mock_redis.zadd.call_args
             assert call_args[0][0] == f"rate_limit:{key}"
             assert 1000.0 in call_args[1]['mapping']
             assert 1000.0 in call_args[1]['mapping'].values()


    def test_clean_old_requests(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test cleaning old requests from Redis."""
        key = "test-key-redis-clean"
        window_seconds = 60
        with patch('time.time', return_value=1000.0):
            cutoff = 1000.0 - window_seconds
            redis_rate_limiter._clean_old_requests(key, window_seconds)
            mock_redis.zremrangebyscore.assert_called_once_with(
                f"rate_limit:{key}", 0, cutoff
            )

    def test_is_blocked(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test checking if a key is blocked in Redis."""
        key = "test-key-redis-isblocked"
        block_key_name = f"rate_limit_block:{key}"
        mock_redis.exists.return_value = 0
        assert redis_rate_limiter._is_blocked(key) is False
        mock_redis.exists.assert_called_with(block_key_name)
        mock_redis.exists.return_value = 1
        assert redis_rate_limiter._is_blocked(key) is True
        mock_redis.exists.assert_called_with(block_key_name)

    def test_block_key(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test blocking a key in Redis."""
        key = "test-key-redis-block"
        block_duration = 300
        redis_rate_limiter._block_key(key, block_duration)
        mock_redis.setex.assert_called_once_with(
            f"rate_limit_block:{key}", block_duration, "1"
        )

    def test_count_recent_requests(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test counting recent requests from Redis."""
        key = "test-key-redis-count"
        window_seconds = 60
        with patch('time.time', return_value=1000.0):
            cutoff = 1000.0 - window_seconds
            mock_redis.zcount.return_value = 5
            count = redis_rate_limiter._count_recent_requests(key, window_seconds)
            mock_redis.zcount.assert_called_once()
            call_args = mock_redis.zcount.call_args[0]
            assert call_args[0] == f"rate_limit:{key}"
            assert cutoff - 1 < call_args[1] < cutoff + 1
            assert call_args[2] == float('inf')
            assert count == 5

    def test_check_rate_limit(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test check_rate_limit with Redis (under limit)."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        key = "test-key-redis-check"
        mock_redis.exists.return_value = 0
        mock_redis.zcount.return_value = 3
        assert redis_rate_limiter.check_rate_limit(key, config) is True
        mock_redis.zadd.assert_called_once()

    def test_check_rate_limit_over_limit(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test check_rate_limit with Redis when over the limit."""
        config = RateLimitConfig(requests=5, window_seconds=60, block_seconds=300)
        key = "test-key-redis-over"
        mock_redis.exists.return_value = 0
        mock_redis.zcount.return_value = 6
        assert redis_rate_limiter.check_rate_limit(key, config) is False
        mock_redis.setex.assert_called_once()

    def test_reset_limits(self, redis_rate_limiter: RedisRateLimiter, mock_redis: MagicMock):
        """Test resetting limits for a key in Redis."""
        key = "test-key-redis-reset"
        redis_rate_limiter.reset_limits(key)
        expected_calls = [
            call(f"rate_limit:{key}"),
            call(f"rate_limit_block:{key}")
        ]
        mock_redis.delete.assert_has_calls(expected_calls, any_order=True)
        assert mock_redis.delete.call_count == 2


class TestRateLimiterFactory:
    """Tests for the RateLimiterFactory."""

    def test_create_in_memory_rate_limiter(self):
        """Test creating an in-memory rate limiter."""
        rate_limiter = RateLimiterFactory.create_rate_limiter("in_memory")
        assert isinstance(rate_limiter, InMemoryRateLimiter)

    @patch("redis.from_url")
    def test_create_redis_rate_limiter(self, mock_from_url: MagicMock):
        """Test creating a Redis rate limiter."""
        mock_redis_client = MagicMock()
        mock_from_url.return_value = mock_redis_client
        rate_limiter = RateLimiterFactory.create_rate_limiter(
            "redis", redis_url="redis://localhost"
        )
        assert isinstance(rate_limiter, RedisRateLimiter)
        assert rate_limiter._redis is mock_redis_client
        mock_from_url.assert_called_once_with("redis://localhost")

    def test_invalid_limiter_type(self):
        """Test creating an invalid limiter type."""
        with pytest.raises(ValueError, match="Unsupported rate limiter type"):
            RateLimiterFactory.create_rate_limiter("invalid_type")

# Mock Request object
class MockRequest:
    def __init__(self, client_host="127.0.0.1", headers=None, api_key=None):
        self.client = MagicMock()
        self.client.host = client_host
        _headers = headers if headers is not None else {}
        if api_key:
            _headers["X-API-Key"] = api_key
        self.headers = _headers
