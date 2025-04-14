"""
Unit tests for the mock PAT service implementation.

This module contains unit tests for the MockPAT service, verifying that it
correctly implements the PATInterface.
"""

from app.core.services.ml.pat.mock import MockPATService  # Corrected import
from app.core.services.ml.pat.interface import PATInterface
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
    ValidationError
)


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
        timestamp = (base_time + datetime.timedelta(seconds=i / 10)).isoformat().replace("+00:00", "Z")
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


@pytest.mark.venv_only
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
        patient_id = "patient123"
        analysis_types = ["activity_level_analysis"]
        result = initialized_mock_pat.analyze_actigraphy(
            patient_id=patient_id,
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=analysis_types
        )
        analysis_id = result["analysis_id"]

        # Retrieve the analysis
        retrieved = initialized_mock_pat.get_analysis_by_id(analysis_id)

        # Verify result
        assert retrieved == result

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
        analysis_types = ["activity_level_analysis"]
        result1 = initialized_mock_pat.analyze_actigraphy(
            patient_id=patient_id,
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=analysis_types
        )
        result2 = initialized_mock_pat.analyze_actigraphy(
            patient_id=patient_id,
            readings=sample_readings,
            start_time="2025-03-28T15:00:00Z",
            end_time="2025-03-28T15:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=analysis_types
        )

        # Retrieve analyses for the patient
        analyses = initialized_mock_pat.get_patient_analyses(patient_id)

        # Verify results
        assert len(analyses) == 2
        assert any(a["analysis_id"] == result1["analysis_id"] for a in analyses)
        assert any(a["analysis_id"] == result2["analysis_id"] for a in analyses)

        # Test with limit
        limited_analyses = initialized_mock_pat.get_patient_analyses(patient_id, limit=1)
        assert len(limited_analyses) == 1

        # Test with analysis_type filter
        filtered_analyses = initialized_mock_pat.get_patient_analyses(
            patient_id, analysis_type="activity_level_analysis"
        )
        assert len(filtered_analyses) == 2

        # Test with date range
        date_filtered = initialized_mock_pat.get_patient_analyses(
            patient_id, start_date="2025-03-28T14:30:00Z", end_date="2025-03-28T16:00:00Z"
        )
        assert len(date_filtered) == 1
        assert date_filtered[0]["analysis_id"] == result2["analysis_id"]

    def test_get_model_info(self, initialized_mock_pat: MockPATService) -> None:
        """Test retrieving model information."""
        info = initialized_mock_pat.get_model_info()
        assert "models" in info
        assert "version" in info
        assert "timestamp" in info
        assert len(info["models"]) > 0
        assert all("id" in model for model in info["models"])
        assert all("name" in model for model in info["models"])
        assert all("version" in model for model in info["models"])
        assert all("description" in model for model in info["models"])
        assert all("capabilities" in model for model in info["models"])
        assert all("input_data_types" in model for model in info["models"])
        assert all("output_metrics" in model for model in info["models"])

    def test_integrate_with_digital_twin(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test integration with a digital twin profile."""
        # Create an analysis first
        patient_id = "patient123"
        analysis_types = ["activity_level_analysis"]
        analysis_result = initialized_mock_pat.analyze_actigraphy(
            patient_id=patient_id,
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=analysis_types
        )
        analysis_id = analysis_result["analysis_id"]

        # Integrate with digital twin
        profile_id = "profile456"
        integration_result = initialized_mock_pat.integrate_with_digital_twin(
            patient_id=patient_id,
            analysis_id=analysis_id,
            profile_id=profile_id,
            integration_types=["behavioral", "physiological"],
            metadata={"source": "test"}
        )

        # Verify result
        assert "integration_id" in integration_result
        assert integration_result["patient_id"] == patient_id
        assert integration_result["analysis_id"] == analysis_id
        assert integration_result["profile_id"] == profile_id
        assert set(integration_result["integration_types"]) == {"behavioral", "physiological"}
        assert "timestamp" in integration_result
        assert integration_result["metadata"] == {"source": "test"}
        assert "integration_results" in integration_result
        assert "behavioral" in integration_result["integration_results"]
        assert "physiological" in integration_result["integration_results"]

        # Verify integration is stored
        integration_id = integration_result["integration_id"]
        assert integration_id in initialized_mock_pat._integrations
        assert initialized_mock_pat._integrations[integration_id]["profile_id"] == profile_id

    def test_integrate_with_digital_twin_resource_not_found(
        self, initialized_mock_pat: MockPATService
    ) -> None:
        """Test integration with a non-existent analysis."""
        with pytest.raises(ResourceNotFoundError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                analysis_id="nonexistent_id",
                profile_id="profile456",
                integration_types=["behavioral"],
                metadata={}
            )

    def test_integrate_with_digital_twin_authorization_error(
        self,
        initialized_mock_pat: MockPATService,
        sample_readings: List[Dict[str, Any]],
        sample_device_info: Dict[str, Any]
    ) -> None:
        """Test integration with an analysis from a different patient."""
        # Create an analysis for patient123
        analysis_result = initialized_mock_pat.analyze_actigraphy(
            patient_id="patient123",
            readings=sample_readings,
            start_time="2025-03-28T14:00:00Z",
            end_time="2025-03-28T14:30:00Z",
            sampling_rate_hz=10.0,
            device_info=sample_device_info,
            analysis_types=["activity_level_analysis"]
        )
        analysis_id = analysis_result["analysis_id"]

        # Attempt integration with a different patient_id
        with pytest.raises(AuthorizationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="different_patient",
                analysis_id=analysis_id,
                profile_id="profile456",
                integration_types=["behavioral"],
                metadata={}
            )

    def test_integration_validation_error(self, initialized_mock_pat: MockPATService) -> None:
        """Test integration with invalid parameters."""
        # Test empty patient_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="",
                analysis_id="some_id",
                profile_id="profile456",
                integration_types=["behavioral"],
                metadata={}
            )

        # Test empty analysis_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                analysis_id="",
                profile_id="profile456",
                integration_types=["behavioral"],
                metadata={}
            )

        # Test empty profile_id
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                analysis_id="some_id",
                profile_id="",
                integration_types=["behavioral"],
                metadata={}
            )

        # Test empty integration_types
        with pytest.raises(ValidationError):
            initialized_mock_pat.integrate_with_digital_twin(
                patient_id="patient123",
                analysis_id="some_id",
                profile_id="profile456",
                integration_types=[],
                metadata={}
            )
