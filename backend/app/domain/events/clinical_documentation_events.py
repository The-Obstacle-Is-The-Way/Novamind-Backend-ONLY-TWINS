# -*- coding: utf-8 -*-
"""
Clinical documentation events module for the NOVAMIND backend.

This module contains domain events related to clinical documentation in the
concierge psychiatry practice, following the Domain-Driven Design pattern.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.entities.clinical_note import NoteStatus, NoteType


@dataclass
class ClinicalDocumentationEvent:
    """Base class for all clinical documentation-related domain events"""

    note_id: UUID
    patient_id: UUID
    provider_id: UUID
    timestamp: datetime = datetime.utcnow()


@dataclass
class ClinicalNoteCreated(ClinicalDocumentationEvent):
    """Event raised when a clinical note is created"""

    note_type: NoteType
    appointment_id: Optional[UUID] = None


@dataclass
class ClinicalNoteUpdated(ClinicalDocumentationEvent):
    """Event raised when a clinical note is updated"""

    previous_version_id: Optional[UUID] = None
    updated_sections: List[str] = None  # List of section names that were updated


@dataclass
class ClinicalNoteSigned(ClinicalDocumentationEvent):
    """Event raised when a clinical note is signed"""

    signing_provider_id: UUID
    signing_timestamp: datetime
    signing_method: str = "Electronic"  # e.g., "Electronic", "Digital Certificate"
    attestation_statement: Optional[str] = None


@dataclass
class ClinicalNoteLocked(ClinicalDocumentationEvent):
    """Event raised when a clinical note is locked"""

    locking_reason: Optional[str] = None
    auto_locked: bool = (
        False  # Whether the note was automatically locked (e.g., after 24 hours)
    )


@dataclass
class DiagnosisAdded(ClinicalDocumentationEvent):
    """Event raised when a diagnosis is added to a clinical note"""

    diagnosis_code: str
    diagnosis_description: str
    is_primary: bool = False


@dataclass
class DiagnosisRemoved(ClinicalDocumentationEvent):
    """Event raised when a diagnosis is removed from a clinical note"""

    diagnosis_code: str
    removal_reason: Optional[str] = None


@dataclass
class ClinicalNoteShared(ClinicalDocumentationEvent):
    """Event raised when a clinical note is shared with another provider or entity"""

    shared_with_provider_id: Optional[UUID] = None
    shared_with_external_entity: Optional[str] = None
    sharing_purpose: str
    patient_consent_obtained: bool = True
    expiration_date: Optional[datetime] = None
