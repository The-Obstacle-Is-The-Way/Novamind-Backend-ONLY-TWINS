"""Unit tests for digital twin API endpoints."""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta
import uuid

from app.main import app
from app.domain.entities.biometric_twin_enhanced import BiometricTwin, BiometricDataPoint, BiometricType, BiometricSource
from app.domain.value_objects.physiological_ranges import PhysiologicalRange


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_digital_twin_service():
    """Create a mock digital twin service."""
    mock_service = MagicMock()
    
    # Setup async method mocks
    mock_service.get_digital_twin = AsyncMock()
    mock_service.update_digital_twin = AsyncMock()
    mock_service.add_biometric_data = AsyncMock()
    mock_service.get_biometric_history = AsyncMock()
    
    return mock_service


@pytest.fixture
def sample_digital_twin():
    """Create a sample digital twin for testing."""
    patient_id = "patient-123"
    timestamp = datetime.now()
    twin_id = str(uuid.uuid4())
    
    # Create HR data
    hr_data_points = [
        BiometricDataPoint(
            timestamp=timestamp - timedelta(days=2),
            value=72.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        ),
        BiometricDataPoint(
            timestamp=timestamp - timedelta(days=1),
            value=75.0,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        ),
        BiometricDataPoint(
            timestamp=timestamp,
            value=70.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
    ]
    
    # This is a simplified version for testing
    return {
        "id": twin_id,
        "patient_id": patient_id,
        "timeseries_data": {
            "heart_rate": {
                "biometric_type": "heart_rate",
                "unit": "bpm",
                "data_points": [point.to_dict() for point in hr_data_points],
                "physiological_range": {
                    "min": 60,
                    "max": 100,
                    "critical_min": 40,
                    "critical_max": 160
                }
            }
        },
        "created_at": (timestamp - timedelta(days=30)).isoformat(),
        "updated_at": timestamp.isoformat()
    }


class TestDigitalTwinEndpoints:
    """Test suite for Digital Twin API endpoints."""

    @patch("app.presentation.api.dependencies.get_digital_twin_service")
    async def test_get_digital_twin(
        self, mock_get_service, test_client, mock_digital_twin_service, sample_digital_twin
    ):
        """Test getting a digital twin."""
        # Setup mocks
        mock_get_service.return_value = mock_digital_twin_service
        mock_digital_twin_service.get_digital_twin.return_value = sample_digital_twin
        
        # Make request
        response = test_client.get(f"/api/v1/patients/{sample_digital_twin['patient_id']}/digital-twin")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_digital_twin["id"]
        assert data["patient_id"] == sample_digital_twin["patient_id"]
        assert "timeseries_data" in data
        assert "heart_rate" in data["timeseries_data"]
    
    @patch("app.presentation.api.dependencies.get_digital_twin_service")
    async def test_get_digital_twin_not_found(
        self, mock_get_service, test_client, mock_digital_twin_service
    ):
        """Test getting a non-existent digital twin."""
        # Setup mocks
        mock_get_service.return_value = mock_digital_twin_service
        mock_digital_twin_service.get_digital_twin.return_value = None
        
        # Make request
        patient_id = "nonexistent-patient"
        response = test_client.get(f"/api/v1/patients/{patient_id}/digital-twin")
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch("app.presentation.api.dependencies.get_digital_twin_service")
    async def test_add_biometric_data(
        self, mock_get_service, test_client, mock_digital_twin_service, sample_digital_twin
    ):
        """Test adding biometric data to a digital twin."""
        # Setup mocks
        mock_get_service.return_value = mock_digital_twin_service
        mock_digital_twin_service.add_biometric_data.return_value = True
        
        # Prepare request data
        patient_id = sample_digital_twin["patient_id"]
        data = {
            "biometric_type": "heart_rate",
            "value": 78.5,
            "source": "wearable",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"device": "fitbit", "activity": "resting"}
        }
        
        # Make request
        response = test_client.post(
            f"/api/v1/patients/{patient_id}/digital-twin/biometrics",
            json=data
        )
        
        # Check response
        assert response.status_code == status.HTTP_201_CREATED
        assert mock_digital_twin_service.add_biometric_data.called
        call_args = mock_digital_twin_service.add_biometric_data.call_args[0]
        assert call_args[0] == patient_id
        assert call_args[1] == data["biometric_type"]
    
    @patch("app.presentation.api.dependencies.get_digital_twin_service")
    async def test_get_biometric_history(
        self, mock_get_service, test_client, mock_digital_twin_service, sample_digital_twin
    ):
        """Test getting biometric history for a patient."""
        # Setup mocks
        mock_get_service.return_value = mock_digital_twin_service
        
        # Extract heart rate data points for mock return
        hr_data = sample_digital_twin["timeseries_data"]["heart_rate"]["data_points"]
        mock_digital_twin_service.get_biometric_history.return_value = hr_data
        
        # Make request
        patient_id = sample_digital_twin["patient_id"]
        biometric_type = "heart_rate"
        response = test_client.get(
            f"/api/v1/patients/{patient_id}/digital-twin/biometrics/{biometric_type}"
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(hr_data)
        
        # Check call arguments
        mock_digital_twin_service.get_biometric_history.assert_called_once_with(
            patient_id, biometric_type, None, None
        )
    
    @patch("app.presentation.api.dependencies.get_digital_twin_service")
    async def test_get_biometric_history_with_timerange(
        self, mock_get_service, test_client, mock_digital_twin_service, sample_digital_twin
    ):
        """Test getting biometric history with time range filters."""
        # Setup mocks
        mock_get_service.return_value = mock_digital_twin_service
        
        # Extract heart rate data points for mock return
        hr_data = sample_digital_twin["timeseries_data"]["heart_rate"]["data_points"]
        mock_digital_twin_service.get_biometric_history.return_value = hr_data[:1]  # Return just one point
        
        # Make request with time range
        patient_id = sample_digital_twin["patient_id"]
        biometric_type = "heart_rate"
        start_time = (datetime.now() - timedelta(days=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        response = test_client.get(
            f"/api/v1/patients/{patient_id}/digital-twin/biometrics/{biometric_type}",
            params={"start_time": start_time, "end_time": end_time}
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        # Check call arguments
        mock_digital_twin_service.get_biometric_history.assert_called_once_with(
            patient_id, biometric_type, start_time, end_time
        )
    
    @patch("app.presentation.api.dependencies.get_digital_twin_service")
    async def test_get_latest_biometrics(
        self, mock_get_service, test_client, mock_digital_twin_service, sample_digital_twin
    ):
        """Test getting latest biometric values."""
        # Setup mocks
        mock_get_service.return_value = mock_digital_twin_service
        
        # Create latest values mock
        latest_values = {
            "heart_rate": {
                "timestamp": datetime.now().isoformat(),
                "value": 72.5,
                "source": "wearable",
                "metadata": {"device": "fitbit"}
            },
            "blood_pressure": {
                "timestamp": datetime.now().isoformat(),
                "value": {"systolic": 120, "diastolic": 80},
                "source": "clinical",
                "metadata": {"position": "sitting"}
            }
        }
        mock_digital_twin_service.get_latest_biometrics.return_value = latest_values
        
        # Make request
        patient_id = sample_digital_twin["patient_id"]
        response = test_client.get(
            f"/api/v1/patients/{patient_id}/digital-twin/biometrics/latest"
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "heart_rate" in data
        assert "blood_pressure" in data
        assert data["heart_rate"]["value"] == 72.5
        assert data["blood_pressure"]["value"] == {"systolic": 120, "diastolic": 80}