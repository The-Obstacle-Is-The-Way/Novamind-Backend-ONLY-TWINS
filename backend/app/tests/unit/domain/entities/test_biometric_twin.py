# -*- coding: utf-8 -*-
"""
Unit tests for BiometricTwin domain entities.

These tests verify that the BiometricTwin and related entities
correctly handle data and maintain their integrity.
"""

from datetime import datetime, UTC, timedelta
from uuid import UUID, uuid4
import pytest

from app.domain.entities.biometric_twin import BiometricDataPoint, BiometricTwin


@pytest.fixture
def sample_patient_id():
    """Create a sample patient ID."""
    
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_data_point(sample_patient_id):
    """Create a sample biometric data point."""
    
    return BiometricDataPoint(
        data_id=UUID("00000000-0000-0000-0000-000000000001"),
        patient_id=sample_patient_id,
        data_type="heart_rate",
        value=75.0,
        timestamp=datetime.now(UTC),
        source="apple_watch",
        metadata={"activity": "resting"},
        confidence=0.95
    )


@pytest.fixture
def sample_twin(sample_patient_id):
    """Create a sample biometric twin."""
    now = datetime.now(UTC)
    return BiometricTwin(
        twin_id=UUID("00000000-0000-0000-0000-000000000002"),
        patient_id=sample_patient_id,
        created_at=now,
        updated_at=now,
        status="active"
    )


class TestBiometricDataPoint:
    """Tests for the BiometricDataPoint entity."""
    
    def test_initialization(self, sample_patient_id):
        """Test that a BiometricDataPoint can be initialized with all required attributes."""
        data_id = uuid4()
        timestamp = datetime.now(UTC)
        
        data_point = BiometricDataPoint(
            data_id=data_id,
            patient_id=sample_patient_id,
            data_type="heart_rate",
            value=75.0,
            timestamp=timestamp,
            source="apple_watch"
        )
        
        assert data_point.data_id  ==  data_id
        assert data_point.patient_id  ==  sample_patient_id
        assert data_point.data_type  ==  "heart_rate"
        assert data_point.value  ==  75.0
        assert data_point.timestamp  ==  timestamp
        assert data_point.source  ==  "apple_watch"
        assert data_point.metadata  ==  {}
        assert data_point.confidence  ==  1.0
    
    def test_initialization_with_optional_attributes(self, sample_patient_id):
        """Test that a BiometricDataPoint can be initialized with optional attributes."""
        data_id = uuid4()
        timestamp = datetime.now(UTC)
        metadata = {"activity": "running", "location": "outdoors"}
        
        data_point = BiometricDataPoint(
            data_id=data_id,
            patient_id=sample_patient_id,
            data_type="heart_rate",
            value=120.0,
            timestamp=timestamp,
            source="apple_watch",
            metadata=metadata,
            confidence=0.85
        )
        
        assert data_point.metadata  ==  metadata
        assert data_point.confidence  ==  0.85
    
    def test_equality(self, sample_patient_id):
        """Test that BiometricDataPoint equality works correctly."""
        data_id = uuid4()
        timestamp = datetime.now(UTC)
        
        data_point1 = BiometricDataPoint(
            data_id=data_id,
            patient_id=sample_patient_id,
            data_type="heart_rate",
            value=75.0,
            timestamp=timestamp,
            source="apple_watch"
        )
        
        data_point2 = BiometricDataPoint(
            data_id=data_id,
            patient_id=sample_patient_id,
            data_type="heart_rate",
            value=75.0,
            timestamp=timestamp,
            source="apple_watch"
        )
        
        data_point3 = BiometricDataPoint(
            data_id=uuid4(),  # Different ID
            patient_id=sample_patient_id,
            data_type="heart_rate",
            value=75.0,
            timestamp=timestamp,
            source="apple_watch"
        )
        
        assert data_point1  ==  data_point2
        assert data_point1  !=  data_point3
        assert data_point1  !=  "not a data point"
    
    def test_representation(self, sample_data_point):
        """Test that the string representation of a BiometricDataPoint is correct."""
        repr_str = repr(sample_data_point)
        
        assert "BiometricDataPoint" in repr_str
        assert str(sample_data_point.data_id) in repr_str
        assert str(sample_data_point.patient_id) in repr_str
        assert sample_data_point.data_type in repr_str
        assert str(sample_data_point.value) in repr_str


class TestBiometricTwin:
    """Tests for the BiometricTwin entity."""
    
    def test_initialization(self, sample_patient_id):
        """Test that a BiometricTwin can be initialized with all required attributes."""
        twin_id = uuid4()
        now = datetime.now(UTC)
        
        twin = BiometricTwin(
            twin_id=twin_id,
            patient_id=sample_patient_id,
            created_at=now,
            updated_at=now,
            status="initializing"
        )
        
        assert twin.twin_id  ==  twin_id
        assert twin.patient_id  ==  sample_patient_id
        assert twin.created_at  ==  now
        assert twin.updated_at  ==  now
        assert twin.status  ==  "initializing"
        assert twin.data_points  ==  {}
        assert twin.models  ==  {}
        assert twin.insights  ==  {}
    
    def test_add_data_point(self, sample_twin, sample_data_point):
        """Test that a data point can be added to a twin."""
        # Add the data point
        sample_twin.add_data_point(sample_data_point)
        
        # Check that it was added correctly
        assert sample_data_point.data_type in sample_twin.data_points
        assert sample_data_point.timestamp in sample_twin.data_points[sample_data_point.data_type]
        assert sample_twin.data_points[sample_data_point.data_type][sample_data_point.timestamp] == sample_data_point
        
        # Check that updated_at was updated
        assert sample_twin.updated_at > sample_twin.created_at
    
    def test_add_data_point_wrong_patient(self, sample_twin):
        """Test that adding a data point with the wrong patient ID raises an error."""
        wrong_patient_data_point = BiometricDataPoint(
            data_id=uuid4(),
            patient_id=uuid4(),  # Different patient ID
            data_type="heart_rate",
            value=75.0,
            timestamp=datetime.now(UTC),
            source="apple_watch"
        )
        
        with pytest.raises(ValueError):
            sample_twin.add_data_point(wrong_patient_data_point)
    
    def test_get_latest_data_point(self, sample_twin, sample_data_point):
        """Test that the latest data point can be retrieved."""
        # Add the data point
        sample_twin.add_data_point(sample_data_point)
        
        # Add another data point with a later timestamp
        later_data_point = BiometricDataPoint(
            data_id=uuid4(),
            patient_id=sample_twin.patient_id,
            data_type=sample_data_point.data_type,
            value=80.0,
            timestamp=sample_data_point.timestamp + timedelta(minutes=5),
            source=sample_data_point.source
        )
        sample_twin.add_data_point(later_data_point)
        
        # Get the latest data point
        latest = sample_twin.get_latest_data_point(sample_data_point.data_type)
        
        # Check that it's the later one
        assert latest  ==  later_data_point
    
    def test_get_latest_data_point_no_data(self, sample_twin):
        """Test that get_latest_data_point returns None when no data points exist."""
        assert sample_twin.get_latest_data_point("heart_rate") is None
    
    def test_get_data_points_in_range(self, sample_twin):
        """Test that data points within a time range can be retrieved."""
        # Create data points at different times
        now = datetime.now(UTC)
        data_type = "heart_rate"
        
        data_points = [
            BiometricDataPoint(
                data_id=uuid4(),
                patient_id=sample_twin.patient_id,
                data_type=data_type,
                value=75.0 + i,
                timestamp=now + timedelta(hours=i),
                source="apple_watch"
            )
            for i in range(5)
        ]
        
        # Add the data points to the twin
        for dp in data_points:
            sample_twin.add_data_point(dp)
        
        # Get data points in a specific range
        start_time = now + timedelta(hours=1)
        end_time = now + timedelta(hours=3)
        range_points = sample_twin.get_data_points_in_range(data_type, start_time, end_time)
        
        # Check that only the points in the range were returned
        assert len(range_points) == 3
        for i in range(1, 4):
            assert (now + timedelta(hours=i)) in range_points
            assert range_points[now + timedelta(hours=i)] == data_points[i]
    
    def test_get_data_points_in_range_no_data(self, sample_twin):
        """Test that get_data_points_in_range returns an empty dict when no data points exist."""
        now = datetime.now(UTC)
        range_points = sample_twin.get_data_points_in_range(
            "heart_rate",
            now,
            now + timedelta(hours=1)
        )
        assert range_points  ==  {}
    
    def test_representation(self, sample_twin, sample_data_point):
        """Test that the string representation of a BiometricTwin is correct."""
        # Add a data point
        sample_twin.add_data_point(sample_data_point)
        
        # Get the representation
        repr_str = repr(sample_twin)
        
        # Check that it contains the expected information
        assert "BiometricTwin" in repr_str
        assert str(sample_twin.twin_id) in repr_str
        assert str(sample_twin.patient_id) in repr_str
        assert sample_twin.status in repr_str
        assert "data_points=1" in repr_str