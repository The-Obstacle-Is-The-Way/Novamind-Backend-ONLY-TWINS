# -*- coding: utf-8 -*-
"""
Module for representing biometric data points in the Digital Twin platform.
Used by standalone tests for unit testing without database dependencies.
"""

from datetime import datetime
from typing import Dict, Optional, Any, Union, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class BiometricDataPoint(BaseModel):
    """
    Represents a single data point from a biometric device.
    
    This entity encapsulates all information about a biometric reading,
    including metadata about the reading's source and confidence level.
    """
    data_id: UUID
    patient_id: UUID  # In production this is non-optional, but tests will monkey patch as needed
    data_type: str
    value: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0

    class Config:
        """Configuration for Pydantic model."""
        # Allow arbitrary types for testing - will be monkey patched
        arbitrary_types_allowed = True