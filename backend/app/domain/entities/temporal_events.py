"""
Temporal events module for the Temporal Neurotransmitter System.

This module defines the foundational data structure for representing
time-based events with values and metadata.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Generic, TypeVar, Set
import uuid
from uuid import UUID
from enum import Enum, auto

T = TypeVar('T', float, int, bool, str)


class CorrelationType(Enum):
    """Types of correlations between events."""
    CAUSATION = "causation"
    ASSOCIATION = "association"
    TEMPORAL = "temporal"
    CAUSAL_CHAIN = "causal_chain"
    BIDIRECTIONAL = "bidirectional"


class TemporalEvent(Generic[T]):
    """
    An event that occurs at a specific point in time.
    
    This class represents any data point with a timestamp, particularly
    neurotransmitter levels measured at specific times. It includes
    both the value and optional metadata for rich context.
    """
    
    def __init__(
        self,
        timestamp: datetime,
        value: T,
        event_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new temporal event.
        
        Args:
            timestamp: When the event occurred
            value: The value associated with this event
            event_id: Unique identifier for the event
            patient_id: Identifier of the associated patient
            metadata: Additional information about this event
        """
        self.timestamp = timestamp
        self.value = value
        self.event_id = event_id or uuid.uuid4()
        self.patient_id = patient_id
        self.metadata = metadata or {}
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add a metadata key-value pair to the event.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def update_value(self, new_value: T) -> None:
        """
        Update the event's value.
        
        Args:
            new_value: New value for the event
        """
        self.value = new_value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.
        
        Returns:
            Dictionary representation of the event
        """
        result = {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata
        }
        
        if self.patient_id:
            result["patient_id"] = str(self.patient_id)
        
        return result
    
    def __str__(self) -> str:
        """
        Get string representation of the event.
        
        Returns:
            String representation
        """
        return f"Event({self.timestamp.isoformat()}: {self.value})"
    
    def __eq__(self, other) -> bool:
        """
        Check if two events are equal.
        
        Args:
            other: Other event to compare with
            
        Returns:
            True if events are equal, False otherwise
        """
        if not isinstance(other, TemporalEvent):
            return False
        
        return (
            self.timestamp == other.timestamp and
            self.value == other.value and
            self.event_id == other.event_id
        )


class CorrelatedEvent(TemporalEvent[T]):
    """
    An event that is correlated with other events.
    
    This class extends TemporalEvent with correlation capabilities,
    tracking relationships between events for analysis.
    """
    
    def __init__(
        self,
        timestamp: datetime = None,
        value: T = None,
        event_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_type: Optional[CorrelationType] = None,
        correlation_strength: float = 0.0,
        correlated_events: Optional[Set[UUID]] = None,
        event_type: Optional[str] = None
    ):
        """
        Initialize a new correlated event.
        
        Args:
            timestamp: When the event occurred
            value: The value associated with this event
            event_id: Unique identifier for the event
            patient_id: Identifier of the associated patient
            metadata: Additional information about this event
            correlation_type: Type of correlation with other events
            correlation_strength: Strength of correlation (0.0-1.0)
            correlated_events: Set of event IDs this event is correlated with
            event_type: Type of the event (e.g., "neurotransmitter_sequence_generated")
        """
        # If timestamp is not provided (for metadata-only events),
        # use current time
        if timestamp is None:
            timestamp = datetime.now()
        
        # For metadata-only events, use empty value
        if value is None:
            value = 0.0 if T == float else ""  # type: ignore
        
        # Update metadata with event_type if provided
        local_metadata = metadata or {}
        if event_type:
            if local_metadata is None:
                local_metadata = {}
            local_metadata["event_type"] = event_type
        
        super().__init__(
            timestamp=timestamp,
            value=value,
            event_id=event_id,
            patient_id=patient_id,
            metadata=local_metadata
        )
        
        self.correlation_type = correlation_type
        self.correlation_strength = max(0.0, min(1.0, correlation_strength))
        self.correlated_events = correlated_events or set()
    
    def add_correlation(
        self,
        event_id: UUID,
        correlation_type: CorrelationType,
        strength: float = 0.5
    ) -> None:
        """
        Add a correlation to another event.
        
        Args:
            event_id: ID of the event to correlate with
            correlation_type: Type of correlation
            strength: Strength of correlation (0.0-1.0)
        """
        self.correlated_events.add(event_id)
        self.correlation_type = correlation_type
        self.correlation_strength = max(0.0, min(1.0, strength))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.
        
        Returns:
            Dictionary representation of the event
        """
        result = super().to_dict()
        
        result.update({
            "correlation_strength": self.correlation_strength,
            "correlated_events": [str(event_id) for event_id in self.correlated_events]
        })
        
        if self.correlation_type:
            result["correlation_type"] = self.correlation_type.value
            
        if "event_type" in self.metadata:
            result["event_type"] = self.metadata["event_type"]
        
        return result


class EventChain:
    """
    A chain of causally connected temporal events.
    
    This class represents a sequence of events that form a causal chain,
    useful for analyzing event propagation and effects over time.
    """
    
    def __init__(
        self,
        name: str,
        chain_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        events: Optional[List[UUID]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize a new event chain.
        
        Args:
            name: Name of the chain
            chain_id: Unique identifier for the chain
            patient_id: Identifier of the associated patient
            events: Ordered list of event IDs in this chain
            metadata: Additional metadata for the chain
            created_at: Creation timestamp
        """
        self.name = name
        self.chain_id = chain_id or uuid.uuid4()
        self.patient_id = patient_id
        self.events = events or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
    
    def add_event(self, event_id: UUID) -> None:
        """
        Add an event to the chain.
        
        Args:
            event_id: The event ID to add
        """
        self.events.append(event_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert chain to dictionary for serialization.
        
        Returns:
            Dictionary representation of the chain
        """
        return {
            "name": self.name,
            "chain_id": str(self.chain_id),
            "created_at": self.created_at.isoformat(),
            "event_count": len(self.events),
            "metadata": self.metadata,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "events": [str(event_id) for event_id in self.events]
        }


class TemporalEventGroup:
    """
    A group of related temporal events.
    
    This class represents a collection of events that form a logical group,
    such as all neurotransmitter measurements from a specific therapeutic session.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        group_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        events: Optional[List[TemporalEvent]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize a new temporal event group.
        
        Args:
            name: Name of the group
            description: Description of the group
            group_id: Unique identifier for the group
            patient_id: Identifier of the associated patient
            events: List of temporal events in this group
            metadata: Additional metadata for the group
            created_at: Creation timestamp
        """
        self.name = name
        self.description = description or ""
        self.group_id = group_id or uuid.uuid4()
        self.patient_id = patient_id
        self.events = events or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
    
    def add_event(self, event: TemporalEvent) -> None:
        """
        Add an event to the group.
        
        Args:
            event: The temporal event to add
        """
        self.events.append(event)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert group to dictionary for serialization.
        
        Returns:
            Dictionary representation of the group
        """
        return {
            "name": self.name,
            "description": self.description,
            "group_id": str(self.group_id),
            "created_at": self.created_at.isoformat(),
            "event_count": len(self.events),
            "metadata": self.metadata,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "events": [event.to_dict() for event in self.events[:100]]  # Limit to first 100 for performance
        }