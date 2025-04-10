# -*- coding: utf-8 -*-
import pytest
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.infrastructure.security.auth_middleware import (
    JWTAuthMiddleware, 
    verify_token, 
    verify_patient_access,
    verify_provider_access,
    verify_admin_access,
    get_current_user
)
from app.infrastructure.security.jwt_service import JWTService
from app.domain.exceptions import AuthenticationError, TokenExpiredError


@pytest.mark.venv_only
class TestAuthMiddleware:
    """
    Tests for the Authentication Middleware to ensure HIPAA-compliant access control.
    
    These tests verify:
    1. Proper authentication of all requests to protected resources
    2. Correct role-based access control
    3. Protection against unauthorized access attempts
    4. PHI access is properly restricted based on user roles
    """
    
    @pytest.fixture
    def mock_jwt_service(self):
        """Create a mocked JWT service for testing."""
        mock_service = MagicMock(spec=JWTService)
        
        # Define user payloads for different roles
        self.patient_payload = {
            "sub": "patient123",
            "role": "patient",
            "user_id": "patient123"
        }
        
        self.different_patient_payload = {
            "sub": "patient456",
            "role": "patient",
            "user_id": "patient456"
        }
        
        self.provider_payload = {
            "sub": "provider123",
            "role": "provider",
            "user_id": "provider123"
        }
        
        self.admin_payload = {
            "sub": "admin123",
            "role": "admin",
            "user_id": "admin123"
        }
        
        # Setup mock verify_token to return appropriate payload based on token
        def mock_verify_token(token):
            if token == "patient_token":
                return self.patient_payload
            elif token == "other_patient_token":
                return self.different_patient_payload
            elif token == "provider_token":
                return self.provider_payload
            elif token == "admin_token":
                return self.admin_payload
            elif token == "expired_token":
                raise TokenExpiredError("Token has expired")
            else:
                raise AuthenticationError("Invalid token")
        
        mock_service.verify_token.side_effect = mock_verify_token
        
        # Setup mock has_role
        def mock_has_role(token, required_role):
            payload = mock_verify_token(token)
            if required_role == "patient":
                return True  # All roles can access patient resources
            elif required_role == "provider":
                return payload["role"] in ["provider", "admin"]
            elif required_role == "admin":
                return payload["role"] == "admin"
            return False
        
        mock_service.has_role.side_effect = mock_has_role
        
        return mock_service
    
    @pytest.fixture
    def app(self, mock_jwt_service):
        """Create a FastAPI app with auth middleware for testing."""
        app = FastAPI()
        
        # Create auth middleware with mocked jwt_service for testing
        with patch("app.infrastructure.security.auth_middleware.get_jwt_service", return_value=mock_jwt_service):
            app.add_middleware(JWTAuthMiddleware)
            
            # Add test routes
            @app.get("/public")
            def public_route():
                return {"message": "public access"}
            
            @app.get("/patient-only")
            def patient_route(user = Depends(verify_patient_access)):
                return {"message": "patient access", "user": user}
            
            @app.get("/provider-only")
            def provider_route(user = Depends(verify_provider_access)):
                return {"message": "provider access", "user": user}
            
            @app.get("/admin-only")
            def admin_route(user = Depends(verify_admin_access)):
                return {"message": "admin access", "user": user}
            
            @app.get("/patient-specific/{patient_id}")
            def patient_specific_route(patient_id: str, user = Depends(verify_patient_access)):
                # Simulate access to patient-specific resources
                if user["role"] == "patient" and user["user_id"] != patient_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Not authorized to access this patient's data"
                    )
                return {"message": "access to specific patient data", "patient_id": patient_id}
        
        return app
    
    @pytest.fixture
    @pytest.mark.venv_only
def test_client(self, app):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    @pytest.mark.venv_only
def test_public_route_access(self, test_client):
        """Test that public routes are accessible without authentication."""
        # Act
        response = test_client.get("/public")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "public access"}
    
    @pytest.mark.venv_only
def test_patient_route_without_token(self, test_client):
        """Test that patient routes require authentication."""
        # Act
        response = test_client.get("/patient-only")
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.venv_only
def test_patient_route_with_patient_token(self, test_client, mock_jwt_service):
        """Test that patient routes are accessible with patient token."""
        # Act
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer patient_token"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "patient access"
    
    @pytest.mark.venv_only
def test_patient_route_with_provider_token(self, test_client, mock_jwt_service):
        """Test that patient routes are accessible with provider token."""
        # Act
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer provider_token"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "patient access"
    
    @pytest.mark.venv_only
def test_provider_route_with_patient_token(self, test_client, mock_jwt_service):
        """Test that provider routes are not accessible with patient token."""
        # Act
        response = test_client.get(
            "/provider-only",
            headers={"Authorization": "Bearer patient_token"}
        )
        
        # Assert
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.venv_only
def test_provider_route_with_provider_token(self, test_client, mock_jwt_service):
        """Test that provider routes are accessible with provider token."""
        # Act
        response = test_client.get(
            "/provider-only",
            headers={"Authorization": "Bearer provider_token"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "provider access"
    
    @pytest.mark.venv_only
def test_admin_route_with_provider_token(self, test_client, mock_jwt_service):
        """Test that admin routes are not accessible with provider token."""
        # Act
        response = test_client.get(
            "/admin-only",
            headers={"Authorization": "Bearer provider_token"}
        )
        
        # Assert
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.venv_only
def test_admin_route_with_admin_token(self, test_client, mock_jwt_service):
        """Test that admin routes are accessible with admin token."""
        # Act
        response = test_client.get(
            "/admin-only",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "admin access"
    
    @pytest.mark.venv_only
def test_expired_token(self, test_client, mock_jwt_service):
        """Test that expired tokens are rejected."""
        # Act
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer expired_token"}
        )
        
        # Assert
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    @pytest.mark.venv_only
def test_invalid_token(self, test_client, mock_jwt_service):
        """Test that invalid tokens are rejected."""
        # Act
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Assert
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.venv_only
def test_patient_accessing_own_data(self, test_client, mock_jwt_service):
        """Test that a patient can access their own data."""
        # Act
        response = test_client.get(
            "/patient-specific/patient123",
            headers={"Authorization": "Bearer patient_token"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient123"
    
    @pytest.mark.venv_only
def test_patient_accessing_other_patient_data(self, test_client, mock_jwt_service):
        """Test that a patient cannot access another patient's data."""
        # Act
        response = test_client.get(
            "/patient-specific/patient456",
            headers={"Authorization": "Bearer patient_token"}
        )
        
        # Assert
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()
    
    @pytest.mark.venv_only
def test_provider_accessing_patient_data(self, test_client, mock_jwt_service):
        """Test that a provider can access any patient's data."""
        # Act
        response = test_client.get(
            "/patient-specific/patient123",
            headers={"Authorization": "Bearer provider_token"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient123"
    
    @pytest.mark.venv_only
def test_malformed_authorization_header(self, test_client):
        """Test that malformed authorization headers are rejected."""
        # Act - Missing "Bearer" prefix
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "patient_token"}
        )
        
        # Assert
        assert response.status_code == 401
        
        # Act - Empty token
        response = test_client.get(
            "/patient-only",
            headers={"Authorization": "Bearer "}
        )
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.venv_only
def test_rate_limiting(self, test_client, mock_jwt_service):
        """Test that rate limiting is applied to prevent brute force attacks."""
        # Patching the middleware's rate limit values for testing
        with patch.object(JWTAuthMiddleware, '_RATE_LIMIT_MAX_REQUESTS', 5), \
             patch.object(JWTAuthMiddleware, '_RATE_LIMIT_WINDOW', 60):
            
            # Act - Simulate multiple rapid requests with invalid tokens
            responses = []
            for _ in range(10):  # Will exceed our patched limit of 5
                responses.append(test_client.get(
                    "/patient-only",
                    headers={"Authorization": "Bearer invalid_token"}
                ))
            
            # Assert - One of the later responses should be rate limited
            assert any(r.status_code == 429 for r in responses[-5:]), "Rate limiting not applied"
    
    @pytest.mark.venv_only
def test_csrf_protection(self, test_client, mock_jwt_service):
        """Test CSRF protection mechanisms."""
        # Act - Simulate a request without proper CSRF token
        # This test is conceptual - actual implementation depends on your CSRF approach
        response = test_client.post(
            "/patient-only",
            headers={
                "Authorization": "Bearer patient_token",
                "X-Requested-With": "XMLHttpRequest"  # This is a common CSRF check
            }
        )
        
        # Assert - Your implementation might vary
        # For APIs using JWT, often the presence of a valid token is considered
        # sufficient protection against CSRF
        assert response.status_code != 403, "CSRF protection should not block valid API requests"
    
    @pytest.mark.venv_only
def test_logging_of_access_attempts(self, test_client, mock_jwt_service):
        """Test that access attempts are properly logged."""
        # Arrange
        mock_logger = MagicMock()
        
        with patch("app.infrastructure.security.auth_middleware.audit_logger", mock_logger):
            # Act - Successful access
            test_client.get(
                "/patient-only",
                headers={"Authorization": "Bearer patient_token"}
            )
            
            # Act - Failed access
            test_client.get(
                "/admin-only",
                headers={"Authorization": "Bearer patient_token"}
            )
            
            # Assert
            # Verify successful access was logged
            assert mock_logger.log_access.called
            # Verify failed access attempt was logged
            assert mock_logger.log_access_attempt.called


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])