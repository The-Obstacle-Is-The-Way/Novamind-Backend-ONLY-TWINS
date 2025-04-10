# -*- coding: utf-8 -*-
"""
Unit tests for the BiometricAlert domain entity.

These tests verify that the BiometricAlert entity correctly implements
its business logic and state transitions.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domain.entities.digital_twin.biometric_alert import (
    BiometricAlert,
    AlertPriority,
    AlertStatus
)


@pytest.fixture
def sample_patient_id():
    """Create a sample patient ID."""
    # Use a fixed UUID for testing to ensure reproducibility
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_provider_id():
    """Create a sample provider ID."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_rule_id():
    """Create a sample rule ID."""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def sample_data_points():
    """Create sample biometric data points."""
    # Use a fixed timestamp for testing to ensure reproducibility
    timestamp = datetime(2025, 3, 27, 12, 0, 0).isoformat()
    return [
        {
            "data_type": "heart_rate",
            "value": 120.0,
            "timestamp": timestamp,
            "source": "apple_watch"
        }
    ]


@pytest.fixture
def sample_alert(sample_patient_id, sample_rule_id, sample_data_points):
    """Create a sample biometric alert."""
    return BiometricAlert(
        patient_id=sample_patient_id,
        alert_type="elevated_heart_rate",
        description="Heart rate exceeded threshold",
        priority=AlertPriority.WARNING,
        data_points=sample_data_points,
        rule_id=sample_rule_id
    )


@pytest.mark.venv_only
class TestBiometricAlert:
    """Tests for the BiometricAlert domain entity."""
    
    @pytest.mark.venv_only
def test_init_with_defaults(self, sample_patient_id, sample_rule_id, sample_data_points):
        """Test initializing a BiometricAlert with default values."""
        # Arrange & Act
        alert = BiometricAlert(
            patient_id=sample_patient_id,
            alert_type="elevated_heart_rate",
            description="Heart rate exceeded threshold",
            priority=AlertPriority.WARNING,
            data_points=sample_data_points,
            rule_id=sample_rule_id
        )
        
        # Assert
        assert alert.patient_id == sample_patient_id
        assert alert.alert_type == "elevated_heart_rate"
        assert alert.description == "Heart rate exceeded threshold"
        assert alert.priority == AlertPriority.WARNING
        assert alert.data_points == sample_data_points
        assert alert.rule_id == sample_rule_id
        assert alert.alert_id is not None
        assert alert.status == AlertStatus.NEW
        assert alert.acknowledged_by is None
        assert alert.acknowledged_at is None
        assert alert.resolved_by is None
        assert alert.resolved_at is None
        assert alert.resolution_notes is None
        assert isinstance(alert.metadata, dict)
        assert len(alert.metadata) == 0
    
    @pytest.mark.venv_only
def test_init_with_custom_values(self, sample_patient_id, sample_rule_id, sample_data_points):
        """Test initializing a BiometricAlert with custom values."""
        # Arrange
        alert_id = uuid4()
        created_at = datetime.utcnow() - timedelta(hours=1)
        updated_at = datetime.utcnow() - timedelta(minutes=30)
        metadata = {"source_system": "test_system"}
        
        # Act
        alert = BiometricAlert(
            patient_id=sample_patient_id,
            alert_type="elevated_heart_rate",
            description="Heart rate exceeded threshold",
            priority=AlertPriority.WARNING,
            data_points=sample_data_points,
            rule_id=sample_rule_id,
            alert_id=alert_id,
            created_at=created_at,
            updated_at=updated_at,
            status=AlertStatus.ACKNOWLEDGED,
            metadata=metadata
        )
        
        # Assert
        assert alert.alert_id == alert_id
        assert alert.created_at == created_at
        assert alert.updated_at == updated_at
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.metadata == metadata
    
    @pytest.mark.venv_only
def test_acknowledge(self, sample_alert, sample_provider_id):
        """Test acknowledging an alert."""
        # Arrange
        assert sample_alert.status == AlertStatus.NEW
        assert sample_alert.acknowledged_by is None
        assert sample_alert.acknowledged_at is None
        
        # Act
        sample_alert.acknowledge(sample_provider_id)
        
        # Assert
        assert sample_alert.status == AlertStatus.ACKNOWLEDGED
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_acknowledge_already_acknowledged(self, sample_alert, sample_provider_id):
        """Test acknowledging an already acknowledged alert."""
        # Arrange
        original_provider_id = UUID("00000000-0000-0000-0000-000000000003")
        sample_alert.acknowledge(original_provider_id)
        original_acknowledged_at = sample_alert.acknowledged_at
        
        # Act
        sample_alert.acknowledge(sample_provider_id)
        
        # Assert - Should not change the acknowledgment
        assert sample_alert.status == AlertStatus.ACKNOWLEDGED
        assert sample_alert.acknowledged_by == original_provider_id
        assert sample_alert.acknowledged_at == original_acknowledged_at
    
    @pytest.mark.venv_only
def test_mark_in_progress(self, sample_alert, sample_provider_id):
        """Test marking an alert as in progress."""
        # Arrange
        assert sample_alert.status == AlertStatus.NEW
        
        # Act
        sample_alert.mark_in_progress(sample_provider_id)
        
        # Assert
        assert sample_alert.status == AlertStatus.IN_PROGRESS
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_mark_in_progress_from_acknowledged(self, sample_alert, sample_provider_id):
        """Test marking an acknowledged alert as in progress."""
        # Arrange
        sample_alert.acknowledge(sample_provider_id)
        assert sample_alert.status == AlertStatus.ACKNOWLEDGED
        
        # Act
        sample_alert.mark_in_progress(sample_provider_id)
        
        # Assert
        assert sample_alert.status == AlertStatus.IN_PROGRESS
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_resolve(self, sample_alert, sample_provider_id):
        """Test resolving an alert."""
        # Arrange
        assert sample_alert.status == AlertStatus.NEW
        notes = "Issue resolved after patient reduced activity"
        
        # Act
        sample_alert.resolve(sample_provider_id, notes)
        
        # Assert
        assert sample_alert.status == AlertStatus.RESOLVED
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.resolved_by == sample_provider_id
        assert sample_alert.resolved_at is not None
        assert sample_alert.resolution_notes == notes
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_resolve_from_in_progress(self, sample_alert, sample_provider_id):
        """Test resolving an in-progress alert."""
        # Arrange
        sample_alert.mark_in_progress(sample_provider_id)
        assert sample_alert.status == AlertStatus.IN_PROGRESS
        notes = "Issue resolved after patient reduced activity"
        
        # Act
        sample_alert.resolve(sample_provider_id, notes)
        
        # Assert
        assert sample_alert.status == AlertStatus.RESOLVED
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.resolved_by == sample_provider_id
        assert sample_alert.resolved_at is not None
        assert sample_alert.resolution_notes == notes
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_dismiss(self, sample_alert, sample_provider_id):
        """Test dismissing an alert."""
        # Arrange
        assert sample_alert.status == AlertStatus.NEW
        notes = "False positive due to device calibration"
        
        # Act
        sample_alert.dismiss(sample_provider_id, notes)
        
        # Assert
        assert sample_alert.status == AlertStatus.DISMISSED
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.resolved_by == sample_provider_id
        assert sample_alert.resolved_at is not None
        assert sample_alert.resolution_notes == notes
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_dismiss_from_acknowledged(self, sample_alert, sample_provider_id):
        """Test dismissing an acknowledged alert."""
        # Arrange
        sample_alert.acknowledge(sample_provider_id)
        assert sample_alert.status == AlertStatus.ACKNOWLEDGED
        notes = "False positive due to device calibration"
        
        # Act
        sample_alert.dismiss(sample_provider_id, notes)
        
        # Assert
        assert sample_alert.status == AlertStatus.DISMISSED
        assert sample_alert.acknowledged_by == sample_provider_id
        assert sample_alert.acknowledged_at is not None
        assert sample_alert.resolved_by == sample_provider_id
        assert sample_alert.resolved_at is not None
        assert sample_alert.resolution_notes == notes
        assert sample_alert.updated_at is not None
    
    @pytest.mark.venv_only
def test_string_representation(self, sample_alert):
        """Test the string representation of the alert."""
        # Act
        string_repr = str(sample_alert)
        
        # Assert
        assert f"alert_id={sample_alert.alert_id}" in string_repr
        assert f"patient_id={sample_alert.patient_id}" in string_repr
        assert f"alert_type={sample_alert.alert_type}" in string_repr
        assert f"priority={sample_alert.priority}" in string_repr
        assert f"status={sample_alert.status}" in string_repr