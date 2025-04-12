"""Unit tests for BiometricTwin domain entity."""
import pytest
from datetime import datetime, timedelta
import uuid

from app.domain.entities.biometric_twin_enhanced import (
    BiometricTwin,
    BiometricTimeseriesData,
    BiometricDataPoint,
    BiometricType,
    BiometricSource
)
from app.domain.value_objects.physiological_ranges import PhysiologicalRange


@pytest.fixture
def sample_data_points():
    """Create sample biometric data points for testing."""
    now = datetime.now()
    return [
        BiometricDataPoint(
            timestamp=now - timedelta(days=2),
            value=72.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        ),
        BiometricDataPoint(
            timestamp=now - timedelta(days=1),
            value=75.0,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        ),
        BiometricDataPoint(
            timestamp=now,
            value=70.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
    ]


@pytest.fixture
def sample_timeseries(sample_data_points):
    """Create a sample biometric timeseries for testing."""
    return BiometricTimeseriesData(
        biometric_type=BiometricType.HEART_RATE,
        unit="bpm",
        data_points=sample_data_points,
        physiological_range=PhysiologicalRange.get_default_range(BiometricType.HEART_RATE.value)
    )


@pytest.fixture
def sample_biometric_twin(sample_timeseries):
    """Create a sample biometric twin for testing."""
    twin_id = str(uuid.uuid4())
    patient_id = "patient-123"
    now = datetime.now()
    
    return BiometricTwin(
        id=twin_id,
        patient_id=patient_id,
        timeseries_data={BiometricType.HEART_RATE: sample_timeseries},
        created_at=now - timedelta(days=30),
        updated_at=now
    )


class TestBiometricDataPoint:
    """Tests for the BiometricDataPoint class."""
    
    def test_init(self):
        """Test initialization of BiometricDataPoint."""
        timestamp = datetime.now()
        value = 72.5
        source = BiometricSource.WEARABLE
        metadata = {"device": "fitbit"}
        
        data_point = BiometricDataPoint(
            timestamp=timestamp,
            value=value,
            source=source,
            metadata=metadata
        )
        
        assert data_point.timestamp == timestamp
        assert data_point.value == value
        assert data_point.source == source
        assert data_point.metadata == metadata
    
    def test_add_metadata(self):
        """Test adding metadata to a data point."""
        data_point = BiometricDataPoint(
            timestamp=datetime.now(),
            value=72.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
        
        data_point.add_metadata({"activity": "resting"})
        
        assert data_point.metadata == {"device": "fitbit", "activity": "resting"}
    
    def test_get_normalized_value(self):
        """Test getting normalized value from various data types."""
        # Simple numeric value
        dp1 = BiometricDataPoint(
            timestamp=datetime.now(),
            value=72.5,
            source=BiometricSource.WEARABLE
        )
        assert dp1.get_normalized_value() == 72.5
        
        # Dictionary with systolic value
        dp2 = BiometricDataPoint(
            timestamp=datetime.now(),
            value={"systolic": 120, "diastolic": 80},
            source=BiometricSource.CLINICAL
        )
        assert dp2.get_normalized_value() == 120.0
        
        # Dictionary with generic value
        dp3 = BiometricDataPoint(
            timestamp=datetime.now(),
            value={"value": 98.6},
            source=BiometricSource.CLINICAL
        )
        assert dp3.get_normalized_value() == 98.6
        
        # Non-numeric value that can't be normalized
        dp4 = BiometricDataPoint(
            timestamp=datetime.now(),
            value="normal",
            source=BiometricSource.PATIENT_REPORTED
        )
        assert dp4.get_normalized_value() == 0.0
    
    def test_to_dict(self):
        """Test converting a data point to dictionary."""
        timestamp = datetime.now()
        data_point = BiometricDataPoint(
            timestamp=timestamp,
            value=72.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
        
        result = data_point.to_dict()
        
        assert result["timestamp"] == timestamp.isoformat()
        assert result["value"] == 72.5
        assert result["source"] == "wearable"
        assert result["metadata"] == {"device": "fitbit"}
    
    def test_from_dict(self):
        """Test creating a data point from dictionary."""
        timestamp = datetime.now()
        data = {
            "timestamp": timestamp.isoformat(),
            "value": 72.5,
            "source": "wearable",
            "metadata": {"device": "fitbit"}
        }
        
        data_point = BiometricDataPoint.from_dict(data)
        
        assert data_point.timestamp == timestamp
        assert data_point.value == 72.5
        assert data_point.source == BiometricSource.WEARABLE
        assert data_point.metadata == {"device": "fitbit"}
    
    def test_comparison(self):
        """Test comparing data points by timestamp."""
        now = datetime.now()
        
        dp1 = BiometricDataPoint(
            timestamp=now - timedelta(hours=1),
            value=72.5,
            source=BiometricSource.WEARABLE
        )
        
        dp2 = BiometricDataPoint(
            timestamp=now,
            value=75.0,
            source=BiometricSource.WEARABLE
        )
        
        assert dp1 < dp2
        assert not (dp2 < dp1)


class TestBiometricTimeseriesData:
    """Tests for the BiometricTimeseriesData class."""
    
    def test_init(self, sample_data_points):
        """Test initialization of BiometricTimeseriesData."""
        timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.HEART_RATE,
            unit="bpm",
            data_points=sample_data_points
        )
        
        assert timeseries.biometric_type == BiometricType.HEART_RATE
        assert timeseries.unit == "bpm"
        assert len(timeseries.data_points) == 3
        assert timeseries.physiological_range is not None
        assert timeseries.physiological_range.min == 60.0
        assert timeseries.physiological_range.max == 100.0
    
    def test_add_data_point(self, sample_timeseries):
        """Test adding a data point to a timeseries."""
        new_point = BiometricDataPoint(
            timestamp=datetime.now() + timedelta(days=1),
            value=68.0,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
        
        initial_count = len(sample_timeseries.data_points)
        sample_timeseries.add_data_point(new_point)
        
        assert len(sample_timeseries.data_points) == initial_count + 1
        assert sample_timeseries.data_points[-1] == new_point
    
    def test_get_latest_value(self, sample_timeseries):
        """Test getting the latest value from a timeseries."""
        latest = sample_timeseries.get_latest_value()
        
        assert latest is not None
        assert latest.value == 70.5
    
    def test_get_values_in_range(self, sample_timeseries):
        """Test getting values within a time range."""
        now = datetime.now()
        # Correctly separate the timedelta parameters
        start_time = now - timedelta(days=1, hours=12)
        end_time = now + timedelta(hours=12)
        
        values = sample_timeseries.get_values_in_range(start_time, end_time)
        
        assert len(values) == 2
        assert values[0].value == 75.0
        assert values[1].value == 70.5
    
    def test_get_abnormal_values(self, sample_timeseries):
        """Test getting abnormal values from a timeseries."""
        # Add an abnormal value
        abnormal_point = BiometricDataPoint(
            timestamp=datetime.now() + timedelta(hours=1),
            value=110.0,  # Above normal range
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
        sample_timeseries.add_data_point(abnormal_point)
        
        abnormal_values = sample_timeseries.get_abnormal_values()
        
        assert len(abnormal_values) == 1
        assert abnormal_values[0].value == 110.0
    
    def test_get_critical_values(self, sample_timeseries):
        """Test getting critical values from a timeseries."""
        # Add a critical value
        critical_point = BiometricDataPoint(
            timestamp=datetime.now() + timedelta(hours=2),
            value=170.0,  # Above critical range
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit", "activity": "exercise"}
        )
        sample_timeseries.add_data_point(critical_point)
        
        critical_values = sample_timeseries.get_critical_values()
        
        assert len(critical_values) == 1
        assert critical_values[0].value == 170.0


class TestBiometricTwin:
    """Tests for the BiometricTwin class."""
    
    def test_init(self, sample_biometric_twin, sample_timeseries):
        """Test initialization of BiometricTwin."""
        assert sample_biometric_twin.patient_id == "patient-123"
        assert sample_biometric_twin.timeseries_data[BiometricType.HEART_RATE] == sample_timeseries
    
    def test_add_biometric_data(self, sample_biometric_twin):
        """Test adding a new biometric timeseries."""
        # Create a new timeseries
        bp_data_point = BiometricDataPoint(
            timestamp=datetime.now(),
            value={"systolic": 120, "diastolic": 80},
            source=BiometricSource.CLINICAL,
            metadata={"position": "sitting"}
        )
        bp_timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.BLOOD_PRESSURE,
            unit="mmHg",
            data_points=[bp_data_point]
        )
        
        # Add to twin
        sample_biometric_twin.add_biometric_data(bp_timeseries)
        
        assert BiometricType.BLOOD_PRESSURE in sample_biometric_twin.timeseries_data
        assert sample_biometric_twin.timeseries_data[BiometricType.BLOOD_PRESSURE] == bp_timeseries
    
    def test_add_data_point(self, sample_biometric_twin):
        """Test adding a data point to an existing timeseries."""
        new_point = BiometricDataPoint(
            timestamp=datetime.now() + timedelta(hours=1),
            value=68.0,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit"}
        )
        
        initial_count = len(sample_biometric_twin.timeseries_data[BiometricType.HEART_RATE].data_points)
        sample_biometric_twin.add_data_point(BiometricType.HEART_RATE, new_point)
        
        assert len(sample_biometric_twin.timeseries_data[BiometricType.HEART_RATE].data_points) == initial_count + 1
    
    def test_add_data_point_new_type(self, sample_biometric_twin):
        """Test adding a data point for a new biometric type."""
        new_point = BiometricDataPoint(
            timestamp=datetime.now(),
            value=98.6,
            source=BiometricSource.CLINICAL,
            metadata={"method": "oral"}
        )
        
        sample_biometric_twin.add_data_point(BiometricType.TEMPERATURE, new_point, "°C")
        
        assert BiometricType.TEMPERATURE in sample_biometric_twin.timeseries_data
        assert len(sample_biometric_twin.timeseries_data[BiometricType.TEMPERATURE].data_points) == 1
        assert sample_biometric_twin.timeseries_data[BiometricType.TEMPERATURE].unit == "°C"
    
    def test_get_biometric_data(self, sample_biometric_twin, sample_timeseries):
        """Test getting biometric data for a specific type."""
        result = sample_biometric_twin.get_biometric_data(BiometricType.HEART_RATE)
        
        assert result == sample_timeseries
        assert result.get_latest_value().value == 70.5
    
    def test_get_latest_values(self, sample_biometric_twin):
        """Test getting latest values for all biometric types."""
        # Add another biometric type
        bp_data_point = BiometricDataPoint(
            timestamp=datetime.now(),
            value={"systolic": 120, "diastolic": 80},
            source=BiometricSource.CLINICAL,
            metadata={"position": "sitting"}
        )
        sample_biometric_twin.add_data_point(BiometricType.BLOOD_PRESSURE, bp_data_point, "mmHg")
        
        latest_values = sample_biometric_twin.get_latest_values()
        
        assert len(latest_values) == 2
        assert BiometricType.HEART_RATE in latest_values
        assert BiometricType.BLOOD_PRESSURE in latest_values
        assert latest_values[BiometricType.HEART_RATE].value == 70.5
        assert latest_values[BiometricType.BLOOD_PRESSURE].value == {"systolic": 120, "diastolic": 80}
    
    def test_to_dict(self, sample_biometric_twin):
        """Test converting a biometric twin to dictionary."""
        result = sample_biometric_twin.to_dict()
        
        assert result["id"] == sample_biometric_twin.id
        assert result["patient_id"] == "patient-123"
        assert "heart_rate" in result["timeseries_data"]
        assert result["timeseries_data"]["heart_rate"]["unit"] == "bpm"
        assert len(result["timeseries_data"]["heart_rate"]["data_points"]) == 3
    
    def test_from_dict(self):
        """Test creating a biometric twin from dictionary."""
        now = datetime.now()
        twin_id = str(uuid.uuid4())
        
        data = {
            "id": twin_id,
            "patient_id": "patient-456",
            "timeseries_data": {
                "heart_rate": {
                    "biometric_type": "heart_rate",
                    "unit": "bpm",
                    "data_points": [
                        {
                            "timestamp": now.isoformat(),
                            "value": 72.5,
                            "source": "wearable",
                            "metadata": {"device": "fitbit"}
                        }
                    ],
                    "physiological_range": {
                        "min": 60.0,
                        "max": 100.0,
                        "critical_min": 40.0,
                        "critical_max": 140.0
                    }
                }
            },
            "created_at": (now - timedelta(days=30)).isoformat(),
            "updated_at": now.isoformat()
        }
        
        twin = BiometricTwin.from_dict(data)
        
        assert twin.id == twin_id
        assert twin.patient_id == "patient-456"
        assert BiometricType.HEART_RATE in twin.timeseries_data
        assert twin.timeseries_data[BiometricType.HEART_RATE].unit == "bpm"
        assert len(twin.timeseries_data[BiometricType.HEART_RATE].data_points) == 1
        assert twin.timeseries_data[BiometricType.HEART_RATE].data_points[0].value == 72.5