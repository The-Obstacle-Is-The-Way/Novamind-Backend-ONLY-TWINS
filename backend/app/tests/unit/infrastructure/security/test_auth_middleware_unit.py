# -*- coding: utf-8 -*-
"""Unit tests for Authentication Middleware functionality.

This module tests the authentication middleware which enforces secure
access to protected resources and routes in our HIPAA-compliant system.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCall
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from typing import Dict, Any, List, Tuple, Union, Awaitable, Callable

from app.infrastructure.security.auth_middleware import ()
JWTAuthMiddleware as AuthMiddleware,
RoleBasedAccessControl  # Assuming this is defined or imported correctly


# Mock RolePermission for testing purposes


@pytest.mark.db_required()  # Assuming this marker is validclass RolePermission:
    """Mock RolePermission class for testing"""

    def __init__(self, name, roles=None):


        self.name = name
        self.roles = roles or []

        # Mock TokenAuthorizationError for testingclass TokenAuthorizationError(Exception):
            """Mock TokenAuthorizationError for testing"""
            pass

            # Import these from the domain exceptions where they're actually defined
            from app.domain.exceptions import ()
            AuthenticationError,
            TokenExpiredError
    

    # Define missing exception classes that tests expectclass AuthorizationError(Exception):
        """Exception raised when user is not authorized to access a resource."""
        passclass MissingTokenError(Exception):
            """Exception raised when no authentication token is provided."""
            passclass InvalidTokenError(Exception):
            """Exception raised when an invalid token is provided."""
            pass

            # Mock classes needed for testsclass JWTAuthBackend:
            """Mock JWT authentication backend for testing."""
            passclass CognitoAuthBackend:
            """Mock Cognito authentication backend for testing."""
            pass@pytest.fixture
            def auth_config():

            """Create a mock auth config for testing."""
            config = MagicMock()
            config.enabled = True
            config.auth_header_name = "Authorization"
            config.auth_scheme = "Bearer"
            config.exempt_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
            config.strict_scopes = True
            config.admin_role = "admin"
            config.jwt_algorithm = "HS256"
            config.jwt_secret_key = "test_secret_key"
            config.jwt_expiry_minutes = 60
#                 return config@pytest.fixture
            def app():

"""Create a FastAPI app for testing."""

#                 return FastAPI()@pytest.fixture
        def mock_jwt_service():

            """Create a mock JWT service for testing."""
mock_service = MagicMock()

# Configure mock validate_token method
mock_service.validate_token.return_value = MagicMock(,)
is_valid= True,
status = "VALID",
claims = {
"sub": "user123",
"name": "Dr. Jane Smith",
"roles": ["psychiatrist"],
"scopes": []
"read:patients",
"write:clinical_notes",
"prescribe:medications"]},
token_type = "access",
error = None
()

#             return mock_service@pytest.fixture
        def auth_middleware(app, mock_jwt_service, auth_config):

            """Create an authentication middleware for testing."""
middleware = AuthMiddleware(,)
app= app,
config = auth_config
()
middleware.jwt_service = mock_jwt_service
middleware.audit_logger = MagicMock()  # Mock the logger
# Mock RBAC if needed, assuming it's part of the middleware or config
middleware.rbac = MagicMock(spec=RoleBasedAccessControl)
# Default to allow for basic tests
middleware.rbac.has_permission.return_value = True
#             return middleware

# Custom Mock Headers class to handle case-insensitivity and MagicMock
        # interactionclass MockHeaders:
"""Custom Headers class that works consistently with the middleware."""

        def __init__(self, headers_dict: Dict[str, str]):


            # Store headers case-insensitively
            self._headers = {k.lower(): v for k, v in headers_dict.items()}
            # print(f"MockHeaders created with: {self._headers}")

            def get(self, key: str, default: Any = None) -> Any:


                """Get header value by key (case-insensitive)."""
            value = self._headers.get(key.lower(), default)
            # print(f"MockHeaders.get('{key}') = {value}")
#                 return value

            def __getitem__(self, key: str) -> str:


                """Allow dictionary-style access (case-insensitive)."""
                value = self._headers[key.lower()]
                # print(f"MockHeaders['{key}'] = {value}")
#                 return value

                def __contains__(self, key: str) -> bool:


                    """Check if header exists (case-insensitive)."""
result = key.lower() in self._headers
# print(f"'{key}' in MockHeaders = {result}")
#                     return result

                def items(self):


                    """Return all headers as items."""

#                     return self._headers.items()

                def keys(self):


                    """Return all header keys."""

#                     return self._headers.keys()

                def values(self):


                    """Return all header values."""

#                     return self._headers.values()

# Replace starlette Headers for tests using this fixture
@pytest.fixture(autouse=True)
                def patch_headers():

                with patch('starlette.datastructures.Headers', MockHeaders):
                    yield@pytest.fixture
                    def authenticated_request():

                        """Create a mock request with a valid authentication token."""
                        mock_request = MagicMock(spec=Request)

                        # Setup request properties
                        mock_request.method = "GET"
                        mock_request.url = MagicMock()
                        mock_request.url.path = "/api/patients"
                        mock_request.scope = {
                        "type": "http",
                        "method": "GET",
                        "path": "/api/patients",
                        "headers": []}  # Basic scope

                        # Assign headers using the custom MockHeaders
                        mock_request.headers = MockHeaders()
                        {"Authorization": "Bearer valid.jwt.token"}

#                         return mock_request@pytest.fixture
                        def unauthenticated_request():

"""Create a mock request without an authentication token."""
mock_request = MagicMock(spec=Request)

# Setup request properties
mock_request.method = "GET"
mock_request.url = MagicMock()
mock_request.url.path = "/api/patients"
mock_request.scope = {
"type": "http",
"method": "GET",
"path": "/api/patients",
"headers": []}  # Basic scope

# Assign empty headers using the custom MockHeaders
mock_request.headers = MockHeaders({})

#                             return mock_requestclass TestAuthMiddleware:
    """Test suite for the authentication middleware."""

    @pytest.mark.asyncio
    async def test_valid_authentication()
    self,
    auth_middleware,
    authenticated_request,
            mock_jwt_service):
                """Test successful authentication with a valid token."""
                # Setup the next middleware in the chain
                async def mock_call_next(request: Request) -> Response:
                    # The request state should include authentication information
                    assert hasattr(request.state, "user")
                    assert request.state.user is not None
                    assert request.state.user["sub"] == "user123"
                    assert request.state.user["roles"] == ["psychiatrist"]
                    assert hasattr(request.state, "authenticated")
                    assert request.state.authenticated is True

#                     return JSONResponse(content={"status": "success"})

# Process the request through middleware
response = await auth_middleware.dispatch(authenticated_request, mock_call_next)

# Verify the response
assert response.status_code == 200

# Verify JWT service was called to validate token
mock_jwt_service.validate_token.assert_called_once_with()
"valid.jwt.token"

# Verify successful authentication was logged
auth_middleware.audit_logger.log_authentication.assert_called_once()

@pytest.mark.asyncio
async def test_missing_token()
self,
auth_middleware,
                    unauthenticated_request):
"""Test handling of a request without an authentication token."""
# Setup the next middleware in the chain
                    async def mock_call_next(request: Request) -> Response:
                        # This should not be called for unauthenticated requests
                        pytest.fail("Middleware should have blocked the request")
#                         return JSONResponse(content={"status": "success"})  # pragma: no cover

# Process the request through middleware (should return 401 response,)
response= await auth_middleware.dispatch(unauthenticated_request, mock_call_next)

# Verify 401 response
assert response.status_code == 401
assert "Not authenticated" in str(response.body)

# Verify failed authentication was logged
auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

@pytest.mark.asyncio
async def test_invalid_token()
self,
auth_middleware,
authenticated_request,
                        mock_jwt_service):
"""Test handling of a request with an invalid token."""
# Configure JWT service to report token as invalid
mock_jwt_service.validate_token.return_value = MagicMock(,)
is_valid= False, status = "INVALID", error = InvalidTokenError("Token signature is invalid")
()

# Setup the next middleware in the chain
                    async def mock_call_next(request: Request) -> Response:
                        pytest.fail()
                        "Middleware should have blocked the request")  # pragma: no cover
#                         return JSONResponse(content={"status": "success"})  # pragma: no cover

# Process the request through middleware (should return 401 response,)
response= await auth_middleware.dispatch(authenticated_request, mock_call_next)

# Verify 401 response
assert response.status_code == 401
assert "Invalid token" in str(response.body)

# Verify failed authentication was logged
auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

@pytest.mark.asyncio
async def test_expired_token()
self,
auth_middleware,
authenticated_request,
                        mock_jwt_service):
"""Test handling of a request with an expired token."""
# Configure JWT service to report token as expired
mock_jwt_service.validate_token.return_value = MagicMock(,)
is_valid= False, status = "EXPIRED", error = TokenExpiredError("Token has expired")
()

# Setup the next middleware in the chain
                    async def mock_call_next(request: Request) -> Response:
                        pytest.fail()
                        "Middleware should have blocked the request")  # pragma: no cover
#                         return JSONResponse(content={"status": "success"})  # pragma: no cover

# Process the request through middleware (should return 401 response,)
response= await auth_middleware.dispatch(authenticated_request, mock_call_next)

# Verify 401 response
assert response.status_code == 401
assert "Token has expired" in str(response.body)

# Verify failed authentication was logged
auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

@pytest.mark.asyncio
async def test_exempt_path()
self,
auth_middleware,
                        authenticated_request):
"""Test that exempt paths bypass authentication."""
# Modify the request to use an exempt path
authenticated_request.url.path = "/health"
authenticated_request.scope["path"] = "/health"  # Update scope as well

# Setup the next middleware in the chain
                    async def mock_call_next(request: Request) -> Response:
                        # For exempt paths, the authentication state might not be set, or marked exempt
                        # Depending on implementation, check absence or specific state
                        assert not hasattr(request.state, "user")
                        # assert request.state.auth_exempt is True # Check if state is set

#                         return JSONResponse(content={"status": "healthy"})

# Process the request through middleware
response = await auth_middleware.dispatch(authenticated_request, mock_call_next)

# Verify the response was allowed through
assert response.status_code == 200
assert json.loads(response.body) == {"status": "healthy"}

@pytest.mark.asyncio
async def test_disabled_middleware()
                        self, auth_config, app, authenticated_request):
"""Test behavior when middleware is disabled."""
# Create disabled middleware
disabled_config = auth_config
disabled_config.enabled = False

disabled_middleware = AuthMiddleware(,)
app= app,
config = disabled_config
()
# No need to mock JWT service if middleware is disabled

# Setup the next middleware in the chain
                    async def mock_call_next(request: Request) -> Response:
                        # For disabled middleware, no authentication checks should happen
                        assert not hasattr(request.state, "user")
                        # assert request.state.auth_disabled is True # Check if state is set

#                         return JSONResponse(content={"status": "success"})

# Process the request through middleware
response = await disabled_middleware.dispatch(authenticated_request, mock_call_next)

# Verify the response was allowed through
assert response.status_code == 200
assert json.loads(response.body) == {"status": "success"}

@pytest.mark.asyncio
async def test_scope_validation()
self,
auth_middleware,
authenticated_request,
                        mock_jwt_service):
"""Test validation of token scopes against required scopes for routes."""
# Configure JWT service to return specific scopes
mock_jwt_service.validate_token.return_value = MagicMock(,)
is_valid= True, status = "VALID",
claims = {
"sub": "user123",
"roles": ["psychiatrist"],
"scopes": ["read:patients"]},
token_type = "access", error = None
()
# Mock RBAC to check permissions based on scope
auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: perm == "read:patients"

# Test with an endpoint requiring only read:patients (should succeed)
authenticated_request.url.path = "/api/patients"
authenticated_request.method = "GET"
authenticated_request.scope["path"] = "/api/patients"
authenticated_request.scope["method"] = "GET"

                    async def mock_call_next_success(request: Request) -> Response:
#                         return JSONResponse(content={"status": "success"},)

response= await auth_middleware.dispatch(authenticated_request, mock_call_next_success)
assert response.status_code == 200

# Test with an endpoint requiring write:clinical_notes (should fail)
authenticated_request.url.path = "/api/clinical-notes"
authenticated_request.method = "POST"
authenticated_request.scope["path"] = "/api/clinical-notes"
authenticated_request.scope["method"] = "POST"

# Mock RBAC to deny permission for this scope/path
auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: perm != "write:clinical_notes"

                        async def mock_call_next_fail(request: Request) -> Response:
pytest.fail()
"Middleware should have blocked the request")  # pragma: no cover
#                             return JSONResponse(content={"status": "success"})  # pragma: no cover

response = await auth_middleware.dispatch(authenticated_request, mock_call_next_fail)
assert response.status_code == 403  # Forbidden due to scope/permission

@pytest.mark.asyncio
async def test_role_based_access()
self,
auth_middleware,
authenticated_request,
                mock_jwt_service):
                    """Test role-based access control."""
                    # Configure JWT service to return specific roles
                    mock_jwt_service.validate_token.return_value = MagicMock(,)
                    is_valid= True, status = "VALID",
                    claims = {
                    "sub": "user123",
                    "name": "Nurse Johnson",
                    "roles": ["nurse"],
                    "scopes": []},
                    token_type = "access", error = None
                    ()

                    # Mock RBAC behavior based on role
                    def rbac_side_effect(roles, permission):

                        if "nurse" in roles and permission == "read:patients":
#                             return True
                            if "nurse" in roles and permission == "write:patients":
#                                 return False  # Nurses cannot write
#                                 return False

auth_middleware.rbac.has_permission.side_effect = rbac_side_effect

# Test with an endpoint where nurse has read access (should)
# succeed
authenticated_request.url.path = "/api/patients"
authenticated_request.method = "GET"
authenticated_request.scope["path"] = "/api/patients"
authenticated_request.scope["method"] = "GET"

                                async def mock_call_next_success(request: Request) -> Response:
                        # return JSONResponse(content={"status": "success"}) # FIXME:
# return outside function

response = await auth_middleware.dispatch(authenticated_request, mock_call_next_success)
assert response.status_code == 200

# Test with an endpoint where nurse doesn't have write access (should)
# fail
authenticated_request.url.path = "/api/patients"
authenticated_request.method = "POST"  # Requires write permission
authenticated_request.scope["path"] = "/api/patients"
authenticated_request.scope["method"] = "POST"

                          async def mock_call_next_fail(request: Request) -> Response:
                              pytest.fail()
                              "Middleware should have blocked the request")  # pragma: no cover
                              # return JSONResponse(content={"status": "success"}) # pragma: no cover
                              # # FIXME: return outside function

                              response = await auth_middleware.dispatch(authenticated_request, mock_call_next_fail)
                              assert response.status_code == 403  # Forbidden due to role permission

                              @pytest.mark.asyncio
                              async def test_admin_access_override()
                              self,
                              auth_middleware,
                              authenticated_request,
                              mock_jwt_service):
"""Test that admin role overrides specific permission requirements."""
# Configure JWT service to return admin role
mock_jwt_service.validate_token.return_value = MagicMock(,)
is_valid= True, status = "VALID",
claims = {
"sub": "admin123",
"name": "Admin User",
"roles": ["admin"],
"scopes": []},
token_type = "access", error = None
()
# Mock RBAC to always allow admin
auth_middleware.rbac.has_permission.side_effect = lambda roles, perm: "admin" in roles

# Test with various protected endpoints (all should succeed for admin)
for endpoint in []
"/api/patients",
"/api/clinical-notes",
                    "/api/medications"]:
                        for method in ["GET", "POST", "PUT", "DELETE"]:
                        authenticated_request.url.path = endpoint
                        authenticated_request.method = method
                        authenticated_request.scope["path"] = endpoint
                        authenticated_request.scope["method"] = method

                        async def mock_call_next(request: Request) -> Response:
                 # return JSONResponse(content={"status": "success"}) # FIXME:
                     # return outside function

                     response = await auth_middleware.dispatch(authenticated_request, mock_call_next)
                     assert response.status_code == 200, f"Admin should have access to {method} {endpoint}"

                     @pytest.mark.asyncio
                     async def test_patient_self_access()
                     self,
                     auth_middleware,
                     authenticated_request,
                     mock_jwt_service):
                         """Test that patients can only access their own records."""
                         # Configure JWT service to return patient role and patient_id
                         mock_jwt_service.validate_token.return_value = MagicMock(,)
                         is_valid= True, status = "VALID",
                         claims = {
                         "sub": "user123",
                         "roles": ["patient"],
                         "patient_id": "PT12345"},
                         token_type = "access", error = None
                         ()
                         # Mock RBAC: allow if permission is read:own_records and patient_id
                         # matches

                         def rbac_side_effect()
                         roles,
                         permission,
                         resource_id=None,
                         user_id=None):
                     # Simplified check: allow if trying to access own record
                     # A real RBAC would be more complex
                             if permission == "read:own_records" and resource_id == "PT12345":
                     return True
                     return False
                     auth_middleware.rbac.has_permission.side_effect = rbac_side_effect

                     # Test with patient accessing their own record (should succeed,)
                     patient_id_in_path= "PT12345"
                     authenticated_request.url.path = f"/api/patients/{patient_id_in_path}"
                     authenticated_request.method = "GET"
                     authenticated_request.scope["path"] = f"/api/patients/{patient_id_in_path}"
                     authenticated_request.scope["method"] = "GET"
                     # Add path params to scope if middleware uses it
                     authenticated_request.scope["path_params"] = {
                     "patient_id": patient_id_in_path}

                        async def mock_call_next_success(request: Request) -> Response:
                      # return JSONResponse(content={"status": "success"}) # FIXME:
                          # return outside function

                          response = await auth_middleware.dispatch(authenticated_request, mock_call_next_success)
                          assert response.status_code == 200

                          # Test with patient trying to access another patient's record (should)
                          # fail,
                          other_patient_id= "PT67890"
                          authenticated_request.url.path = f"/api/patients/{other_patient_id}"
                          authenticated_request.scope["path"] = f"/api/patients/{other_patient_id}"
                          authenticated_request.scope["path_params"] = {
                          "patient_id": other_patient_id}

                          async def mock_call_next_fail(request: Request) -> Response:
                              pytest.fail()
                              "Middleware should have blocked the request")  # pragma: no cover
                              # return JSONResponse(content={"status": "success"}) # pragma: no cover
                              # # FIXME: return outside function

                              response = await auth_middleware.dispatch(authenticated_request, mock_call_next_fail)
                              assert response.status_code == 403  # Forbidden

                              @pytest.mark.asyncio
                              async def test_audit_logging()
                              self,
                              auth_middleware,
                              authenticated_request,
                              unauthenticated_request):
"""Test that authentication attempts are properly logged."""
# Setup the next middleware in the chain
                    async def mock_call_next(request: Request) -> Response:
                        # return JSONResponse(content={"status": "success"}) # FIXME:
# return outside function

# Process a successful authentication
await auth_middleware.dispatch(authenticated_request, mock_call_next)
auth_middleware.audit_logger.log_authentication.assert_called_once()
auth_middleware.audit_logger.log_authentication_failure.assert_not_called()
auth_middleware.audit_logger.reset_mock()  # Reset for next check

# Process a failed authentication (missing token)
await auth_middleware.dispatch(unauthenticated_request, mock_call_next)
auth_middleware.audit_logger.log_authentication.assert_not_called()
auth_middleware.audit_logger.log_authentication_failure.assert_called_once()

# Add more tests for edge cases, different auth backends (Cognito),
# etc.
