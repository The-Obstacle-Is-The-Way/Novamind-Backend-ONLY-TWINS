# -*- coding: utf-8 -*-
"""
Integration tests for the actigraphy API endpoints.

This module tests the interaction between the API endpoints and the PAT service.
It uses FastAPI's TestClient to make requests to the API and validates the responses.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.presentation.api.dependencies import get_pat_service # Corrected import path
from app.api.schemas.actigraphy import (
    AnalysisType,
    DeviceInfo,
    AnalyzeActigraphyRequest, # Corrected schema name
    AccelerometerReading,
)
from app.core.services.ml.pat.mock import MockPATService # Corrected class name
from app.main import app


# Create test client
client = TestClient(app)


# Helper function to create sample readings
def create_sample_readings(num_readings: int = 10) -> List[Dict[str, Any]]:
    """Create sample accelerometer readings for testing."""
    start_time = datetime.now() - timedelta(hours=1)
    readings = []
    
    for i in range(num_readings):
        timestamp = start_time + timedelta(seconds=i * 6)  # 10Hz
        reading = {
            "timestamp": timestamp.isoformat(),
            "x": 0.1 * i,
            "y": 0.2 * i,
            "z": 0.3 * i,
        }
        readings.append(reading)
        
    return readings


# Mock JWT token authentication
def mock_validate_token(token: str) -> Dict[str, Any]:
    """Mock JWT token validation."""
    return {"sub": "test-user-id", "role": "clinician"}


def mock_get_current_user_id(payload: Dict[str, Any]) -> str:
    """Mock get current user ID."""
    return payload["sub"]


# Mock PAT service for testing
@pytest.fixture
def mock_pat_service():
    """Fixture for a mock PAT service."""
    service = MockPAT()
    service.initialize({})
    return service


# Override dependencies for testing
@pytest.fixture(autouse=True)
def override_dependencies(mock_pat_service):
    """Override dependencies for testing."""
    app.dependency_overrides[get_pat_service] = lambda: mock_pat_service
    
    # Mock JWT token validation
    with patch("app.api.routes.actigraphy.validate_token", side_effect=mock_validate_token), \
         patch("app.api.routes.actigraphy.get_current_user_id", side_effect=mock_get_current_user_id):
        yield
    
    # Reset dependencies after test
    app.dependency_overrides = {}


class TestActigraphyAPI:
    """Integration tests for the actigraphy API endpoints."""
    
    def test_analyze_actigraphy(self):
        """Test the analyze actigraphy endpoint."""
        # Prepare test data
        patient_id = "test-patient-1"
        readings = [
            AccelerometerReading(
                timestamp=reading["timestamp"],
                x=reading["x"],
                y=reading["y"],
                z=reading["z"]
            )
            for reading in create_sample_readings(20)
        ]
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        device_info = DeviceInfo(
            device_type="fitbit",
            model="versa-3",
            firmware_version="1.2.3"
        )
        
        request_data = AnalyzeRequest(
            patient_id=patient_id,
            readings=readings,
            start_time=start_time,
            end_time=end_time,
            sampling_rate_hz=10.0,
            device_info=device_info,
            analysis_types=[AnalysisType.SLEEP_QUALITY, AnalysisType.ACTIVITY_LEVELS]
        )
        
        # Make request
        response = client.post(
            "/api/actigraphy/analyze",
            json=request_data.model_dump(),
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "analysis_id" in data
        assert "patient_id" in data
        assert data["patient_id"] == patient_id
        assert "timestamp" in data
        
        # Check for sleep metrics
        assert "sleep_metrics" in data
        sleep_metrics = data["sleep_metrics"]
        assert 0 <= sleep_metrics["sleep_efficiency"] <= 1
        
        # Check for activity levels
        assert "activity_levels" in data
        activity_levels = data["activity_levels"]
        assert "sedentary" in activity_levels
        assert "light" in activity_levels
        assert "moderate" in activity_levels
        assert "vigorous" in activity_levels
    
    def test_get_embeddings(self):
        """Test the get embeddings endpoint."""
        # Prepare test data
        patient_id = "test-patient-1"
        readings = [
            AccelerometerReading(
                timestamp=reading["timestamp"],
                x=reading["x"],
                y=reading["y"],
                z=reading["z"]
            )
            for reading in create_sample_readings(20)
        ]
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        request_data = {
            "patient_id": patient_id,
            "readings": [reading.model_dump() for reading in readings],
            "start_time": start_time,
            "end_time": end_time,
            "sampling_rate_hz": 10.0
        }
        
        # Make request
        response = client.post(
            "/api/actigraphy/embeddings",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "embedding_id" in data
        assert "patient_id" in data
        assert data["patient_id"] == patient_id
        assert "timestamp" in data
        assert "embeddings" in data
        assert isinstance(data["embeddings"], list)
        assert len(data["embeddings"]) == data["embedding_size"]
    
    def test_get_analysis_by_id(self, mock_pat_service):
        """Test retrieving an analysis by ID."""
        # First create an analysis
        patient_id = "test-patient-1"
        readings = create_sample_readings(20)
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        analysis = mock_pat_service.analyze_actigraphy(
            patient_id=patient_id,
            readings=readings,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            sampling_rate_hz=10.0,
            device_info={"device_type": "fitbit", "model": "versa-3"},
            analysis_types=["sleep_quality"]
        )
        
        analysis_id = analysis["analysis_id"]
        
        # Make request
        response = client.get(
            f"/api/actigraphy/analysis/{analysis_id}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["analysis_id"] == analysis_id
        assert data["patient_id"] == patient_id
        assert "sleep_metrics" in data
    
    def test_get_patient_analyses(self, mock_pat_service):
        """Test retrieving analyses for a patient."""
        # First create multiple analyses for the same patient
        patient_id = "test-patient-2"
        
        for i in range(3):
            readings = create_sample_readings(20)
            start_time = datetime.now() - timedelta(hours=i+1)
            end_time = datetime.now() - timedelta(hours=i)
            
            mock_pat_service.analyze_actigraphy(
                patient_id=patient_id,
                readings=readings,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                sampling_rate_hz=10.0,
                device_info={"device_type": "fitbit", "model": "versa-3"},
                analysis_types=["sleep_quality", "activity_levels"]
            )
        
        # Make request
        response = client.get(
            f"/api/actigraphy/patient/{patient_id}/analyses",
            params={"limit": 10, "offset": 0},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == patient_id
        assert "analyses" in data
        assert isinstance(data["analyses"], list)
        assert len(data["analyses"]) == 3
        assert data["total"] == 3
    
    def test_get_model_info(self):
        """Test retrieving model information."""
        # Make request
        response = client.get(
            "/api/actigraphy/model-info",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "model_name" in data
        assert data["model_name"] == "PAT"
        assert "model_version" in data
        assert "supported_analysis_types" in data
        assert isinstance(data["supported_analysis_types"], list)
    
    def test_integrate_with_digital_twin(self, mock_pat_service):
        """Test integrating actigraphy analysis with a digital twin."""
        # Prepare test data
        patient_id = "test-patient-1"
        profile_id = "test-profile-1"
        
        # First create an analysis
        readings = create_sample_readings(20)
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        analysis = mock_pat_service.analyze_actigraphy(
            patient_id=patient_id,
            readings=readings,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            sampling_rate_hz=10.0,
            device_info={"device_type": "fitbit", "model": "versa-3"},
            analysis_types=["sleep_quality", "activity_levels"]
        )
        
        request_data = {
            "patient_id": patient_id,
            "profile_id": profile_id,
            "actigraphy_analysis": analysis
        }
        
        # Make request
        response = client.post(
            "/api/actigraphy/digital-twin/integrate",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "profile_id" in data
        assert data["profile_id"] == profile_id
        assert "patient_id" in data
        assert data["patient_id"] == patient_id
        assert "timestamp" in data
        assert "integrated_profile" in data
    
    def test_unauthorized_access(self):
        """Test unauthorized access to the API."""
        # Make request without token
        response = client.get(
            "/api/actigraphy/model-info"
        )
        
        # Verify response
        assert response.status_code == status.HTTP_403_FORBIDDEN