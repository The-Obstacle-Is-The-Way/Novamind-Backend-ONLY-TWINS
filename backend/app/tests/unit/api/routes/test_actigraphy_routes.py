"""
Unit tests for the actigraphy API routes.

This module contains unit tests for the actigraphy API routes, verifying that they
correctly handle requests, responses, and errors.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.routes.actigraphy import router
from app.api.schemas.actigraphy import AnalysisType
from app.core.services.ml.pat.exceptions import (
    AnalysisError,
    AuthorizationError,
    EmbeddingError,
    ResourceNotFoundError,
    ValidationError,
)


# Mock data
@pytest.fixture
def mock_token() -> str:
    """Create a mock JWT token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXRpZW50MTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.signature"


@pytest.fixture
def patient_id() -> str:
    """Create a mock patient ID."""
    return "patient123"


@pytest.fixture
def sample_readings() -> List[Dict[str, Any]]:
    """Create sample accelerometer readings."""
    base_time = datetime.now()
    readings = []
    
    for i in range(10):
        timestamp = (base_time + timedelta(seconds=i/10)).isoformat() + "Z"
        reading = {
            "timestamp": timestamp,
            "x": 0.1 * i,
            "y": 0.2 * i,
            "z": 0.3 * i,
            "heart_rate": 60 + i,
            "metadata": {"activity": "walking" if i % 2 == 0 else "sitting"}
        }
        readings.append(reading)
    
    return readings


@pytest.fixture
def device_info() -> Dict[str, Any]:
    """Create sample device info."""
    return {
        "device_type": "smartwatch",
        "model": "Apple Watch Series 9",
        "manufacturer": "Apple",
        "firmware_version": "1.2.3",
        "position": "wrist_left",
        "metadata": {"battery_level": 85}
    }


@pytest.fixture
def analysis_request(patient_id: str, sample_readings: List[Dict[str, Any]], device_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create an analysis request."""
    return {
        "patient_id": patient_id,
        "readings": sample_readings,
        "start_time": datetime.now().isoformat() + "Z",
        "end_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z",
        "sampling_rate_hz": 10.0,
        "device_info": device_info,
        "analysis_types": [AnalysisType.ACTIVITY_LEVEL.value, AnalysisType.SLEEP.value]
    }


@pytest.fixture
def embedding_request(patient_id: str, sample_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create an embedding request."""
    return {
        "patient_id": patient_id,
        "readings": sample_readings,
        "start_time": datetime.now().isoformat() + "Z",
        "end_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z",
        "sampling_rate_hz": 10.0
    }


@pytest.fixture
def integration_request(patient_id: str) -> Dict[str, Any]:
    """Create an integration request."""
    return {
        "patient_id": patient_id,
        "profile_id": "profile123",
        "analysis_id": "analysis123"
    }


@pytest.fixture
def analysis_result(patient_id: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create an analysis result."""
    return {
        "analysis_id": "analysis123",
        "patient_id": patient_id,
        "timestamp": datetime.now().isoformat() + "Z",
        "analysis_types": [AnalysisType.ACTIVITY_LEVEL.value, AnalysisType.SLEEP.value],
        "device_info": device_info,
        "data_summary": {
            "start_time": datetime.now().isoformat() + "Z",
            "end_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z",
            "duration_seconds": 3600.0,
            "readings_count": 10,
            "sampling_rate_hz": 10.0
        },
        "results": {
            AnalysisType.ACTIVITY_LEVEL.value: {
                "activity_levels": {
                    "sedentary": {
                        "percentage": 0.6,
                        "duration_seconds": 2160.0
                    },
                    "light": {
                        "percentage": 0.3,
                        "duration_seconds": 1080.0
                    },
                    "moderate": {
                        "percentage": 0.08,
                        "duration_seconds": 288.0
                    },
                    "vigorous": {
                        "percentage": 0.02,
                        "duration_seconds": 72.0
                    }
                },
                "step_count": 5000,
                "calories_burned": 1200,
                "distance_km": 3.5,
                "avg_heart_rate_bpm": 72
            },
            AnalysisType.SLEEP.value: {
                "sleep_stages": {
                    "awake": {
                        "percentage": 0.1,
                        "duration_seconds": 360.0
                    },
                    "light": {
                        "percentage": 0.5,
                        "duration_seconds": 1800.0
                    },
                    "deep": {
                        "percentage": 0.3,
                        "duration_seconds": 1080.0
                    },
                    "rem": {
                        "percentage": 0.1,
                        "duration_seconds": 360.0
                    }
                },
                "sleep_efficiency": 0.9,
                "sleep_latency_seconds": 600,
                "interruptions_count": 2,
                "avg_heart_rate_bpm": 55,
                "respiratory_rate_bpm": 14.5
            }
        }
    }


@pytest.fixture
def embedding_result(patient_id: str) -> Dict[str, Any]:
    """Create an embedding result."""
    return {
        "embedding_id": "embedding123",
        "patient_id": patient_id,
        "timestamp": datetime.now().isoformat() + "Z",
        "data_summary": {
            "start_time": datetime.now().isoformat() + "Z",
            "end_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z",
            "duration_seconds": 3600.0,
            "readings_count": 10,
            "sampling_rate_hz": 10.0
        },
        "embedding": {
            "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
            "dimension": 5,
            "model_version": "mock-embedding-v1.0"
        }
    }


@pytest.fixture
def integration_result(patient_id: str) -> Dict[str, Any]:
    """Create an integration result."""
    return {
        "integration_id": "integration123",
        "patient_id": patient_id,
        "profile_id": "profile123",
        "analysis_id": "analysis123",
        "timestamp": datetime.now().isoformat() + "Z",
        "status": "success",
        "insights": [
            {
                "type": "activity_pattern",
                "description": "Daily activity levels show a predominantly sedentary pattern",
                "recommendation": "Consider incorporating more light activity throughout the day",
                "confidence": 0.85
            },
            {
                "type": "sleep_quality",
                "description": "Sleep efficiency suggests suboptimal rest quality",
                "recommendation": "Consistent sleep schedule and improved sleep hygiene may be beneficial",
                "confidence": 0.9
            }
        ],
        "profile_update": {
            "updated_aspects": [
                "physical_activity_patterns",
                "sleep_patterns",
                "behavioral_patterns"
            ],
            "confidence_score": 0.92,
            "updated_at": datetime.now().isoformat() + "Z"
        }
    }


@pytest.fixture
def model_info() -> Dict[str, Any]:
    """Create model info."""
    return {
        "name": "MockPAT",
        "version": "1.0.0",
        "description": "Mock implementation of the PAT service for testing",
        "capabilities": [
            "activity_level_analysis",
            "sleep_analysis",
            "gait_analysis",
            "tremor_analysis",
            "embedding_generation"
        ],
        "maintainer": "Concierge Psychiatry Platform Team",
        "last_updated": "2025-03-28",
        "active": True
    }


@pytest.fixture
def analyses_list(patient_id: str) -> Dict[str, Any]:
    """Create a list of analyses."""
    return {
        "analyses": [
            {
                "analysis_id": "analysis123",
                "timestamp": datetime.now().isoformat() + "Z",
                "analysis_types": [AnalysisType.ACTIVITY_LEVEL.value, AnalysisType.SLEEP.value],
                "data_summary": {
                    "start_time": datetime.now().isoformat() + "Z",
                    "end_time": (datetime.now() + timedelta(hours=1)).isoformat() + "Z",
                    "duration_seconds": 3600.0,
                    "readings_count": 10,
                    "sampling_rate_hz": 10.0
                }
            },
            {
                "analysis_id": "analysis456",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
                "analysis_types": [AnalysisType.ACTIVITY_LEVEL.value],
                "data_summary": {
                    "start_time": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
                    "end_time": (datetime.now() - timedelta(days=1) + timedelta(hours=1)).isoformat() + "Z",
                    "duration_seconds": 3600.0,
                    "readings_count": 10,
                    "sampling_rate_hz": 10.0
                }
            }
        ],
        "pagination": {
            "total": 2,
            "limit": 10,
            "offset": 0,
            "has_more": False
        }
    }


# Test client
@pytest.fixture
def client() -> TestClient:
    """Create a test client for the actigraphy routes."""
    return TestClient(router)


# Mock authentication
@pytest.fixture(autouse=True)
def mock_auth() -> None:
    """Mock authentication functions."""
    with patch("app.api.routes.actigraphy.validate_jwt", return_value=None), \
         patch("app.api.routes.actigraphy.get_current_user_id", return_value="patient123"):
        yield


# Mock PAT service
@pytest.fixture
def mock_pat_service(
    analysis_result: Dict[str, Any],
    embedding_result: Dict[str, Any],
    integration_result: Dict[str, Any],
    model_info: Dict[str, Any],
    analyses_list: Dict[str, Any]
) -> MagicMock:
    """Create a mock PAT service."""
    mock_service = MagicMock()
    
    # Mock methods
    mock_service.analyze_actigraphy.return_value = analysis_result
    mock_service.get_actigraphy_embeddings.return_value = embedding_result
    mock_service.get_analysis_by_id.return_value = analysis_result
    mock_service.get_patient_analyses.return_value = analyses_list
    mock_service.get_model_info.return_value = model_info
    mock_service.integrate_with_digital_twin.return_value = integration_result
    
    return mock_service


@pytest.fixture(autouse=True)
def mock_get_pat_service(mock_pat_service: MagicMock) -> None:
    """Mock the get_pat_service dependency."""
    with patch("app.api.routes.actigraphy.get_pat_service", return_value=mock_pat_service):
        yield


class TestActigraphyRoutes:
    """Tests for the actigraphy API routes."""
    
    def test_analyze_actigraphy_success(
        self,
        client: TestClient,
        mock_token: str,
        analysis_request: Dict[str, Any],
        analysis_result: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test successful actigraphy analysis."""
        # Make the request
        response = client.post(
            "/analyze",
            json=analysis_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == analysis_result
        
        # Verify service call
        mock_pat_service.analyze_actigraphy.assert_called_once()
    
    def test_analyze_actigraphy_unauthorized(
        self,
        client: TestClient,
        mock_token: str,
        analysis_request: Dict[str, Any]
    ) -> None:
        """Test unauthorized actigraphy analysis."""
        # Change patient ID to trigger authorization error
        modified_request = analysis_request.copy()
        modified_request["patient_id"] = "different_patient"
        
        # Make the request
        response = client.post(
            "/analyze",
            json=modified_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    def test_analyze_actigraphy_validation_error(
        self,
        client: TestClient,
        mock_token: str,
        analysis_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test actigraphy analysis with validation error."""
        # Setup the mock to raise a validation error
        mock_pat_service.analyze_actigraphy.side_effect = ValidationError("Invalid input")
        
        # Make the request
        response = client.post(
            "/analyze",
            json=analysis_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid input" in response.json()["detail"]
    
    def test_analyze_actigraphy_analysis_error(
        self,
        client: TestClient,
        mock_token: str,
        analysis_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test actigraphy analysis with analysis error."""
        # Setup the mock to raise an analysis error
        mock_pat_service.analyze_actigraphy.side_effect = AnalysisError("Analysis failed")
        
        # Make the request
        response = client.post(
            "/analyze",
            json=analysis_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Analysis failed" in response.json()["detail"]
    
    def test_get_actigraphy_embeddings_success(
        self,
        client: TestClient,
        mock_token: str,
        embedding_request: Dict[str, Any],
        embedding_result: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test successful embedding generation."""
        # Make the request
        response = client.post(
            "/embeddings",
            json=embedding_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == embedding_result
        
        # Verify service call
        mock_pat_service.get_actigraphy_embeddings.assert_called_once()
    
    def test_get_actigraphy_embeddings_unauthorized(
        self,
        client: TestClient,
        mock_token: str,
        embedding_request: Dict[str, Any]
    ) -> None:
        """Test unauthorized embedding generation."""
        # Change patient ID to trigger authorization error
        modified_request = embedding_request.copy()
        modified_request["patient_id"] = "different_patient"
        
        # Make the request
        response = client.post(
            "/embeddings",
            json=modified_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    def test_get_actigraphy_embeddings_validation_error(
        self,
        client: TestClient,
        mock_token: str,
        embedding_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test embedding generation with validation error."""
        # Setup the mock to raise a validation error
        mock_pat_service.get_actigraphy_embeddings.side_effect = ValidationError("Invalid input")
        
        # Make the request
        response = client.post(
            "/embeddings",
            json=embedding_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid input" in response.json()["detail"]
    
    def test_get_actigraphy_embeddings_embedding_error(
        self,
        client: TestClient,
        mock_token: str,
        embedding_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test embedding generation with embedding error."""
        # Setup the mock to raise an embedding error
        mock_pat_service.get_actigraphy_embeddings.side_effect = EmbeddingError("Embedding failed")
        
        # Make the request
        response = client.post(
            "/embeddings",
            json=embedding_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Embedding failed" in response.json()["detail"]
    
    def test_get_analysis_by_id_success(
        self,
        client: TestClient,
        mock_token: str,
        analysis_result: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test successful analysis retrieval."""
        # Make the request
        response = client.get(
            f"/analyses/{analysis_result['analysis_id']}",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == analysis_result
        
        # Verify service call
        mock_pat_service.get_analysis_by_id.assert_called_once_with(analysis_result["analysis_id"])
    
    def test_get_analysis_by_id_not_found(
        self,
        client: TestClient,
        mock_token: str,
        mock_pat_service: MagicMock
    ) -> None:
        """Test analysis retrieval with not found error."""
        # Setup the mock to raise a not found error
        mock_pat_service.get_analysis_by_id.side_effect = ResourceNotFoundError("Analysis not found")
        
        # Make the request
        response = client.get(
            "/analyses/nonexistent",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    def test_get_analysis_by_id_unauthorized(
        self,
        client: TestClient,
        mock_token: str,
        analysis_result: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test unauthorized analysis retrieval."""
        # Setup the mock to return an analysis with a different patient ID
        modified_result = analysis_result.copy()
        modified_result["patient_id"] = "different_patient"
        mock_pat_service.get_analysis_by_id.return_value = modified_result
        
        # Make the request
        response = client.get(
            f"/analyses/{analysis_result['analysis_id']}",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    def test_get_patient_analyses_success(
        self,
        client: TestClient,
        mock_token: str,
        patient_id: str,
        analyses_list: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test successful patient analyses retrieval."""
        # Make the request
        response = client.get(
            f"/patient/{patient_id}/analyses",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == analyses_list
        
        # Verify service call
        mock_pat_service.get_patient_analyses.assert_called_once_with(
            patient_id=patient_id,
            limit=10,
            offset=0
        )
    
    def test_get_patient_analyses_unauthorized(
        self,
        client: TestClient,
        mock_token: str
    ) -> None:
        """Test unauthorized patient analyses retrieval."""
        # Make the request with a different patient ID
        response = client.get(
            "/patient/different_patient/analyses",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    def test_get_model_info_success(
        self,
        client: TestClient,
        mock_token: str,
        model_info: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test successful model info retrieval."""
        # Make the request
        response = client.get(
            "/model-info",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == model_info
        
        # Verify service call
        mock_pat_service.get_model_info.assert_called_once()
    
    def test_integrate_with_digital_twin_success(
        self,
        client: TestClient,
        mock_token: str,
        integration_request: Dict[str, Any],
        integration_result: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test successful digital twin integration."""
        # Make the request
        response = client.post(
            "/integrate-with-digital-twin",
            json=integration_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == integration_result
        
        # Verify service call
        mock_pat_service.integrate_with_digital_twin.assert_called_once()
    
    def test_integrate_with_digital_twin_unauthorized(
        self,
        client: TestClient,
        mock_token: str,
        integration_request: Dict[str, Any]
    ) -> None:
        """Test unauthorized digital twin integration."""
        # Change patient ID to trigger authorization error
        modified_request = integration_request.copy()
        modified_request["patient_id"] = "different_patient"
        
        # Make the request
        response = client.post(
            "/integrate-with-digital-twin",
            json=modified_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    def test_integrate_with_digital_twin_not_found(
        self,
        client: TestClient,
        mock_token: str,
        integration_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test digital twin integration with not found error."""
        # Setup the mock to raise a not found error
        mock_pat_service.integrate_with_digital_twin.side_effect = ResourceNotFoundError("Analysis not found")
        
        # Make the request
        response = client.post(
            "/integrate-with-digital-twin",
            json=integration_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    def test_integrate_with_digital_twin_authorization_error(
        self,
        client: TestClient,
        mock_token: str,
        integration_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test digital twin integration with authorization error."""
        # Setup the mock to raise an authorization error
        mock_pat_service.integrate_with_digital_twin.side_effect = AuthorizationError("Not authorized")
        
        # Make the request
        response = client.post(
            "/integrate-with-digital-twin",
            json=integration_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    def test_integrate_with_digital_twin_validation_error(
        self,
        client: TestClient,
        mock_token: str,
        integration_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test digital twin integration with validation error."""
        # Setup the mock to raise a validation error
        mock_pat_service.integrate_with_digital_twin.side_effect = ValidationError("Invalid input")
        
        # Make the request
        response = client.post(
            "/integrate-with-digital-twin",
            json=integration_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid input" in response.json()["detail"]
    
    def test_integrate_with_digital_twin_integration_error(
        self,
        client: TestClient,
        mock_token: str,
        integration_request: Dict[str, Any],
        mock_pat_service: MagicMock
    ) -> None:
        """Test digital twin integration with integration error."""
        # Setup the mock to raise an integration error
        mock_pat_service.integrate_with_digital_twin.side_effect = IntegrationError("Integration failed")
        
        # Make the request
        response = client.post(
            "/integrate-with-digital-twin",
            json=integration_request,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Check the response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Integration failed" in response.json()["detail"]