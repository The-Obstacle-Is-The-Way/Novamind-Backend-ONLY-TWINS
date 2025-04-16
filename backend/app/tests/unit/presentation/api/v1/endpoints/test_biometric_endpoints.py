# -*- coding: utf-8 -*-
"""
Unit tests for biometric endpoints dependencies.

These tests verify that the biometric endpoints dependencies correctly
handle authentication and patient ID validation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, Generator # Added Generator

import pytest
from fastapi import FastAPI, Depends, HTTPException, status  # Added status
from fastapi.testclient import TestClient

# Corrected exception import syntax
from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
)  # Removed extra parenthesis after 'import'

# Assuming these dependencies exist in the specified path
# Corrected dependency import syntax
from app.presentation.api.dependencies.auth import get_current_user # Removed get_current_user_id, get_current_user_role
from app.domain.entities.biometric_twin import BiometricDataPoint # Import corrected
# Correct import for the dependency function
from app.presentation.api.v1.endpoints.biometric_endpoints import (
    get_patient_id,
    require_clinician_role,
    require_admin_role,
    # router, # Removed - Endpoint modules typically don't export routers directly
    # get_biometric_twin_service, # Moved import to dependencies
    # BiometricDataBatchRequest, # This is a schema, should not be imported from endpoint
    # BiometricDataResponse # This is also a schema
)
# Import service dependencies from the correct location
from app.presentation.api.dependencies.services import get_digital_twin_service # Corrected service name
# Import schema from the correct location
from app.presentation.api.v1.schemas.biometric_schemas import BiometricDataPointBatchCreate, BiometricDataPointResponse

# Assuming JWTService exists for mocking
# from app.infrastructure.security.jwt_service import JWTService
# Mocking JWTService directly as its location might still be in flux

@pytest.fixture
def mock_jwt_service():
    """Create a mock JWT service."""
    service = MagicMock() # Using simple MagicMock for now
    service.decode_token = AsyncMock() # Make decode_token async
    # Add other methods if needed by dependencies
    return service

@pytest.fixture
def app(mock_jwt_service): # Removed redundant decorator
    """Create a FastAPI test app with test endpoints."""
    app_instance = FastAPI()

    # --- Mock Dependency Setup --- 
    # Define override functions that return the mock service
    def override_get_jwt_service():
        return mock_jwt_service
    
    # How dependencies are provided to Depends() matters.
    # If get_current_user_id etc. accept jwt_service as kwarg:
    # You might override a factory function that provides jwt_service.
    # Example: Assuming a dependency function get_jwt_service exists
    # try:
    #     from app.presentation.api.dependencies.auth import get_jwt_service 
    #     app_instance.dependency_overrides[get_jwt_service] = override_get_jwt_service
    # except ImportError:
    #     print("Warning: Could not import get_jwt_service to override.")
    # Alternatively, if dependencies are classes needing injection, override those.
    
    # Define test endpoints using the dependencies
    @app_instance.get("/test/user-id")
    async def test_get_current_user_id_endpoint(
        current_user: User = Depends(get_current_user) # Depend on get_current_user
    ):
        return {"user_id": str(current_user.id)} # Extract ID from user object

    @app_instance.get("/test/patient/{patient_id}")
    async def test_get_patient_id_endpoint(
        patient_id: UUID = Depends(get_patient_id)
    ):
        return {"patient_id": str(patient_id)}

    @app_instance.get("/test/user-role")
    async def test_get_current_user_role_endpoint(
        current_user: User = Depends(get_current_user) # Depend on get_current_user
    ):
        return {"role": current_user.role} # Extract role from user object

    @app_instance.get("/test/clinician-only")
    async def test_require_clinician_role_endpoint(
        _: None = Depends(require_clinician_role),
        current_user: User = Depends(get_current_user) # Depend on get_current_user
    ):
        return {"user_id": str(current_user.id)} # Return user_id for assertion

    @app_instance.get("/test/admin-only")
    async def test_require_admin_role_endpoint(
        _: None = Depends(require_admin_role),
        current_user: User = Depends(get_current_user) # Depend on get_current_user
    ):
        return {"user_id": str(current_user.id)} # Return user_id for assertion

    return app_instance

@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]: # Corrected type hint
    """Create a test client for the FastAPI app."""
    # Need to use TestClient context manager if lifespan events are involved
    with TestClient(app) as test_client:
        yield test_client

# Correctly indented class definition
@pytest.mark.db_required() # Assuming this marker is correctly defined elsewhere
class TestBiometricEndpointsDependencies:
    """Tests for the biometric endpoints dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_user_id_success(self, client: TestClient, mock_jwt_service):
        """Test that get_current_user_id returns the user ID from the token."""
        user_id = uuid4()
        # Mock the decode_token method on the *instance* passed to the fixture
        mock_jwt_service.decode_token.return_value = {
            "sub": str(user_id),
            "role": "clinician",
        }

        # Use the client fixture, which wraps the app
        response = client.get(
            "/test/user-id", headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"user_id": str(user_id)}
        mock_jwt_service.decode_token.assert_called_once_with("test_token")

    @pytest.mark.asyncio
    async def test_get_current_user_id_missing_sub(
        self, client: TestClient, mock_jwt_service):
        """Test that get_current_user_id raises an error if sub is missing."""
        mock_jwt_service.decode_token.return_value = {"role": "clinician"}  # No 'sub'

        response = client.get(
            "/test/user-id", headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Check the detail message structure based on actual exception handling
        assert "Invalid authentication credentials" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_get_current_user_id_authentication_exception(
        self, client: TestClient, mock_jwt_service):
        """Test that get_current_user_id handles AuthenticationError."""
        mock_jwt_service.decode_token.side_effect = AuthenticationError("Invalid token")

        response = client.get(
            "/test/user-id", headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_get_current_user_id_generic_exception(
        self, client: TestClient, mock_jwt_service):
        """Test that get_current_user_id handles generic exceptions."""
        mock_jwt_service.decode_token.side_effect = Exception("Unexpected error")

        response = client.get(
            "/test/user-id", headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication error" in response.json().get("detail", "") # Assuming a generic message

    @pytest.mark.asyncio
    async def test_get_patient_id(self, client: TestClient, mock_jwt_service):
        """Test that get_patient_id returns the patient ID from the path."""
        patient_id = uuid4()
        # Mock token needed if the endpoint itself requires authentication
        mock_jwt_service.decode_token.return_value = {
            "sub": str(uuid4()), "role": "clinician",
        }  

        response = client.get(
            f"/test/patient/{patient_id}",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        assert response.json() == {"patient_id": str(patient_id)}

    @pytest.mark.asyncio
    async def test_get_current_user_role_success(
        self, client: TestClient, mock_jwt_service):
        """Test that get_current_user_role returns the role from the token."""
        mock_jwt_service.decode_token.return_value = {
            "sub": str(uuid4()),
            "role": "admin",
        }

        response = client.get(
            "/test/user-role", headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"role": "admin"}
        
    # ... (Add tests for get_current_user_role_missing_role) ...

    @pytest.mark.asyncio
    async def test_require_clinician_role_success(
        self, client: TestClient, mock_jwt_service):
        """Test clinician-only endpoint access with clinician role."""
        user_id = uuid4()
        mock_jwt_service.decode_token.return_value = {
            "sub": str(user_id),
            "role": "clinician",
        }
        response = client.get(
            "/test/clinician-only", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        assert response.json() == {"user_id": str(user_id)}

    @pytest.mark.asyncio
    async def test_require_clinician_role_admin(
        self, client: TestClient, mock_jwt_service):
        """Test clinician-only endpoint access with admin role (should also pass)."""
        user_id = uuid4()
        mock_jwt_service.decode_token.return_value = {
            "sub": str(user_id),
            "role": "admin",
        }
        response = client.get(
            "/test/clinician-only", headers={"Authorization": "Bearer test_token"}
        )
        # Assuming admin also passes clinician check
        assert response.status_code == 200 
        assert response.json() == {"user_id": str(user_id)}

    @pytest.mark.asyncio
    async def test_require_clinician_role_patient(
        self, client: TestClient, mock_jwt_service):
        """Test clinician-only endpoint access denial with patient role."""
        mock_jwt_service.decode_token.return_value = {
            "sub": str(uuid4()),
            "role": "patient",
        }
        response = client.get(
            "/test/clinician-only", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "clinician role required" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_require_admin_role_success(self, client: TestClient, mock_jwt_service):
        """Test admin-only endpoint access with admin role."""
        user_id = uuid4()
        mock_jwt_service.decode_token.return_value = {
            "sub": str(user_id),
            "role": "admin",
        }
        response = client.get(
            "/test/admin-only", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        assert response.json() == {"user_id": str(user_id)}

    @pytest.mark.asyncio
    async def test_require_admin_role_clinician(
        self, client: TestClient, mock_jwt_service):
        """Test admin-only endpoint access denial with clinician role."""
        mock_jwt_service.decode_token.return_value = {
            "sub": str(uuid4()),
            "role": "clinician",
        }
        response = client.get(
            "/test/admin-only", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin role required" in response.json().get("detail", "")

    # Add tests for missing role in token for require_ role dependencies
    # Add tests for invalid token / authentication errors
