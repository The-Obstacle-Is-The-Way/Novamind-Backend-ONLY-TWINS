"""Unit tests for digital twin API endpoints."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status, HTTPException
from fastapi.testclient import TestClient
import uuid
import json
from datetime import datetime, timedelta

from app.presentation.api.v1.endpoints.digital_twin import (
    router, 
    get_digital_twin, 
    get_all_digital_twins,
    create_digital_twin,
    update_digital_twin,
    get_biometric_data,
    add_biometric_data
)
from app.presentation.api.v1.endpoints.dependencies import get_current_user, get_current_active_user
from app.application.services.digital_twin_service import DigitalTwinService
from app.domain.entities.biometric_twin import (
    BiometricTwin, 
    BiometricTimeseriesData,
    BiometricDataPoint,
    BiometricType,
    BiometricSource
)
from app.domain.entities.patient import Patient
from app.domain.entities.user import User
from app.domain.value_objects.physiological_ranges import PhysiologicalRange


@pytest.fixture
def mock_digital_twin_service():
    """Create a mock digital twin service."""
    service = MagicMock(spec=DigitalTwinService)
    
    # Configure some default behaviors
    service.get_digital_twin.return_value = BiometricTwin(
        id=str(uuid.uuid4()),
        patient_id="p12345",
        timeseries_data={},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    service.get_all_digital_twins.return_value = [
        BiometricTwin(
            id=str(uuid.uuid4()),
            patient_id="p12345",
            timeseries_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        BiometricTwin(
            id=str(uuid.uuid4()),
            patient_id="p67890",
            timeseries_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    return service


@pytest.fixture
def mock_current_user():
    """Create a mock current user."""
    return User(
        id=str(uuid.uuid4()),
        username="testdoctor",
        email="doctor@example.com",
        full_name="Dr. Test",
        disabled=False,
        role="doctor",
        permissions=["read:patients", "write:patients"]
    )


@pytest.fixture
def app_with_dependencies(mock_digital_twin_service, mock_current_user):
    """Create a FastAPI app with the router and mocked dependencies."""
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Override dependencies
    async def mock_get_current_user():
        return mock_current_user
    
    async def mock_get_digital_twin_service():
        return mock_digital_twin_service
    
    # Apply overrides to the router
    app.include_router(
        router,
        prefix="/api/v1/digital-twins",
        dependencies=[],
    )
    
    app.dependency_overrides[get_current_active_user] = mock_get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # Add override for the digital twin service
    for route in router.routes:
        if hasattr(route, "dependencies"):
            for dep_index, dep in enumerate(route.dependencies):
                if dep.dependency.__name__ == "get_digital_twin_service":
                    route.dependencies[dep_index].dependency = mock_get_digital_twin_service
    
    return app


@pytest.fixture
def client(app_with_dependencies):
    """Create a test client."""
    return TestClient(app_with_dependencies)


@pytest.fixture
def sample_biometric_data():
    """Create sample biometric data for testing."""
    now = datetime.now()
    
    heart_rate_data = BiometricTimeseriesData(
        biometric_type=BiometricType.HEART_RATE,
        unit="bpm",
        data_points=[
            BiometricDataPoint(
                timestamp=now - timedelta(days=1),
                value=72.5,
                source=BiometricSource.WEARABLE,
                metadata={"device": "fitbit"}
            ),
            BiometricDataPoint(
                timestamp=now,
                value=75.2,
                source=BiometricSource.WEARABLE,
                metadata={"device": "fitbit"}
            )
        ],
        physiological_range=PhysiologicalRange(min=60, max=100)
    )
    
    return heart_rate_data


class TestDigitalTwinEndpoints:
    """Test suite for digital twin API endpoints."""
    
    def test_get_digital_twin(self, client, mock_digital_twin_service):
        """Test getting a digital twin by ID."""
        twin_id = str(uuid.uuid4())
        
        # Configure mock to return a specific digital twin
        mock_twin = BiometricTwin(
            id=twin_id,
            patient_id="p12345",
            timeseries_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_digital_twin_service.get_digital_twin.return_value = mock_twin
        
        # Make request
        response = client.get(f"/api/v1/digital-twins/{twin_id}")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == twin_id
        assert data["patient_id"] == "p12345"
        
        # Verify service was called
        mock_digital_twin_service.get_digital_twin.assert_called_once_with(twin_id)
    
    def test_get_digital_twin_not_found(self, client, mock_digital_twin_service):
        """Test getting a non-existent digital twin."""
        twin_id = str(uuid.uuid4())
        
        # Configure mock to return None
        mock_digital_twin_service.get_digital_twin.return_value = None
        
        # Make request
        response = client.get(f"/api/v1/digital-twins/{twin_id}")
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_get_all_digital_twins(self, client, mock_digital_twin_service):
        """Test getting all digital twins."""
        # Make request
        response = client.get("/api/v1/digital-twins/")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # Two mock twins from fixture
        
        # Verify service was called
        mock_digital_twin_service.get_all_digital_twins.assert_called_once()
    
    def test_create_digital_twin(self, client, mock_digital_twin_service):
        """Test creating a new digital twin."""
        # Set up request data
        patient_id = "p12345"
        new_twin_id = str(uuid.uuid4())
        
        # Configure mock to return the created twin
        mock_digital_twin_service.create_digital_twin.return_value = BiometricTwin(
            id=new_twin_id,
            patient_id=patient_id,
            timeseries_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Make request
        response = client.post(
            "/api/v1/digital-twins/",
            json={"patient_id": patient_id}
        )
        
        # Check response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == new_twin_id
        assert data["patient_id"] == patient_id
        
        # Verify service was called
        mock_digital_twin_service.create_digital_twin.assert_called_once_with(patient_id)
    
    def test_update_digital_twin(self, client, mock_digital_twin_service, sample_biometric_data):
        """Test updating a digital twin."""
        twin_id = str(uuid.uuid4())
        
        # Configure mock to return the updated twin
        updated_twin = BiometricTwin(
            id=twin_id,
            patient_id="p12345",
            timeseries_data={
                BiometricType.HEART_RATE: sample_biometric_data
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_digital_twin_service.update_digital_twin.return_value = updated_twin
        
        # Make request with serialized biometric data
        update_data = {
            "timeseries_data": {
                "heart_rate": sample_biometric_data.to_dict()
            }
        }
        
        response = client.put(
            f"/api/v1/digital-twins/{twin_id}",
            json=update_data
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == twin_id
        assert "heart_rate" in data["timeseries_data"]
        
        # Verify service was called
        mock_digital_twin_service.update_digital_twin.assert_called_once()
    
    def test_get_biometric_data(self, client, mock_digital_twin_service, sample_biometric_data):
        """Test getting biometric data for a specific type."""
        twin_id = str(uuid.uuid4())
        biometric_type = BiometricType.HEART_RATE
        
        # Configure mock to return biometric data
        mock_digital_twin_service.get_biometric_data.return_value = sample_biometric_data
        
        # Make request
        response = client.get(f"/api/v1/digital-twins/{twin_id}/biometric/{biometric_type.value}")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["biometric_type"] == biometric_type.value
        assert data["unit"] == "bpm"
        assert len(data["data_points"]) == 2
        
        # Verify service was called
        mock_digital_twin_service.get_biometric_data.assert_called_once_with(
            twin_id, biometric_type
        )
    
    def test_add_biometric_data(self, client, mock_digital_twin_service, sample_biometric_data):
        """Test adding biometric data to a digital twin."""
        twin_id = str(uuid.uuid4())
        
        # Configure mock
        mock_digital_twin_service.add_biometric_data.return_value = BiometricTwin(
            id=twin_id,
            patient_id="p12345",
            timeseries_data={
                BiometricType.HEART_RATE: sample_biometric_data
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Make request
        response = client.post(
            f"/api/v1/digital-twins/{twin_id}/biometric",
            json=sample_biometric_data.to_dict()
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == twin_id
        assert "heart_rate" in data["timeseries_data"]
        
        # Verify service was called
        mock_digital_twin_service.add_biometric_data.assert_called_once()
    
    def test_add_biometric_data_invalid(self, client, mock_digital_twin_service):
        """Test adding invalid biometric data."""
        twin_id = str(uuid.uuid4())
        
        # Invalid data (missing required fields)
        invalid_data = {
            "biometric_type": "heart_rate",
            # Missing unit and data_points
        }
        
        # Make request
        response = client.post(
            f"/api/v1/digital-twins/{twin_id}/biometric",
            json=invalid_data
        )
        
        # Check response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Service should not be called with invalid data
        mock_digital_twin_service.add_biometric_data.assert_not_called()


@patch("app.presentation.api.v1.endpoints.digital_twin.DigitalTwinService")
class TestDigitalTwinEndpointsDirect:
    """Test suite for direct calling of the endpoint functions."""
    
    @pytest.mark.asyncio
    async def test_get_digital_twin_direct(self, mock_service_class):
        """Test get_digital_twin directly without the router."""
        # Setup
        twin_id = str(uuid.uuid4())
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Test the successful case
        mock_service.get_digital_twin.return_value = BiometricTwin(
            id=twin_id,
            patient_id="p12345",
            timeseries_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await get_digital_twin(twin_id, mock_service)
        assert result.id == twin_id
        
        # Test the not found case
        mock_service.get_digital_twin.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_digital_twin(twin_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_get_all_digital_twins_direct(self, mock_service_class):
        """Test get_all_digital_twins directly."""
        # Setup
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Configure mock to return some digital twins
        mock_twins = [
            BiometricTwin(
                id=str(uuid.uuid4()),
                patient_id="p12345",
                timeseries_data={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BiometricTwin(
                id=str(uuid.uuid4()),
                patient_id="p67890",
                timeseries_data={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_service.get_all_digital_twins.return_value = mock_twins
        
        # Call function
        result = await get_all_digital_twins(mock_service)
        
        # Check result
        assert len(result) == 2
        assert result[0].id == mock_twins[0].id
        assert result[1].id == mock_twins[1].id
    
    @pytest.mark.asyncio
    async def test_create_digital_twin_direct(self, mock_service_class):
        """Test create_digital_twin directly."""
        # Setup
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        patient_id = "p12345"
        
        # Configure mock
        new_twin = BiometricTwin(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            timeseries_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_service.create_digital_twin.return_value = new_twin
        
        # Call function
        from app.presentation.api.v1.schemas.digital_twin import DigitalTwinCreate
        result = await create_digital_twin(
            DigitalTwinCreate(patient_id=patient_id),
            mock_service
        )
        
        # Check result
        assert result.id == new_twin.id
        assert result.patient_id == patient_id
        
        # Verify service called
        mock_service.create_digital_twin.assert_called_once_with(patient_id)