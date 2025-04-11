# -*- coding: utf-8 -*-
"""
Biometric Twin Entity for the Digital Twin Psychiatry Platform.

This module defines the BiometricTwin entity, which serves as a digital representation
of a patient's physiological and neurological state over time. It integrates with
wearable devices, neuroimaging data, and other biometric sources to create a
comprehensive digital model of the patient's biological state.
"""

from datetime import datetime, UTC, UTC
from typing import Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from app.domain.exceptions import ValidationError


class BiometricDataPoint:
    """
    Represents a single biometric measurement at a specific point in time.
    
    This class encapsulates various types of biometric data (heart rate, cortisol,
    sleep patterns, etc.) with timestamps and metadata for comprehensive tracking.
    """
    
    def __init__(
        self,
        data_type: str,
        value: Union[float, int, str, Dict],
        timestamp: datetime,
        source: str,
        metadata: Optional[Dict] = None,
        confidence: float = 1.0,
        data_id: UUID = None
    ) -> None:
        """
        Initialize a new BiometricDataPoint.
        
        Args:
            data_type: Type of biometric data (e.g., "heart_rate", "cortisol", "eeg")
            value: The measured value (can be numeric, string, or structured data)
            timestamp: When the measurement was taken
            source: Device or system that provided the measurement
            metadata: Additional contextual information about the measurement
            confidence: Confidence level in the measurement (0.0-1.0)
            data_id: Unique identifier for this data point
        """
        self.data_id = data_id or uuid4()
        self.data_type = data_type
        self.value = value
        self.timestamp = timestamp
        self.source = source
        self.metadata = metadata or {}
        self.confidence = confidence
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate the biometric data point."""
        if not self.data_type:
            raise ValidationError("Biometric data type cannot be empty")
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValidationError("Confidence must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict:
        """Convert the data point to a dictionary representation."""
        return {
            "data_id": str(self.data_id),
            "data_type": self.data_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
            "confidence": self.confidence
        }


class BiometricTwin:
    """
    Digital twin of a patient's biometric and physiological state.
    
    This entity aggregates multiple biometric data streams to create a comprehensive
    digital representation of a patient's physiological and neurological state over time.
    It enables advanced analysis, pattern recognition, and predictive modeling for
    personalized psychiatric care.
    """
    
    def __init__(
        self,
        patient_id: UUID,
        twin_id: UUID = None,
        data_points: List[BiometricDataPoint] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        baseline_established: bool = False,
        connected_devices: Set[str] = None
    ) -> None:
        """
        Initialize a new BiometricTwin.
        
        Args:
            patient_id: ID of the patient this twin represents
            twin_id: Unique identifier for this biometric twin
            data_points: Collection of biometric measurements
            created_at: When this twin was first created
            updated_at: When this twin was last updated
            baseline_established: Whether baseline measurements have been established
            connected_devices: Set of devices currently connected to this twin
        """
        self.twin_id = twin_id or uuid4()
        self.patient_id = patient_id
        self.data_points = data_points or []
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or self.created_at
        self.baseline_established = baseline_established
        self.connected_devices = connected_devices or set()
        
        # Cached analysis results
        self._cached_analyses = {}
    
    def add_data_point(self, data_point: BiometricDataPoint) -> None:
        """
        Add a new biometric data point to the twin.
        
        Args:
            data_point: The biometric data point to add
        """
        self.data_points.append(data_point)
        self.updated_at = datetime.now(UTC)
        
        # Invalidate cached analyses that might be affected by this new data
        self._invalidate_affected_caches(data_point.data_type)
    
    def get_data_points_by_type(
        self, 
        data_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BiometricDataPoint]:
        """
        Retrieve data points of a specific type within an optional time range.
        
        Args:
            data_type: Type of biometric data to retrieve
            start_time: Optional start of time range
            end_time: Optional end of time range
            
        Returns:
            List of matching biometric data points
        """
        filtered_points = [dp for dp in self.data_points if dp.data_type == data_type]
        
        if start_time:
            filtered_points = [dp for dp in filtered_points if dp.timestamp >= start_time]
        
        if end_time:
            filtered_points = [dp for dp in filtered_points if dp.timestamp <= end_time]
        
        return sorted(filtered_points, key=lambda dp: dp.timestamp)
    
    def establish_baseline(self) -> bool:
        """
        Establish baseline measurements for this biometric twin.
        
        This method analyzes existing data points to establish baseline values
        for various biometric measurements, which can be used for future
        comparative analysis.
        
        Returns:
            True if baseline was successfully established, False otherwise
        """
        # Check if we have enough data to establish a baseline
        data_types = set(dp.data_type for dp in self.data_points)
        required_types = {"heart_rate", "sleep_quality", "activity_level"}
        
        if not required_types.issubset(data_types):
            return False
        
        # For each required type, ensure we have at least 7 days of data
        now = datetime.now(UTC)
        seven_days_ago = datetime.now(UTC)  # Simplified for example
        
        for data_type in required_types:
            points = self.get_data_points_by_type(data_type, seven_days_ago, now)
            if len(points) < 7:  # At least one measurement per day
                return False
        
        self.baseline_established = True
        self.updated_at = datetime.now(UTC)
        return True
    
    def detect_anomalies(
        self, 
        data_type: str,
        threshold: float = 2.0,
        window_size: int = 7
    ) -> List[BiometricDataPoint]:
        """
        Detect anomalous measurements for a specific data type.
        
        Args:
            data_type: Type of biometric data to analyze
            threshold: Standard deviation threshold for anomaly detection
            window_size: Number of days to include in the analysis window
            
        Returns:
            List of data points identified as anomalies
        """
        if not self.baseline_established:
            return []
        
        # Get recent data points for the specified type
        recent_points = self.get_data_points_by_type(data_type)
        
        if len(recent_points) < 3:  # Need at least 3 points for meaningful analysis
            return []
        
        # Simple anomaly detection based on statistical properties
        # In a real implementation, this would use more sophisticated algorithms
        values = [float(dp.value) if isinstance(dp.value, (int, float)) else 0.0 
                 for dp in recent_points]
        
        if not values:
            return []
        
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
        
        # Identify anomalies
        anomalies = []
        for dp, value in zip(recent_points, values):
            if abs(value - mean) > threshold * std_dev:
                anomalies.append(dp)
        
        return anomalies
    
    def correlate_with_symptoms(
        self, 
        symptom_records: List[Dict],
        data_types: List[str] = None
    ) -> Dict[str, float]:
        """
        Correlate biometric data with reported symptoms.
        
        Args:
            symptom_records: List of symptom records with timestamps
            data_types: Optional list of specific data types to correlate
            
        Returns:
            Dictionary mapping data types to correlation coefficients
        """
        # This would implement a correlation analysis between biometric data
        # and reported symptoms. For simplicity, we return a mock result.
        return {
            "heart_rate_variability": 0.72,
            "sleep_quality": 0.68,
            "cortisol_levels": 0.81
        }
    
    def _invalidate_affected_caches(self, data_type: str) -> None:
        """
        Invalidate cached analyses affected by changes to a specific data type.
        
        Args:
            data_type: The type of data that was modified
        """
        affected_keys = [k for k in self._cached_analyses.keys() if data_type in k]
        for key in affected_keys:
            del self._cached_analyses[key]
    
    def connect_device(self, device_id: str) -> None:
        """
        Connect a new biometric monitoring device to this twin.
        
        Args:
            device_id: Identifier for the device to connect
        """
        self.connected_devices.add(device_id)
        self.updated_at = datetime.now(UTC)
    
    def disconnect_device(self, device_id: str) -> None:
        """
        Disconnect a biometric monitoring device from this twin.
        
        Args:
            device_id: Identifier for the device to disconnect
        """
        if device_id in self.connected_devices:
            self.connected_devices.remove(device_id)
            self.updated_at = datetime.now(UTC)
    
    def to_dict(self) -> Dict:
        """Convert the biometric twin to a dictionary representation."""
        return {
            "twin_id": str(self.twin_id),
            "patient_id": str(self.patient_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "baseline_established": self.baseline_established,
            "connected_devices": list(self.connected_devices),
            "data_points_count": len(self.data_points)
        }