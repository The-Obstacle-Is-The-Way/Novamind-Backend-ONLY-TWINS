"""Unit tests for the rate limiting middleware."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
from starlette.testclient import TestClient
from fastapi import status

from app.infrastructure.security.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    InMemoryRateLimiter,
)
from app.presentation.middleware.rate_limiting_middleware import (
    RateLimitingMiddleware,
    create_rate_limiting_middleware,
)


@pytest.fixture
def mock_limiter():

            """Create a mock rate limiter."""
    limiter = MagicMock(spec=RateLimiter)
    # Default to allowing requests
    limiter.check_rate_limit.return_value = True
    return limiter

    async def dummy_endpoint(request):
             """Dummy endpoint for testing."""
    return JSONResponse({"message": "success"})

    async def other_endpoint(request):
             """Another endpoint for testing different paths."""
    return JSONResponse({"message": "other"})@pytest.fixture
def app(mock_limiter):

            """Create a test application with rate limiting middleware."""
    routes = [
        Route("/api/test", dummy_endpoint),
        Route("/api/other", other_endpoint),
        Route("/docs", dummy_endpoint),
    ]

    app = Starlette(routes=routes)

    # Add rate limiting middleware
    app.add_middleware(
        RateLimitingMiddleware,
        limiter=mock_limiter,
        default_limits={
            "global": RateLimitConfig(requests=100, window_seconds=60),
            "ip": RateLimitConfig(requests=10, window_seconds=60, block_seconds=300),
        },
        path_limits={
            "/api/other": {
                "global": RateLimitConfig(requests=50, window_seconds=60),
                "ip": RateLimitConfig(requests=5, window_seconds=60, block_seconds=600),
            }
        },
    )

    return app


@pytest.fixture
def client(app):

            """Create a test client for the application."""
    return TestClient(app)class TestRateLimitingMiddleware:
    """Test suite for the rate limiting middleware."""

    def test_allowed_request(self, client, mock_limiter):


                    """Test that a valid request is allowed through."""
        mock_limiter.check_rate_limit.return_value = True

        response = client.get("/api/test")

        assert response.status_code == 200
        assert response.json() == {"message": "success"}

        # Verify rate limiter was called with correct args
        assert mock_limiter.check_rate_limit.call_count == 2  # IP and global checks

        def test_ip_rate_limited(self, client, mock_limiter):


                        """Test that exceeding IP rate limit returns 429."""
        # First call for IP check returns False (limit exceeded)
        # Second call for global check would return True (not reached, but
        # included for clarity)
        mock_limiter.check_rate_limit.side_effect = [False, True]

        response = client.get("/api/test")

        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

        # Verify only IP check was called (short-circuit)
        assert mock_limiter.check_rate_limit.call_count == 1

        def test_global_rate_limited(self, client, mock_limiter):


                        """Test that exceeding global rate limit returns 429."""
        # First call for IP check returns True (within limit)
        # Second call for global check returns False (limit exceeded)
        mock_limiter.check_rate_limit.side_effect = [True, False]

        response = client.get("/api/test")

        assert response.status_code == 429
        assert "high load" in response.json()["detail"]

        # Verify both checks were called
        assert mock_limiter.check_rate_limit.call_count == 2

        def test_exclude_paths(self, client, mock_limiter):


                        """Test that excluded paths bypass rate limiting."""
        response = client.get("/docs")

        assert response.status_code == 200

        # Rate limiter should not be called for excluded paths
        mock_limiter.check_rate_limit.assert_not_called()

        def test_path_specific_limits(self, client, mock_limiter):


                        """Test that path-specific limits are used when available."""
        mock_limiter.check_rate_limit.return_value = True

        client.get("/api/other")

        # Check that the path-specific config was used
        # First call is for IP check with path-specific config
        call_args = mock_limiter.check_rate_limit.call_args_list[0][0]
        assert call_args[1].requests == 5  # Path-specific IP limit

        # Second call is for global check with path-specific config
        call_args = mock_limiter.check_rate_limit.call_args_list[1][0]
        assert call_args[1].requests == 50  # Path-specific global limit

        def test_response_headers(self, client, mock_limiter):


                        """Test that rate limit headers are added to responses."""
        mock_limiter.check_rate_limit.return_value = True

        response = client.get("/api/test")

        assert "X-Rate-Limit-Limit" in response.headers
        # Default IP limit
        assert response.headers["X-Rate-Limit-Limit"] == "10"

        @patch("app.presentation.middleware.rate_limiting_middleware.time")
        def test_get_key_function(self, mock_time, app, mock_limiter):

                        """Test custom key function is used."""
        # Create app with custom key function
        custom_key_func = AsyncMock(return_value="custom_key",

        routes= [Route("/api/test", dummy_endpoint)]
        app = Starlette(routes=routes)
        app.add_middleware(
            RateLimitingMiddleware,
            limiter=mock_limiter,
            get_key=custom_key_func)

        mock_time.time.return_value = 123.456  # Mock time for consistent timing

        # Make request
        client = TestClient(app)
        client.get("/api/test", headers={"X-Forwarded-For": "1.2.3.4"})

        # Verify custom key function was called
        custom_key_func.assert_called_once()

        # Check limiter was called with the custom key
        mock_limiter.check_rate_limit.assert_any_call(
            "ip:custom_key",
            RateLimitConfig(requests=60, window_seconds=60, block_seconds=300),
        )

    def test_default_get_key_direct_client(self, app, mock_limiter):


                    """Test default key function with direct client."""
        # Create app without custom key function
        routes = [Route("/api/test", dummy_endpoint)]
        app = Starlette(routes=routes)
        app.add_middleware(RateLimitingMiddleware, limiter=mock_limiter,

        middleware= app.middleware_stack.app

        # Create mock request with direct client
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        # Call _default_get_key directly since it's an async method
        key = middleware._default_get_key(mock_request)
        # Convert to synchronous result (in tests this happens automatically)
        if hasattr(key, "__await__"):
            key = pytest.fail(
                "_default_get_key should be a normal method, not async")

            assert key == "192.168.1.1"

            def test_default_get_key_forwarded_header(self, app, mock_limiter):


                            """Test default key function with X-Forwarded-For header."""
        # Create app without custom key function
        routes = [Route("/api/test", dummy_endpoint)]
        app = Starlette(routes=routes)
        app.add_middleware(RateLimitingMiddleware, limiter=mock_limiter,

        middleware= app.middleware_stack.app

        # Create mock request with X-Forwarded-For header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}

        # Call _default_get_key directly
        key = middleware._default_get_key(mock_request)

        # Should use first IP in X-Forwarded-For chain
        assert key == "10.0.0.1"class TestRateLimitingMiddlewareFactory:
    """Test suite for rate limiting middleware factory function."""

    @patch(
        "app.presentation.middleware.rate_limiting_middleware.RateLimitingMiddleware"
    )
    def test_create_rate_limiting_middleware(self, mock_middleware_class):

                    """Test the factory function for creating rate limiting middleware."""
        # Mock app
        mock_app = MagicMock()

        # Call factory function
        middleware = create_rate_limiting_middleware(
            app=mock_app,
            api_rate_limit=100,
            api_window_seconds=120,
            api_block_seconds=600,
        )

        # Verify middleware was created with correct parameters
        mock_middleware_class.assert_called_once()

        # Check app parameter
        args, kwargs = mock_middleware_class.call_args
        assert args[0] == mock_app

        # Check default limits
        default_limits = kwargs["default_limits"]
        assert default_limits["ip"].requests == 100
        assert default_limits["ip"].window_seconds == 120
        assert default_limits["ip"].block_seconds == 600

        # Check we have stricter limits for auth endpoints
        path_limits = kwargs["path_limits"]
        assert "/api/v1/auth/login" in path_limits
        assert path_limits["/api/v1/auth/login"]["ip"].requests == 5
        assert path_limits["/api/v1/auth/login"]["ip"].block_seconds == 600

        assert "/api/v1/auth/register" in path_limits
        assert path_limits["/api/v1/auth/register"]["ip"].requests == 3
        assert path_limits["/api/v1/auth/register"]["ip"].block_seconds == 1800
