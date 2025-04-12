# -*- coding: utf-8 -*-
"""
HIPAA Compliance Testing - API Security Tests

These tests validate that API endpoints properly secure access to sensitive patient data
according to HIPAA requirements. Tests focus on authentication, authorization,
input validation, and secure communication.
"""

import json
import uuid
import pytest
from unittest.mock import patch, MagicMock

from fastapi import status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.testclient import TestClient

# Removed direct app import
# Corrected path, removed AuthHandler
from app.api.dependencies.auth import get_current_user
# from app.infrastructure.security.rate_limiting import RateLimiter #
# RateLimiter removed or refactored


# Removed local test_client fixture; tests will use client from conftest.py
@pytest.fixture
def mock_token():
                """Generate a mock JWT token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJyb2xlIjoicGF0aWVudCIsImV4cCI6OTk5OTk5OTk5OX0.signature"
    @pytest.fixture
    def mock_user():
                """Sample user data for testing."""    
    return {
        "id": str(uuid.uuid4()),
        "username": "test_user",
        "role": "patient",
        "full_name": "Test User"
    }
@pytest.fixture
def mock_admin_user():
                """Sample admin user data for testing."""    
    return {
        "id": str(uuid.uuid4()),
        "username": "admin_user",
        "role": "psychiatrist",
        "full_name": "Admin User"
    }


@pytest.mark.db_required()
class TestAuthentication:
    """Test authentication mechanisms."""
    def test_missing_token(self, client: TestClient) # Use client fixture
        """Test that requests without tokens are rejected."""
        response = test_client.get("/api/v1/patients/me")
        assert response.status_code  ==  status.HTTP_401_UNAUTHORIZED
    def test_invalid_token(self, client: TestClient) # Use client fixture
            """Test that invalid tokens are rejected."""
            response = test_client.get()
            "/api/v1/patients/me",
            headers={"Authorization": "Bearer invalid.token.here"}
    (            )
            assert response.status_code  ==  status.HTTP_401_UNAUTHORIZED
    def test_expired_token(self, client: TestClient) # Use client fixture
                """Test that expired tokens are rejected."""
        # Create an expired token (exp in the past)
                expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJyb2xlIjoicGF0aWVudCIsImV4cCI6MTU4MzI2MTIzNH0.signature"
        
    (    with patch('app.presentation.api.auth.AuthHandler.decode_token' ))
    (    side_effect=HTTPException(status_code=401, detail="Token expired"))
    response = test_client.get()
    "/api/v1/patients/me",
    headers={"Authorization": f"Bearer {expired_token}"}
    (    )
    assert response.status_code  ==  status.HTTP_401_UNAUTHORIZED
    def test_tampered_token(self, client: TestClient) # Use client fixture
                    """Test that tampered tokens are rejected."""
        # Token with modified payload
                    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYWNrZXIiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjk5OTk5OTk5OTl9.invalid_signature"
        
    (    with patch('app.presentation.api.auth.AuthHandler.decode_token' ))
    (    side_effect=HTTPException(status_code=401, detail="Invalid token"))
    response = test_client.get()
    "/api/v1/patients/me",
    headers={"Authorization": f"Bearer {tampered_token}"}
    (    )
    assert response.status_code  ==  status.HTTP_401_UNAUTHORIZED
    def test_valid_token(self, client: TestClient, mock_token, mock_user) # Use client fixture
                        """Test that valid tokens are accepted."""
    ((                        with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)))
                        response = test_client.get()
                        "/api/v1/patients/me",
                        headers={"Authorization": f"Bearer {mock_token}"}
    (                        )
                        assert response.status_code  ==  status.HTTP_200_OK
    class TestAuthorization:
        """Test authorization and access control."""
    def test_patient_accessing_own_data(self, client: TestClient, mock_token, mock_user) # Use client fixture
        """Test that patients can access their own data."""
        user_id = mock_user["id"]
        
    ((    with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)))
    response = test_client.get()
    f"/api/v1/patients/{user_id}",
    headers={"Authorization": f"Bearer {mock_token}"}
    (    )
    assert response.status_code  ==  status.HTTP_200_OK
    def test_patient_accessing_other_patient_data(self, client: TestClient, mock_token, mock_user) # Use client fixture
            """Test that patients cannot access other patients' data."""
            other_user_id = str(uuid.uuid4())  # Different from mock_user["id"]
        
    (    with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)), \
    patch('app.presentation.api.endpoints.patients.verify_patient_access',)
    (    side_effect=HTTPException(status_code=403, detail="Access denied"))
    response = test_client.get()
    f"/api/v1/patients/{other_user_id}",
    headers={"Authorization": f"Bearer {mock_token}"}
    (    )
    assert response.status_code  ==  status.HTTP_403_FORBIDDEN
    def test_admin_accessing_patient_data(self, client: TestClient, mock_token, mock_admin_user) # Use client fixture
                """Test that admins/psychiatrists can access patient data."""
                patient_id = str(uuid.uuid4())
        
    ((    with patch('app.presentation.api.auth.get_current_user', return_value=mock_admin_user)))
    response = test_client.get()
    f"/api/v1/patients/{patient_id}",
    headers={"Authorization": f"Bearer {mock_token}"}
    (    )
    assert response.status_code  ==  status.HTTP_200_OK
    def test_role_specific_endpoint(self, client: TestClient, mock_token, mock_user, mock_admin_user) # Use client fixture
                    """Test that role-specific endpoints enforce proper access control."""
        # Admin-only endpoint
    (                    with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)), \
                    patch('app.presentation.api.endpoints.admin.verify_admin_access', )
    (                    side_effect=HTTPException(status_code=403, detail="Admin access required"))
                    response = test_client.get()
                    "/api/v1/admin/dashboard",
                    headers={"Authorization": f"Bearer {mock_token}"}
    (                    )
                    assert response.status_code  ==  status.HTTP_403_FORBIDDEN
        
        # Admin accessing admin endpoint
    ((    with patch('app.presentation.api.auth.get_current_user', return_value=mock_admin_user)))
    response = test_client.get()
    "/api/v1/admin/dashboard",
    headers={"Authorization": f"Bearer {mock_token}"}
    (    )
    assert response.status_code  ==  status.HTTP_200_OK


    # Removed TestRateLimiting class as RateLimiter component seems removed/refactored
    class TestInputValidation:
    """Test input validation for security."""
    def test_invalid_input_format(self, client: TestClient, mock_token, mock_user) # Use client fixture
        """Test that invalid input format is rejected."""
    ((        with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)))
        response = test_client.post()
        "/api/v1/patients",
        headers={"Authorization": f"Bearer {mock_token}"},
        json={"name": "Test Patient"}  # Missing required fields
    (        )
        assert response.status_code  ==  status.HTTP_422_UNPROCESSABLE_ENTITY
    def test_input_sanitization(self, client: TestClient, mock_token, mock_user) # Use client fixture
            """Test that input is properly sanitized."""
            malicious_input = {
            "name": "Test Patient<script>alert('XSS')</script>",
            "email": "test@example.com' OR 1=1--",
            "notes": "Normal notes; DROP TABLE patients;"
            }
        
(    with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)), \
    patch('app.presentation.api.endpoints.patients.sanitize_input') as mock_sanitize:
            
        mock_sanitize.return_value = {
        "name": "Test Patient",
        "email": "test@example.com",
        "notes": "Normal notes"
    }
            
    test_client.post()
    "/api/v1/patients",
    headers={"Authorization": f"Bearer {mock_token}"},
    json=malicious_input
(    )
            
            # Verify sanitize was called with the malicious input
    mock_sanitize.assert_called_once_with(malicious_input)
    def test_input_length_limits(self, client: TestClient, mock_token, mock_user) # Use client fixture
                """Test that input length limits are enforced."""
        # Create overly long inputs
                overly_long_text = "x" * 10000  # 10,000 characters
        
    input_data = {
    "name": overly_long_text,
    "email": f"{overly_long_text}@example.com",
    "notes": overly_long_text
    }
        
((    with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)))
    response = test_client.post()
    "/api/v1/patients",
    headers={"Authorization": f"Bearer {mock_token}"},
    json=input_data
(    )
            
            # Should return validation error due to length constraints
    assert response.status_code  ==  status.HTTP_422_UNPROCESSABLE_ENTITY
class TestSecureHeaders:
    """Test secure headers for HTTP responses."""
    def test_security_headers(self, client: TestClient) # Use client fixture
        """Test that security headers are present in responses."""
        response = test_client.get("/api/v1/health")
        
        # Check for required security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
        
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
        
    assert "Content-Security-Policy" in response.headers
        
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    def test_cors_configuration(self, client: TestClient) # Use client fixture
            """Test proper CORS configuration."""
        # Send an OPTIONS request (preflight)
            response = test_client.options()
            "/api/v1/health",
            headers={"Origin": "https://example.com", 
            "Access-Control-Request-Method": "GET"}
    (            )
        
        # Check CORS headers
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers
        
        # Ensure wildcard is not used for HIPAA compliance
    assert response.headers["Access-Control-Allow-Origin"] != "*"
    class TestErrorHandling:
    """Test secure error handling."""
    def test_error_messages_do_not_leak_info(self, client: TestClient) # Use client fixture
        """Test that error messages don't leak sensitive information."""
        # Test with a non-existent endpoint
        response = test_client.get("/api/v1/nonexistent")
        assert response.status_code  ==  status.HTTP_404_NOT_FOUND
        
        # Error message should be generic
    error_data = response.json()
    assert "detail" in error_data
    assert "not found" in error_data["detail"].lower()
    assert "stacktrace" not in error_data
    assert "line" not in error_data["detail"].lower()
    assert "file" not in error_data["detail"].lower()
    def test_database_error_handling(self, client: TestClient, mock_token, mock_user) # Use client fixture
            """Test that database errors don't leak sensitive information."""
    (            with patch('app.presentation.api.auth.get_current_user', return_value=mock_user)), \
            patch('app.presentation.api.endpoints.patients.PatientService.get_patient', )
    ((            side_effect=Exception("SQL error: table patients has no column named ssn")))
            
    response = test_client.get()
    f"/api/v1/patients/{mock_user['id']}",
    headers={"Authorization": f"Bearer {mock_token}"}
    (    )
            
    assert response.status_code  ==  status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Error should not contain database details
    error_data = response.json()
    assert "SQL" not in error_data["detail"]
    assert "table" not in error_data["detail"]
    assert "column" not in error_data["detail"]
    assert "ssn" not in error_data["detail"]