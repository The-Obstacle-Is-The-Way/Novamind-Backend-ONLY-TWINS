"""
Temporal sequence models for the Temporal Neurotransmitter System.

This module defines the core classes for representing time series data
for neurotransmitter levels and other temporal measurements.
"""
import math
import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

import numpy as np

from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter, TemporalResolution

T = TypeVar('T', float, int, bool, str)


class InterpolationMethod(Enum):
    """Methods for interpolating between temporal data points."""
    LINEAR = "linear"
    CUBIC = "cubic"
    NEAREST = "nearest"
    ZERO = "zero"
    NONE = "none"


class TemporalSequence(Generic[T]):
    """
    A sequence of temporal events representing a time series.
    
    This class is the foundation for tracking how any value changes over time,
    particularly neurotransmitter levels in different brain regions.
    It provides methods for analyzing trends, statistics, and interpolating values.
    """
    
    def __init__(
        self,
        sequence_id: UUID,
        feature_names: list[str],
        timestamps: list[datetime],
        values: list[list[float]],
        patient_id: UUID,
        metadata: dict[str, Any] | None = None,
        name: str | None = None,
        brain_region: BrainRegion | None = None,
        neurotransmitter: Neurotransmitter | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None
    ):
        """
        Initialize a new temporal sequence.
        
        Args:
            sequence_id: Unique identifier for the sequence
            feature_names: Names of the features in this sequence
            timestamps: List of timestamps for each data point
            values: List of feature vector values, one per timestamp
            patient_id: Identifier of the associated patient
            metadata: Additional metadata for the sequence
            name: Name of the sequence
            brain_region: Associated brain region if applicable
            neurotransmitter: Associated neurotransmitter if applicable
            created_at: Creation timestamp
            updated_at: Last update timestamp
            temporal_resolution: Time resolution of the sequence
        """
        # Validate input lengths match
        if len(timestamps) != len(values):
            raise ValueError("Number of timestamps must match number of value vectors")
            
        if any(len(value_vec) != len(feature_names) for value_vec in values):
            raise ValueError("Each value vector must have the same number of features")
        
        self.sequence_id = sequence_id
        self._feature_names = feature_names
        self._timestamps = timestamps
        self._values = values
        self.patient_id = patient_id
        self.metadata = metadata or {}
        self.name = name or f"Sequence-{str(sequence_id)[:8]}"
        self.brain_region = brain_region
        self.neurotransmitter = neurotransmitter
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
        self.temporal_resolution = temporal_resolution
        
        # Cache for sequence length
        self._sequence_length = len(timestamps)
    @property
    def timestamps(self) -> list[datetime]:
        """Get all timestamps in the sequence, ordered chronologically."""
        return self._timestamps
    
    @property
    def values(self) -> list[list[float]]:
        """
        Get all values in the sequence, ordered chronologically.
        """
        return self._values
    @values.setter
    def values(self, new_values: list[list[float]]) -> None:
        """
        Set the values for this sequence.
        
        Args:
            new_values: List of values to set
        """
        if len(new_values) != len(self._timestamps):
            raise ValueError("Number of value vectors must match number of timestamps")
            
        if any(len(value_vec) != len(self._feature_names) for value_vec in new_values):
            raise ValueError("Each value vector must have the same number of features")
            
        self._values = new_values
        self.updated_at = datetime.now(UTC)
        self.metadata["explicit_values"] = True
    
    @property
    def feature_names(self) -> list[str]:
        """Get the names of features in this sequence."""
        if self._feature_names:
            return self._feature_names
        elif self.neurotransmitter:
            return [self.neurotransmitter.value]
        else:
            return ["value"]
    
    @feature_names.setter
    def feature_names(self, new_feature_names: list[str]) -> None:
        """
        Set the feature names for this sequence.
        
        Args:
            new_feature_names: List of feature names
        """
        self._feature_names = new_feature_names
        
        # Update metadata for consistency
        self.metadata["feature_names"] = new_feature_names
    
    @property
    def sequence_length(self) -> int:
        """
        Get the number of timestamps in the sequence.
        """
        return self._sequence_length
        
    @property
    def feature_dimension(self) -> int:
        """
        Get the dimension of the feature vectors.
        """
        return len(self._feature_names)
    
    @classmethod
    def create(
        cls,
        feature_names: list[str],
        timestamps: list[datetime],
        values: list[list[float]],
        patient_id: UUID,
        metadata: dict[str, Any] | None = None
    ) -> 'TemporalSequence':
        """
        Factory method to create a temporal sequence with an auto-generated ID.
        
        Args:
            feature_names: Names of the features in this sequence
            timestamps: List of timestamps for each data point
            values: List of feature vector values, one per timestamp
            patient_id: Identifier of the associated patient
            metadata: Additional metadata for the sequence
            
        Returns:
            A new TemporalSequence instance
        """
        return cls(
            sequence_id=uuid.uuid4(),
            feature_names=feature_names,
            timestamps=timestamps,
            values=values,
            patient_id=patient_id,
            metadata=metadata
        )
        
    def to_numpy_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert to input/output numpy arrays for machine learning.
        
        Returns:
            X: Input features array (all except last timestamp)
            y: Target outputs array (all except first timestamp)
        """
        # Convert values to numpy array
        values_array = np.array(self._values)
        
        # Input features are all but the last value
        X = values_array[:-1]
        
        # Targets are all but the first value
        y = values_array[1:]
        
        return X, y
    
    def to_padded_tensor(self, max_length: int) -> dict[str, np.ndarray]:
        """
        Convert to a padded tensor representation.
        
        Args:
            max_length: Maximum sequence length to pad to
            
        Returns:
            Dictionary with:
                - values: Padded values array
                - mask: Boolean mask indicating valid entries
                - seq_len: Actual sequence length
        """
        # Create the values array padded to max_length
        padded_values = np.zeros((max_length, self.feature_dimension))
        mask = np.zeros(max_length, dtype=bool)
        
        # Fill with actual values up to sequence_length
        actual_length = min(self.sequence_length, max_length)
        padded_values[:actual_length] = self._values[:actual_length]
        mask[:actual_length] = True
        
        return {
            "values": padded_values,
            "mask": mask,
            "seq_len": self.sequence_length
        }
    
    def extract_subsequence(self, start_idx: int, end_idx: int) -> 'TemporalSequence':
        """
        Extract a subsequence from this sequence.
        
        Args:
            start_idx: Start index (inclusive)
            end_idx: End index (exclusive)
            
        Returns:
            A new TemporalSequence containing the subsequence
        """
        if start_idx < 0 or end_idx > self.sequence_length or start_idx >= end_idx:
            raise ValueError(f"Invalid subsequence indices: {start_idx}:{end_idx}")
            
        return TemporalSequence(
            sequence_id=uuid.uuid4(),
            feature_names=self._feature_names,
            timestamps=self._timestamps[start_idx:end_idx],
            values=self._values[start_idx:end_idx],
            patient_id=self.patient_id,
            metadata=self.metadata.copy()
        )
    
    def get_value_at(self, timestamp: datetime, feature_index: int = 0, interpolation: InterpolationMethod = InterpolationMethod.LINEAR) -> float | None:
        """
        Get a value at a specific timestamp, interpolating if necessary.
        
        Args:
            timestamp: Target timestamp
            feature_index: Index of the feature to retrieve
            interpolation: Method to use for interpolation
            
        Returns:
            Interpolated value or None if it can't be determined
        """
        # Check for exact match
        for i, ts in enumerate(self._timestamps):
            if ts == timestamp:
                return self._values[i][feature_index]
        
        # Return None if no data or interpolation is NONE
        if not self._timestamps or interpolation == InterpolationMethod.NONE:
            return None
        
        # Find surrounding timestamps
        before_indices = [i for i, ts in enumerate(self._timestamps) if ts < timestamp]
        after_indices = [i for i, ts in enumerate(self._timestamps) if ts > timestamp]
        
        if not before_indices or not after_indices:
            return None
        
        # Get closest indices before and after
        before_idx = max(before_indices)
        after_idx = min(after_indices)
        
        # Get timestamps and values
        before_ts = self._timestamps[before_idx]
        after_ts = self._timestamps[after_idx]
        before_value = self._values[before_idx][feature_index]
        after_value = self._values[after_idx][feature_index]
        
        # Interpolate based on method
        if interpolation == InterpolationMethod.NEAREST:
            if (timestamp - before_ts) < (after_ts - timestamp):
                return before_value
            else:
                return after_value
        
        # Linear interpolation
        total_seconds = (after_ts - before_ts).total_seconds()
        position = (timestamp - before_ts).total_seconds() / total_seconds
        
        if interpolation == InterpolationMethod.LINEAR:
            return before_value + (after_value - before_value) * position
        
        # Other interpolation methods would be implemented here
        # For now, default to linear
        return before_value + (after_value - before_value) * position
    
    def get_feature_statistics(self) -> dict[str, dict[str, float]]:
        """
        Calculate statistics for each feature in the sequence.
        
        Returns:
            Dictionary mapping feature names to their statistics
        """
        result = {}
        
        # Convert to numpy for easier computation
        values_array = np.array(self._values)
        
        for i, feature_name in enumerate(self._feature_names):
            feature_values = values_array[:, i]
            
            result[feature_name] = {
                "min": float(np.min(feature_values)),
                "max": float(np.max(feature_values)),
                "mean": float(np.mean(feature_values)),
                "std": float(np.std(feature_values)),
                "median": float(np.median(feature_values))
            }
            
        return result
    
    def get_trend(self, feature_index: int = 0, window_size: timedelta | None = None) -> str:
        """
        Calculate trend direction over time for a specific feature.
        
        Args:
            feature_index: Index of the feature to analyze
            window_size: Optional time window to analyze
            
        Returns:
            Trend description ("increasing", "decreasing", "stable", "volatile")
        """
        if not self._timestamps or len(self._timestamps) < 2:
            return "insufficient_data"
        
        # Get values for the specified feature
        values = [v[feature_index] for v in self._values]
        timestamps = self._timestamps
        
        # If window size is provided, only analyze the most recent window
        if window_size:
            cutoff = datetime.now(UTC) - window_size
            windowed_data = [(ts, v) for ts, v in zip(timestamps, values, strict=False) if ts >= cutoff]
            if len(windowed_data) < 2:
                return "insufficient_data"
            
            timestamps = [item[0] for item in windowed_data]
            values = [item[1] for item in windowed_data]
        
        # Calculate start and end values
        start_value = values[0]
        end_value = values[-1]
        
        # Calculate percent change
        if start_value == 0:
            percent_change = float('inf') if end_value > 0 else 0
        else:
            percent_change = (end_value - start_value) / start_value * 100
        
        # Calculate volatility (standard deviation of percent changes between adjacent points)
        changes = []
        for i in range(1, len(values)):
            if values[i-1] == 0:
                continue
            change = (values[i] - values[i-1]) / values[i-1]
            changes.append(change)
        
        volatility = 0
        if changes:
            mean = sum(changes) / len(changes)
            variance = sum((x - mean) ** 2 for x in changes) / len(changes)
            volatility = math.sqrt(variance)
        
        # Determine trend based on percent change and volatility
        if volatility > 0.2:  # 20% standard deviation in changes
            return "volatile"
        elif percent_change > 10:  # 10% increase
            return "increasing"
        elif percent_change < -10:  # 10% decrease
            return "decreasing"
        else:
            return "stable"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert sequence to dictionary for serialization.
        
        Returns:
            Dictionary representation of the sequence
        """
        result = {
            "name": self.name,
            "sequence_id": str(self.sequence_id),
            "sequence_length": self.sequence_length,
            "feature_dimension": self.feature_dimension,
            "feature_names": self.feature_names,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "patient_id": str(self.patient_id),
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "values": self.values
        }
            
        if self.brain_region:
            result["brain_region"] = self.brain_region.value
            
        if self.neurotransmitter:
            result["neurotransmitter"] = self.neurotransmitter.value
            
        if self.temporal_resolution:
            result["temporal_resolution"] = self.temporal_resolution.value
        
        return result