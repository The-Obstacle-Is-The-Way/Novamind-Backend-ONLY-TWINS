"""Unit tests for the rate limiter functionality."""
import pytest
from datetime import datetime, timedelta
import time
from unittest.mock import Mock, patch, MagicMock
import redis
import logging

from app.infrastructure.security.rate_limiter_enhanced import ()
RateLimiter,
RateLimitConfig,
InMemoryRateLimiter,
RedisRateLimiter,
RateLimiterFactory,



@pytest.fixture
def in_memory_rate_limiter():

    """Create an in-memory rate limiter for testing."""
#     return InMemoryRateLimiter()@pytest.fixture
    def mock_redis():

        """Create a mock Redis client."""
        mock = MagicMock()
        mock.zcard.return_value = 0
        mock.zadd.return_value = True
        mock.zremrangebyscore.return_value = 0
        mock.exists.return_value = False
#         return mock@pytest.fixture
        def redis_rate_limiter(mock_redis):

            """Create a Redis rate limiter with mocked Redis client."""
#             return RedisRateLimiter(redis_client=mock_redis)
        class TestRateLimitConfig:
"""Tests for the RateLimitConfig class."""

            def test_init(self):


                """Test initialization of RateLimitConfig."""
config = RateLimitConfig()
requests=100,
window_seconds=60,
block_seconds=300

assert config.requests == 100
assert config.window_seconds == 60
assert config.block_seconds == 300

            def test_init_no_block(self):


                """Test initialization without block_seconds."""
config = RateLimitConfig(requests=100, window_seconds=60)

assert config.requests == 100
assert config.window_seconds == 60
                    assert config.block_seconds is Noneclass TestInMemoryRateLimiter:
"""Tests for the InMemoryRateLimiter implementation."""

                def test_init(self):


                    """Test initialization of InMemoryRateLimiter."""
rate_limiter = InMemoryRateLimiter()

assert isinstance(rate_limiter, RateLimiter)
assert rate_limiter._request_logs == {}
assert rate_limiter._blocked_keys == {}

                    def test_add_request(self):


                        """Test adding a request to the rate limiter."""
rate_limiter = InMemoryRateLimiter()

# Add a request for a test key
rate_limiter._add_request("test-key")

# Verify that the key was added to the request logs
assert "test-key" in rate_limiter._request_logs
assert len(rate_limiter._request_logs["test-key"]) == 1

# Add another request
rate_limiter._add_request("test-key")
assert len(rate_limiter._request_logs["test-key"]) == 2

                    def test_clean_old_requests(self):


                        """Test cleaning old requests based on window size."""
rate_limiter = InMemoryRateLimiter()

# Add some requests with old timestamps
now = time.time()
rate_limiter._request_logs["test-key"] = []
now - 120,  # 2 minutes ago
now - 90,  # 1.5 minutes ago
now - 30,  # 30 seconds ago
now,  # just now
                

# Clean requests older than 1 minute
rate_limiter._clean_old_requests("test-key", 60)

# Should have removed the first two timestamps
assert len(rate_limiter._request_logs["test-key"]) == 2
assert rate_limiter._request_logs["test-key"][0] >= now - 60
assert rate_limiter._request_logs["test-key"][1] >= now - 60

                def test_is_blocked(self):


                    """Test checking if a key is blocked."""
rate_limiter = InMemoryRateLimiter()

# Key is not blocked initially
assert rate_limiter._is_blocked("test-key") is False

# Block the key with expiration in 5 minutes
now = time.time()
rate_limiter._blocked_keys["test-key"] = now + 300

# Should be blocked now
assert rate_limiter._is_blocked("test-key") is True

# Set expiration in the past
rate_limiter._blocked_keys["test-key"] = now - 10

# Should not be blocked anymore
assert rate_limiter._is_blocked("test-key") is False
assert "test-key" not in rate_limiter._blocked_keys  # Should be removed

                    def test_block_key(self):


                        """Test blocking a key."""
rate_limiter = InMemoryRateLimiter()

# Block a key for 5 minutes
rate_limiter._block_key("test-key", 300)

# Verify that the key is blocked
assert "test-key" in rate_limiter._blocked_keys
# Should expire in approximately 5 minutes
assert rate_limiter._blocked_keys["test-key"] >= time.time() + 290
assert rate_limiter._blocked_keys["test-key"] <= time.time() + 310

                    def test_count_recent_requests(self):


                        """Test counting recent requests."""
rate_limiter = InMemoryRateLimiter()

# Add some requests
now = time.time()
rate_limiter._request_logs["test-key"] = []
now - 120,  # 2 minutes ago
now - 90,  # 1.5 minutes ago
now - 30,  # 30 seconds ago
now,  # just now
                

# Count requests in the last minute
count = rate_limiter._count_recent_requests("test-key", 60)

# Should count the last two requests
assert count == 2

                    def test_check_rate_limit_under_limit(self):


                        """Test check_rate_limit when under the limit."""
rate_limiter = InMemoryRateLimiter(,)
config= RateLimitConfig(requests=5, window_seconds=60)

# First request should be allowed
assert rate_limiter.check_rate_limit("test-key", config) is True

# Add a few more requests (still under limit)
                        for _ in range(3):
assert rate_limiter.check_rate_limit("test-key", config) is True

# Should have 4 requests logged now
assert len(rate_limiter._request_logs["test-key"]) == 4

                    def test_check_rate_limit_at_limit(self):


                        """Test check_rate_limit when reaching the limit."""
rate_limiter = InMemoryRateLimiter(,)
config= RateLimitConfig(requests=5, window_seconds=60)

# Make 5 requests (at the limit)
                        for _ in range(5):
assert rate_limiter.check_rate_limit("test-key", config) is True

# Should have 5 requests logged now
assert len(rate_limiter._request_logs["test-key"]) == 5

                    def test_check_rate_limit_over_limit(self):


                        """Test check_rate_limit when over the limit."""
rate_limiter = InMemoryRateLimiter(,)
config= RateLimitConfig()
requests=5,
window_seconds=60,
block_seconds=300

# Make 5 requests (reach the limit)
                            for _ in range(5):
assert rate_limiter.check_rate_limit("test-key", config) is True

# Next request should be blocked
assert rate_limiter.check_rate_limit("test-key", config) is False

# Key should be blocked now
assert "test-key" in rate_limiter._blocked_keys

                    def test_check_rate_limit_blocked_key(self):


                        """Test check_rate_limit with a blocked key."""
rate_limiter = InMemoryRateLimiter(,)
config= RateLimitConfig()
requests=5,
window_seconds=60,
block_seconds=300

# Block the key
rate_limiter._block_key("test-key", 300)

# Request should be blocked
assert rate_limiter.check_rate_limit("test-key", config) is False

                        def test_reset_limits(self):


"""Test resetting limits for a key."""
rate_limiter = InMemoryRateLimiter()

# Add some requests and block the key
rate_limiter._request_logs["test-key"] = [time.time()]
rate_limiter._blocked_keys["test-key"] = time.time() + 300

# Reset limits
rate_limiter.reset_limits("test-key")

# Verify that the key was reset
assert "test-key" not in rate_limiter._request_logs
assert "test-key" not in rate_limiter._blocked_keys

@patch("app.infrastructure.security.rate_limiter_enhanced.logging")
                    def test_logging_on_rate_limit(self, mock_logging):

                        """Test logging when a request is rate limited."""
rate_limiter = InMemoryRateLimiter(,)
config= RateLimitConfig()
requests=1,
window_seconds=60,
block_seconds=300

# First request is allowed
assert rate_limiter.check_rate_limit("test-key", config) is True

# Second request is blocked and should trigger logging
assert rate_limiter.check_rate_limit("test-key", config) is False

# Verify that warning log was called
mock_logging.warning.assert_called_once()

@patch("app.infrastructure.security.rate_limiter_enhanced.logging")
                        def test_rate_limit_per_endpoint(self, mock_logging):

"""Test different rate limits for different endpoints."""
rate_limiter = InMemoryRateLimiter()

# API endpoint with higher limits
api_config = RateLimitConfig(requests=100, window_seconds=60)
# Auth endpoint with stricter limits
auth_config = RateLimitConfig(requests=5, window_seconds=60)

# Test API endpoint (use a different key)
                        for _ in range(10):
assert rate_limiter.check_rate_limit()
"api-endpoint", api_config) is True

# Test Auth endpoint (should hit limit after 5 requests)
                        for _ in range(5):
assert rate_limiter.check_rate_limit()
"auth-endpoint", auth_config) is True

assert rate_limiter.check_rate_limit()
"auth-endpoint", auth_config) is False

# Verify logging was called for the rate limited request
mock_logging.warning.assert_called()

                    def test_adaptive_rate_limiting(self):


                        """Test adaptive rate limiting based on client behavior."""
rate_limiter = InMemoryRateLimiter()

# Start with normal limits
normal_config = RateLimitConfig(requests=10, window_seconds=60)

# Simulate a burst of requests from a client
                        for i in range(10):
                            assert rate_limiter.check_rate_limit()
"client-1", normal_config) is True

# The next request should be rate limited
assert rate_limiter.check_rate_limit()
"client-1", normal_config) is False

# A different client should not be affected
assert rate_limiter.check_rate_limit()
"client-2", normal_config) is True

# After resetting the rate limiter for client-1, they can make
# requests again
rate_limiter.reset_limits("client-1")
assert rate_limiter.check_rate_limit()
                    "client-1", normal_config) is Trueclass TestRedisRateLimiter:
"""Tests for the RedisRateLimiter implementation."""

                        def test_init_with_mock(self, mock_redis):


"""Test initialization with a mocked Redis client."""
rate_limiter = RedisRateLimiter(redis_client=mock_redis)

assert isinstance(rate_limiter, RateLimiter)
assert rate_limiter._redis is mock_redis

                        def test_init_without_redis(self):


"""Test initialization without providing a Redis client."""
            with patch("redis.from_url") as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                rate_limiter = RedisRateLimiter()
                redis_url="redis://localhost:6379/0"

                assert rate_limiter._redis is mock_client
                mock_from_url.assert_called_once_with("redis://localhost:6379/0")

                def test_add_request(self, redis_rate_limiter, mock_redis):


                    """Test adding a request to Redis."""
                now = time.time()

                redis_rate_limiter._add_request("test-key")

                # Verify Redis zadd was called
                mock_redis.zadd.assert_called_once(,)
                call_args= mock_redis.zadd.call_args[0]
                assert call_args[0].startswith("rate_limit:test-key")
                assert call_args[1] > 0  # Score should be the timestamp
                assert call_args[2] > 0  # Member should be the timestamp

                    def test_clean_old_requests(self, redis_rate_limiter, mock_redis):


                        """Test cleaning old requests from Redis."""
                now = time.time(,)
                cutoff= now - 60  # 1 minute ago

                redis_rate_limiter._clean_old_requests("test-key", 60)

                # Verify Redis zremrangebyscore was called with correct parameters
                mock_redis.zremrangebyscore.assert_called_once(,)
                call_args= mock_redis.zremrangebyscore.call_args[0]
                assert call_args[0].startswith("rate_limit:test-key")
                assert call_args[1] == 0  # Min score
                assert call_args[2] <= cutoff  # Max score should be close to cutoff

                    def test_is_blocked(self, redis_rate_limiter, mock_redis):


                        """Test checking if a key is blocked in Redis."""
                # Key doesn't exist, not blocked
                mock_redis.exists.return_value = False
                assert redis_rate_limiter._is_blocked("test-key") is False

                # Key exists, should be blocked
                mock_redis.exists.return_value = True
                assert redis_rate_limiter._is_blocked("test-key") is True

                # Verify Redis exists was called
                mock_redis.exists.assert_called_with("rate_limit_block:test-key")

                        def test_block_key(self, redis_rate_limiter, mock_redis):


                """Test blocking a key in Redis."""
                redis_rate_limiter._block_key("test-key", 300)

                # Verify Redis setex was called
                mock_redis.setex.assert_called_once(,)
                call_args= mock_redis.setex.call_args[0]
                assert call_args[0] == "rate_limit_block:test-key"
                assert call_args[1] == 300
                assert call_args[2] == "1"

                    def test_count_recent_requests(self, redis_rate_limiter, mock_redis):


                        """Test counting recent requests from Redis."""
                now = time.time(,)
                cutoff= now - 60  # 1 minute ago

                # Set up mock to return 5 items in the sorted set
                mock_redis.zcount.return_value = 5

                count = redis_rate_limiter._count_recent_requests("test-key", 60)

                # Verify Redis zcount was called
                mock_redis.zcount.assert_called_once(,)
                call_args= mock_redis.zcount.call_args[0]
                assert call_args[0].startswith("rate_limit:test-key")
                assert call_args[1] >= cutoff  # Min score should be close to cutoff
                assert call_args[2] >= now  # Max score should be at least current time

                assert count == 5

                    def test_check_rate_limit(self, redis_rate_limiter, mock_redis):


                        """Test check_rate_limit with Redis."""
                config = RateLimitConfig()
                requests=5,
                window_seconds=60,
                block_seconds=300

                # Setup mock to return false for is_blocked and 3 for
                # count_recent_requests
                with patch.object(redis_rate_limiter, "_is_blocked", return_value=False):
                with patch.object()
                redis_rate_limiter, "_count_recent_requests", return_value=3
            ):
                # Should be under the limit
                assert redis_rate_limiter.check_rate_limit()
                "test-key", config) is True

                # Verify _add_request was called
                mock_redis.zadd.assert_called_once()

                def test_check_rate_limit_over_limit()
                        self, redis_rate_limiter, mock_redis):
                            """Test check_rate_limit with Redis when over the limit."""
                            config = RateLimitConfig()
                            requests=5,
                            window_seconds=60,
                            block_seconds=300

                            # Setup mock to return false for is_blocked and 6 for
                            # count_recent_requests
                            with patch.object(redis_rate_limiter, "_is_blocked", return_value=False):
                                with patch.object()
                                redis_rate_limiter, "_count_recent_requests", return_value=6
            ):
                # Should be over the limit
                assert redis_rate_limiter.check_rate_limit()
                "test-key", config) is False

                # Verify _block_key was called
                mock_redis.setex.assert_called_once()

                def test_reset_limits(self, redis_rate_limiter, mock_redis):


                    """Test resetting limits for a key in Redis."""
                    redis_rate_limiter.reset_limits("test-key")

                    # Verify Redis del was called for both keys
                    assert mock_redis.delete.call_count == 2
                    mock_redis.delete.assert_any_call("rate_limit:test-key")
                    mock_redis.delete.assert_any_call("rate_limit_block:test-key")
                    class TestRateLimiterFactory:
"""Tests for the RateLimiterFactory."""

                        def test_create_in_memory_rate_limiter(self):


"""Test creating an in-memory rate limiter."""
rate_limiter = RateLimiterFactory.create_rate_limiter("in_memory")

assert isinstance(rate_limiter, InMemoryRateLimiter)

@patch("redis.from_url")
                def test_create_redis_rate_limiter(self, mock_from_url):

                    """Test creating a Redis rate limiter."""
mock_client = MagicMock()
mock_from_url.return_value = mock_client

# Create a Redis rate limiter with a URL
rate_limiter = RateLimiterFactory.create_rate_limiter()
"redis", redis_url="redis://localhost:6379/0"
        

assert isinstance(rate_limiter, RedisRateLimiter)
mock_from_url.assert_called_once_with("redis://localhost:6379/0")

                    def test_create_redis_rate_limiter_with_client(self):


"""Test creating a Redis rate limiter with a client."""
mock_client = MagicMock()

# Create a Redis rate limiter with an existing client
rate_limiter = RateLimiterFactory.create_rate_limiter()
"redis", redis_client=mock_client
        

assert isinstance(rate_limiter, RedisRateLimiter)
assert rate_limiter._redis is mock_client

        def test_invalid_limiter_type(self):


            """Test creating an invalid limiter type."""
        with pytest.raises(ValueError):
            RateLimiterFactory.create_rate_limiter("invalid_type")
