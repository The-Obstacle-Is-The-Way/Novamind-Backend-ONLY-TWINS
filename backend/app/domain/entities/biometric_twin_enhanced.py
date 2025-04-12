"""
Biometric Twin entity for the digital psychiatric twin platform.

This module defines the core domain entities for biometric data within the
digital twin system, providing rich domain behavior and data validation.
"""

import json
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Union, ClassVar

from app.domain.value_objects.physiological_ranges import PhysiologicalRange


class BiometricSource(str, Enum):
    """Source of biometric data."""
    
    WEARABLE = "wearable"
    """Data from wearable devices (smartwatches, fitness trackers, etc.)."""
    
    CLINICAL = "clinical"
    """Data collected in clinical settings."""
    
    PATIENT_REPORTED = "patient_reported"
    """Data self-reported by patients."""
    
    HOME_DEVICE = "home_device"
    """Data from home monitoring devices."""
    
    IMPLANT = "implant"
    """Data from implanted medical devices."""
    
    ENVIRONMENTAL = "environmental"
    """Environmental sensor data."""


class BiometricType(str, Enum):
    """Types of biometric measurements."""
    
    HEART_RATE = "heart_rate"
    """Heart rate in beats per minute."""
    
    BLOOD_PRESSURE = "blood_pressure"
    """Blood pressure with systolic and diastolic values."""
    
    TEMPERATURE = "temperature"
    """Body temperature in degrees Celsius."""
    
    RESPIRATORY_RATE = "respiratory_rate"
    """Breathing rate in breaths per minute."""
    
    BLOOD_GLUCOSE = "blood_glucose"
    """Blood glucose level in mg/dL."""
    
    OXYGEN_SATURATION = "oxygen_saturation"
    """Blood oxygen saturation level as percentage."""
    
    SLEEP = "sleep"
    """Sleep metrics including duration, quality, stages."""
    
    ACTIVITY = "activity"
    """Physical activity measurements including steps, calories."""
    
    WEIGHT = "weight"
    """Body weight in kilograms."""
    
    STRESS = "stress"
    """Stress level indicators."""
    
    HRV = "hrv"
    """Heart rate variability metrics."""
    
    EEG = "eeg"
    """Electroencephalogram data."""
    
    EMG = "emg"
    """Electromyogram data."""
    
    CORTISOL = "cortisol"
    """Cortisol levels."""


class BiometricDataPoint:
    """
    Single biometric measurement at a point in time.
    
    This represents an individual measurement from any biometric source,
    with associated metadata and timestamp.
    """
    
    def __init__(
        self,
        timestamp: datetime,
        value: Any,
        source: BiometricSource,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a biometric data point.
        
        Args:
            timestamp: When the data was recorded
            value: The measurement value
            source: Source of the biometric data
            metadata: Optional additional information
        """
        self.timestamp = timestamp
        self.value = value
        self.source = source
        self.metadata = metadata or {}
    
    def add_metadata(self, additional_metadata: Dict[str, Any]) -> None:
        """
        Add additional metadata to this data point.
        
        Args:
            additional_metadata: Metadata to add
        """
        self.metadata.update(additional_metadata)
    
    def get_normalized_value(self) -> float:
        """
        Get a normalized numeric value for comparison.
        
        For complex values like blood pressure, this extracts a key metric.
        
        Returns:
            Normalized value as a float
        """
        if isinstance(self.value, (int, float)):
            return float(self.value)
        
        # Extract main value from complex types
        if isinstance(self.value, dict):
            if "systolic" in self.value:
                return float(self.value["systolic"])
            if "value" in self.value:
                return float(self.value["value"])
        
        # Default to 0 if can't normalize
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with data point fields
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "source": str(self.source.value if isinstance(self.source, Enum) else self.source),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BiometricDataPoint":
        """
        Create a BiometricDataPoint from dictionary data.
        
        Args:
            data: Dictionary with data point fields
            
        Returns:
            New BiometricDataPoint instance
        """
        # Parse the timestamp
        if isinstance(data["timestamp"], str):
            timestamp = datetime.fromisoformat(data["timestamp"])
        else:
            timestamp = data["timestamp"]
        
        # Parse the source
        if isinstance(data["source"], str):
            try:
                source = BiometricSource(data["source"])
            except ValueError:
                # Fallback for unknown source values
                source = data["source"]
        else:
            source = data["source"]
        
        return cls(
            timestamp=timestamp,
            value=data["value"],
            source=source,
            metadata=data.get("metadata", {})
        )
    
    def __lt__(self, other: "BiometricDataPoint") -> bool:
        """
        Compare data points by timestamp.
        
        Args:
            other: Data point to compare with
            
        Returns:
            True if this data point is earlier
        """
        if not isinstance(other, BiometricDataPoint):
            return NotImplemented
        return self.timestamp < other.timestamp
    
    def __eq__(self, other: object) -> bool:
        """
        Check if data points are equal.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if data points are equal
        """
        if not isinstance(other, BiometricDataPoint):
            return NotImplemented
        return (
            self.timestamp == other.timestamp and
            self.value == other.value and
            self.source == other.source and
            self.metadata == other.metadata
        )


class BiometricTimeseriesData:
    """
    Time series of biometric measurements of a specific type.
    
    This represents a collection of measurements for a single biometric type,
    with associated metadata and physiological range information.
    """
    
    def __init__(
        self,
        biometric_type: BiometricType,
        unit: str,
        data_points: List[BiometricDataPoint],
        physiological_range: Optional[PhysiologicalRange] = None
    ):
        """
        Initialize a biometric timeseries.
        
        Args:
            biometric_type: Type of biometric data
            unit: Unit of measurement
            data_points: List of data points
            physiological_range: Normal and critical ranges
        """
        self.biometric_type = biometric_type
        self.unit = unit
        self.data_points = sorted(data_points, key=lambda x: x.timestamp)
        
        # If no range provided, try to get default
        if physiological_range is None and isinstance(biometric_type, BiometricType):
            self.physiological_range = PhysiologicalRange.get_default_range(biometric_type.value)
        else:
            self.physiological_range = physiological_range
    
    def add_data_point(self, data_point: BiometricDataPoint) -> None:
        """
        Add a new data point to the timeseries.
        
        Args:
            data_point: Data point to add
        """
        self.data_points.append(data_point)
        self.data_points.sort(key=lambda x: x.timestamp)
    
    def get_latest_value(self) -> Optional[BiometricDataPoint]:
        """
        Get the most recent data point.
        
        Returns:
            Latest data point or None if empty
        """
        if not self.data_points:
            return None
        return max(self.data_points, key=lambda x: x.timestamp)
    
    def get_values_in_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[BiometricDataPoint]:
        """
        Get data points within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of data points within range
        """
        return [
            dp for dp in self.data_points
            if start_time <= dp.timestamp <= end_time
        ]
    
    def get_abnormal_values(self) -> List[BiometricDataPoint]:
        """
        Get data points outside normal physiological range.
        
        Returns:
            List of abnormal data points
        """
        if not self.physiological_range:
            return []
        
        return [
            dp for dp in self.data_points
            if not self.physiological_range.is_normal(dp.get_normalized_value())
        ]
    
    def get_critical_values(self) -> List[BiometricDataPoint]:
        """
        Get data points in critical physiological range.
        
        Returns:
            List of critical data points
        """
        if not self.physiological_range:
            return []
        
        return [
            dp for dp in self.data_points
            if self.physiological_range.is_critical(dp.get_normalized_value())
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with timeseries fields
        """
        return {
            "biometric_type": str(self.biometric_type.value if isinstance(self.biometric_type, Enum) else self.biometric_type),
            "unit": self.unit,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "physiological_range": self.physiological_range.to_dict() if self.physiological_range else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BiometricTimeseriesData":
        """
        Create a BiometricTimeseriesData from dictionary data.
        
        Args:
            data: Dictionary with timeseries fields
            
        Returns:
            New BiometricTimeseriesData instance
        """
        # Parse the biometric type
        if isinstance(data["biometric_type"], str):
            try:
                biometric_type = BiometricType(data["biometric_type"])
            except ValueError:
                # Fallback for unknown type values
                biometric_type = data["biometric_type"]
        else:
            biometric_type = data["biometric_type"]
        
        # Parse the data points
        data_points = [
            BiometricDataPoint.from_dict(dp)
            for dp in data["data_points"]
        ]
        
        # Parse the physiological range
        physiological_range = None
        if data.get("physiological_range"):
            physiological_range = PhysiologicalRange.from_dict(
                data["physiological_range"]
            )
        
        return cls(
            biometric_type=biometric_type,
            unit=data["unit"],
            data_points=data_points,
            physiological_range=physiological_range
        )


class BiometricTwin:
    """
    Digital twin of a patient's biometric data.
    
    This is the aggregate root entity that contains all biometric timeseries
    for a patient, providing a complete picture of their physiological state.
    """
    
    def __init__(
        self,
        id: str,
        patient_id: str,
        timeseries_data: Dict[BiometricType, BiometricTimeseriesData],
        created_at: datetime,
        updated_at: datetime
    ):
        """
        Initialize a biometric twin.
        
        Args:
            id: Unique identifier
            patient_id: Associated patient ID
            timeseries_data: Dictionary of biometric timeseries
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.patient_id = patient_id
        self.timeseries_data = timeseries_data
        self.created_at = created_at
        self.updated_at = updated_at
    
    def add_biometric_data(self, timeseries: BiometricTimeseriesData) -> None:
        """
        Add a new biometric timeseries.
        
        Args:
            timeseries: Biometric timeseries to add
        """
        self.timeseries_data[timeseries.biometric_type] = timeseries
        self.updated_at = datetime.now()
    
    def add_data_point(
        self,
        biometric_type: BiometricType,
        data_point: BiometricDataPoint,
        unit: Optional[str] = None
    ) -> None:
        """
        Add a data point to an existing timeseries.
        
        Args:
            biometric_type: Type of biometric data
            data_point: Data point to add
            unit: Unit of measurement (for new timeseries)
        """
        # Update existing timeseries
        if biometric_type in self.timeseries_data:
            self.timeseries_data[biometric_type].add_data_point(data_point)
        # Create new timeseries
        else:
            if unit is None:
                unit = self._get_default_unit(biometric_type)
            
            self.timeseries_data[biometric_type] = BiometricTimeseriesData(
                biometric_type=biometric_type,
                unit=unit,
                data_points=[data_point]
            )
        
        self.updated_at = datetime.now()
    
    def get_biometric_data(
        self, biometric_type: BiometricType
    ) -> Optional[BiometricTimeseriesData]:
        """
        Get timeseries for a specific biometric type.
        
        Args:
            biometric_type: Type of biometric data
            
        Returns:
            Biometric timeseries or None if not found
        """
        return self.timeseries_data.get(biometric_type)
    
    def get_latest_values(self) -> Dict[BiometricType, BiometricDataPoint]:
        """
        Get the latest value for each biometric type.
        
        Returns:
            Dictionary of biometric types to latest data points
        """
        result = {}
        for biometric_type, timeseries in self.timeseries_data.items():
            latest = timeseries.get_latest_value()
            if latest:
                result[biometric_type] = latest
        return result
    
    def detect_abnormal_values(self) -> Dict[BiometricType, List[BiometricDataPoint]]:
        """
        Detect abnormal values across all biometric types.
        
        Returns:
            Dictionary of biometric types to abnormal data points
        """
        result = {}
        for biometric_type, timeseries in self.timeseries_data.items():
            abnormal = timeseries.get_abnormal_values()
            if abnormal:
                result[biometric_type] = abnormal
        return result
    
    def detect_critical_values(self) -> Dict[BiometricType, List[BiometricDataPoint]]:
        """
        Detect critical values across all biometric types.
        
        Returns:
            Dictionary of biometric types to critical data points
        """
        result = {}
        for biometric_type, timeseries in self.timeseries_data.items():
            critical = timeseries.get_critical_values()
            if critical:
                result[biometric_type] = critical
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with biometric twin fields
        """
        # Convert the timeseries dictionary keys to strings
        timeseries_dict = {}
        for biometric_type, timeseries in self.timeseries_data.items():
            key = biometric_type.value if isinstance(biometric_type, Enum) else str(biometric_type)
            timeseries_dict[key] = timeseries.to_dict()
        
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "timeseries_data": timeseries_dict,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BiometricTwin":
        """
        Create a BiometricTwin from dictionary data.
        
        Args:
            data: Dictionary with biometric twin fields
            
        Returns:
            New BiometricTwin instance
        """
        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        updated_at = datetime.fromisoformat(data["updated_at"]) if isinstance(data["updated_at"], str) else data["updated_at"]
        
        # Parse timeseries data
        timeseries_data = {}
        for type_str, ts_data in data["timeseries_data"].items():
            try:
                biometric_type = BiometricType(type_str)
            except ValueError:
                # Fallback for unknown type values
                biometric_type = type_str
            
            timeseries_data[biometric_type] = BiometricTimeseriesData.from_dict(ts_data)
        
        return cls(
            id=data["id"],
            patient_id=data["patient_id"],
            timeseries_data=timeseries_data,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _get_default_unit(self, biometric_type: BiometricType) -> str:
        """
        Get the default unit for a biometric type.
        
        Args:
            biometric_type: Type of biometric data
            
        Returns:
            Default unit of measurement
        """
        if isinstance(biometric_type, str):
            biometric_type_str = biometric_type
        else:
            biometric_type_str = biometric_type.value
        
        units = {
            "heart_rate": "bpm",
            "blood_pressure": "mmHg",
            "temperature": "°C",
            "respiratory_rate": "breaths/min",
            "blood_glucose": "mg/dL",
            "oxygen_saturation": "%",
            "sleep": "hours",
            "activity": "steps",
            "weight": "kg",
            "stress": "score",
            "hrv": "ms",
            "eeg": "μV",
            "emg": "μV",
            "cortisol": "μg/dL"
        }
        
        return units.get(biometric_type_str, "units")