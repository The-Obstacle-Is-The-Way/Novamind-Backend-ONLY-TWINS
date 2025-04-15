"""
Domain entity representing a clinical Appointment.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from app.domain.entities.base_entity import BaseEntity

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class AppointmentType(str, Enum):
    INITIAL_CONSULTATION = "initial_consultation"
    FOLLOW_UP = "follow_up"
    THERAPY_SESSION = "therapy_session"
    MEDICATION_MANAGEMENT = "medication_management"
    ASSESSMENT = "assessment"

@dataclass
class Appointment(BaseEntity):
    """Appointment entity."""
    # Non-default fields first (id is inherited from BaseEntity)
    patient_id: UUID
    provider_id: UUID # ID of the clinician/provider
    start_time: datetime
    end_time: datetime
    appointment_type: AppointmentType
    
    # Fields with default values/factories
    # id: UUID = field(default_factory=uuid4) # Removed, inherited from BaseEntity
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None # Optional notes about the appointment itself
    location: Optional[str] = None # e.g., "Telehealth", "Clinic Room 3"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.end_time <= self.start_time:
            raise ValueError("Appointment end time must be after start time.")
        # Call BaseEntity's post_init if it exists
        if hasattr(super(), '__post_init__'):
            super().__post_init__()

    def update_status(self, new_status: AppointmentStatus):
        """Update the appointment status."""
        # Add logic here if status transitions need validation
        self.status = new_status
        self.touch()

    def reschedule(self, new_start_time: datetime, new_end_time: Optional[datetime] = None):
        """Reschedule the appointment."""
        if new_end_time is None:
            duration = self.end_time - self.start_time
            new_end_time = new_start_time + duration
        
        if new_end_time <= new_start_time:
             raise ValueError("Rescheduled end time must be after start time.")

        self.start_time = new_start_time
        self.end_time = new_end_time
        # Reset status to scheduled or confirmed if needed
        if self.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]:
            self.status = AppointmentStatus.SCHEDULED # Or CONFIRMED based on policy
        self.touch()

    def touch(self):
        """Update the last_updated timestamp."""
        self.last_updated = datetime.utcnow()

