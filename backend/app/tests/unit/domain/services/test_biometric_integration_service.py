# -*- coding: utf-8 -*-
"""
Unit tests for the BiometricIntegrationService.

This module contains tests for the BiometricIntegrationService, ensuring it
correctly integrates biometric data into patient digital twins.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID, uuid4

from app.domain.entities.digital_twin.biometric_twin import BiometricTwin, BiometricDataPoint
from app.domain.exceptions import BiometricIntegrationError
from app.domain.services.biometric_integration_service import BiometricIntegrationService


@pytest.mark.db_required
class TestBiometricIntegrationService:
    """Tests for the BiometricIntegrationService class."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a BiometricIntegrationService instance for testing."""
        return BiometricIntegrationService(biometric_twin_repository=mock_repository)
    
    @pytest.mark.db_required
def test_get_or_create_biometric_twin_existing(self, service, mock_repository):
        """Test retrieving an existing biometric twin."""
        # Arrange
        patient_id = uuid4()
        mock_twin = BiometricTwin(patient_id=patient_id)
        mock_repository.get_by_patient_id.return_value = mock_twin
        
        # Act
        result = service.get_or_create_biometric_twin(patient_id)
        
        # Assert
        assert result == mock_twin
        mock_repository.get_by_patient_id.assert_called_once_with(patient_id)
        mock_repository.save.assert_not_called()
    
    @pytest.mark.db_required
def test_get_or_create_biometric_twin_new(self, service, mock_repository):
        """Test creating a new biometric twin when one doesn't exist."""
        # Arrange
        patient_id = uuid4()
        mock_repository.get_by_patient_id.return_value = None
        mock_repository.save.side_effect = lambda twin: twin
        
        # Act
        result = service.get_or_create_biometric_twin(patient_id)
        
        # Assert
        assert isinstance(result, BiometricTwin)
        assert result.patient_id == patient_id
        mock_repository.get_by_patient_id.assert_called_once_with(patient_id)
        mock_repository.save.assert_called_once()
    
    @pytest.mark.db_required
def test_get_or_create_biometric_twin_error(self, service, mock_repository):
        """Test error handling when repository operations fail."""
        # Arrange
        patient_id = uuid4()
        mock_repository.get_by_patient_id.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(BiometricIntegrationError) as exc_info:
            service.get_or_create_biometric_twin(patient_id)
        
        assert "Failed to get or create biometric twin" in str(exc_info.value)
    
    @pytest.mark.db_required
def test_add_biometric_data(self, service, mock_repository):
        """Test adding a biometric data point."""
        # Arrange
        patient_id = uuid4()
        mock_twin = MagicMock(spec=BiometricTwin)
        mock_twin.patient_id = patient_id
        
        # Mock the get_or_create_biometric_twin method
        service.get_or_create_biometric_twin = MagicMock(return_value=mock_twin)
        
        # Act
        data_point = service.add_biometric_data(
            patient_id=patient_id,
            data_type="heart_rate",
            value=75,
            source="smartwatch",
            metadata={"activity": "resting"},
            confidence=0.95
        )
        
        # Assert
        assert data_point.data_type == "heart_rate"
        assert data_point.value == 75
        assert data_point.source == "smartwatch"
        assert data_point.metadata == {"activity": "resting"}
        assert data_point.confidence == 0.95
        
        mock_twin.add_data_point.assert_called_once()
        mock_repository.save.assert_called_once_with(mock_twin)
    
    @pytest.mark.db_required
def test_add_biometric_data_with_error(self, service, mock_repository):
        """Test error handling when adding biometric data fails."""
        # Arrange
        patient_id = uuid4()
        service.get_or_create_biometric_twin = MagicMock(side_effect=Exception("Repository error"))
        
        # Act & Assert
        with pytest.raises(BiometricIntegrationError) as exc_info:
            service.add_biometric_data(
                patient_id=patient_id,
                data_type="heart_rate",
                value=75,
                source="smartwatch"
            )
        
        assert "Failed to add biometric data" in str(exc_info.value)
    
    @pytest.mark.db_required
def test_batch_add_biometric_data(self, service, mock_repository):
        """Test adding multiple biometric data points in a batch."""
        # Arrange
        patient_id = uuid4()
        mock_twin = MagicMock(spec=BiometricTwin)
        mock_twin.patient_id = patient_id
        
        # Mock the get_or_create_biometric_twin method
        service.get_or_create_biometric_twin = MagicMock(return_value=mock_twin)
        
        # Prepare batch data
        batch_data = [
            {
                "data_type": "heart_rate",
                "value": 75,
                "source": "smartwatch",
                "timestamp": datetime.utcnow()
            },
            {
                "data_type": "blood_pressure",
                "value": "120/80",
                "source": "blood_pressure_monitor",
                "timestamp": datetime.utcnow()
            }
        ]
        
        # Act
        result = service.batch_add_biometric_data(patient_id, batch_data)
        
        # Assert
        assert len(result) == 2
        assert result[0].data_type == "heart_rate"
        assert result[1].data_type == "blood_pressure"
        
        assert mock_twin.add_data_point.call_count == 2
        mock_repository.save.assert_called_once_with(mock_twin)
    
    @pytest.mark.db_required
def test_get_biometric_data(self, service, mock_repository):
        """Test retrieving biometric data with filtering."""
        # Arrange
        patient_id = uuid4()
        mock_twin = MagicMock(spec=BiometricTwin)
        
        # Create some test data points
        now = datetime.utcnow()
        data_points = [
            BiometricDataPoint(
                data_type="heart_rate",
                value=75,
                timestamp=now,
                source="smartwatch"
            ),
            BiometricDataPoint(
                data_type="heart_rate",
                value=80,
                timestamp=now - timedelta(hours=1),
                source="smartwatch"
            ),
            BiometricDataPoint(
                data_type="blood_pressure",
                value="120/80",
                timestamp=now,
                source="blood_pressure_monitor"
            )
        ]
        
        # Set up the mock twin's data points
        mock_twin.data_points = data_points
        mock_repository.get_by_patient_id.return_value = mock_twin
        
        # Act - Get all heart rate data
        result = service.get_biometric_data(
            patient_id=patient_id,
            data_type="heart_rate"
        )
        
        # Assert
        assert len(result) == 2
        assert all(dp.data_type == "heart_rate" for dp in result)
        
        # Act - Get data from a specific source
        result = service.get_biometric_data(
            patient_id=patient_id,
            source="blood_pressure_monitor"
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].data_type == "blood_pressure"
    
    @pytest.mark.db_required
def test_get_biometric_data_no_twin(self, service, mock_repository):
        """Test retrieving biometric data when no twin exists."""
        # Arrange
        patient_id = uuid4()
        mock_repository.get_by_patient_id.return_value = None
        
        # Act
        result = service.get_biometric_data(patient_id)
        
        # Assert
        assert result == []
    
    @pytest.mark.db_required
def test_analyze_trends(self, service, mock_repository):
        """Test analyzing trends in biometric data."""
        # Arrange
        patient_id = uuid4()
        
        # Mock the get_biometric_data method to return test data
        now = datetime.utcnow()
        test_data = [
            BiometricDataPoint(
                data_type="heart_rate",
                value=70,
                timestamp=now - timedelta(days=3),
                source="smartwatch"
            ),
            BiometricDataPoint(
                data_type="heart_rate",
                value=75,
                timestamp=now - timedelta(days=2),
                source="smartwatch"
            ),
            BiometricDataPoint(
                data_type="heart_rate",
                value=80,
                timestamp=now - timedelta(days=1),
                source="smartwatch"
            ),
            BiometricDataPoint(
                data_type="heart_rate",
                value=85,
                timestamp=now,
                source="smartwatch"
            )
        ]
        
        service.get_biometric_data = MagicMock(return_value=test_data)
        
        # Act
        result = service.analyze_trends(
            patient_id=patient_id,
            data_type="heart_rate",
            window_days=7
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["data_type"] == "heart_rate"
        assert result["data_points_count"] == 4
        assert result["trend"] == "increasing"  # Values are increasing
        assert result["average"] == 77.5  # (70+75+80+85)/4
        assert result["minimum"] == 70
        assert result["maximum"] == 85
    
    @pytest.mark.db_required
def test_analyze_trends_insufficient_data(self, service, mock_repository):
        """Test analyzing trends with insufficient data."""
        # Arrange
        patient_id = uuid4()
        service.get_biometric_data = MagicMock(return_value=[])
        
        # Act
        result = service.analyze_trends(
            patient_id=patient_id,
            data_type="heart_rate"
        )
        
        # Assert
        assert result["status"] == "insufficient_data"
    
    @pytest.mark.db_required
def test_detect_correlations(self, service, mock_repository):
        """Test detecting correlations between different biometric data types."""
        # Arrange
        patient_id = uuid4()
        mock_twin = MagicMock(spec=BiometricTwin)
        mock_repository.get_by_patient_id.return_value = mock_twin
        
        # Mock the get_data_points_by_type method to return sufficient data
        now = datetime.utcnow()
        heart_rate_data = [
            BiometricDataPoint(
                data_type="heart_rate",
                value=70 + i,
                timestamp=now - timedelta(hours=i),
                source="smartwatch"
            ) for i in range(10)
        ]
        
        sleep_data = [
            BiometricDataPoint(
                data_type="sleep_quality",
                value=0.8 - (i * 0.05),
                timestamp=now - timedelta(hours=i),
                source="sleep_tracker"
            ) for i in range(10)
        ]
        
        # Configure the mock to return different data based on the data_type argument
        def get_data_points_by_type_side_effect(data_type, *args, **kwargs):
            if data_type == "heart_rate":
                return heart_rate_data
            elif data_type == "sleep_quality":
                return sleep_data
            else:
                return []
        
        mock_twin.get_data_points_by_type.side_effect = get_data_points_by_type_side_effect
        
        # Act
        result = service.detect_correlations(
            patient_id=patient_id,
            primary_data_type="heart_rate",
            secondary_data_types=["sleep_quality", "activity_level"]
        )
        
        # Assert
        assert "sleep_quality" in result
        assert isinstance(result["sleep_quality"], float)
        assert "activity_level" in result
        assert isinstance(result["activity_level"], float)
    
    @pytest.mark.db_required
def test_connect_device(self, service, mock_repository):
        """Test connecting a device to a biometric twin."""
        # Arrange
        patient_id = uuid4()
        mock_twin = MagicMock(spec=BiometricTwin)
        
        # Mock the get_or_create_biometric_twin method
        service.get_or_create_biometric_twin = MagicMock(return_value=mock_twin)
        
        # Mock the add_biometric_data method
        service.add_biometric_data = MagicMock()
        
        # Act
        result = service.connect_device(
            patient_id=patient_id,
            device_id="smartwatch-123",
            device_type="smartwatch",
            connection_metadata={"model": "Apple Watch Series 7"}
        )
        
        # Assert
        assert result is True
        mock_twin.connect_device.assert_called_once_with("smartwatch-123")
        service.add_biometric_data.assert_called_once()
        mock_repository.save.assert_called_once_with(mock_twin)
    
    @pytest.mark.db_required
def test_disconnect_device(self, service, mock_repository):
        """Test disconnecting a device from a biometric twin."""
        # Arrange
        patient_id = uuid4()
        mock_twin = MagicMock(spec=BiometricTwin)
        mock_repository.get_by_patient_id.return_value = mock_twin
        
        # Mock the add_biometric_data method
        service.add_biometric_data = MagicMock()
        
        # Act
        result = service.disconnect_device(
            patient_id=patient_id,
            device_id="smartwatch-123",
            reason="user_requested"
        )
        
        # Assert
        assert result is True
        mock_twin.disconnect_device.assert_called_once_with("smartwatch-123")
        service.add_biometric_data.assert_called_once()
        mock_repository.save.assert_called_once_with(mock_twin)
    
    @pytest.mark.db_required
def test_disconnect_device_no_twin(self, service, mock_repository):
        """Test disconnecting a device when no twin exists."""
        # Arrange
        patient_id = uuid4()
        mock_repository.get_by_patient_id.return_value = None
        
        # Act
        result = service.disconnect_device(
            patient_id=patient_id,
            device_id="smartwatch-123"
        )
        
        # Assert
        assert result is False