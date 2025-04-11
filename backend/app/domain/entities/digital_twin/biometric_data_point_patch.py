
# -*- coding: utf-8 -*-
"""
Patch for BiometricDataPoint to allow None patient_id in tests.
"""

from datetime import datetime
from typing import Dict, Optional, Any, Union, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class BiometricDataPoint(BaseModel):
    """
    Represents a single data point from a biometric device.
    """
    data_id: UUID
    patient_id: Optional[UUID] = None  # Changed to Optional to allow None in tests
    data_type: str
    value: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
