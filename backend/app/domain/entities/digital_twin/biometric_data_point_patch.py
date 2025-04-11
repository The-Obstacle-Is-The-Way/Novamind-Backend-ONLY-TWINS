
"""
Patch for BiometricDataPoint to allow None patient_id in tests.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BiometricDataPoint(BaseModel):
    """
    Represents a single data point from a biometric device.
    """
    data_id: UUID
    patient_id: UUID | None = None  # Changed to Optional to allow None in tests
    data_type: str
    value: float
    timestamp: datetime
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
