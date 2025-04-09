"""
Pytest configuration for API endpoint tests.

This module contains common fixtures and configuration for testing the API endpoints.
"""

import jwt
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.models.users import User


@pytest.fixture
def mock_current_user():
    """Fixture that provides a mock get_current_user function.
    
    Returns:
        Mock get_current_user function
    """
    async def mock_get_current_user(
        credentials: HTTPAuthorizationCredentials = None,
    ) -> User:
        """Mock the get_current_user dependency.
        
        Args:
            credentials: HTTP Authentication credentials
            
        Returns:
            Mock user
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # For test purposes, use a simple token validation scheme
        try:
            # In a test environment, we're using simple tokens
            payload = jwt.decode(
                credentials.credentials,
                "test-secret",
                algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            role = payload.get("role", "patient")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return User(
                id=user_id,
                email=f"{user_id}@example.com",
                role=role,
                is_active=True,
                full_name=f"Test {role.capitalize()}"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    return mock_get_current_user


@pytest.fixture
def override_auth_dependency(app: FastAPI, mock_current_user):
    """Fixture that overrides the authentication dependency.
    
    Args:
        app: FastAPI application
        mock_current_user: Mock get_current_user function
        
    Returns:
        FastAPI application with overridden authentication dependency
    """
    app.dependency_overrides[get_current_user] = mock_current_user
    return app


@pytest.fixture
def patient_token() -> str:
    """Fixture that returns a JWT token for a patient user.
    
    Returns:
        JWT token
    """
    payload = {
        "sub": "test-patient-id",
        "role": "patient"
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def provider_token() -> str:
    """Fixture that returns a JWT token for a provider user.
    
    Returns:
        JWT token
    """
    payload = {
        "sub": "test-provider-id",
        "role": "provider"
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def admin_token() -> str:
    """Fixture that returns a JWT token for an admin user.
    
    Returns:
        JWT token
    """
    payload = {
        "sub": "test-admin-id",
        "role": "admin"
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")