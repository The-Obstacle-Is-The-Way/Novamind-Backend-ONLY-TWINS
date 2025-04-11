# -*- coding: utf-8 -*-
"""
Appointment events module for the NOVAMIND backend.

This module contains domain events related to appointments in the
concierge psychiatry practice, following the Domain-Driven Design pattern.
"""

from dataclasses import dataclass
from datetime import datetime, UTC, UTC
from typing import Optional
from uuid import UUID

from app.domain.entities.appointment import AppointmentStatus, AppointmentType


@dataclass
class AppointmentEvent:
    """Base class for all appointment-related domain events"""

    appointment_id: UUID
    patient_id: UUID
    provider_id: UUID
    timestamp: datetime = datetime.now(UTC)


@dataclass
class AppointmentScheduled(AppointmentEvent):
    """Event raised when an appointment is scheduled"""

    appointment_date: datetime
    appointment_type: AppointmentType
    is_telehealth: bool
    notes: Optional[str] = None


@dataclass
class AppointmentRescheduled(AppointmentEvent):
    """Event raised when an appointment is rescheduled"""

    old_date: datetime
    new_date: datetime
    reason: Optional[str] = None


@dataclass
class AppointmentCancelled(AppointmentEvent):
    """Event raised when an appointment is cancelled"""

    cancellation_reason: Optional[str] = None
    cancellation_fee_applied: bool = False
    cancelled_by_patient: bool = False


@dataclass
class AppointmentConfirmed(AppointmentEvent):
    """Event raised when an appointment is confirmed"""

    confirmation_method: str  # e.g., "SMS", "Email", "Phone"
    confirmation_timestamp: datetime


@dataclass
class AppointmentCompleted(AppointmentEvent):
    """Event raised when an appointment is completed"""

    duration_minutes: int
    clinical_note_id: Optional[UUID] = None


@dataclass
class AppointmentNoShow(AppointmentEvent):
    """Event raised when a patient doesn't show up for an appointment"""

    no_show_fee_applied: bool = False
    follow_up_scheduled: bool = False
