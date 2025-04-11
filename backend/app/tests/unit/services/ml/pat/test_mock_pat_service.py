"""
Unit tests for the mock PAT service implementation.

This module contains unit tests for the MockPAT service, verifying that it
correctly implements the PATInterface.
"""

import datetime
import json
import pytest
from typing import Any, Dict, List

from app.core.services.ml.pat.exceptions import (
    AnalysisError,
    AuthorizationError,
    EmbeddingError,
    InitializationError,
    IntegrationError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.services.ml.pat.interface import PATInterface
from app.core.services.ml.pat.mock import MockPATService # Corrected import


@pytest.fixture
def mock_pat() -> MockPATService:
    """Create a MockPAT instance."""
    return MockPATService()


@pytest.fixture
def initialized_mock_pat() -> MockPATService:
    """Create and initialize a MockPAT instance."""
    pat = MockPATService()
    pat.initialize({"mock_delay_ms": 0})
    return pat


@pytest.fixture
def sample_readings() -> List[Dict[str, Any]]:
    """Create sample accelerometer readings."""
    base_time = datetime.datetime.fromisoformat("2025-03-28T14:00:00+00:00")
    readings = []
    
    for i in range(100):
        timestamp = (base_time + datetime.timedelta(seconds=i/10)).isoformat().replace("+00:00", "Z")
        reading = {
            "timestamp": timestamp,
            "x": 0.1 * i % 2,
            "y": 0.2 * i % 3,
            "z": 0.3 * i % 4,
            "heart_rate": 60 + (i % 20),
            "metadata": {"activity": "walking" if i % 30 > 15 else "sitting"}
        }
        readings.append(reading)
    
    return readings


@pytest.fixture
def sample_device_info() -> Dict[str, Any]:
    """Create sample device info."""
    return {
        "device_type": "smartwatch",
        "model": "Apple Watch Series 9",
        "manufacturer": "Apple",
        "firmware_version": "1.2.3",
        "position": "wrist_left",
        "metadata": {"battery_level": 85}
    }


class TestMockPAT:
    """Tests for the MockPAT class."""
    
    def test_initialization(self, mock_pat: MockPATService) -> None:
        """Test successful initialization."""
        # Initialize with default config
        mock_pat.initialize({})
        
        # Verify initialized state
        assert mock_pat._initialized is True
        assert mock_pat._config == {}
        assert mock_pat._mock_delay_ms == 0
        
        # Initialize with mock delay
        mock_pat = MockPATService()
        mock_pat.initialize({"mock_delay_ms": 100})
        
        # Verify config is stored
        assert mock_pat._initialized is True
        assert mock_pat._config == {"mock_delay_ms": 100}
        assert mock_pat._mock_delay_ms == 100
    
    def test_initialization_error(self, mock_pat: MockPATService) -> None:
        """Test initialization with faulty config."""
        with pytest.raises(InitializationError):
            # Force an error by passing something that will cause initialize to fail
            mock_pat._simulate_delay = None  # type: ignore
            mock_pat.initialize({})
    
    def test_uninitialized_error(self, mock_pat: MockPATService) -> None:
        """Test calling methods before initialization."""
        with pytest.raises(InitializationError):
            mock_pat.get_model_info()
    
    def test_analyze_actigraphy(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test successful actigraphy analysis."""
        # Define parameters
        patient_id = "patient123"
        start_time = "2025-03-28T14:00:00Z"
        end_time = "2025-03-28T14:30:00Z"
        sampling_rate_hz = 10.0
        analysis_types = ["activity_level_analysis", "sleep_analysis"]
        
        # Call analyze_actigraphy
        result = initialized_mock_pat.analyze_actigraphy(
            patient_id=patient_id,
            readings=sample_readings,
            start_time=start_time,
            end_time=end_time,
            sampling_rate_hz=sampling_rate_hz,
            device_info=sample_device_info,
            analysis_types=analysis_types
        )
        
        # Verify result
        assert "analysis_id" in result
        assert result["patient_id"] == patient_id
        assert "timestamp" in result
        assert set(result["analysis_types"]) == set(analysis_types)
        assert result["device_info"] == sample_device_info
        
        # Verify data summary
        assert result["data_summary"]["start_time"] == start_time
        assert result["data_summary"]["end_time"] == end_time
        assert result["data_summary"]["readings_count"] == len(sample_readings)
        assert result["data_summary"]["sampling_rate_hz"] == sampling_rate_hz
        
        # Verify results for each analysis type
        assert all(analysis_type in result["results"] for analysis_type in analysis_types)
        
        # Verify the analysis is stored
        analysis_id = result["analysis_id"]
        assert analysis_id in initialized_mock_pat._analyses
    
    def test_analyze_actigraphy_validation_error(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test actigraphy analysis with invalid parameters."""
        # Test empty patient_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.analyze_actigraphy(
                patient_id="",
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0,
                device_info=sample_device_info,
                analysis_types=["activity_level_analysis"]
            )
        
        # Test empty readings
        with pytest.raises(ValidationError):
            initialized_mock_pat.analyze_actigraphy(
                patient_id="patient123",
                readings=[],
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0,
                device_info=sample_device_info,
                analysis_types=["activity_level_analysis"]
            )
        
        # Test invalid sampling rate
        with pytest.raises(ValidationError):
            initialized_mock_pat.analyze_actigraphy(
                patient_id="patient123",
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=0.0,
                device_info=sample_device_info,
                analysis_types=["activity_level_analysis"]
            )
        
        # Test invalid analysis type
        with pytest.raises(ValidationError):
            initialized_mock_pat.analyze_actigraphy(
                patient_id="patient123",
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0,
                device_info=sample_device_info,
                analysis_types=["invalid_analysis_type"]
            )
    
    def test_get_actigraphy_embeddings(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]]
    ) -> None:
        """Test successful embedding generation."""
        # Define parameters
        patient_id = "patient123"
        start_time = "2025-03-28T14:00:00Z"
        end_time = "2025-03-28T14:30:00Z"
        sampling_rate_hz = 10.0
        
        # Call get_actigraphy_embeddings
        result = initialized_mock_pat.get_actigraphy_embeddings(
            patient_id=patient_id,
            readings=sample_readings,
            start_time=start_time,
            end_time=end_time,
            sampling_rate_hz=sampling_rate_hz
        )
        
        # Verify result
        assert "embedding_id" in result
        assert result["patient_id"] == patient_id
        assert "timestamp" in result
        
        # Verify data summary
        assert result["data_summary"]["start_time"] == start_time
        assert result["data_summary"]["end_time"] == end_time
        assert result["data_summary"]["readings_count"] == len(sample_readings)
        assert result["data_summary"]["sampling_rate_hz"] == sampling_rate_hz
        
        # Verify embedding
        assert "embedding" in result
        assert "vector" in result["embedding"]
        assert "dimension" in result["embedding"]
        assert "model_version" in result["embedding"]
        assert len(result["embedding"]["vector"]) == result["embedding"]["dimension"]
        
        # Verify the embedding is stored
        embedding_id = result["embedding_id"]
        assert embedding_id in initialized_mock_pat._embeddings
    
    def test_get_actigraphy_embeddings_validation_error(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]]
    ) -> None:
        """Test embedding generation with invalid parameters."""
        # Test empty patient_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.get_actigraphy_embeddings(
                patient_id="",
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0
            )
        
        # Test empty readings
        with pytest.raises(ValidationError):
            initialized_mock_pat.get_actigraphy_embeddings(
                patient_id="patient123",
                readings=[],
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0
            )
        
        # Test invalid sampling rate
        with pytest.raises(ValidationError):
            initialized_mock_pat.get_actigraphy_embeddings(
                patient_id="patient123",
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=0.0
            )
    
    def test_get_analysis_by_id(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test retrieving an analysis by ID."""
        # Create an analysis first
        analysis = initialized_mock_pat.analyze_actigraphy(
            patient_id="patient123",
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=["activity_level_analysis"]
        )
        analysis_id = analysis["analysis_id"]
        
        # Retrieve the analysis
        result = initialized_mock_pat.get_analysis_by_id(analysis_id)
        
        # Verify the retrieved analysis
        assert result["analysis_id"] == analysis_id
        assert result["patient_id"] == "patient123"
        assert result["analysis_types"] == ["activity_level_analysis"]
    
    def test_get_analysis_by_id_not_found(self, initialized_mock_pat: MockPATService) -> None:
        """Test retrieving a non-existent analysis."""
        with pytest.raises(ResourceNotFoundError):
            initialized_mock_pat.get_analysis_by_id("nonexistent_id")
    
    def test_get_patient_analyses(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test retrieving analyses for a patient."""
        # Create analyses for patient123
        patient_id = "patient123"
        for _ in range(3):
            initialized_mock_pat.analyze_actigraphy(
                patient_id=patient_id,
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0,
                device_info=sample_device_info,
                analysis_types=["activity_level_analysis"]
            )
        
        # Create analyses for patient456
        for _ in range(2):
            initialized_mock_pat.analyze_actigraphy(
                patient_id="patient456",
                readings=sample_readings,
                start_time="2025-03-28T14:00:00Z",
                end_time="2025-03-28T14:30:00Z",
                sampling_rate_hz=10.0,
                device_info=sample_device_info,
                analysis_types=["activity_level_analysis"]
            )
        
        # Retrieve analyses for patient123
        result = initialized_mock_pat.get_patient_analyses(
            patient_id=patient_id,
            limit=10,
            offset=0
        )
        
        # Verify result
        assert "analyses" in result
        assert "pagination" in result
        assert len(result["analyses"]) == 3
        assert result["pagination"]["total"] == 3
        assert result["pagination"]["limit"] == 10
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["has_more"] is False
        
        # Test pagination
        result = initialized_mock_pat.get_patient_analyses(
            patient_id=patient_id,
            limit=2,
            offset=0
        )
        assert len(result["analyses"]) == 2
        assert result["pagination"]["total"] == 3
        assert result["pagination"]["has_more"] is True
        
        result = initialized_mock_pat.get_patient_analyses(
            patient_id=patient_id,
            limit=2,
            offset=2
        )
        assert len(result["analyses"]) == 1
        assert result["pagination"]["total"] == 3
        assert result["pagination"]["has_more"] is False
    
    def test_get_model_info(self, initialized_mock_pat: MockPATService) -> None:
        """Test retrieving model information."""
        # Get model info
        result = initialized_mock_pat.get_model_info()
        
        # Verify result
        assert "name" in result
        assert "version" in result
        assert "description" in result
        assert "capabilities" in result
        assert "maintainer" in result
        assert "last_updated" in result
        assert "active" in result
        assert isinstance(result["capabilities"], list)
        assert "activity_level_analysis" in result["capabilities"]
    
    def test_integrate_with_digital_twin(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test integration with a digital twin profile."""
        # Create an analysis first
        patient_id = "patient123"
        profile_id = "profile123"
        
        analysis = initialized_mock_pat.analyze_actigraphy(
            patient_id=patient_id,
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=["activity_level_analysis", "sleep_analysis"]
        )
        analysis_id = analysis["analysis_id"]
        
        # Integrate with digital twin
        result = initialized_mock_pat.integrate_with_digital_twin(
            patient_id=patient_id,
            profile_id=profile_id,
            analysis_id=analysis_id
        )
        
        # Verify result
        assert "integration_id" in result
        assert result["patient_id"] == patient_id
        assert result["profile_id"] == profile_id
        assert result["analysis_id"] == analysis_id
        assert result["status"] == "success"
        assert "insights" in result
        assert "profile_update" in result
        assert len(result["insights"]) > 0
        assert all(
            key in result["profile_update"]
            for key in ["updated_aspects", "confidence_score", "updated_at"]
        )
    
    def test_integrate_with_digital_twin_resource_not_found(
        self,
        initialized_mock_pat: MockPATService
    ) -> None:
        """Test integration with a non-existent analysis."""
        with pytest.raises(ResourceNotFoundError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                profile_id="profile123",
                analysis_id="nonexistent_id"
            )
    
    def test_integrate_with_digital_twin_authorization_error(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test integration with an analysis from a different patient."""
        # Create an analysis for patient123
        analysis = initialized_mock_pat.analyze_actigraphy(
            patient_id="patient123",
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=["activity_level_analysis"]
        )
        analysis_id = analysis["analysis_id"]
        
        # Try to integrate with a different patient
        with pytest.raises(AuthorizationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="different_patient",
                profile_id="profile123",
                analysis_id=analysis_id
            )
    
    def test_integration_validation_error(self, initialized_mock_pat: MockPATService) -> None:
        """Test integration with invalid parameters."""
        # Test empty patient_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="",
                profile_id="profile123",
                analysis_id="analysis123"
            )
        
        # Test empty profile_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                profile_id="",
                analysis_id="analysis123"
            )
        
        # Test empty analysis_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                profile_id="profile123",
                analysis_id=""
            )