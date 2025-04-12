"""Unit tests for Digital Twin API endpoints."""

import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app.presentation.api.v1.digital_twin_endpoints import router


# Setup test app
app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


@pytest.fixture
def mock_digital_twin_service(mocker: MockerFixture):
    """Create a mock digital twin service."""
    service_mock = AsyncMock()
    mocker.patch(
        "app.presentation.api.dependencies.get_digital_twin_service",
        return_value=service_mock,
    )
    return service_mock


@pytest.fixture
def sample_twin_data():
    """Create sample twin data for testing."""
    now = datetime.now()
    return {
        "id": "12345678-1234-5678-1234-567812345678",
        "patient_id": "patient-123",
        "timeseries_data": {
            "heart_rate": {
                "biometric_type": "heart_rate",
                "unit": "bpm",
                "data_points": [
                    {
                        "timestamp": (now - timedelta(days=1)).isoformat(),
                        "value": 72.5,
                        "source": "wearable",
                        "metadata": {"device": "fitbit"},
                    },
                    {
                        "timestamp": now.isoformat(),
                        "value": 75.0,
                        "source": "wearable",
                        "metadata": {"device": "fitbit"},
                    },
                ],
                "physiological_range": {
                    "min": 60.0,
                    "max": 100.0,
                    "critical_min": 40.0,
                    "critical_max": 140.0,
                },
            }
        },
        "created_at": (now - timedelta(days=30)).isoformat(),
        "updated_at": now.isoformat(),
    }


@pytest.fixture
def sample_biometric_data():
    """Create sample biometric data for testing."""
    return {
        "biometric_type": "heart_rate",
        "value": 72.5,
        "source": "wearable",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"device": "fitbit", "activity": "resting"},
    }


@pytest.fixture
def sample_abnormal_values():
    """Create sample abnormal values for testing."""
    now = datetime.now()
    return {
        "heart_rate": [
            {
                "timestamp": now.isoformat(),
                "value": 110.5,
                "source": "wearable",
                "metadata": {"device": "fitbit", "activity": "exercise"},
            }
        ]
    }


@pytest.fixture
def sample_critical_values():
    """Create sample critical values for testing."""
    now = datetime.now()
    return {
        "heart_rate": [
            {
                "timestamp": now.isoformat(),
                "value": 150.0,
                "source": "wearable",
                "metadata": {"device": "fitbit", "activity": "exercise"},
            }
        ]
    }


@pytest.fixture
def sample_latest_biometrics():
    """Create sample latest biometrics for testing."""
    now = datetime.now()
    return {
        "heart_rate": {
            "timestamp": now.isoformat(),
            "value": 75.0,
            "source": "wearable",
            "metadata": {"device": "fitbit"},
        },
        "blood_pressure": {
            "timestamp": now.isoformat(),
            "value": {"systolic": 120, "diastolic": 80},
            "source": "clinical",
            "metadata": {"position": "sitting"},
        },
    }


class TestDigitalTwinEndpoints:
    """Tests for the digital twin endpoints."""

    def test_create_digital_twin(self, mock_digital_twin_service, sample_twin_data):
        """Test creating a digital twin."""
        # Configure mock
        mock_digital_twin_service.create_digital_twin.return_value = sample_twin_data

        # Make request
        response = client.post(
            "/api/v1/digital-twins", json={"patient_id": "patient-123"}
        )

        # Check response
        assert response.status_code == 201
        assert response.json() == sample_twin_data

        # Verify service called correctly
        mock_digital_twin_service.create_digital_twin.assert_called_once_with(
            "patient-123"
        )

    def test_create_digital_twin_error(self, mock_digital_twin_service):
        """Test error handling when creating a digital twin fails."""
        # Configure mock
        mock_digital_twin_service.create_digital_twin.return_value = None

        # Make request
        response = client.post(
            "/api/v1/digital-twins", json={"patient_id": "patient-123"}
        )

        # Check response
        assert response.status_code == 500
        assert "Failed to create digital twin" in response.json()["detail"]

    def test_get_digital_twin(self, mock_digital_twin_service, sample_twin_data):
        """Test getting a digital twin."""
        # Configure mock
        mock_digital_twin_service.get_digital_twin.return_value = sample_twin_data

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-123")

        # Check response
        assert response.status_code == 200
        assert response.json() == sample_twin_data

        # Verify service called correctly
        mock_digital_twin_service.get_digital_twin.assert_called_once_with(
            "patient-123"
        )

    def test_get_digital_twin_not_found(self, mock_digital_twin_service):
        """Test handling when a digital twin is not found."""
        # Configure mock
        mock_digital_twin_service.get_digital_twin.return_value = None

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-456")

        # Check response
        assert response.status_code == 404
        assert "Digital twin not found" in response.json()["detail"]

        def test_get_digital_twin_summary(
        self, mock_digital_twin_service, sample_twin_data, sample_latest_biometrics
    ):
        """Test getting a digital twin summary."""
        # Configure mocks
        mock_digital_twin_service.get_digital_twin.return_value = sample_twin_data
        mock_digital_twin_service.get_latest_biometrics.return_value = (
            sample_latest_biometrics
        )

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-123/summary")

        # Check response
        assert response.status_code == 200
        assert response.json()["id"] == sample_twin_data["id"]
        assert response.json()["patient_id"] == "patient-123"
        assert response.json()["latest_readings"] == sample_latest_biometrics
        assert response.json()["updated_at"] == sample_twin_data["updated_at"]

        # Verify service called correctly
        mock_digital_twin_service.get_digital_twin.assert_called_once_with(
            "patient-123"
        )
        mock_digital_twin_service.get_latest_biometrics.assert_called_once_with(
            "patient-123"
        )

    def test_add_biometric_data(self, mock_digital_twin_service, sample_biometric_data):
        """Test adding biometric data."""
        # Configure mock
        mock_digital_twin_service.add_biometric_data.return_value = True

        # Make request
        response = client.post(
            "/api/v1/digital-twins/patient/patient-123/biometrics",
            json=sample_biometric_data,
        )

        # Check response
        assert response.status_code == 201
        assert response.json()["status"] == "success"

        # Verify service called correctly
        mock_digital_twin_service.add_biometric_data.assert_called_once_with(
            patient_id="patient-123",
            biometric_type=sample_biometric_data["biometric_type"],
            value=sample_biometric_data["value"],
            source=sample_biometric_data["source"],
            timestamp=sample_biometric_data["timestamp"],
            metadata=sample_biometric_data["metadata"],
        )

    def test_add_biometric_data_error(
        self, mock_digital_twin_service, sample_biometric_data
    ):
        """Test error handling when adding biometric data fails."""
        # Configure mock
        mock_digital_twin_service.add_biometric_data.return_value = False

        # Make request
        response = client.post(
            "/api/v1/digital-twins/patient/patient-123/biometrics",
            json=sample_biometric_data,
        )

        # Check response
        assert response.status_code == 500
        assert "Failed to add biometric data" in response.json()["detail"]

    def test_get_biometric_history(self, mock_digital_twin_service):
        """Test getting biometric history."""
        # Sample history data
        history_data = [
            {
                "timestamp": datetime.now().isoformat(),
                "value": 72.5,
                "source": "wearable",
                "metadata": {"device": "fitbit"},
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "value": 68.0,
                "source": "wearable",
                "metadata": {"device": "fitbit"},
            },
        ]

        # Configure mock
        mock_digital_twin_service.get_biometric_history.return_value = history_data

        # Make request
        response = client.get(
            "/api/v1/digital-twins/patient/patient-123/biometrics/heart_rate"
        )

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == history_data
        assert response.json()["count"] == 2

        # Verify service called correctly
        mock_digital_twin_service.get_biometric_history.assert_called_once_with(
            patient_id="patient-123",
            biometric_type="heart_rate",
            start_time=None,
            end_time=None,
        )

    def test_get_biometric_history_with_time_range(self, mock_digital_twin_service):
        """Test getting biometric history with time range filters."""
        # Sample history data
        history_data = [
            {
                "timestamp": datetime.now().isoformat(),
                "value": 72.5,
                "source": "wearable",
                "metadata": {"device": "fitbit"},
            }
        ]

        # Configure mock
        mock_digital_twin_service.get_biometric_history.return_value = history_data

        # Make request with query parameters
        start_time = (datetime.now() - timedelta(days=1)).isoformat()
        end_time = datetime.now().isoformat()

        response = client.get(
            f"/api/v1/digital-twins/patient/patient-123/biometrics/heart_rate",
            params={"start_time": start_time, "end_time": end_time},
        )

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == history_data
        assert response.json()["count"] == 1

        # Verify service called correctly
        mock_digital_twin_service.get_biometric_history.assert_called_once()
        call_args = mock_digital_twin_service.get_biometric_history.call_args[1]
        assert call_args["patient_id"] == "patient-123"
        assert call_args["biometric_type"] == "heart_rate"
        # We don't check the exact values because the ISO format may have microseconds differences
        assert call_args["start_time"] is not None
        assert call_args["end_time"] is not None

    def test_get_biometric_history_empty(self, mock_digital_twin_service):
        """Test getting empty biometric history."""
        # Configure mock
        mock_digital_twin_service.get_biometric_history.return_value = []

        # Make request
        response = client.get(
            "/api/v1/digital-twins/patient/patient-123/biometrics/heart_rate"
        )

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == []
        assert response.json()["count"] == 0

    def test_get_abnormal_values(
        self, mock_digital_twin_service, sample_abnormal_values
    ):
        """Test getting abnormal values."""
        # Configure mock
        mock_digital_twin_service.detect_abnormal_values.return_value = (
            sample_abnormal_values
        )

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-123/abnormal")

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == sample_abnormal_values
        assert response.json()["count"] == 1  # One abnormal value

        # Verify service called correctly
        mock_digital_twin_service.detect_abnormal_values.assert_called_once_with(
            "patient-123"
        )

    def test_get_abnormal_values_empty(self, mock_digital_twin_service):
        """Test getting empty abnormal values."""
        # Configure mock
        mock_digital_twin_service.detect_abnormal_values.return_value = {}

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-123/abnormal")

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == {}
        assert response.json()["count"] == 0

        def test_get_critical_values(
        self, mock_digital_twin_service, sample_critical_values
    ):
        """Test getting critical values."""
        # Configure mock
        mock_digital_twin_service.detect_critical_values.return_value = (
            sample_critical_values
        )

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-123/critical")

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == sample_critical_values
        assert response.json()["count"] == 1  # One critical value

        # Verify service called correctly
        mock_digital_twin_service.detect_critical_values.assert_called_once_with(
            "patient-123"
        )

    def test_get_critical_values_empty(self, mock_digital_twin_service):
        """Test getting empty critical values."""
        # Configure mock
        mock_digital_twin_service.detect_critical_values.return_value = {}

        # Make request
        response = client.get("/api/v1/digital-twins/patient/patient-123/critical")

        # Check response
        assert response.status_code == 200
        assert response.json()["data"] == {}
        assert response.json()["count"] == 0
