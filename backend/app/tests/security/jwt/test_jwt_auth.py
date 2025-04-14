#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIPAA JWT Authentication Security Tests

These tests validate the JWT authentication and authorization mechanisms
that protect the API endpoints according to HIPAA requirements for access control
(§164.308(a)(4)(ii)(B) - Access authorization).

The tests validate:
    1. JWT token validation
    2. Role-based access control
    3. Token expiration and refresh
    4. Authentication failure handling
    5. Session security
"""

import json
import pytest
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from app.infrastructure.security.jwt_auth import (
    JWTAuthService,
    AuthenticationError,
    TokenValidationError,
)
from app.domain.models.user import User, UserRole

# Mock data for testing
TEST_USERS = {
    "admin": {
        "user_id": str(uuid.uuid4()),
        "role": "admin",
        "permissions": ["read:all", "write:all"]
    },
    "doctor": {
        "user_id": str(uuid.uuid4()),
        "role": "doctor",
        "permissions": ["read:patients", "write:medical_records"]
    },
    "patient": {
        "user_id": str(uuid.uuid4()),
        "role": "patient",
        "permissions": ["read:own_records"]
    }
}

# Resource access patterns for testing
RESOURCE_ACCESS = {
    "admin": {
        "patients": "allow",
        "medical_records": "allow",
        "billing": "allow",
        "system_settings": "allow"
    },
    "doctor": {
        "patients": "allow",
        "medical_records": "allow",
        "billing": "allow_own",
        "system_settings": "deny"
    },
    "patient": {
        "patients": "allow_own",
        "medical_records": "allow_own",
        "billing": "allow_own",
        "system_settings": "deny"
    }
}

# Mock FastAPI request for testing
@pytest.mark.db_required()
class MockRequest:
    def __init__(self, headers=None, cookies=None):
        self.headers = headers or {}
        self.cookies = cookies or {}

# Mock FastAPI response for testing
class MockResponse:
    def __init__(self, status_code=200, body=None, headers=None):
        self.status_code = status_code
        self.body = body or {}
        self.headers = headers or {}

    def json(self):
        return self.body

@pytest.fixture
def auth_service():
    """Fixture for JWTAuthService with test configuration."""
    return JWTAuthService(
        secret_key="test-secret-key-1234567890-abcdef",
        token_expiry_minutes=60,
        refresh_token_expiry_days=30
    )

@pytest.fixture
def user():
    """Fixture for a test user."""
    return User(
        id="user123",
        username="testuser",
        email="test@example.com",
        role=UserRole.PRACTITIONER,
        hashed_password="hashedpassword123"
    )

@pytest.fixture
def admin_user():
    """Fixture for a test admin user."""
    return User(
        id="admin123",
        username="adminuser",
        email="admin@example.com",
        role=UserRole.ADMIN,
        hashed_password="hashedpassword123"
    )

class TestJWTAuthentication:
    """Test suite for JWT authentication system."""

    def setUp(self):
        """Set up test environment."""
        self.auth_service = JWTAuthService(
            secret_key="test-secret-key-1234567890-abcdef",
            token_expiry_minutes=60,
            refresh_token_expiry_days=30
        )

    def test_token_creation(self, auth_service):
        """Test token creation with user data."""
        user = TEST_USERS["doctor"]

        token = auth_service.create_token({
            "sub": user["user_id"],
            "role": user["role"],
            "permissions": user["permissions"]
        })

        # Token should be a string
        assert isinstance(token, str), "Created token is not a string"

        # Token should be parseable
        decoded = auth_service.decode_token(token, verify=False)  # Just decode without verification

        assert decoded["sub"] == user["user_id"], "User ID claim is incorrect"
        assert decoded["role"] == user["role"], "Role claim is incorrect"
        assert decoded["permissions"] == user["permissions"], "Permissions claim is incorrect"

    def test_token_validation(self, auth_service, token_factory):
        """Test that tokens are properly validated"""
        # Valid token
        valid_token = token_factory(user_type="admin", expired=False)
        validation_result = auth_service.validate_token(valid_token)

        assert validation_result["is_valid"], "Valid token was rejected"
        assert validation_result["user_id"] == TEST_USERS["admin"]["user_id"], "User ID from token is incorrect"

        # Expired token
        expired_token = token_factory(user_type="admin", expired=True)
        validation_result = auth_service.validate_token(expired_token)

        assert not validation_result["is_valid"], "Expired token was accepted"
        assert "expired" in validation_result["error"].lower(), "Error does not indicate token expiration"

        # Invalid token
        invalid_token = token_factory(invalid=True)
        validation_result = auth_service.validate_token(invalid_token)

        assert not validation_result["is_valid"], "Invalid token was accepted"
        assert "invalid" in validation_result["error"].lower(), "Error does not indicate token invalidity"

    def test_role_based_access(self, auth_service, token_factory):
        """Test that role-based access control works correctly"""
        # Test each role's access to different resources
        for role, resources in RESOURCE_ACCESS.items():
            token = token_factory(user_type=role)

            for resource, access_level in resources.items():
                request_path = f"/api/{resource}"
                owner_id = TEST_USERS[role]["user_id"] if "own" in access_level else None

                # Prepare request context with token
                request = MockRequest(headers={"Authorization": f"Bearer {token}"})

                # Check authorization
                is_authorized = auth_service.check_resource_access(request, resource_path=request_path, resource_owner_id=owner_id)

                if access_level == "allow":
                    assert is_authorized, f"Role {role} was denied access to {resource} with access level {access_level}"
                elif access_level == "allow_own" and owner_id:
                    assert is_authorized, f"Role {role} was denied access to own {resource}"
                elif access_level == "deny":
                    assert not is_authorized, f"Role {role} was allowed access to {resource} despite deny rule"

    def test_token_from_request(self, auth_service, token_factory):
        """Test that tokens are correctly extracted from requests"""
        # Generate test token
        token = token_factory(user_type="doctor")

        # Test token in Authorization header
        request_with_header = MockRequest(headers={"Authorization": f"Bearer {token}"})
        extracted_token = auth_service.extract_token_from_request(request_with_header)
        assert extracted_token == token, "Failed to extract token from Authorization header"

        # Test token in cookie
        request_with_cookie = MockRequest(cookies={"access_token": token})
        extracted_token = auth_service.extract_token_from_request(request_with_cookie)
        assert extracted_token == token, "Failed to extract token from cookie"

        # Test missing token
        request_without_token = MockRequest()
        extracted_token = auth_service.extract_token_from_request(request_without_token)
        assert extracted_token is None, "Should return None for request without token"

    def test_unauthorized_response(self, auth_service):
        """Test that unauthorized requests get proper responses"""
        # Test expired token response
        expired_response = auth_service.create_unauthorized_response(error_type="token_expired", message="Token has expired")
        assert expired_response.status_code == 401, "Expired token should return 401 Unauthorized"
        assert "expired" in expired_response.json()["error"].lower(), "Error message should mention expiration"

        # Test invalid token response
        invalid_response = auth_service.create_unauthorized_response(error_type="invalid_token", message="Token is invalid")
        assert invalid_response.status_code == 401, "Invalid token should return 401 Unauthorized"
        assert "invalid" in invalid_response.json()["error"].lower(), "Error message should mention invalidity"

        # Test insufficient permissions response
        forbidden_response = auth_service.create_unauthorized_response(error_type="insufficient_permissions", message="Insufficient permissions to access resource")
        assert forbidden_response.status_code == 403, "Insufficient permissions should return 403 Forbidden"
        assert "permission" in forbidden_response.json()["error"].lower(), "Error message should mention permissions"

    def test_refresh_token(self, auth_service, token_factory):
        """Test token refresh functionality"""
        # Create refresh token
        user = TEST_USERS["patient"]
        refresh_token = auth_service.create_refresh_token(user["user_id"])

        # Refresh should create new access token
        refresh_result = auth_service.refresh_access_token(refresh_token)
        assert refresh_result["success"], "Token refresh failed for valid refresh token"
        assert "access_token" in refresh_result, "No access token returned after refresh"

        # Verify new token
        new_token = refresh_result["access_token"]
        decoded = auth_service.decode_token(new_token, verify=False)
        assert decoded["sub"] == user["user_id"], "User ID in refreshed token is incorrect"

        # Invalid refresh token
        invalid_refresh_result = auth_service.refresh_access_token("invalid.refresh.token")
        assert not invalid_refresh_result["success"], "Invalid refresh token was accepted"

    def test_hipaa_compliance_in_errors(self, auth_service, token_factory):
        """Test that authentication errors don't leak sensitive information"""
        # Create a context with invalid authentication
        invalid_token = token_factory(invalid=True)

        # Get error response
        error_response = auth_service.create_unauthorized_response(error_type="invalid_token", message="Token validation failed")
        response_json = error_response.json()

        # Error response should not contain PHI
        assert "user_id" not in response_json, "Error response contains user ID (PHI)"
        assert "patient" not in json.dumps(response_json).lower(), "Error response may contain patient reference"

        # Error should be generic enough not to leak information
        assert len(response_json["error"]) < 100, "Error message too detailed, may leak information"

    def test_token_security_properties(self, auth_service):
        """Test security properties of generated tokens"""
        user = TEST_USERS["admin"]

        # Generate token with short expiration
        short_token = auth_service.create_token({
            "sub": user["user_id"],
            "role": user["role"],
            # 5 minutes
            "exp": int(time.time()) + 300
        })

        # Token should use secure algorithm
        token_parts = short_token.split('.')
        assert len(token_parts) == 3, "Token is not a valid JWT with three parts"

        # Check token expiration enforcement
        time.sleep(1)  # Wait briefly
        token_with_leeway = auth_service.create_token({
            "sub": user["user_id"],
            "role": user["role"],
            # Expires now
            "exp": int(time.time())
        }, leeway=2)

        validation_result = auth_service.validate_token(token_with_leeway)
        assert validation_result["is_valid"], "Token validation should allow reasonable leeway"

        # Check reasonable expiration time (should be > 5 min and < 12 hours)
        default_token = auth_service.create_token({
            "sub": user["user_id"],
            "role": user["role"]
        })

        decoded = auth_service.decode_token(default_token, verify=False)
        now = int(time.time())

        assert decoded["exp"] > now + 300, "Token expiration too short for practical use"
        assert decoded["exp"] < now + 43200, "Token expiration too long for security (>12 hours)"

@pytest.fixture
def token_factory(auth_service):
    """Create test tokens with different properties"""
    def _create_token(user_type="admin", expired=False, invalid=False):
        user = TEST_USERS[user_type]

        if invalid:
            payload = {
                "sub": user["user_id"],
                "role": user["role"],
                "permissions": user["permissions"]
            }
        else:
            payload = {
                "sub": user["user_id"],
                "role": user["role"],
                "permissions": user["permissions"]
            }

            if expired:
                # Set expiration in the past
                payload["exp"] = int(time.time()) - 3600  # 1 hour ago
            else:
                # Valid token expires in the future
                payload["exp"] = int(time.time()) + 3600  # 1 hour from now

        return auth_service.create_token(payload)

    return _create_token
