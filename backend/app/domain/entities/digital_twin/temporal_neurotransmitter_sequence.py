"""
Domain entity representing a time series sequence of a specific neurotransmitter
in a specific brain region for a digital twin.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List
from uuid import UUID

from ..digital_twin_enums import BrainRegion, Neurotransmitter


@dataclass
class TemporalNeurotransmitterSequence:
    """Represents a temporal sequence of neurotransmitter levels."""
    # Non-default fields first
    patient_id: UUID
    brain_region: BrainRegion
    neurotransmitter: Neurotransmitter
    
    # Fields with defaults
    sequence_id: UUID = field(default_factory=uuid.uuid4)
    timestamps: List[datetime] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if len(self.timestamps) != len(self.values):
            raise ValueError("Timestamps and values must have the same length")

    def add_point(self, timestamp: datetime, value: float):
        """Adds a new data point to the sequence."""
        # TODO: Implement logic to handle duplicate timestamps or maintain order?
        self.timestamps.append(timestamp)
        self.values.append(value)
        self.updated_at = datetime.now(timezone.utc)

    def get_latest_value(self) -> float | None:
        """Returns the most recent value in the sequence."""
        if not self.values:
            return None
        # Assumes lists are ordered chronologically
        return self.values[-1]

    # TODO: Add more methods for analysis (e.g., mean, interpolation) as needed
