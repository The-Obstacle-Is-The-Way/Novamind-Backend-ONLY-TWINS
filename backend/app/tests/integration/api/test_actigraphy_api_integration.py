"""
Integration tests for the Actigraphy API.

This module tests the integration between the API routes and the
PAT service implementation.
"""

import json
import uuid
from datetime import datetime, timedelta
from app.domain.utils.datetime_utils import UTC
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient  # Keep for type hinting
from unittest.mock import patch

from app.core.services.ml.pat.mock import MockPATService
from app.presentation.api.dependencies.services import get_pat_service  # Corrected import path


@pytest.fixture
def mock_pat_service():
    """Fixture for mock PAT service."""
    service = MockPATService()
    service.initialize({})
    return service

def auth_headers():
    """Authentication headers for API requests."""
    # Use the mock token recognized by the mocked JWT service
    return {
        "Authorization": "Bearer patient_token_string",
        "Content-Type": "application/json"
    }


@pytest.fixture
def actigraphy_data():
    """Sample actigraphy data for testing."""
    # Generate 1 hour of data at 50Hz
    start_time = datetime.now(UTC).replace(microsecond=0)
    readings = []

    for i in range(180):  # 3 minutes of data (simplified for testing)
        timestamp = start_time + timedelta(seconds=i)
        readings.append({
            "x": 0.1 + (i % 10) * 0.01,
            "y": 0.2 + (i % 5) * 0.01,
            "z": 0.3 + (i % 7) * 0.01,
            "timestamp": timestamp.isoformat() + "Z"
        })

    end_time = (start_time + timedelta(seconds=179)).isoformat() + "Z"
    start_time = start_time.isoformat() + "Z"

    return {
        "patient_id": "test-patient-123",
        "readings": readings,
        "start_time": start_time,
        "end_time": end_time,
        "sampling_rate_hz": 1.0,
        # DeviceInfo fields must match schema: device_type and model are required; others optional
        "device_info": {
            "device_type": "ActiGraph GT9X",
            "model": "GT9X",
            "manufacturer": None,
            "firmware_version": "1.7.0",
            "position": None,
            "metadata": None
        },
        # Use correct analysis type values
        "analysis_types": ["activity_levels", "sleep_quality"]
    }

# Fixtures to create app and client for integration tests
@pytest.fixture
def test_app(mock_pat_service, actigraphy_data):
    from app.main import create_application
    from app.presentation.api.dependencies.auth import get_current_user
    from app.presentation.api.v1.endpoints.actigraphy import get_pat_service
    app_instance = create_application()
    # Override PAT service and authentication
    app_instance.dependency_overrides[get_pat_service] = lambda: mock_pat_service
    # Use patient_id from fixture for current_user
    app_instance.dependency_overrides[get_current_user] = lambda: {"id": actigraphy_data["patient_id"], "roles": []}
    return app_instance

@pytest.fixture
def client(test_app):
    """Override client to use TestClient for sync calls."""
    return TestClient(test_app)


@pytest.mark.db_required()
class TestActigraphyAPI:
    """Integration tests for the Actigraphy API."""

    def test_analyze_actigraphy(
        self,
        client: TestClient,
        auth_headers,
        actigraphy_data
    ):
        """Test analyzing actigraphy data."""
        response = client.post(
            "/api/v1/actigraphy/analyze",
            headers=auth_headers,
            json=actigraphy_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert "patient_id" in data
        assert data["patient_id"] == actigraphy_data["patient_id"]
        assert "timestamp" in data
        assert "results" in data
        assert "data_summary" in data
        assert data["data_summary"]["readings_count"] == len(actigraphy_data["readings"])

    def test_get_actigraphy_embeddings(
        self,
        client: TestClient,
        auth_headers,
        actigraphy_data
    ):
        """Test generating embeddings from actigraphy data."""
        # Remove unnecessary fields for embedding generation
        embedding_data = {
            "patient_id": actigraphy_data["patient_id"],
            "readings": actigraphy_data["readings"],
            "start_time": actigraphy_data["start_time"],
            "end_time": actigraphy_data["end_time"],
            "sampling_rate_hz": actigraphy_data["sampling_rate_hz"]
        }

        response = client.post(
            "/api/v1/actigraphy/embeddings",
            headers=auth_headers,
            json=embedding_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "embedding_id" in data
        assert "patient_id" in data
        assert data["patient_id"] == actigraphy_data["patient_id"]
        assert "timestamp" in data
        assert "embedding" in data
        assert "vector" in data["embedding"]
        assert "dimension" in data["embedding"]

    def test_get_analysis_by_id(
        self,
        client: TestClient,
        auth_headers,
        mock_pat_service
    ):
        """Test retrieving an analysis by ID."""
        # First create an analysis
        analysis_data = mock_pat_service.analyze_actigraphy(
            patient_id="test-patient-123",
            readings=[{
                "x": 0.1, 
                "y": 0.2, 
                "z": 0.3,
                "timestamp": "2025-03-28T12:00:00Z"
            }],
            start_time="2025-03-28T12:00:00Z",
            end_time="2025-03-28T12:01:00Z",
            sampling_rate_hz=1.0,
            device_info={"name": "Test Device"},
            analysis_types=["activity_levels"]
        )

        analysis_id = analysis_data["analysis_id"]

        response = client.get(
            f"/api/v1/actigraphy/analyses/{analysis_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["analysis_id"] == analysis_id
        assert "patient_id" in data
        assert "timestamp" in data

    def test_get_patient_analyses(
        self,
        client: TestClient,
        auth_headers,
        mock_pat_service
    ):
        """Test retrieving analyses for a patient."""
        patient_id = "test-patient-123"

        # Create a few analyses for the patient
        for i in range(3):
            mock_pat_service.analyze_actigraphy(
                patient_id=patient_id,
                readings=[{
                    "x": 0.1, 
                    "y": 0.2, 
                    "z": 0.3,
                    "timestamp": f"2025-03-28T12:0{i}:00Z"
                }],
                start_time=f"2025-03-28T12:0{i}:00Z",
                end_time=f"2025-03-28T12:0{i + 1}:00Z",
                sampling_rate_hz=1.0,
                device_info={"name": "Test Device"},
                analysis_types=["activity_levels"]
            )

        response = client.get(
            f"/api/v1/actigraphy/patient/{patient_id}/analyses",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        for analysis in data:
            assert "analysis_id" in analysis
            assert "patient_id" in analysis
            assert analysis["patient_id"] == patient_id

    def test_get_model_info(self, client: TestClient, auth_headers):
        """Test getting model information."""
        response = client.get(
            "/api/v1/actigraphy/model-info",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data
        assert "version" in data
        assert "deployment_date" in data
        assert "supported_devices" in data
        assert "supported_analyses" in data

    def test_integrate_with_digital_twin(
        self,
        client: TestClient,
        auth_headers,
        mock_pat_service
    ):
        """Test integrating analysis with digital twin."""
        # Create an analysis
        analysis_data = mock_pat_service.analyze_actigraphy(
            patient_id="test-patient-123",
            readings=[{
                "x": 0.1, 
                "y": 0.2, 
                "z": 0.3,
                "timestamp": "2025-03-28T12:00:00Z"
            }],
            start_time="2025-03-28T12:00:00Z",
            end_time="2025-03-28T12:01:00Z",
            sampling_rate_hz=1.0,
            device_info={"name": "Test Device"},
            analysis_types=["activity_levels"]
        )

        # Integration request
        payload = {
            "analysis_id": analysis_data["analysis_id"],
            "patient_id": "test-patient-123",
            "integration_options": {
                "update_symptom_tracking": True,
                "update_sleep_pattern": True,
                "include_raw_data": False
            }
        }

        response = client.post(
            "/api/v1/actigraphy/integrate-with-digital-twin",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "integration_id" in data
        assert "patient_id" in data
        assert "analysis_id" in data
        assert "integrated_data_points" in data

    def test_unauthorized_access(self, client: TestClient, actigraphy_data):
        """Test unauthorized access to API."""
        response = client.post(
            "/api/v1/actigraphy/analyze",
            json=actigraphy_data
        )
        # No auth headers provided
        assert response.status_code == 401  # Unauthorized
        assert "detail" in response.json()
