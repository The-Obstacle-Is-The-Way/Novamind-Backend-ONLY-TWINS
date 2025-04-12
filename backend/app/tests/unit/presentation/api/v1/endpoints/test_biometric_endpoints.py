# -*- coding: utf-8 -*-
"""
Unit tests for biometric endpoints dependencies.

These tests verify that the biometric endpoints dependencies correctly
handle authentication and patient ID validation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import Dict, Any, Optional # Added Optional

import pytest
from fastapi import FastAPI, Depends, HTTPException, status # Added status
from fastapi.testclient import TestClient

from app.domain.exceptions import AuthenticationError, AuthorizationError # Corrected exception names
# Assuming these dependencies exist in the specified path
from app.presentation.api.v1.endpoints.biometric_endpoints import (
    get_current_user_id,
    get_patient_id,
    get_current_user_role,
    require_clinician_role,
    require_admin_role
)
# Assuming JWTService exists for mocking
from app.infrastructure.security.jwt_service import JWTService


@pytest.fixture
def mock_jwt_service():
    """Create a mock JWT service."""
    service = MagicMock(spec=JWTService) # Use spec for better mocking
    service.decode_token = MagicMock()
    return service


@pytest.fixture
def app(mock_jwt_service):
    """Create a FastAPI test app with test endpoints."""
    app_instance = FastAPI()

    # Override JWTService dependency (assuming it's injected somewhere)
    # This might need adjustment based on how JWTService is actually provided
    # For now, we'll assume it's available via app state or another dependency
    # A common pattern is to override a dependency function like 'get_jwt_service'
    # app_instance.dependency_overrides[get_jwt_service] = lambda: mock_jwt_service

    # Test endpoints using the dependencies
    @app_instance.get("/test/user-id")
    async def test_get_current_user_id_endpoint(user_id: UUID = Depends(get_current_user_id(jwt_service=mock_jwt_service))): # Pass mock directly if needed
        return {"user_id": str(user_id)}

    @app_instance.get("/test/patient/{patient_id}")
    async def test_get_patient_id_endpoint(patient_id: UUID = Depends(get_patient_id)):
        return {"patient_id": str(patient_id)}

    @app_instance.get("/test/user-role")
    async def test_get_current_user_role_endpoint(role: str = Depends(get_current_user_role(jwt_service=mock_jwt_service))): # Pass mock directly if needed
        return {"role": role}

    @app_instance.get("/test/clinician-only")
    async def test_require_clinician_role_endpoint(
        _: None = Depends(require_clinician_role(jwt_service=mock_jwt_service)), # Pass mock
        user_id: UUID = Depends(get_current_user_id(jwt_service=mock_jwt_service)) # Pass mock
    ):
        return {"user_id": str(user_id)}

    @app_instance.get("/test/admin-only")
    async def test_require_admin_role_endpoint(
        _: None = Depends(require_admin_role(jwt_service=mock_jwt_service)), # Pass mock
        user_id: UUID = Depends(get_current_user_id(jwt_service=mock_jwt_service)) # Pass mock
    ):
        return {"user_id": str(user_id)}

    return app_instance


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    
    return TestClient(app)


class TestBiometricEndpointsDependencies:
    """Tests for the biometric endpoints dependencies."""

    def test_get_current_user_id_success(self, client, mock_jwt_service):
        """Test that get_current_user_id returns the user ID from the token."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        mock_jwt_service.decode_token.return_value = {"sub": user_id}

        # Execute
    response = client.get(
    "/test/user-id",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == {"user_id": user_id}
    mock_jwt_service.decode_token.assert_called_once_with("test_token")

    def test_get_current_user_id_missing_sub(self, client, mock_jwt_service):
        """Test that get_current_user_id raises an error if sub is missing."""
        # Setup
        mock_jwt_service.decode_token.return_value = {} # Missing 'sub'

        # Execute
    response = client.get(
    "/test/user-id",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]

    def test_get_current_user_id_authentication_exception(self, client, mock_jwt_service):
        """Test that get_current_user_id handles AuthenticationError."""
        # Setup
        mock_jwt_service.decode_token.side_effect = AuthenticationError("Invalid token")

        # Execute
    response = client.get(
    "/test/user-id",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]

    def test_get_current_user_id_generic_exception(self, client, mock_jwt_service):
        """Test that get_current_user_id handles generic exceptions."""
        # Setup
        mock_jwt_service.decode_token.side_effect = Exception("Unexpected error")

        # Execute
    response = client.get(
    "/test/user-id",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 401
        # The generic exception handler might return a different detail message
    assert "Authentication error" in response.json()["detail"]

    def test_get_patient_id(self, client, mock_jwt_service):
        """Test that get_patient_id returns the patient ID from the path."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        patient_id = "12345678-1234-5678-1234-567812345678"
        mock_jwt_service.decode_token.return_value = {"sub": user_id} # Needed for auth on endpoint

        # Execute
    response = client.get(
    f"/test/patient/{patient_id}",
    headers={"Authorization": "Bearer test_token"} # Assuming endpoint requires auth
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == {"patient_id": patient_id}

    def test_get_current_user_role_success(self, client, mock_jwt_service):
        """Test that get_current_user_role returns the role from the token."""
        # Setup
        mock_jwt_service.decode_token.return_value = {"role": "clinician"}

        # Execute
    response = client.get(
    "/test/user-role",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == {"role": "clinician"}

    def test_get_current_user_role_missing_role(self, client, mock_jwt_service):
        """Test that get_current_user_role raises an error if role is missing."""
        # Setup
        mock_jwt_service.decode_token.return_value = {"sub": "user123"} # Missing 'role'

        # Execute
    response = client.get(
    "/test/user-role",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]

    def test_require_clinician_role_success(self, client, mock_jwt_service):
        """Test that require_clinician_role allows clinicians."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        mock_jwt_service.decode_token.return_value = {"sub": user_id, "role": "clinician"}

        # Execute
    response = client.get(
    "/test/clinician-only",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == {"user_id": user_id}

    def test_require_clinician_role_admin(self, client, mock_jwt_service):
        """Test that require_clinician_role allows admins."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        mock_jwt_service.decode_token.return_value = {"sub": user_id, "role": "admin"}

        # Execute
    response = client.get(
    "/test/clinician-only",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == {"user_id": user_id}

    def test_require_clinician_role_patient(self, client, mock_jwt_service):
        """Test that require_clinician_role rejects patients."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        mock_jwt_service.decode_token.return_value = {"sub": user_id, "role": "patient"} # Assuming 'patient' role exists

        # Execute
    response = client.get(
    "/test/clinician-only",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 403
    assert "requires clinician privileges" in response.json()["detail"]

    def test_require_admin_role_success(self, client, mock_jwt_service):
        """Test that require_admin_role allows admins."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        mock_jwt_service.decode_token.return_value = {"sub": user_id, "role": "admin"}

        # Execute
    response = client.get(
    "/test/admin-only",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 200
    assert response.json() == {"user_id": user_id}

    def test_require_admin_role_clinician(self, client, mock_jwt_service):
        """Test that require_admin_role rejects clinicians."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        mock_jwt_service.decode_token.return_value = {"sub": user_id, "role": "clinician"}

        # Execute
    response = client.get(
    "/test/admin-only",
    headers={"Authorization": "Bearer test_token"}
    )

        # Verify
    assert response.status_code == 403
    assert "requires admin privileges" in response.json()["detail"]