"""
Integration tests for the PAT service.

This module contains pytest tests that verify the integration between different
components of the PAT service, including the factory, API routes, and service
implementations.
"""

import json
import os
import tempfile
from typing import Any, Dict, Generator, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.ml import get_pat_service
from app.api.routes.actigraphy import router as actigraphy_router
from app.core.services.ml.pat.factory import PATFactory
from app.core.services.ml.pat.interface import PATInterface
from app.core.services.ml.pat.mock import MockPAT


@pytest.fixture
@pytest.mark.venv_only
def test_app() -> FastAPI:
    """Fixture that returns a test FastAPI application.
    
    Returns:
        Test FastAPI application
    """
    # Create a FastAPI application with only the actigraphy routes
    app = FastAPI()
    app.include_router(actigraphy_router, prefix="/api/v1")
    
    # Override the PAT service dependency to use a MockPAT instance
    temp_dir = tempfile.mkdtemp()
    pat = MockPAT()
    pat.initialize({"storage_path": temp_dir})
    
    app.dependency_overrides[get_pat_service] = lambda: pat
    
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Fixture that returns a test client for the FastAPI application.
    
    Args:
        test_app: Test FastAPI application
        
    Returns:
        Test client
    """
    return TestClient(test_app)


@pytest.fixture
def sample_readings() -> List[Dict[str, Any]]:
    """Fixture that returns sample accelerometer readings.
    
    Returns:
        List of sample accelerometer readings
    """
    return [
        {
            "timestamp": "2025-01-01T00:00:00Z",
            "x": 0.1,
            "y": 0.2,
            "z": 0.3
        },
        {
            "timestamp": "2025-01-01T00:00:01Z",
            "x": 0.2,
            "y": 0.3,
            "z": 0.4
        },
        {
            "timestamp": "2025-01-01T00:00:02Z",
            "x": 0.3,
            "y": 0.4,
            "z": 0.5
        }
    ]


@pytest.fixture
def sample_device_info() -> Dict[str, Any]:
    """Fixture that returns sample device information.
    
    Returns:
        Sample device information
    """
    return {
        "device_type": "smartwatch",
        "model": "SampleWatch",
        "manufacturer": "SampleTech",
        "firmware_version": "1.0.0"
    }


@pytest.fixture
def pat_storage() -> Generator[str, None, None]:
    """Fixture that provides a temporary directory for PAT storage.
    
    Yields:
        Temporary directory path
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_pat(pat_storage: str) -> MockPAT:
    """Fixture that returns a configured MockPAT instance.
    
    Args:
        pat_storage: Temporary storage directory
        
    Returns:
        Configured MockPAT instance
    """
    pat = MockPAT()
    pat.initialize({"storage_path": pat_storage})
    return pat


@pytest.mark.venv_only
def test_factory_create_mock_pat(pat_storage: str) -> None:
    """Test that the factory creates a MockPAT instance.
    
    Args:
        pat_storage: Temporary storage directory
    """
    config = {
        "provider": "mock",
        "storage_path": pat_storage
    }
    
    pat = PATFactory.get_pat_service(config)
    
    assert isinstance(pat, MockPAT)
    assert pat.storage_path == pat_storage


@pytest.mark.venv_only
def test_analyze_actigraphy_api(
    client: TestClient,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
) -> None:
    """Test the analyze actigraphy API endpoint.
    
    Args:
        client: Test client
        sample_readings: Sample accelerometer readings
        sample_device_info: Sample device information
    """
    # Prepare request data
    request_data = {
        "patient_id": "test-patient-1",
        "readings": sample_readings,
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-01T00:00:02Z",
        "sampling_rate_hz": 1.0,
        "device_info": sample_device_info,
        "analysis_types": ["sleep_quality", "activity_levels"]
    }
    
    # Send request
    response = client.post(
        "/api/v1/actigraphy/analyze",
        json=request_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "analysis_id" in data
    assert data["patient_id"] == "test-patient-1"
    assert "timestamp" in data
    assert data["device_info"] == sample_device_info
    assert data["analysis_period"]["start_time"] == "2025-01-01T00:00:00Z"
    assert data["analysis_period"]["end_time"] == "2025-01-01T00:00:02Z"
    assert data["sampling_info"]["rate_hz"] == 1.0
    assert data["sampling_info"]["sample_count"] == 3
    
    # Verify analyses are included
    assert "sleep_metrics" in data
    assert "activity_levels" in data


@pytest.mark.venv_only
def test_get_embeddings_api(
    client: TestClient,
    sample_readings: List[Dict[str, Any]]
) -> None:
    """Test the get embeddings API endpoint.
    
    Args:
        client: Test client
        sample_readings: Sample accelerometer readings
    """
    # Prepare request data
    request_data = {
        "patient_id": "test-patient-1",
        "readings": sample_readings,
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-01T00:00:02Z",
        "sampling_rate_hz": 1.0
    }
    
    # Send request
    response = client.post(
        "/api/v1/actigraphy/embeddings",
        json=request_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "embedding_id" in data
    assert data["patient_id"] == "test-patient-1"
    assert "timestamp" in data
    assert "embedding_vector" in data
    assert data["embedding_dimensions"] > 0
    assert data["analysis_period"]["start_time"] == "2025-01-01T00:00:00Z"
    assert data["analysis_period"]["end_time"] == "2025-01-01T00:00:02Z"
    assert data["sampling_info"]["rate_hz"] == 1.0
    assert data["sampling_info"]["sample_count"] == 3


@pytest.mark.venv_only
def test_get_analysis_by_id_api(
    client: TestClient,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
) -> None:
    """Test the get analysis by ID API endpoint.
    
    Args:
        client: Test client
        sample_readings: Sample accelerometer readings
        sample_device_info: Sample device information
    """
    # First, create an analysis
    request_data = {
        "patient_id": "test-patient-1",
        "readings": sample_readings,
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-01T00:00:02Z",
        "sampling_rate_hz": 1.0,
        "device_info": sample_device_info,
        "analysis_types": ["sleep_quality", "activity_levels"]
    }
    
    create_response = client.post(
        "/api/v1/actigraphy/analyze",
        json=request_data
    )
    
    # Get the analysis ID
    analysis_id = create_response.json()["analysis_id"]
    
    # Now get the analysis by ID
    response = client.get(f"/api/v1/actigraphy/analysis/{analysis_id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify it matches the original
    assert data["analysis_id"] == analysis_id
    assert data["patient_id"] == "test-patient-1"
    assert data["device_info"] == sample_device_info


@pytest.mark.venv_only
def test_get_patient_analyses_api(
    client: TestClient,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
) -> None:
    """Test the get patient analyses API endpoint.
    
    Args:
        client: Test client
        sample_readings: Sample accelerometer readings
        sample_device_info: Sample device information
    """
    # Create multiple analyses for a patient
    patient_id = "test-patient-2"
    
    for i in range(3):
        request_data = {
            "patient_id": patient_id,
            "readings": sample_readings,
            "start_time": f"2025-01-0{i+1}T00:00:00Z",
            "end_time": f"2025-01-0{i+1}T00:00:02Z",
            "sampling_rate_hz": 1.0,
            "device_info": sample_device_info,
            "analysis_types": ["sleep_quality", "activity_levels"]
        }
        
        client.post(
            "/api/v1/actigraphy/analyze",
            json=request_data
        )
    
    # Get analyses for the patient
    response = client.get(
        f"/api/v1/actigraphy/patient/{patient_id}/analyses",
        params={"limit": 10, "offset": 0}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["total"] == 3
    assert len(data["analyses"]) == 3
    assert data["limit"] == 10
    assert data["offset"] == 0
    
    # Test pagination
    response = client.get(
        f"/api/v1/actigraphy/patient/{patient_id}/analyses",
        params={"limit": 2, "offset": 0}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify pagination
    assert data["total"] == 3
    assert len(data["analyses"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


@pytest.mark.venv_only
def test_get_model_info_api(client: TestClient) -> None:
    """Test the get model info API endpoint.
    
    Args:
        client: Test client
    """
    response = client.get("/api/v1/actigraphy/model-info")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "model_name" in data
    assert "version" in data
    assert "description" in data
    assert "capabilities" in data
    assert "provider" in data


@pytest.mark.venv_only
def test_integrate_with_digital_twin_api(
    client: TestClient,
    sample_readings: List[Dict[str, Any]],
    sample_device_info: Dict[str, Any]
) -> None:
    """Test the integrate with digital twin API endpoint.
    
    Args:
        client: Test client
        sample_readings: Sample accelerometer readings
        sample_device_info: Sample device information
    """
    # First, create an analysis
    request_data = {
        "patient_id": "test-patient-3",
        "readings": sample_readings,
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-01T00:00:02Z",
        "sampling_rate_hz": 1.0,
        "device_info": sample_device_info,
        "analysis_types": ["sleep_quality", "activity_levels"]
    }
    
    create_response = client.post(
        "/api/v1/actigraphy/analyze",
        json=request_data
    )
    
    # Get the analysis ID
    analysis_id = create_response.json()["analysis_id"]
    
    # Now integrate with digital twin
    integration_data = {
        "patient_id": "test-patient-3",
        "profile_id": "test-profile-1",
        "analysis_id": analysis_id
    }
    
    response = client.post(
        "/api/v1/actigraphy/integrate-digital-twin",
        json=integration_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["patient_id"] == "test-patient-3"
    assert data["profile_id"] == "test-profile-1"
    assert data["integration_status"] == "success"
    assert "timestamp" in data
    assert "integrated_profile" in data