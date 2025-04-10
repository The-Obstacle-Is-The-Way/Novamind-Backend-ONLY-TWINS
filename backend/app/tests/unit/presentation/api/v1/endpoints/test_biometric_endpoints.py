# -*- coding: utf-8 -*-
"""
Unit tests for biometric endpoints dependencies.

These tests verify that the biometric endpoints dependencies correctly
handle authentication and patient ID validation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

from app.domain.exceptions import AuthenticationError, AuthorizationError # Corrected exception names
from app.presentation.api.v1.endpoints.biometric_endpoints import (
    get_current_user_id,
    get_patient_id,
    get_current_user_role,
    require_clinician_role,
    require_admin_role
)


@pytest.fixture
def mock_jwt_service():
    """Create a mock JWT service."""
    service = MagicMock()
    service.decode_token = MagicMock()
    return service


@pytest.fixture
def app(mock_jwt_service):
    """Create a FastAPI test app with test endpoints."""
    app = FastAPI()
    
    # Override dependencies
    app.dependency_overrides[lambda: None] = lambda: mock_jwt_service
    
    # Test endpoints
    @app.get("/test/user-id")
    async def test_get_current_user_id(user_id: UUID = Depends(get_current_user_id)):
        return {"user_id": str(user_id)}
    
    @app.get("/test/patient/{patient_id}")
    async def test_get_patient_id(patient_id: UUID = Depends(get_patient_id)):
        return {"patient_id": str(patient_id)}
    
    @app.get("/test/user-role")
    async def test_get_current_user_role(role: str = Depends(get_current_user_role)):
        return {"role": role}
    
    @app.get("/test/clinician-only")
    async def test_require_clinician_role(
        _: None = Depends(require_clinician_role),
        user_id: UUID = Depends(get_current_user_id)
    ):
        return {"user_id": str(user_id)}
    
    @app.get("/test/admin-only")
    async def test_require_admin_role(
        _: None = Depends(require_admin_role),
        user_id: UUID = Depends(get_current_user_id)
    ):
        return {"user_id": str(user_id)}
    
    return app


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
        mock_jwt_service.decode_token.return_value = {}
        
        # Execute
        response = client.get(
            "/test/user-id",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify
        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]
    
    def test_get_current_user_id_authentication_exception(self, client, mock_jwt_service):
        """Test that get_current_user_id handles AuthenticationException."""
        # Setup
        mock_jwt_service.decode_token.side_effect = AuthenticationException("Invalid token")
        
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
        assert "Authentication error" in response.json()["detail"]
    
    def test_get_patient_id(self, client, mock_jwt_service):
        """Test that get_patient_id returns the patient ID from the path."""
        # Setup
        user_id = "00000000-0000-0000-0000-000000000001"
        patient_id = "12345678-1234-5678-1234-567812345678"
        mock_jwt_service.decode_token.return_value = {"sub": user_id}
        
        # Execute
        response = client.get(
            f"/test/patient/{patient_id}",
            headers={"Authorization": "Bearer test_token"}
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
        mock_jwt_service.decode_token.return_value = {}
        
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
        mock_jwt_service.decode_token.return_value = {"sub": user_id, "role": "patient"}
        
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