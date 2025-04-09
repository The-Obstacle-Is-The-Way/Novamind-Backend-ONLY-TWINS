# -*- coding: utf-8 -*-
"""
BiometricAlert domain entity.

This module defines the BiometricAlert entity, which represents a clinical alert
generated from biometric data analysis that may require clinical intervention.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class AlertPriority(str, Enum):
    """Priority levels for biometric alerts."""
    URGENT = "urgent"
    WARNING = "warning"
    INFORMATIONAL = "informational"


class AlertStatus(str, Enum):
    """Status of a biometric alert."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class BiometricAlert:
    """
    BiometricAlert domain entity.
    
    Represents a clinical alert generated from biometric data analysis
    that may require clinical intervention.
    """
    
    def __init__(
        self,
        patient_id: UUID,
        alert_type: str,
        description: str,
        priority: AlertPriority,
        data_points: List[Dict[str, Any]],
        rule_id: UUID,
        alert_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        status: Optional[AlertStatus] = None,
        acknowledged_by: Optional[UUID] = None,
        acknowledged_at: Optional[datetime] = None,
        resolved_by: Optional[UUID] = None,
        resolved_at: Optional[datetime] = None,
        resolution_notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a BiometricAlert.
        
        Args:
            patient_id: ID of the patient this alert is for
            alert_type: Type of alert (e.g., elevated_heart_rate, sleep_disruption)
            description: Human-readable description of the alert
            priority: Urgency level of the alert
            data_points: Biometric data points that triggered the alert
            rule_id: ID of the clinical rule that generated this alert
            alert_id: Unique identifier for this alert (generated if not provided)
            created_at: When the alert was created (current time if not provided)
            updated_at: When the alert was last updated (current time if not provided)
            status: Current status of the alert (NEW if not provided)
            acknowledged_by: ID of the provider who acknowledged the alert
            acknowledged_at: When the alert was acknowledged
            resolved_by: ID of the provider who resolved the alert
            resolved_at: When the alert was resolved
            resolution_notes: Notes on how the alert was resolved
            metadata: Additional contextual information
        """
        self.patient_id = patient_id
        self.alert_type = alert_type
        self.description = description
        self.priority = priority
        self.data_points = data_points
        self.rule_id = rule_id
        
        # Generate ID and timestamps if not provided
        self.alert_id = alert_id or uuid4()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # Status and acknowledgment
        self.status = status or AlertStatus.NEW
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = acknowledged_at
        self.resolved_by = resolved_by
        self.resolved_at = resolved_at
        self.resolution_notes = resolution_notes
        
        # Additional data
        self.metadata = metadata or {}
    
    def acknowledge(self, provider_id: UUID) -> None:
        """
        Acknowledge the alert.
        
        Args:
            provider_id: ID of the provider acknowledging the alert
        """
        if self.status == AlertStatus.NEW:
            self.status = AlertStatus.ACKNOWLEDGED
            self.acknowledged_by = provider_id
            self.acknowledged_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def mark_in_progress(self, provider_id: UUID) -> None:
        """
        Mark the alert as in progress.
        
        Args:
            provider_id: ID of the provider working on the alert
        """
        if self.status in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]:
            self.status = AlertStatus.IN_PROGRESS
            
            # If not already acknowledged, acknowledge it
            if not self.acknowledged_by:
                self.acknowledged_by = provider_id
                self.acknowledged_at = datetime.utcnow()
            
            self.updated_at = datetime.utcnow()
    
    def resolve(self, provider_id: UUID, notes: Optional[str] = None) -> None:
        """
        Resolve the alert.
        
        Args:
            provider_id: ID of the provider resolving the alert
            notes: Optional notes about the resolution
        """
        if self.status in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS]:
            self.status = AlertStatus.RESOLVED
            self.resolved_by = provider_id
            self.resolved_at = datetime.utcnow()
            
            if notes:
                self.resolution_notes = notes
            
            # If not already acknowledged, acknowledge it
            if not self.acknowledged_by:
                self.acknowledged_by = provider_id
                self.acknowledged_at = datetime.utcnow()
            
            self.updated_at = datetime.utcnow()
    
    def dismiss(self, provider_id: UUID, notes: Optional[str] = None) -> None:
        """
        Dismiss the alert as not requiring action.
        
        Args:
            provider_id: ID of the provider dismissing the alert
            notes: Optional notes about why the alert was dismissed
        """
        if self.status in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS]:
            self.status = AlertStatus.DISMISSED
            self.resolved_by = provider_id
            self.resolved_at = datetime.utcnow()
            
            if notes:
                self.resolution_notes = notes
            
            # If not already acknowledged, acknowledge it
            if not self.acknowledged_by:
                self.acknowledged_by = provider_id
                self.acknowledged_at = datetime.utcnow()
            
            self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the alert."""
        return (
            f"<BiometricAlert(alert_id={self.alert_id}, "
            f"patient_id={self.patient_id}, "
            f"alert_type={self.alert_type}, "
            f"priority={self.priority}, "
            f"status={self.status})>"
        )