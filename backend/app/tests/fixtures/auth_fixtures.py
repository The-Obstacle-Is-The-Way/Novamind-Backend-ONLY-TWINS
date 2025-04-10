# -*- coding: utf-8 -*-
"""
Authentication fixtures for tests.

This module provides pytest fixtures for authentication-related testing,
ensuring consistent test authentication across the entire test suite.
"""

import pytest
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock

from fastapi import Depends, Request
from jose import jwt

# Default test values
DEFAULT_TEST_USER_ID = "test-user-123"
DEFAULT_TEST_ROLES = ["clinician", "researcher"]
DEFAULT_TEST_PERMISSIONS = ["read:patients", "write:clinical_notes"]
DEFAULT_TEST_JWT_SECRET = "test-jwt-secret-key-for-testing-only"
DEFAULT_JWT_ALGORITHM = "HS256"


@pytest.fixture
def test_token_payload() -> Dict[str, Any]:
    """Provide a standard token payload for testing."""
    return {
        "sub": DEFAULT_TEST_USER_ID,
        "roles": DEFAULT_TEST_ROLES,
        "permissions": DEFAULT_TEST_PERMISSIONS,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "iat": datetime.now(UTC),
        "jti": "test-token-id-12345",
        "iss": "novamind-test",
        "aud": "api-test"
    }


@pytest.fixture
def test_token(test_token_payload: Dict[str, Any]) -> str:
    """Generate a JWT token for testing."""
    return jwt.encode(
        test_token_payload,
        DEFAULT_TEST_JWT_SECRET,
        algorithm=DEFAULT_JWT_ALGORITHM
    )


@pytest.fixture
def mock_get_current_user():
    """Mock the get_current_user dependency."""
    with patch("app.api.dependencies.auth.get_current_user") as mock:
        mock.return_value = {
            "id": DEFAULT_TEST_USER_ID,
            "roles": DEFAULT_TEST_ROLES,
            "permissions": DEFAULT_TEST_PERMISSIONS,
            "is_active": True,
            "created_at": datetime.now(UTC).isoformat(),
            "email": "test@example.com"
        }
        yield mock


@pytest.fixture
def mock_get_current_clinician():
    """Mock the get_current_clinician dependency."""
    with patch("app.api.dependencies.auth.get_current_active_clinician") as mock:
        mock.return_value = {
            "id": DEFAULT_TEST_USER_ID,
            "roles": ["clinician"],
            "permissions": DEFAULT_TEST_PERMISSIONS,
            "is_active": True,
            "created_at": datetime.now(UTC).isoformat(),
            "email": "clinician@example.com",
            "specialty": "Psychiatry"
        }
        yield mock


@pytest.fixture
def mock_get_current_admin():
    """Mock the get_current_admin dependency."""
    with patch("app.api.dependencies.auth.get_current_active_admin") as mock:
        mock.return_value = {
            "id": DEFAULT_TEST_USER_ID,
            "roles": ["admin"],
            "permissions": ["*"],  # Admin has all permissions
            "is_active": True,
            "created_at": datetime.now(UTC).isoformat(),
            "email": "admin@example.com"
        }
        yield mock


@pytest.fixture
def mock_verify_patient_access():
    """Mock the verify_patient_access dependency."""
    with patch("app.api.dependencies.auth.verify_patient_access") as mock:
        mock.return_value = None  # Success case returns None
        yield mock


@pytest.fixture
def authenticated_request(test_token: str) -> MagicMock:
    """Create a mock request with authentication."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": f"Bearer {test_token}"}
    
    # Set up state with authentication info
    mock_request.state = MagicMock()
    mock_request.state.authenticated = True
    mock_request.state.user = {
        "id": DEFAULT_TEST_USER_ID,
        "roles": DEFAULT_TEST_ROLES,
        "permissions": DEFAULT_TEST_PERMISSIONS
    }
    
    return mock_request


@pytest.fixture
def mock_token_dependency():
    """
    Create a fixture that mocks the OAuth2PasswordBearer dependency.
    
    This is useful for testing endpoints that require token authentication.
    """
    with patch("app.core.auth.oauth2_scheme") as mock_oauth2:
        mock_oauth2.return_value = "test.jwt.token"
        yield mock_oauth2


@pytest.fixture
def override_auth_dependencies(app, test_token_payload: Dict[str, Any]):
    """
    Override FastAPI auth dependencies for testing.
    
    This fixture overrides auth dependencies in the app with mocked versions
    that return predefined test values.
    """
    from app.api.dependencies import auth
    
    # Store original dependencies
    original_deps = {
        "get_current_token_payload": auth.get_current_token_payload,
        "get_current_user": auth.get_current_user,
        "get_current_active_clinician": auth.get_current_active_clinician,
        "get_current_active_admin": auth.get_current_active_admin
    }
    
    # Create async mocks
    async def mock_get_token_payload() -> Dict[str, Any]:
        return test_token_payload
        
    async def mock_get_current_user() -> Dict[str, Any]:
        return {
            "id": test_token_payload["sub"],
            "roles": test_token_payload["roles"],
            "permissions": test_token_payload["permissions"],
            "is_active": True
        }
    
    async def mock_get_current_clinician() -> Dict[str, Any]:
        user = await mock_get_current_user()
        user["roles"] = ["clinician"]
        return user
        
    async def mock_get_current_admin() -> Dict[str, Any]:
        user = await mock_get_current_user()
        user["roles"] = ["admin"]
        user["permissions"] = ["*"]
        return user
    
    # Apply overrides
    app.dependency_overrides[auth.get_current_token_payload] = mock_get_token_payload
    app.dependency_overrides[auth.get_current_user] = mock_get_current_user
    app.dependency_overrides[auth.get_current_active_clinician] = mock_get_current_clinician
    app.dependency_overrides[auth.get_current_active_admin] = mock_get_current_admin
    
    yield
    
    # Remove overrides and restore original dependencies
    for dep in original_deps:
        if dep in app.dependency_overrides:
            del app.dependency_overrides[dep]