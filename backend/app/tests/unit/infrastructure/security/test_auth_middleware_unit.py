# -*- coding: utf-8 -*-
"""Unit tests for Authentication Middleware functionality.

This module tests the authentication middleware which enforces secure
access to protected resources and routes in our HIPAA-compliant system.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.datastructures import Headers, State
from starlette.responses import JSONResponse
from starlette.types import Scope, Receive, Send, ASGIApp
from typing import Dict, Any, Awaitable, Callable

# Assuming these exceptions are correctly defined in the domain layer
from app.domain.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    MissingTokenError,
    AuthorizationError, # Assuming this exists or define locally if needed
)

# Assuming RoleBasedAccessControl is correctly defined/imported
# If not, define a mock or import the actual class
try:
    from app.infrastructure.security.rbac import RoleBasedAccessControl
except ImportError:
    class RoleBasedAccessControl: # Mock if not available
        def has_permission(self, roles: list, permission: str) -> bool:
            print(f"Mock RBAC check: Roles={roles}, Permission={permission}")
            # Default allow for basic tests, override in specific tests
            return True

# Import the middleware being tested
from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware as AuthMiddleware

# Mock TokenAuthorizationError if it's a custom exception used internally
# class TokenAuthorizationError(Exception):
#     """Mock TokenAuthorizationError for testing"""
#     pass

# Mock classes needed for tests if they are not imported elsewhere
# class JWTAuthBackend:
#     """Mock JWT authentication backend for testing."""
#     pass
# class CognitoAuthBackend:
#     """Mock Cognito authentication backend for testing."""
#     pass

@pytest.fixture
def auth_config():
    """Create a mock auth config for testing."""
    config = MagicMock()
    config.enabled = True
    config.auth_header_name = "Authorization"
    config.auth_scheme = "Bearer"
    config.exempt_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
    config.strict_scopes = True # Assuming this is a valid config option
    config.admin_role = "admin" # Assuming this is a valid config option
    # JWT specific configs might be needed if JWTAuthBackend is used directly
    # config.jwt_algorithm = "HS256"
    # config.jwt_secret_key = "test_secret_key"
    # config.jwt_expiry_minutes = 60
    return config

@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()

@pytest.fixture
def mock_jwt_service():
    """Create a mock JWT service for testing."""
    mock_service = MagicMock()
    # Configure mock validate_token method for successful validation by default
    mock_service.validate_token.return_value = MagicMock(
        is_valid=True,
        status="VALID",
        claims={
            "sub": "user123",
            "name": "Dr. Jane Smith",
            "roles": ["psychiatrist"],
            "scopes": ["read:patients", "write:clinical_notes", "prescribe:medications"]
        },
        token_type="access",
        error=None
    )
    return mock_service

@pytest.fixture
def auth_middleware(app, mock_jwt_service, auth_config):
    """Create an authentication middleware instance for testing."""
    middleware = AuthMiddleware(
        app=app,
        config=auth_config
    )
    middleware.jwt_service = mock_jwt_service # Inject mock service
    middleware.audit_logger = MagicMock()  # Mock the logger
    middleware.rbac = MagicMock(spec=RoleBasedAccessControl) # Mock RBAC
    middleware.rbac.has_permission.return_value = True # Default allow
    return middleware

# Using Starlette Headers directly, ensure tests provide dicts or valid Headers objects
# If custom MockHeaders is needed due to specific interactions, define it here.

@pytest.fixture
def authenticated_request():
    """Create a mock request with a valid authentication token."""
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = MagicMock()
    mock_request.url.path = "/api/patients"
    # Provide headers as a list of tuples for scope
    headers_list: list[tuple[bytes, bytes]] = [(b"authorization", b"Bearer valid.jwt.token")]
    mock_request.scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/patients",
        "headers": headers_list,
        "app": FastAPI(), # Add app to scope
        "state": {} # Initialize state
    }
    # Use Starlette Headers
    mock_request.headers = Headers(scope=mock_request.scope)
    return mock_request

@pytest.fixture
def unauthenticated_request():
    """Create a mock request without an authentication token."""
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = MagicMock()
    mock_request.url.path = "/api/patients"
    headers_list: list[tuple[bytes, bytes]] = []
    mock_request.scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/patients",
        "headers": headers_list,
        "app": FastAPI(), # Add app to scope
        "state": {} # Initialize state
    }
    mock_request.headers = Headers(scope=mock_request.scope)
    return mock_request


class TestAuthMiddleware:
    """Test suite for the authentication middleware."""

    @pytest.mark.asyncio
    async def test_valid_authentication(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test successful authentication with a valid token."""
        async def mock_call_next(request: Request) -> Response:
            """Mock the next call in the middleware chain."""
            assert hasattr(request.state, "user")
            assert request.state.user is not None
            assert request.state.user["sub"] == "user123"
            assert request.state.user["roles"] == ["psychiatrist"]
            assert hasattr(request.state, "authenticated")
            assert request.state.authenticated is True
            return JSONResponse(content={"status": "success"})

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next)

        assert response.status_code == 200
        mock_jwt_service.validate_token.assert_called_once_with("valid.jwt.token")
        auth_middleware.audit_logger.log_authentication.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_token(
        self,
        auth_middleware: AuthMiddleware,
        unauthenticated_request: Request
    ):
        """Test handling of a request without an authentication token."""
        async def mock_call_next(request: Request) -> Response:
            pytest.fail("Middleware should have blocked the request")
            # return JSONResponse(content={"status": "success"}) # pragma: no cover

        response = await auth_middleware.dispatch(unauthenticated_request, mock_call_next)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        content = json.loads(response.body)
        assert "Not authenticated" in content["detail"]
        auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_token(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test handling of a request with an invalid token."""
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=False, status="INVALID", error=InvalidTokenError("Token signature is invalid")
        )

        async def mock_call_next(request: Request) -> Response:
            pytest.fail("Middleware should have blocked the request")
            # return JSONResponse(content={"status": "success"}) # pragma: no cover

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        content = json.loads(response.body)
        assert "Invalid token" in content["detail"]
        auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_expired_token(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test handling of a request with an expired token."""
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=False, status="EXPIRED", error=TokenExpiredError("Token has expired")
        )

        async def mock_call_next(request: Request) -> Response:
            pytest.fail("Middleware should have blocked the request")
            # return JSONResponse(content={"status": "success"}) # pragma: no cover

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        content = json.loads(response.body)
        assert "Token has expired" in content["detail"]
        auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_exempt_path(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request # Use an authenticated request to show it's bypassed
    ):
        """Test that exempt paths bypass authentication."""
        # Modify the request to use an exempt path
        authenticated_request.scope["path"] = "/health"
        # Recreate headers based on updated scope if necessary, or ensure mock handles it
        authenticated_request.headers = Headers(scope=authenticated_request.scope)
        # Update the URL mock if path is used from there
        authenticated_request.url.path = "/health"


        async def mock_call_next(request: Request) -> Response:
            """Mock the next call, ensuring no auth state is set."""
            assert not hasattr(request.state, "user")
            # Optionally check for an 'auth_exempt' state if implemented
            # assert request.state.auth_exempt is True
            return JSONResponse(content={"status": "healthy"})

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next)

        assert response.status_code == 200
        assert json.loads(response.body) == {"status": "healthy"}
        # Ensure JWT service was NOT called for exempt paths
        auth_middleware.jwt_service.validate_token.assert_not_called()
        auth_middleware.audit_logger.log_authentication.assert_not_called()


    @pytest.mark.asyncio
    async def test_disabled_middleware(
        self,
        auth_config: MagicMock,
        app: FastAPI,
        authenticated_request: Request
    ):
        """Test behavior when middleware is disabled."""
        auth_config.enabled = False # Disable via config
        disabled_middleware = AuthMiddleware(app=app, config=auth_config)
        # No need to set jwt_service or logger if disabled check happens early

        async def mock_call_next(request: Request) -> Response:
            """Mock the next call, ensuring no auth state is set."""
            assert not hasattr(request.state, "user")
            return JSONResponse(content={"status": "success"})

        response = await disabled_middleware.dispatch(authenticated_request, mock_call_next)

        assert response.status_code == 200
        assert json.loads(response.body) == {"status": "success"}

    @pytest.mark.asyncio
    async def test_scope_validation_success(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test successful validation of token scopes against required scopes."""
        # Configure JWT service with specific scopes
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=True, status="VALID",
            claims={"sub": "user123", "roles": ["psychiatrist"], "scopes": ["read:patients"]},
            token_type="access", error=None
        )
        # Mock RBAC to allow if the permission is 'read:patients'
        auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: perm == "read:patients"

        # Set request path and method requiring 'read:patients'
        authenticated_request.scope["path"] = "/api/patients"
        authenticated_request.scope["method"] = "GET"
        authenticated_request.headers = Headers(scope=authenticated_request.scope)
        authenticated_request.url.path = "/api/patients"
        authenticated_request.method = "GET"


        async def mock_call_next_success(request: Request) -> Response:
            return JSONResponse(content={"status": "success"})

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next_success)
        assert response.status_code == 200
        auth_middleware.rbac.has_permission.assert_called_once_with(["psychiatrist"], "read:patients") # Verify RBAC check

    @pytest.mark.asyncio
    async def test_scope_validation_failure(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test failed validation when token scopes don't match required scopes."""
        # Configure JWT service with specific scopes
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=True, status="VALID",
            claims={"sub": "user123", "roles": ["psychiatrist"], "scopes": ["read:patients"]},
            token_type="access", error=None
        )
        # Mock RBAC to deny 'write:clinical_notes'
        auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: perm != "write:clinical_notes"

        # Set request path and method requiring 'write:clinical_notes'
        authenticated_request.scope["path"] = "/api/clinical-notes"
        authenticated_request.scope["method"] = "POST"
        authenticated_request.headers = Headers(scope=authenticated_request.scope)
        authenticated_request.url.path = "/api/clinical-notes"
        authenticated_request.method = "POST"

        async def mock_call_next_fail(request: Request) -> Response:
            pytest.fail("Middleware should have blocked the request")
            # return JSONResponse(content={"status": "success"}) # pragma: no cover

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next_fail)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        content = json.loads(response.body)
        assert "Forbidden" in content["detail"] # Or specific permission message
        auth_middleware.rbac.has_permission.assert_called_once_with(["psychiatrist"], "write:clinical_notes") # Verify RBAC check

    @pytest.mark.asyncio
    async def test_role_based_access_success(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test successful role-based access control."""
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=True, status="VALID",
            claims={"sub": "nurse456", "roles": ["nurse"], "scopes": ["read:vitals"]},
            token_type="access", error=None
        )
        # Mock RBAC: nurse can read vitals
        auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: "nurse" in roles and perm == "read:vitals"

        authenticated_request.scope["path"] = "/api/vitals"
        authenticated_request.scope["method"] = "GET"
        authenticated_request.headers = Headers(scope=authenticated_request.scope)
        authenticated_request.url.path = "/api/vitals"
        authenticated_request.method = "GET"

        async def mock_call_next_success(request: Request) -> Response:
            return JSONResponse(content={"status": "success"})

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next_success)
        assert response.status_code == 200
        auth_middleware.rbac.has_permission.assert_called_once_with(["nurse"], "read:vitals")

    @pytest.mark.asyncio
    async def test_role_based_access_failure(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock
    ):
        """Test failed role-based access control."""
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=True, status="VALID",
            claims={"sub": "nurse456", "roles": ["nurse"], "scopes": ["read:vitals"]},
            token_type="access", error=None
        )
        # Mock RBAC: nurse cannot prescribe
        auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: not ("nurse" in roles and perm == "prescribe:medications")

        authenticated_request.scope["path"] = "/api/prescriptions"
        authenticated_request.scope["method"] = "POST" # Requires prescribe permission
        authenticated_request.headers = Headers(scope=authenticated_request.scope)
        authenticated_request.url.path = "/api/prescriptions"
        authenticated_request.method = "POST"

        async def mock_call_next_fail(request: Request) -> Response:
            pytest.fail("Middleware should have blocked the request")
            # return JSONResponse(content={"status": "success"}) # pragma: no cover

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next_fail)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        auth_middleware.rbac.has_permission.assert_called_once_with(["nurse"], "prescribe:medications")

    @pytest.mark.asyncio
    async def test_admin_access_override(
        self,
        auth_middleware: AuthMiddleware,
        authenticated_request: Request,
        mock_jwt_service: MagicMock,
        auth_config: MagicMock
    ):
        """Test that admin role overrides specific permission requirements."""
        mock_jwt_service.validate_token.return_value = MagicMock(
            is_valid=True, status="VALID",
            claims={"sub": "admin123", "roles": [auth_config.admin_role], "scopes": []}, # Admin role, no specific scopes needed
            token_type="access", error=None
        )
        # RBAC should allow admin regardless of specific permission check result
        auth_middleware.rbac.has_permission.return_value = False # Mock RBAC denying permission

        # Use an endpoint that would normally require specific permission
        authenticated_request.scope["path"] = "/api/admin/settings"
        authenticated_request.scope["method"] = "PUT"
        authenticated_request.headers = Headers(scope=authenticated_request.scope)
        authenticated_request.url.path = "/api/admin/settings"
        authenticated_request.method = "PUT"

        async def mock_call_next_success(request: Request) -> Response:
            # Admin should have access
            return JSONResponse(content={"status": "success"})

        response = await auth_middleware.dispatch(authenticated_request, mock_call_next_success)
        assert response.status_code == 200
        # RBAC check might still happen, but the middleware logic should override based on admin role
        # auth_middleware.rbac.has_permission.assert_called_once_with([auth_config.admin_role], "update:settings") # Adjust permission name

    # Add more tests for edge cases, different header formats, specific error handling, etc.
