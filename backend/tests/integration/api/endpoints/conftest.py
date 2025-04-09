"""
Pytest configuration for API endpoint tests.

This module contains common fixtures and configuration for testing the API endpoints.
"""

import jwt
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from app.api.dependencies.auth import get_current_user
from app.domain.entities.user import User


@pytest.fixture
def mock_current_user():
    """Fixture that provides a mock get_current_user function.
    
    Returns a test user with admin privileges for testing protected endpoints.
    """
    test_user = User(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
        roles=["admin", "clinician"]
    )
    
    async def override_get_current_user(*args, **kwargs):
        return test_user
    
    return override_get_current_user


@pytest.fixture
def mock_auth_dependency(monkeypatch, mock_current_user):
    """Fixture that overrides the authentication dependency.
    
    This allows API tests to run without needing to authenticate.
    """
    monkeypatch.setattr(
        "app.api.dependencies.auth.get_current_user", mock_current_user
    )
    yield
    monkeypatch.undo()


@pytest.fixture
def test_client(mock_auth_dependency):
    """Fixture that provides a FastAPI test client with mocked authentication.
    
    Returns a configured test client for making requests to the API.
    """
    from app.main import app
    
    with TestClient(app) as client:
        yield client