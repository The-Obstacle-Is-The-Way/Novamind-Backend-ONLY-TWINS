"""Unit tests for BiometricTwin entity."""
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.domain.entities.biometric_twin import BiometricTwin
from app.domain.entities.biometric_data_point import BiometricDataPoint
from app.domain.value_objects.biometric_types import BiometricType


class TestBiometricTwin:
    """Test suite for BiometricTwin entity."""
    
    @pytest.fixture
    def sample_twin(self):
        """Create a sample biometric twin for testing."""
        return BiometricTwin(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            patient_id=UUID("00000000-0000-0000-0000-000000000002"),
            created_by=UUID("00000000-0000-0000-0000-000000000003")
        
    
    def test_initialization(self, sample_twin):
        """Test BiometricTwin initialization."""
        assert sample_twin.id == UUID("00000000-0000-0000-0000-000000000001")
        assert sample_twin.patient_id == UUID("00000000-0000-0000-0000-000000000002")
        assert sample_twin.created_by == UUID("00000000-0000-0000-0000-000000000003")
        assert sample_twin.data_points == {}
    
    def test_add_data_point(self, sample_twin):
        """Test adding a data point to the biometric twin."""
        # Create a sample data point
        data_point = BiometricDataPoint(
            data_id=uuid4(),
            patient_id=sample_twin.patient_id,
            data_type=BiometricType.HEART_RATE,
            value=75.0,
            timestamp=datetime.now(),
            source="apple_watch"
        
        
        # Add to the twin
    sample_twin.add_data_point(data_point)
        
        # Verify data point was added correctly
    assert BiometricType.HEART_RATE in sample_twin.data_points
    assert len(sample_twin.data_points[BiometricType.HEART_RATE]) == 1
    assert sample_twin.data_points[BiometricType.HEART_RATE][0] == data_point
    
    def test_add_multiple_data_points(self, sample_twin):
        """Test adding multiple data points of the same type."""
        now = datetime.now()
        data_points = []
        
        # Create 5 heart rate data points
    for i in range(5):
    data_points.append(BiometricDataPoint(
    data_id=uuid4(),
    patient_id=sample_twin.patient_id,
    data_type=BiometricType.HEART_RATE,
    value=75.0 + i,
    timestamp=now + timedelta(minutes=i),
    source="apple_watch"
    
        
        # Add all data points
    for dp in data_points:
    sample_twin.add_data_point(dp)
        
        # Verify all were added
    assert BiometricType.HEART_RATE in sample_twin.data_points
    assert len(sample_twin.data_points[BiometricType.HEART_RATE]) == 5
        
        # Verify they're stored in timestamp order
    stored_points = sample_twin.data_points[BiometricType.HEART_RATE]
    for i in range(1, len(stored_points)):
    assert stored_points[i-1].timestamp <= stored_points[i].timestamp
    
    def test_add_multiple_data_types(self, sample_twin):
        """Test adding data points of different types."""
        now = datetime.now()
        
        # Add a heart rate data point
    heart_point = BiometricDataPoint(
    data_id=uuid4(),
    patient_id=sample_twin.patient_id,
    data_type=BiometricType.HEART_RATE,
    value=75.0,
    timestamp=now,
    source="apple_watch"
    
    sample_twin.add_data_point(heart_point)
        
        # Add a step count data point
    step_point = BiometricDataPoint(
    data_id=uuid4(),
    patient_id=sample_twin.patient_id,
    data_type=BiometricType.STEP_COUNT,
    value=10000,
    timestamp=now,
    source="apple_watch"
    
    sample_twin.add_data_point(step_point)
        
        # Verify both types exist
    assert BiometricType.HEART_RATE in sample_twin.data_points
    assert BiometricType.STEP_COUNT in sample_twin.data_points
        
        # Verify each has the correct point
    assert len(sample_twin.data_points[BiometricType.HEART_RATE]) == 1
    assert len(sample_twin.data_points[BiometricType.STEP_COUNT]) == 1
    assert sample_twin.data_points[BiometricType.HEART_RATE][0] == heart_point
    assert sample_twin.data_points[BiometricType.STEP_COUNT][0] == step_point
    
    def test_get_latest_data_point(self, sample_twin):
        """Test getting the latest data point of a specific type."""
        now = datetime.now()
        data_type = BiometricType.HEART_RATE
        
        # Create data points with different timestamps
    data_points = []
    for i in range(5):
    data_points.append(BiometricDataPoint(
    data_id=uuid4(),
    patient_id=sample_twin.patient_id,
    data_type=data_type,
    value=75.0 + i,
    timestamp=now + timedelta(hours=i),
    source="apple_watch"
    
        
        # Add them out of order to test sorting
    sample_twin.add_data_point(data_points[2])  # middle
    sample_twin.add_data_point(data_points[0])  # earliest
    sample_twin.add_data_point(data_points[4])  # latest
    sample_twin.add_data_point(data_points[1])
    sample_twin.add_data_point(data_points[3])
        
        # Get the latest
    latest = sample_twin.get_latest_data_point(data_type)
        
        # Should be the one with the highest timestamp (index 4)
    assert latest == data_points[4]
    
    def test_get_latest_data_point_empty(self, sample_twin):
        """Test getting the latest data point when none exist."""
        # No data points added, should return None
        latest = sample_twin.get_latest_data_point(BiometricType.HEART_RATE)
        assert latest is None
    
    def test_get_data_points_in_range(self, sample_twin):
        """Test getting data points within a time range."""
        now = datetime.now()
        data_type = BiometricType.HEART_RATE
        
        # Create data points across a 5-hour span
    data_points = []
    for i in range(5):
    data_points.append(BiometricDataPoint(
    data_id=uuid4(),
    patient_id=sample_twin.patient_id,
    data_type=data_type,
    value=75.0 + i,
    timestamp=now + timedelta(hours=i),
    source="apple_watch"
    
        
        # Add the data points to the twin
    for dp in data_points:
    sample_twin.add_data_point(dp)
        
        # Get data points in a specific range
    start_time = now + timedelta(hours=1)
    end_time = now + timedelta(hours=3)
    range_points = sample_twin.get_data_points_in_range(data_type, start_time, end_time)
        
        # Check that only the points in the range were returned
    assert len(range_points) == 3  # Should include hours 1, 2, 3
    for point in range_points:
    assert point.timestamp >= start_time
    assert point.timestamp <= end_time
        
        # Verify correct points were returned (indexes 1, 2, 3)
    assert data_points[1] in range_points
    assert data_points[2] in range_points
    assert data_points[3] in range_points
        
        # Verify excluded points were not returned
    assert data_points[0] not in range_points  # too early
    assert data_points[4] not in range_points  # too late
    
    def test_get_data_points_in_range_empty(self, sample_twin):
        """Test getting data points in a range when none exist in that range."""
        now = datetime.now()
        
        # Add a single data point
    data_point = BiometricDataPoint(
    data_id=uuid4(),
    patient_id=sample_twin.patient_id,
    data_type=BiometricType.HEART_RATE,
    value=75.0,
    timestamp=now,
    source="apple_watch"
    
    sample_twin.add_data_point(data_point)
        
        # Request a range that doesn't include the point
    start_time = now + timedelta(hours=1)
    end_time = now + timedelta(hours=2)
    range_points = sample_twin.get_data_points_in_range(
    BiometricType.HEART_RATE, start_time, end_time
    
        
        # Should return an empty list
    assert len(range_points) == 0
