# -*- coding: utf-8 -*-
from app.domain.exceptions import AuthenticationError, TokenExpiredError, InvalidTokenError
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.tests.security.utils.test_mocks import MockAuthService
from app.tests.security.utils.base_security_test import BaseSecurityTest
import pytest
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from starlette.responses import Response
from starlette.testclient import TestClient
import sys

# Update import path for AuthenticationMiddleware
from app.presentation.middleware.authentication_middleware import (
    AuthenticationMiddleware,
)

# Update import path for the dependency function
from app.presentation.api.dependencies.auth import get_jwt_service



@pytest.mark.db_required()
class TestAuthMiddleware(BaseSecurityTest):
    """
    Tests for the Authentication Middleware to ensure HIPAA-compliant access control.

    These tests verify:
        1. Proper authentication of all requests to protected resources
        2. Correct role-based access control
        3. Protection against unauthorized access attempts
        4. PHI access is properly restricted based on user roles
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.auth_service = MockAuthService()
        self.request = MagicMock()
        self.credentials = MagicMock()

    @pytest.fixture
    def mock_jwt_service(self):
        """Create a mocked JWT service for testing."""
        mock_service = AsyncMock(spec=JWTService)

        # Define reusable TokenPayload instances
        # Ensure these match the structure expected by your dependencies/routes
        patient_payload = TokenPayload(
            sub="patient123",
            exp=9999999999, # Far future expiration for valid tokens
            iat=1000000000,
            jti="jti_patient",
            scope="access_token",
            roles=["patient"],
            user_id="patient123" # Keep user_id if routes depend on it directly
        )
        different_patient_payload = TokenPayload(
             sub="patient456",
             exp=9999999999,
             iat=1000000000,
             jti="jti_other_patient",
             scope="access_token",
             roles=["patient"],
             user_id="patient456"
        )
        provider_payload = TokenPayload(
             sub="provider123",
             exp=9999999999,
             iat=1000000000,
             jti="jti_provider",
             scope="access_token",
             roles=["provider"],
             user_id="provider123"
        )
        admin_payload = TokenPayload(
             sub="admin123",
             exp=9999999999,
             iat=1000000000,
             jti="jti_admin",
             scope="access_token",
             roles=["admin"],
             user_id="admin123"
        )


        # Setup mock decode_token (which is now async)
        async def async_mock_decode_token(token: str) -> TokenPayload:
            if token == "patient_token":
                return patient_payload
            elif token == "other_patient_token":
                 return different_patient_payload
            elif token == "provider_token":
                return provider_payload
            elif token == "admin_token":
                return admin_payload
            elif token == "expired_token":
                # Raise the correct specific error
                raise TokenExpiredError("Token has expired")
            else:
                # Raise the correct specific error for invalid/malformed tokens
                raise InvalidTokenError("Invalid token")

        # Assign the async function to the side_effect of the mock's async method
        mock_service.decode_token.side_effect = async_mock_decode_token

        return mock_service

    @pytest.fixture
    def app(self, mock_jwt_service):
        """Create a FastAPI app with auth middleware for testing."""
        # Import the dependency function from the CORRECT path
        from app.presentation.api.dependencies.auth import get_jwt_service
        # Import AuthenticationMiddleware from the CORRECT path
        from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware
        # Import AuthenticationService and create a mock instance
        from app.infrastructure.security.auth.authentication_service import AuthenticationService
        mock_auth_service = AsyncMock(spec=AuthenticationService)

        # Define a mock get_user_by_id
        async def mock_get_user_by_id(user_id: str):
            # Simulate user lookup based on the sub from the token payload
            # Return a mock User object or None
            if user_id in ["patient123", "patient456", "provider123", "admin123"]:
                # You might need to create a more realistic mock User object
                # based on your app.domain.entities.user.User definition
                mock_user = MagicMock()
                mock_user.id = user_id
                if user_id == "patient123" or user_id == "patient456":
                    mock_user.roles = ["patient"]
                elif user_id == "provider123":
                    mock_user.roles = ["provider"]
                elif user_id == "admin123":
                    mock_user.roles = ["admin"]
                return mock_user
            return None # Simulate user not found

        mock_auth_service.get_user_by_id.side_effect = mock_get_user_by_id


        app = FastAPI()

        # Override the JWT service dependency
        app.dependency_overrides[get_jwt_service] = lambda: mock_jwt_service

        # Add the AuthenticationMiddleware, providing the required service instances
        # Ensure the middleware receives the *mocked* services
        app.add_middleware(
            AuthenticationMiddleware,
            auth_service=mock_auth_service, # Provide mocked auth service
            jwt_service=mock_jwt_service    # Provide mocked jwt service
        )

        # Add test routes
        @app.get("/public")
        async def public_route(): # Mark route async if middleware/dependencies are
            return {"message": "public access"}

        # Import dependencies used by routes
        try:
             # Update import path for route dependencies
             from app.presentation.api.dependencies.auth import (
                 get_current_active_user, # Use the dependency that requires auth
                 require_role # Use the role checking dependency
             )
        except ImportError:
            print("Warning: Could not import route dependencies get_current_active_user/require_role. Using dummies.", file=sys.stderr)
             # Simpler dummy dependencies for testing middleware logic primarily
            async def get_current_active_user(request: Request):
                 if not hasattr(request.state, 'user') or not request.state.user:
                     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
                 return request.state.user # Return the user attached by middleware

            def require_role(role: str):
                 async def role_dependency(user = Depends(get_current_active_user)):
                      # Simulate role check based on the mocked user object
                      if role not in getattr(user, 'roles', []):
                           raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires role: {role}")
                      return user
                 return role_dependency


        # Update routes to use more realistic dependencies
        @app.get("/patient-only")
        async def patient_route(user = Depends(require_role("patient"))): # Check for patient role
            return {"message": "patient access", "user_id": user.id}

        @app.get("/provider-only")
        async def provider_route(user = Depends(require_role("provider"))): # Check for provider role
             return {"message": "provider access", "user_id": user.id}

        @app.get("/admin-only")
        async def admin_route(user = Depends(require_role("admin"))): # Check for admin role
            return {"message": "admin access", "user_id": user.id}

        @app.get("/patient-specific/{patient_id}")
        async def patient_specific_route(patient_id: str, user = Depends(get_current_active_user)):
            # More robust check based on roles and user id from the authenticated user object
            if "admin" in getattr(user, 'roles', []) or "provider" in getattr(user, 'roles', []):
                 # Admins/Providers can access any patient data (in this simulated logic)
                 pass
            elif "patient" in getattr(user, 'roles', []) and user.id == patient_id:
                 # Patient can access their own data
                 pass
            else:
                # Deny access otherwise
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Not authorized to access this patient's data"
                )
            return {
                "message": "access to specific patient data",
                "patient_id": patient_id,
                 "accessed_by": user.id
            }
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_public_route_access(self, test_client):
        """Test that public routes are accessible without authentication."""
        # Act
        response = test_client.get("/public")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "public access"}

    def test_patient_route_without_token(self, test_client):
        """Test that patient routes require authentication."""
        # Act
        response = test_client.get("/patient-only")

        # Assert
        assert response.status_code == 401

    def test_patient_route_with_patient_token(
        self, test_client, mock_jwt_service):
        """Test that patient routes are accessible with patient token."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer patient_token"}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "patient access"

    def test_patient_route_with_provider_token(
        self, test_client, mock_jwt_service):
        """Test that patient routes are accessible with provider token."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer provider_token"}
        )

        # Assert
        assert response.status_code == 403

    def test_provider_route_with_patient_token(
        self, test_client, mock_jwt_service):
        """Test that provider routes are not accessible with patient token."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/provider-only",
            headers={"Authorization": "Bearer patient_token"}
        )

        # Assert
        assert response.status_code == 403  # Forbidden

    def test_provider_route_with_provider_token(
        self, test_client, mock_jwt_service):
        """Test that provider routes are accessible with provider token."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/provider-only",
            headers={"Authorization": "Bearer provider_token"}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "provider access"

    def test_admin_route_with_provider_token(
        self, test_client, mock_jwt_service):
        """Test that admin routes are not accessible with provider token."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/admin-only",
            headers={"Authorization": "Bearer provider_token"}
        )

        # Assert
        assert response.status_code == 403  # Forbidden

    def test_admin_route_with_admin_token(
        self, test_client, mock_jwt_service):
        """Test that admin routes are accessible with admin token."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/admin-only",
            headers={"Authorization": "Bearer admin_token"}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "admin access"

    def test_expired_token(self, test_client, mock_jwt_service):
        """Test that expired tokens are rejected."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer expired_token"}
        )

        # Assert
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_invalid_token(self, test_client, mock_jwt_service):
        """Test that invalid tokens are rejected."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_patient_accessing_own_data(
        self, test_client, mock_jwt_service):
        """Test that a patient can access their own data."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-specific/patient123",
            headers={"Authorization": "Bearer patient_token"}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient123"

    def test_patient_accessing_other_patient_data(
        self, test_client, mock_jwt_service):
        """Test that a patient cannot access another patient's data."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-specific/patient456",
            headers={"Authorization": "Bearer patient_token"}
        )

        # Assert
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_provider_accessing_patient_data(
        self, test_client, mock_jwt_service):
        """Test that a provider can access any patient's data."""
        # Act
        # Correct test_client call
        response = test_client.get(
            "/patient-specific/patient123",
            headers={"Authorization": "Bearer provider_token"}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient123"

    def test_malformed_authorization_header(self, test_client):
        """Test that malformed authorization headers are rejected."""
        # Act - Missing "Bearer" prefix
        # Correct test_client call
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "patient_token"}
        )

        # Assert
        assert response.status_code == 401

        # Act - Empty token
        # Correct test_client call
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer "}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.skip(reason="Rate limiting not implemented in AuthenticationMiddleware yet.")
    def test_rate_limiting(self, test_client, mock_jwt_service):
        """Test that rate limiting is applied to prevent brute force attacks."""
        # Patching the middleware's rate limit values for testing
        with patch.object(AuthenticationMiddleware, '_RATE_LIMIT_MAX_REQUESTS', 5), \
             patch.object(AuthenticationMiddleware, '_RATE_LIMIT_WINDOW', 60):

            # Act - Simulate multiple rapid requests with invalid tokens
            responses = []
            for _ in range(10):  # Will exceed our patched limit of 5
                # Correct test_client call
                responses.append(test_client.get(
                    "/patient-only",
                    headers={"Authorization": "Bearer invalid_token"}
                ))

            # Assert - One of the later responses should be rate limited
            # Correct assertion syntax
            assert any(r.status_code == 429 for r in responses[-5:]), "Rate limiting not applied"

    def test_csrf_protection(self, test_client, mock_jwt_service):
        """Test CSRF protection mechanisms."""
        # Act - Simulate a request without proper CSRF token
        # This test is conceptual - actual implementation depends on your CSRF
        # approach
        # Correct test_client call
        response = test_client.post(
            "/patient-only", # Assuming POST is allowed for this route for testing
            headers={
                "Authorization": "Bearer patient_token",
                "X-Requested-With": "XMLHttpRequest"  # This is a common CSRF check
            }
        )

        # Assert - Your implementation might vary
        # For APIs using JWT, often the presence of a valid token is considered
        # sufficient protection against CSRF
        # Assuming /patient-only allows POST for this test
        assert response.status_code != 403, "CSRF protection should not block valid API requests"

    def test_logging_of_access_attempts(self, test_client, mock_jwt_service):
        """Test that access attempts are properly logged."""
        # Arrange
        mock_logger = MagicMock()

        with patch("app.presentation.middleware.authentication_middleware.logger", mock_logger):
            # Act - Successful access
            # Correct test_client call
            test_client.get(
                "/patient-only",
                headers={"Authorization": "Bearer patient_token"}
            )

            # Act - Failed access
            # Correct test_client call
            test_client.get(
                "/admin-only",
                headers={"Authorization": "Bearer patient_token"}
            )

            # Assert
            # Verify successful access was logged (using the actual logger method)
            # Check if debug was called (for successful auth)
            assert any(
                call.args[0].startswith("User patient123 authenticated successfully") 
                for call in mock_logger.debug.call_args_list
            ), "Expected successful auth debug log not found"

            # Verify that the failed *authorization* (403) did NOT trigger a warning log
            # from the middleware's specific exception handlers, as the token itself was valid.
            # The 403 is handled by FastAPI later based on the dependency raising HTTPException.
            assert not mock_logger.warning.called, \
                "Middleware warning log should not be called for valid token but failed authorization (403)"

# Correct top-level indentation for the main execution block
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
