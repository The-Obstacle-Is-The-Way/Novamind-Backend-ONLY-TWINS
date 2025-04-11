# -*- coding: utf-8 -*-
"""
Patient events module for the NOVAMIND backend.

This module contains domain events related to patients in the
concierge psychiatry practice, following the Domain-Driven Design pattern.
"""

from dataclasses import dataclass
from datetime import datetime, UTC, UTC
from typing import Dict, Optional
from uuid import UUID


@dataclass
class PatientEvent:
    """Base class for all patient-related domain events"""

    patient_id: UUID
    timestamp: datetime = datetime.now(UTC)


@dataclass
class PatientRegistered(PatientEvent):
    """Event raised when a new patient is registered"""

    first_name: str
    last_name: str
    preferred_provider_id: Optional[UUID] = None


@dataclass
class PatientInformationUpdated(PatientEvent):
    """Event raised when patient information is updated"""

    updated_fields: Dict[str, str]
    updated_by: UUID  # User ID who made the update


@dataclass
class PatientProviderAssigned(PatientEvent):
    """Event raised when a provider is assigned to a patient"""

    provider_id: UUID
    is_primary: bool = True
    previous_provider_id: Optional[UUID] = None


@dataclass
class PatientStatusChanged(PatientEvent):
    """Event raised when a patient's status changes"""

    new_status: str  # e.g., "Active", "Inactive", "On Hold"
    previous_status: str
    reason: Optional[str] = None


@dataclass
class PatientConsentUpdated(PatientEvent):
    """Event raised when a patient's consent status is updated"""

    consent_type: str  # e.g., "Treatment", "Information Sharing", "Research"
    consented: bool
    consent_document_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None


@dataclass
class PatientArchived(PatientEvent):
    """Event raised when a patient record is archived"""

    reason: str
    archived_by: UUID  # User ID who archived the patient
    retention_period_years: int = 7  # Default HIPAA retention period
