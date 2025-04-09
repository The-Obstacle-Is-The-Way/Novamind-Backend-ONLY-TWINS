"""
Temporal sequence models for the Temporal Neurotransmitter System.

This module defines the core classes for representing time series data
for neurotransmitter levels and other temporal measurements.
"""
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Tuple, Optional, Any, Union, Iterator, Generic, TypeVar
import uuid
from uuid import UUID
import statistics
import math
from enum import Enum, auto

from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter, TemporalResolution
from app.domain.entities.temporal_events import TemporalEvent


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
        name: str,
        sequence_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        events: Optional[List[TemporalEvent[T]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        brain_region: Optional[BrainRegion] = None,
        neurotransmitter: Optional[Neurotransmitter] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        temporal_resolution: Optional[TemporalResolution] = None
    ):
        """
        Initialize a new temporal sequence.
        
        Args:
            name: Name of the sequence
            sequence_id: Unique identifier for the sequence
            patient_id: Identifier of the associated patient
            events: List of temporal events in this sequence
            metadata: Additional metadata for the sequence
            brain_region: Associated brain region if applicable
            neurotransmitter: Associated neurotransmitter if applicable
            created_at: Creation timestamp
            updated_at: Last update timestamp
            temporal_resolution: Time resolution of the sequence
        """
        self.name = name
        self.sequence_id = sequence_id or uuid.uuid4()
        self.patient_id = patient_id
        self.events = sorted(events or [], key=lambda e: e.timestamp)
        self.metadata = metadata or {}
        self.brain_region = brain_region
        self.neurotransmitter = neurotransmitter
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
        self.temporal_resolution = temporal_resolution
        
        # Initialize feature names and cached values
        self._feature_names = []
        self._values = None  # Explicitly set to None initially
        self._sequence_length = None  # For tests that need to override the computed length
        
        # If feature_names are in metadata, initialize the internal property
        if metadata and "feature_names" in metadata:
            self._feature_names = metadata["feature_names"]
        elif neurotransmitter:
            self._feature_names = [neurotransmitter.value]
    
    @property
    def timestamps(self) -> List[datetime]:
        """Get all timestamps in the sequence, ordered chronologically."""
        return [event.timestamp for event in self.events]
    
    @property
    def values(self) -> List[T]:
        """
        Get all values in the sequence, ordered chronologically.
        
        If _values is explicitly set (for testing), returns that.
        Otherwise, extracts values from events.
        """
        if self._values is not None:
            return self._values
        return [event.value for event in self.events]
    
    @values.setter
    def values(self, new_values: List[T]) -> None:
        """
        Set the values for this sequence.
        
        Args:
            new_values: List of values to set
        """
        self._values = new_values
        
        # Update metadata to indicate values were explicitly set
        self.metadata["explicit_values"] = True
    
    @property
    def feature_names(self) -> List[str]:
        """Get the names of features in this sequence."""
        if self._feature_names:
            return self._feature_names
        elif self.neurotransmitter:
            return [self.neurotransmitter.value]
        else:
            return ["value"]
    
    @feature_names.setter
    def feature_names(self, new_feature_names: List[str]) -> None:
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
        Get the number of events in the sequence.
        
        If _sequence_length is explicitly set (for testing), returns that.
        Otherwise, computes from the events list.
        """
        if self._sequence_length is not None:
            return self._sequence_length
        return len(self.events)
    
    @sequence_length.setter
    def sequence_length(self, length: int) -> None:
        """
        Set an explicit sequence length (used primarily in tests).
        
        Args:
            length: The sequence length to set
        """
        self._sequence_length = length
        
        # Update metadata to indicate length was explicitly set
        self.metadata["explicit_length"] = length
    
    def add_event(self, event: TemporalEvent[T]) -> None:
        """
        Add a temporal event to the sequence.
        
        Args:
            event: The temporal event to add
        """
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp)
        self.updated_at = datetime.now(UTC)
        
        # Clear cached values when adding events
        self._values = None
    
    def add_value(self, timestamp: datetime, value: T, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a value at a specific timestamp.
        
        Args:
            timestamp: When the value occurred
            value: The value to add
            metadata: Additional metadata for this event
        """
        event = TemporalEvent(timestamp=timestamp, value=value, metadata=metadata or {})
        self.add_event(event)
    
    def get_events_in_range(self, start: datetime, end: datetime) -> List[TemporalEvent[T]]:
        """
        Get events within a specific time range.
        
        Args:
            start: Start of the time range
            end: End of the time range
            
        Returns:
            List of events within the specified range
        """
        return [event for event in self.events if start <= event.timestamp <= end]
    
    def get_values_in_range(self, start: datetime, end: datetime) -> List[T]:
        """
        Get values within a specific time range.
        
        Args:
            start: Start of the time range
            end: End of the time range
            
        Returns:
            List of values within the specified range
        """
        events = self.get_events_in_range(start, end)
        return [event.value for event in events]
    
    def get_value_at(self, timestamp: datetime, interpolation: InterpolationMethod = InterpolationMethod.LINEAR) -> Optional[T]:
        """
        Get a value at a specific timestamp, interpolating if necessary.
        
        Args:
            timestamp: Target timestamp
            interpolation: Method to use for interpolation
            
        Returns:
            Interpolated value or None if it can't be determined
        """
        # Check for exact match
        for event in self.events:
            if event.timestamp == timestamp:
                return event.value
        
        # Return None if no events or interpolation is NONE
        if not self.events or interpolation == InterpolationMethod.NONE:
            return None
        
        # Find surrounding events
        before_events = [e for e in self.events if e.timestamp < timestamp]
        after_events = [e for e in self.events if e.timestamp > timestamp]
        
        if not before_events or not after_events:
            return None
        
        # Get closest events before and after
        before_event = max(before_events, key=lambda e: e.timestamp)
        after_event = min(after_events, key=lambda e: e.timestamp)
        
        # Interpolate based on method
        if interpolation == InterpolationMethod.NEAREST:
            if (timestamp - before_event.timestamp) < (after_event.timestamp - timestamp):
                return before_event.value
            else:
                return after_event.value
        
        # For numeric types, we can do linear interpolation
        if isinstance(before_event.value, (int, float)) and isinstance(after_event.value, (int, float)):
            total_seconds = (after_event.timestamp - before_event.timestamp).total_seconds()
            position = (timestamp - before_event.timestamp).total_seconds() / total_seconds
            
            if interpolation == InterpolationMethod.LINEAR:
                return before_event.value + (after_event.value - before_event.value) * position
            
            # Other interpolation methods would be implemented here
            # For now, default to linear if not NEAREST
            return before_event.value + (after_event.value - before_event.value) * position
            
        # For non-numeric types, use nearest
        return before_event.value if (timestamp - before_event.timestamp) < (after_event.timestamp - timestamp) else after_event.value
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics for the sequence.
        
        Returns:
            Dictionary with computed statistics
        """
        if not self.events:
            return {
                "count": 0,
                "duration": 0,
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
                "std_dev": None,
                "first_timestamp": None,
                "last_timestamp": None
            }
        
        # Extract values if they are numeric
        numeric_values = []
        for event in self.events:
            if isinstance(event.value, (int, float)):
                numeric_values.append(event.value)
        
        # Calculate duration
        duration = (self.events[-1].timestamp - self.events[0].timestamp).total_seconds()
        
        # Return statistics
        stats = {
            "count": len(self.events),
            "duration": duration,
            "first_timestamp": self.events[0].timestamp,
            "last_timestamp": self.events[-1].timestamp
        }
        
        # Add numeric statistics if applicable
        if numeric_values:
            stats.update({
                "mean": statistics.mean(numeric_values),
                "median": statistics.median(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
            })
        
        return stats
    
    def get_trend(self, window_size: Optional[timedelta] = None) -> str:
        """
        Calculate trend direction over time.
        
        Args:
            window_size: Optional time window to analyze
            
        Returns:
            Trend description ("increasing", "decreasing", "stable", "volatile")
        """
        if not self.events or len(self.events) < 2:
            return "insufficient_data"
        
        # If window size is provided, only analyze the most recent window
        if window_size:
            cutoff = datetime.now(UTC) - window_size
            events = [e for e in self.events if e.timestamp >= cutoff]
            if not events or len(events) < 2:
                return "insufficient_data"
        else:
            events = self.events
        
        # Check if values are numeric
        if not all(isinstance(e.value, (int, float)) for e in events):
            return "non_numeric_data"
        
        # Calculate start and end values
        start_value = events[0].value
        end_value = events[-1].value
        
        # Calculate percent change
        if start_value == 0:
            percent_change = float('inf') if end_value > 0 else 0
        else:
            percent_change = (end_value - start_value) / start_value * 100
        
        # Calculate volatility (standard deviation of percent changes between adjacent points)
        changes = []
        for i in range(1, len(events)):
            if events[i-1].value == 0:
                continue
            change = (events[i].value - events[i-1].value) / events[i-1].value
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
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert sequence to dictionary for serialization.
        
        Returns:
            Dictionary representation of the sequence
        """
        result = {
            "name": self.name,
            "sequence_id": str(self.sequence_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "event_count": len(self.events),
            "statistics": self.get_statistics(),
            "trend": self.get_trend(),
            "metadata": self.metadata,
            "feature_names": self.feature_names
        }
        
        if self.patient_id:
            result["patient_id"] = str(self.patient_id)
            
        if self.brain_region:
            result["brain_region"] = self.brain_region.value
            
        if self.neurotransmitter:
            result["neurotransmitter"] = self.neurotransmitter.value
            
        if self.temporal_resolution:
            result["temporal_resolution"] = self.temporal_resolution.value
            
        # Add events data
        if self.events:
            result["events"] = [event.to_dict() for event in self.events[:100]]  # Limit to first 100 for performance
            if len(self.events) > 100:
                result["events_truncated"] = True
                result["total_events"] = len(self.events)
        
        return result
    
    def __iter__(self) -> Iterator[TemporalEvent[T]]:
        """
        Iterate through events in chronological order.
        
        Returns:
            Iterator of temporal events
        """
        return iter(self.events)
    
    def __len__(self) -> int:
        """
        Get the number of events in the sequence.
        
        Returns:
            Number of events
        """
        return len(self.events)
    
    def __getitem__(self, index) -> TemporalEvent[T]:
        """
        Get an event by index.
        
        Args:
            index: Index of the event
            
        Returns:
            The temporal event at the specified index
        """
        return self.events[index]