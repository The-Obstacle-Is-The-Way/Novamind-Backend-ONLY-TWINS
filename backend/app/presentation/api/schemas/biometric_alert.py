# -*- coding: utf-8 -*-
"""
Pydantic schemas for biometric alert API endpoints.

These schemas define the data structures for request and response payloads
in the biometric alert API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class AlertPriorityEnum(str, Enum):
    """Priority levels for biometric alerts."""
    URGENT = "urgent"
    WARNING = "warning"
    INFORMATIONAL = "informational"


class AlertStatusEnum(str, Enum):
    """Status of a biometric alert."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class DataPointSchema(BaseModel):
    """Schema for a biometric data point that triggered an alert."""
    data_type: str = Field(..., description="Type of biometric data (e.g., heart_rate, blood_pressure)")
    value: float = Field(..., description="Value of the biometric measurement")
    timestamp: datetime = Field(..., description="When the measurement was taken")
    source: str = Field(..., description="Source of the measurement (e.g., apple_watch, fitbit)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context about the measurement")


class BiometricAlertCreateSchema(BaseModel):
    """Schema for creating a new biometric alert."""
    patient_id: UUID = Field(..., description="ID of the patient this alert is for")
    alert_type: str = Field(..., description="Type of alert (e.g., elevated_heart_rate, sleep_disruption)")
    description: str = Field(..., description="Human-readable description of the alert")
    priority: AlertPriorityEnum = Field(..., description="Urgency level of the alert")
    data_points: List[Dict[str, Any]] = Field(..., description="Biometric data points that triggered the alert")
    rule_id: UUID = Field(..., description="ID of the clinical rule that generated this alert")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional contextual information")


class BiometricAlertResponseSchema(BaseModel):
    """Schema for biometric alert responses."""
    alert_id: UUID = Field(..., description="Unique identifier for this alert")
    patient_id: UUID = Field(..., description="ID of the patient this alert is for")
    alert_type: str = Field(..., description="Type of alert (e.g., elevated_heart_rate, sleep_disruption)")
    description: str = Field(..., description="Human-readable description of the alert")
    priority: AlertPriorityEnum = Field(..., description="Urgency level of the alert")
    status: AlertStatusEnum = Field(..., description="Current status of the alert")
    created_at: datetime = Field(..., description="When the alert was created")
    updated_at: datetime = Field(..., description="When the alert was last updated")
    data_points: List[Dict[str, Any]] = Field(..., description="Biometric data points that triggered the alert")
    rule_id: UUID = Field(..., description="ID of the clinical rule that generated this alert")
    
    # Acknowledgment and resolution fields
    acknowledged_by: Optional[UUID] = Field(default=None, description="ID of the provider who acknowledged the alert")
    acknowledged_at: Optional[datetime] = Field(default=None, description="When the alert was acknowledged")
    resolved_by: Optional[UUID] = Field(default=None, description="ID of the provider who resolved the alert")
    resolved_at: Optional[datetime] = Field(default=None, description="When the alert was resolved")
    resolution_notes: Optional[str] = Field(default=None, description="Notes on how the alert was resolved")
    
    # Additional data
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional contextual information")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class AlertStatusUpdateSchema(BaseModel):
    """Schema for updating the status of a biometric alert."""
    status: AlertStatusEnum = Field(..., description="New status for the alert")
    notes: Optional[str] = Field(default=None, description="Optional notes about the status update")


class AlertListResponseSchema(BaseModel):
    """Schema for paginated list of biometric alerts."""
    items: List[BiometricAlertResponseSchema] = Field(..., description="List of biometric alerts")
    total: int = Field(..., description="Total number of alerts matching the criteria")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True