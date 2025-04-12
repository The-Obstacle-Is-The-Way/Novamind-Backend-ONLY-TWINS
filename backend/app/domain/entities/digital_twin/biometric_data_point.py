"""
Module for representing biometric data points in the Digital Twin platform.
Used by standalone tests for unit testing without database dependencies.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BiometricDataPoint(BaseModel):
    """
    Represents a single data point from a biometric device.
    
    This entity encapsulates all information about a biometric reading,
    including metadata about the reading's source and confidence level.
    """
    data_id: UUID
    patient_id: UUID | None = None  # In production this is non-optional, but tests may need None
    data_type: str
    value: float
    timestamp: datetime
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0

    model_config = ConfigDict(
        # Allow arbitrary types for testing - will be monkey patched
        arbitrary_types_allowed=True
    )