"""Unit tests for the BiometricTwin domain entity."""
import pytest
from datetime import datetime, timedelta
import uuid
import json
from typing import List, Dict, Any, Optional

from app.domain.entities.biometric_twin import (
    BiometricTwin,
    BiometricDataPoint,
    BiometricTimeseriesData,
    BiometricSource,
    BiometricType
)
from app.domain.entities.patient import Patient
from app.domain.value_objects.physiological_ranges import PhysiologicalRange


@pytest.fixture
def mock_patient():
    """Create a mock patient."""
    return Patient(
        id="p12345",
        first_name="John",
        last_name="Doe",
        dob=datetime(1980, 1, 1).date(),
        medical_record_number="MRN123456"
    )


@pytest.fixture
def sample_biometric_data():
    """Create sample biometric data points."""
    now = datetime.now()
    return [
        BiometricDataPoint(
            timestamp=now - timedelta(days=2),
            value=120.5,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit", "measurement_condition": "resting"}
        ),
        BiometricDataPoint(
            timestamp=now - timedelta(days=1),
            value=118.2,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit", "measurement_condition": "resting"}
        ),
        BiometricDataPoint(
            timestamp=now,
            value=122.1,
            source=BiometricSource.WEARABLE,
            metadata={"device": "fitbit", "measurement_condition": "resting"}
        )
    ]


@pytest.fixture
def biometric_twin(mock_patient, sample_biometric_data):
    """Create a biometric twin for testing."""
    # Create timeseriesdata objects
    heart_rate_data = BiometricTimeseriesData(
        biometric_type=BiometricType.HEART_RATE,
        unit="bpm",
        data_points=sample_biometric_data,
        physiological_range=PhysiologicalRange(min=60, max=100, critical_min=40, critical_max=160)
    )
    
    # Create a blood pressure timeseries with systolic/diastolic pairs
    now = datetime.now()
    bp_data_points = [
        BiometricDataPoint(
            timestamp=now - timedelta(days=2),
            value={"systolic": 120, "diastolic": 80},  # Using dict for BP
            source=BiometricSource.CLINICAL,
            metadata={"position": "sitting"}
        ),
        BiometricDataPoint(
            timestamp=now,
            value={"systolic": 118, "diastolic": 78},
            source=BiometricSource.CLINICAL,
            metadata={"position": "sitting"}
        )
    ]
    
    blood_pressure_data = BiometricTimeseriesData(
        biometric_type=BiometricType.BLOOD_PRESSURE,
        unit="mmHg",
        data_points=bp_data_points,
        physiological_range=PhysiologicalRange(
            min={"systolic": 90, "diastolic": 60},
            max={"systolic": 120, "diastolic": 80},
            critical_min={"systolic": 70, "diastolic": 40},
            critical_max={"systolic": 180, "diastolic": 120}
        )
    )
    
    return BiometricTwin(
        id=str(uuid.uuid4()),
        patient_id=mock_patient.id,
        timeseries_data={
            BiometricType.HEART_RATE: heart_rate_data,
            BiometricType.BLOOD_PRESSURE: blood_pressure_data
        },
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestBiometricDataPoint:
    """Test suite for the BiometricDataPoint class."""
    
    def test_init_with_scalar_value(self):
        """Test initialization with a scalar value."""
        point = BiometricDataPoint(
            timestamp=datetime.now(),
            value=98.6,
            source=BiometricSource.MANUAL
        )
        assert point.value == 98.6
        assert point.source == BiometricSource.MANUAL
    
    def test_init_with_dict_value(self):
        """Test initialization with a dictionary value."""
        bp_value = {"systolic": 120, "diastolic": 80}
        point = BiometricDataPoint(
            timestamp=datetime.now(),
            value=bp_value,
            source=BiometricSource.CLINICAL
        )
        assert point.value == bp_value
        assert point.source == BiometricSource.CLINICAL
    
    def test_metadata_optional(self):
        """Test that metadata is optional."""
        point = BiometricDataPoint(
            timestamp=datetime.now(),
            value=98.6,
            source=BiometricSource.MANUAL
        )
        assert point.metadata == {}
    
    def test_add_metadata(self):
        """Test adding metadata to a data point."""
        point = BiometricDataPoint(
            timestamp=datetime.now(),
            value=98.6,
            source=BiometricSource.MANUAL
        )
        point.add_metadata({"location": "home", "device": "thermometer"})
        assert point.metadata == {"location": "home", "device": "thermometer"}
        
        # Test adding more metadata
        point.add_metadata({"mood": "good"})
        assert "mood" in point.metadata
        assert point.metadata["mood"] == "good"
        
        # Ensure original metadata is preserved
        assert point.metadata["location"] == "home"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime.now()
        point = BiometricDataPoint(
            timestamp=timestamp,
            value=98.6,
            source=BiometricSource.MANUAL,
            metadata={"device": "thermometer"}
        )
        result = point.to_dict()
        
        assert result["timestamp"] == timestamp.isoformat()
        assert result["value"] == 98.6
        assert result["source"] == BiometricSource.MANUAL.value
        assert result["metadata"] == {"device": "thermometer"}
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        now = datetime.now()
        data = {
            "timestamp": now.isoformat(),
            "value": 98.6,
            "source": "manual",
            "metadata": {"device": "thermometer"}
        }
        
        point = BiometricDataPoint.from_dict(data)
        
        assert point.timestamp.isoformat() == now.isoformat()
        assert point.value == 98.6
        assert point.source == BiometricSource.MANUAL
        assert point.metadata == {"device": "thermometer"}
    
    def test_comparison(self):
        """Test comparing data points by timestamp."""
        now = datetime.now()
        earlier = BiometricDataPoint(
            timestamp=now - timedelta(hours=1),
            value=98.6,
            source=BiometricSource.MANUAL
        )
        later = BiometricDataPoint(
            timestamp=now,
            value=98.6,
            source=BiometricSource.MANUAL
        )
        
        assert earlier < later
        assert later > earlier
        assert earlier != later


class TestBiometricTimeseriesData:
    """Test suite for the BiometricTimeseriesData class."""
    
    def test_init(self, sample_biometric_data):
        """Test initialization."""
        timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.HEART_RATE,
            unit="bpm",
            data_points=sample_biometric_data,
            physiological_range=PhysiologicalRange(min=60, max=100)
        )
        
        assert timeseries.biometric_type == BiometricType.HEART_RATE
        assert timeseries.unit == "bpm"
        assert len(timeseries.data_points) == 3
        assert timeseries.physiological_range.min == 60
        assert timeseries.physiological_range.max == 100
    
    def test_add_data_point(self, sample_biometric_data):
        """Test adding a data point."""
        timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.HEART_RATE,
            unit="bpm",
            data_points=sample_biometric_data,
            physiological_range=PhysiologicalRange(min=60, max=100)
        )
        
        # Initial count
        initial_count = len(timeseries.data_points)
        
        # Add new point
        new_point = BiometricDataPoint(
            timestamp=datetime.now() + timedelta(days=1),
            value=125.3,
            source=BiometricSource.WEARABLE
        )
        timeseries.add_data_point(new_point)
        
        # Check point was added
        assert len(timeseries.data_points) == initial_count + 1
        assert new_point in timeseries.data_points
    
    def test_get_latest_value(self, sample_biometric_data):
        """Test getting the latest value."""
        timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.HEART_RATE,
            unit="bpm",
            data_points=sample_biometric_data,
            physiological_range=PhysiologicalRange(min=60, max=100)
        )
        
        latest = timeseries.get_latest_value()
        
        # Should be the point with the most recent timestamp
        assert latest == max(sample_biometric_data, key=lambda point: point.timestamp)
        assert latest.value == 122.1  # The value of the latest point
    
    def test_get_values_in_range(self, sample_biometric_data):
        """Test retrieving values within a time range."""
        timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.HEART_RATE,
            unit="bpm",
            data_points=sample_biometric_data,
            physiological_range=PhysiologicalRange(min=60, max=100)
        )
        
        now = datetime.now()
        start_time = now - timedelta(days=1, hours=12)
        end_time = now + timedelta(hours=1)
        
        # Get values in range
        filtered_points = timeseries.get_values_in_range(start_time, end_time)
        
        # Should contain the points within the time range
        assert len(filtered_points) == 2
        for point in filtered_points:
            assert start_time <= point.timestamp <= end_time
    
    def test_to_dict(self, sample_biometric_data):
        """Test conversion to dictionary."""
        timeseries = BiometricTimeseriesData(
            biometric_type=BiometricType.HEART_RATE,
            unit="bpm",
            data_points=sample_biometric_data,
            physiological_range=PhysiologicalRange(min=60, max=100)
        )
        
        result = timeseries.to_dict()
        
        assert result["biometric_type"] == BiometricType.HEART_RATE.value
        assert result["unit"] == "bpm"
        assert len(result["data_points"]) == 3
        assert "physiological_range" in result
        assert result["physiological_range"]["min"] == 60
        assert result["physiological_range"]["max"] == 100
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        now = datetime.now()
        data = {
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
                "min": 60,
                "max": 100,
                "critical_min": 40,
                "critical_max": 160
            }
        }
        
        timeseries = BiometricTimeseriesData.from_dict(data)
        
        assert timeseries.biometric_type == BiometricType.HEART_RATE
        assert timeseries.unit == "bpm"
        assert len(timeseries.data_points) == 1
        assert timeseries.data_points[0].value == 72.5
        assert timeseries.physiological_range.min == 60
        assert timeseries.physiological_range.max == 100


class TestBiometricTwin:
    """Test suite for the BiometricTwin class."""
    
    def test_init(self, biometric_twin, mock_patient):
        """Test initialization."""
        assert biometric_twin.patient_id == mock_patient.id
        assert BiometricType.HEART_RATE in biometric_twin.timeseries_data
        assert BiometricType.BLOOD_PRESSURE in biometric_twin.timeseries_data
        assert isinstance(biometric_twin.created_at, datetime)
        assert isinstance(biometric_twin.updated_at, datetime)
    
    def test_add_biometric_data(self, biometric_twin):
        """Test adding new biometric data."""
        # Create new timeseries data
        now = datetime.now()
        temperature_data = BiometricTimeseriesData(
            biometric_type=BiometricType.TEMPERATURE,
            unit="°F",
            data_points=[
                BiometricDataPoint(
                    timestamp=now,
                    value=98.6,
                    source=BiometricSource.MANUAL
                )
            ],
            physiological_range=PhysiologicalRange(min=97, max=99, critical_min=95, critical_max=104)
        )
        
        # Add to biometric twin
        biometric_twin.add_biometric_data(temperature_data)
        
        # Verify it was added
        assert BiometricType.TEMPERATURE in biometric_twin.timeseries_data
        assert biometric_twin.timeseries_data[BiometricType.TEMPERATURE].unit == "°F"
        assert len(biometric_twin.timeseries_data[BiometricType.TEMPERATURE].data_points) == 1
    
    def test_get_latest_values(self, biometric_twin):
        """Test getting the latest values for all biometric types."""
        latest_values = biometric_twin.get_latest_values()
        
        assert BiometricType.HEART_RATE in latest_values
        assert BiometricType.BLOOD_PRESSURE in latest_values
        
        # Check values
        assert latest_values[BiometricType.HEART_RATE].value == 122.1
        assert latest_values[BiometricType.BLOOD_PRESSURE].value == {"systolic": 118, "diastolic": 78}
    
    def test_to_dict(self, biometric_twin):
        """Test conversion to dictionary."""
        result = biometric_twin.to_dict()
        
        assert result["id"] == biometric_twin.id
        assert result["patient_id"] == biometric_twin.patient_id
        assert "timeseries_data" in result
        assert "heart_rate" in result["timeseries_data"]
        assert "blood_pressure" in result["timeseries_data"]
        assert "created_at" in result
        assert "updated_at" in result
    
    def test_from_dict(self, biometric_twin):
        """Test creation from dictionary."""
        # Convert existing twin to dict and back
        twin_dict = biometric_twin.to_dict()
        new_twin = BiometricTwin.from_dict(twin_dict)
        
        # Check that everything matches
        assert new_twin.id == biometric_twin.id
        assert new_twin.patient_id == biometric_twin.patient_id
        assert len(new_twin.timeseries_data) == len(biometric_twin.timeseries_data)
        assert BiometricType.HEART_RATE in new_twin.timeseries_data
        assert BiometricType.BLOOD_PRESSURE in new_twin.timeseries_data
    
    def test_detect_abnormal_values(self, biometric_twin):
        """Test detection of abnormal values based on physiological ranges."""
        # Add an abnormal heart rate data point
        heart_rate_data = biometric_twin.timeseries_data[BiometricType.HEART_RATE]
        abnormal_point = BiometricDataPoint(
            timestamp=datetime.now() + timedelta(hours=1),
            value=180.0,  # Above normal range
            source=BiometricSource.WEARABLE
        )
        heart_rate_data.add_data_point(abnormal_point)
        
        # Get abnormal values
        abnormal_values = biometric_twin.detect_abnormal_values()
        
        # Should contain heart rate
        assert BiometricType.HEART_RATE in abnormal_values
        
        # Check the abnormal value
        assert abnormal_point in abnormal_values[BiometricType.HEART_RATE]
        
        # Blood pressure should be normal (within range)
        assert BiometricType.BLOOD_PRESSURE not in abnormal_values
    
    def test_get_biometric_data(self, biometric_twin):
        """Test retrieving biometric data for a specific type."""
        heart_rate_data = biometric_twin.get_biometric_data(BiometricType.HEART_RATE)
        
        assert heart_rate_data is not None
        assert heart_rate_data.biometric_type == BiometricType.HEART_RATE
        assert heart_rate_data.unit == "bpm"
        assert len(heart_rate_data.data_points) == 3
        
        # Test for non-existent type
        assert biometric_twin.get_biometric_data(BiometricType.GLUCOSE) is None