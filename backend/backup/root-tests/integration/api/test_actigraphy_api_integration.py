"""
Integration tests for the Actigraphy API.

This module tests the integration between the API routes and the
PAT service implementation.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.services.ml.pat.mock import MockPATService
from app.api.deps import get_pat_service
from app.main import app


@pytest.fixture
def mock_pat_service():
    """Fixture for mock PAT service."""
    service = MockPATService()
    service.initialize({})
    return service


@pytest.fixture
def client(mock_pat_service):
    """Test client with mocked PAT service."""
    # Override the dependency to use our mock service
    app.dependency_overrides[get_pat_service] = lambda: mock_pat_service
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear dependency overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def actigraphy_data():
    """Sample actigraphy data for testing."""
    # Generate 1 hour of data at 50Hz
    start_time = datetime.utcnow().replace(microsecond=0)
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
        "sampling_rate_hz": 1.0,  # 1 sample per second
        "device_info": {
            "name": "ActiGraph GT9X",
            "firmware": "1.7.0",
            "device_id": "AG12345"
        },
        "analysis_types": ["activity_levels", "sleep_analysis"]
    }


class TestActigraphyAPI:
    """Integration tests for the Actigraphy API."""
    
    def test_analyze_actigraphy(self, client, auth_headers, actigraphy_data):
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
    
    def test_get_actigraphy_embeddings(self, client, auth_headers, actigraphy_data):
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
    
    def test_get_analysis_by_id(self, client, auth_headers, mock_pat_service):
        """Test retrieving an analysis by ID."""
        # First create an analysis
        analysis_data = mock_pat_service.analyze_actigraphy(
            patient_id="test-patient-123",
            readings=[{"x": 0.1, "y": 0.2, "z": 0.3, "timestamp": "2025-03-28T12:00:00Z"}],
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
    
    def test_get_patient_analyses(self, client, auth_headers, mock_pat_service):
        """Test retrieving analyses for a patient."""
        patient_id = "test-patient-123"
        
        # Create a few analyses for the patient
        for i in range(3):
            mock_pat_service.analyze_actigraphy(
                patient_id=patient_id,
                readings=[{"x": 0.1, "y": 0.2, "z": 0.3, "timestamp": f"2025-03-28T12:0{i}:00Z"}],
                start_time=f"2025-03-28T12:0{i}:00Z",
                end_time=f"2025-03-28T12:0{i+1}:00Z",
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
        assert "analyses" in data
        assert isinstance(data["analyses"], list)
        assert len(data["analyses"]) > 0
        assert "pagination" in data
    
    def test_get_model_info(self, client, auth_headers):
        """Test getting model information."""
        response = client.get(
            "/api/v1/actigraphy/model-info",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "capabilities" in data
        assert "description" in data
    
    def test_integrate_with_digital_twin(self, client, auth_headers, mock_pat_service):
        """Test integrating analysis with digital twin."""
        # Create an analysis
        analysis_data = mock_pat_service.analyze_actigraphy(
            patient_id="test-patient-123",
            readings=[{"x": 0.1, "y": 0.2, "z": 0.3, "timestamp": "2025-03-28T12:00:00Z"}],
            start_time="2025-03-28T12:00:00Z",
            end_time="2025-03-28T12:01:00Z",
            sampling_rate_hz=1.0,
            device_info={"name": "Test Device"},
            analysis_types=["activity_levels"]
        )
        
        integration_data = {
            "patient_id": "test-patient-123",
            "profile_id": "test-profile-456",
            "analysis_id": analysis_data["analysis_id"]
        }
        
        response = client.post(
            "/api/v1/actigraphy/integrate-with-digital-twin",
            headers=auth_headers,
            json=integration_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "integration_id" in data
        assert "patient_id" in data
        assert data["patient_id"] == integration_data["patient_id"]
        assert "profile_id" in data
        assert data["profile_id"] == integration_data["profile_id"]
        assert "analysis_id" in data
        assert data["analysis_id"] == integration_data["analysis_id"]
        assert "status" in data
        assert data["status"] == "success"
    
    def test_unauthorized_access(self, client, actigraphy_data):
        """Test unauthorized access to API."""
        response = client.post(
            "/api/v1/actigraphy/analyze",
            json=actigraphy_data
        )
        
        # Should fail with 401 Unauthorized
        assert response.status_code == 401