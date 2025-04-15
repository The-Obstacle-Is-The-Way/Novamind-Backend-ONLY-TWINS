# -*- coding: utf-8 -*-
"""
Pydantic schemas for biometric data API endpoints.

This module defines the request and response schemas for the biometric data
API endpoints, ensuring proper validation and serialization of data.
"""

from datetime import datetime, UTC
from app.domain.utils.datetime_utils import UTC
from typing import Dict, List, Optional, Union, Any
from uuid import UUID

# Import ConfigDict for V2 style config
from pydantic import BaseModel, Field, validator, ConfigDict


class BiometricDataPointCreate(BaseModel):
    """Schema for creating a new biometric data point."""
    
    data_type: str = Field(
        ...,
        description="Type of biometric data (e.g., 'heart_rate', 'blood_pressure')",
        examples=["heart_rate", "blood_pressure", "sleep_quality"]
    )
    value: Union[float, int, str, Dict[str, Any]] = Field(
        ...,
        description="The measured value (can be numeric, string, or structured data)",
        examples=[75, "120/80", {"deep_sleep": 3.5, "rem_sleep": 2.1}]
    )
    source: str = Field(
        ...,
        description="Device or system that provided the measurement",
        examples=["smartwatch", "blood_pressure_monitor", "sleep_tracker"]
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When the measurement was taken (defaults to current time)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional contextual information about the measurement",
        examples=[{"activity": "resting"}, {"location": "home"}]
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in the measurement (0.0-1.0)"
    )
    
    @validator("data_type")
    def validate_data_type(cls, v):
        """Validate that data_type is not empty."""
        if not v or not v.strip():
            raise ValueError("Biometric data type cannot be empty")
        return v


class BiometricDataPointBatchCreate(BaseModel):
    """Schema for creating multiple biometric data points in a batch."""
    
    data_points: List[BiometricDataPointCreate] = Field(
        ...,
        min_items=1,
        description="List of biometric data points to create"
    )


class BiometricDataPointResponse(BaseModel):
    """Schema for biometric data point response."""
    
    data_id: UUID = Field(
        ...,
        description="Unique identifier for this data point"
    )
    data_type: str = Field(
        ...,
        description="Type of biometric data"
    )
    value: Union[float, int, str, Dict[str, Any]] = Field(
        ...,
        description="The measured value"
    )
    timestamp: datetime = Field(
        ...,
        description="When the measurement was taken"
    )
    source: str = Field(
        ...,
        description="Device or system that provided the measurement"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional contextual information about the measurement"
    )
    confidence: float = Field(
        ...,
        description="Confidence level in the measurement (0.0-1.0)"
    )
    
    # V2 Config
    model_config = ConfigDict(json_encoders={
        datetime: lambda dt: dt.isoformat(),
        UUID: lambda uuid: str(uuid)
    })


class BiometricDataPointListResponse(BaseModel):
    """Schema for a list of biometric data points."""
    
    data_points: List[BiometricDataPointResponse] = Field(
        ...,
        description="List of biometric data points"
    )
    count: int = Field(
        ...,
        description="Total number of data points in the response"
    )


class BiometricTwinResponse(BaseModel):
    """Schema for biometric twin response."""
    
    twin_id: UUID = Field(
        ...,
        description="Unique identifier for this biometric twin"
    )
    patient_id: UUID = Field(
        ...,
        description="ID of the patient this twin represents"
    )
    created_at: datetime = Field(
        ...,
        description="When this twin was first created"
    )
    updated_at: datetime = Field(
        ...,
        description="When this twin was last updated"
    )
    baseline_established: bool = Field(
        ...,
        description="Whether baseline measurements have been established"
    )
    connected_devices: List[str] = Field(
        default_factory=list,
        description="List of devices currently connected to this twin"
    )
    data_points_count: int = Field(
        ...,
        description="Number of data points associated with this twin"
    )
    
    # V2 Config
    model_config = ConfigDict(json_encoders={
        datetime: lambda dt: dt.isoformat(),
        UUID: lambda uuid: str(uuid)
    })


class DeviceConnectionRequest(BaseModel):
    """Schema for connecting a device to a biometric twin."""
    
    device_id: str = Field(
        ...,
        description="Unique identifier for the device",
        examples=["smartwatch-123", "glucose-monitor-456"]
    )
    device_type: str = Field(
        ...,
        description="Type of device",
        examples=["smartwatch", "glucose_monitor", "blood_pressure_monitor"]
    )
    connection_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional information about the connection",
        examples=[{"model": "Apple Watch Series 7", "os_version": "8.5"}]
    )


class DeviceDisconnectionRequest(BaseModel):
    """Schema for disconnecting a device from a biometric twin."""
    
    device_id: str = Field(
        ...,
        description="Unique identifier for the device",
        examples=["smartwatch-123", "glucose-monitor-456"]
    )
    reason: Optional[str] = Field(
        default="user_initiated",
        description="Reason for disconnection",
        examples=["user_initiated", "battery_low", "connection_lost"]
    )


class TrendAnalysisResponse(BaseModel):
    """Schema for trend analysis response."""
    
    status: str = Field(
        ...,
        description="Status of the analysis",
        examples=["success", "insufficient_data", "invalid_data"]
    )
    data_type: str = Field(
        ...,
        description="Type of biometric data analyzed"
    )
    period: str = Field(
        ...,
        description="Time period of the analysis",
        examples=["7 days", "30 days"]
    )
    data_points_count: int = Field(
        ...,
        description="Number of data points included in the analysis"
    )
    average: Optional[float] = Field(
        default=None,
        description="Average value over the period"
    )
    minimum: Optional[float] = Field(
        default=None,
        description="Minimum value over the period"
    )
    maximum: Optional[float] = Field(
        default=None,
        description="Maximum value over the period"
    )
    trend: Optional[str] = Field(
        default=None,
        description="Detected trend direction",
        examples=["increasing", "decreasing", "stable", "fluctuating"]
    )
    last_value: Optional[float] = Field(
        default=None,
        description="Most recent value"
    )
    last_updated: Optional[str] = Field(
        default=None,
        description="Timestamp of the most recent data point"
    )
    message: Optional[str] = Field(
        default=None,
        description="Additional information or explanation"
    )


class CorrelationAnalysisRequest(BaseModel):
    """Schema for correlation analysis request."""
    
    primary_data_type: str = Field(
        ...,
        description="Primary type of biometric data",
        examples=["heart_rate", "stress_level"]
    )
    secondary_data_types: List[str] = Field(
        ...,
        min_items=1,
        description="Other types to correlate with the primary type",
        examples=[["sleep_quality", "activity_level", "stress_level"]]
    )
    window_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to include in the analysis"
    )


class CorrelationAnalysisResponse(BaseModel):
    """Schema for correlation analysis response."""
    
    correlations: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping data types to correlation coefficients"
    )
    primary_data_type: str = Field(
        ...,
        description="Primary type of biometric data used in the analysis"
    )
    window_days: int = Field(
        ...,
        description="Number of days included in the analysis"
    )
    data_points_count: Dict[str, int] = Field(
        ...,
        description="Dictionary mapping data types to the number of data points used"
    )