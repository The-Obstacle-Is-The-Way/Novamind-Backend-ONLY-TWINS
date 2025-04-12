"""Unit tests for Digital Twin API endpoints."""
import json
from uuid import UUID
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.domain.entities.digital_twin import DigitalTwin
from app.domain.entities.patient import Patient
from app.domain.value_objects.twin_status import TwinStatus
from app.application.dtos.digital_twin import DigitalTwinResponse, DigitalTwinCreateRequest


@pytest.fixture
def sample_twin():
    """Create a sample digital twin for testing."""
    return DigitalTwin(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        patient_id=UUID("00000000-0000-0000-0000-000000000002"),
        status=TwinStatus.ACTIVE,
        version="1.0.0",
        metadata={"model_type": "ensemble", "features": ["heart_rate", "steps", "sleep"]},
        created_by=UUID("00000000-0000-0000-0000-000000000003")
    )


@pytest.fixture
def sample_patient():
    """Create a sample patient for testing."""
    return Patient(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01",
        email="john.doe@example.com",
        phone="123-456-7890",
        active=True
    )


@pytest.fixture
def mock_jwt_auth():
    """Mock the JWT authentication."""
    # Assuming get_current_user_id exists in the endpoint's dependencies
    try:
        from app.presentation.api.dependencies.auth import get_current_user_id
        with patch(
            "app.presentation.api.dependencies.auth.get_current_user_id",
            return_value=UUID("00000000-0000-0000-0000-000000000001")
        ) as mock_auth:
            yield mock_auth
    except ImportError:
        print("Warning: get_current_user_id dependency not found for mocking.")
        yield None  # Yield None if dependency not found


@pytest.fixture
def mock_digital_twin_service():
    """Mock the digital twin service."""
    mock_service = MagicMock()
    
    # Configure common method returns
    mock_service.get_digital_twin.return_value = None  # Default, can be overridden in tests
    mock_service.create_digital_twin.return_value = None  # Default, can be overridden in tests
    
    # Patch the service in the dependency injection
    with patch(
        "app.presentation.api.dependencies.services.get_digital_twin_service",
        return_value=mock_service
    ):
        yield mock_service


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    # Import here to avoid circular imports
    from app.presentation.api.app import create_app
    
    app = create_app()
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app)


class TestDigitalTwinEndpoints:
    """Test suite for Digital Twin API endpoints."""
    
    def test_get_digital_twin(self, client, mock_digital_twin_service, sample_twin, mock_jwt_auth):
        """Test getting a digital twin by ID."""
        # Configure the mock service to return our sample twin
        mock_digital_twin_service.get_digital_twin.return_value = sample_twin
        
        # Make the request
    twin_id = str(sample_twin.id)
    response = client.get(f"/api/v1/digital-twins/{twin_id}")
        
        # Check response
    assert response.status_code == 200
        
        # Parse response JSON
    response_data = response.json()
    assert response_data["id"] == twin_id
    assert response_data["patient_id"] == str(sample_twin.patient_id)
    assert response_data["status"] == sample_twin.status.value
        
        # Verify service was called with the correct ID
    mock_digital_twin_service.get_digital_twin.assert_called_once_with(UUID(twin_id))
    
    def test_get_digital_twin_not_found(self, client, mock_digital_twin_service, mock_jwt_auth):
        """Test getting a non-existent digital twin returns 404."""
        # Configure the mock service to return None (not found)
        mock_digital_twin_service.get_digital_twin.return_value = None
        
        # Make the request
    twin_id = "00000000-0000-0000-0000-000000000099"  # Non-existent ID
    response = client.get(f"/api/v1/digital-twins/{twin_id}")
        
        # Check response
    assert response.status_code == 404
        
        # Verify service was called with the correct ID
    mock_digital_twin_service.get_digital_twin.assert_called_once_with(UUID(twin_id))
    
    def test_create_digital_twin(self, client, mock_digital_twin_service, sample_twin, mock_jwt_auth):
        """Test creating a new digital twin."""
        # Configure the mock service to return our sample twin
        mock_digital_twin_service.create_digital_twin.return_value = sample_twin
        
        # Create a request body
    request_data = {
    "patient_id": str(sample_twin.patient_id),
    "metadata": sample_twin.metadata
    }
        
        # Make the request
    response = client.post(
    "/api/v1/digital-twins",
    json=request_data
    )
        
        # Check response
    assert response.status_code == 201
        
        # Parse response JSON
    response_data = response.json()
    assert response_data["id"] == str(sample_twin.id)
    assert response_data["patient_id"] == str(sample_twin.patient_id)
    assert response_data["status"] == sample_twin.status.value