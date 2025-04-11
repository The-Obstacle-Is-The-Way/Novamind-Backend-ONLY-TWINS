"""
Appointment Entity

This module defines the Appointment entity for the domain layer,
representing a scheduled meeting between a patient and a provider.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.exceptions import InvalidAppointmentStateError, InvalidAppointmentTimeError


class AppointmentStatus(Enum):
    """Status of an appointment."""
    
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(Enum):
    """Type of appointment."""
    
    INITIAL_CONSULTATION = "initial_consultation"
    FOLLOW_UP = "follow_up"
    MEDICATION_REVIEW = "medication_review"
    THERAPY = "therapy"
    EMERGENCY = "emergency"
    TELEHEALTH = "telehealth"
    IN_PERSON = "in_person"


class AppointmentPriority(Enum):
    """Priority of an appointment."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Appointment:
    """
    Appointment entity representing a scheduled meeting between a patient and a provider.
    
    This entity encapsulates all the business logic related to appointments,
    including scheduling, rescheduling, cancellation, and completion.
    """
    
    def __init__(
        self,
        id: UUID | str | None = None,
        patient_id: UUID | str = None,
        provider_id: UUID | str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        appointment_type: AppointmentType | str = None,
        status: AppointmentStatus | str = AppointmentStatus.SCHEDULED,
        priority: AppointmentPriority | str = AppointmentPriority.NORMAL,
        location: str | None = None,
        notes: str | None = None,
        reason: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        cancelled_at: datetime | None = None,
        cancelled_by: UUID | str | None = None,
        cancellation_reason: str | None = None,
        reminder_sent: bool = False,
        reminder_sent_at: datetime | None = None,
        follow_up_scheduled: bool = False,
        follow_up_appointment_id: UUID | str | None = None,
        previous_appointment_id: UUID | str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        """
        Initialize an appointment.
        
        Args:
            id: Unique identifier for the appointment
            patient_id: ID of the patient
            provider_id: ID of the provider
            start_time: Start time of the appointment
            end_time: End time of the appointment
            appointment_type: Type of appointment
            status: Status of the appointment
            priority: Priority of the appointment
            location: Location of the appointment
            notes: Notes about the appointment
            reason: Reason for the appointment
            created_at: Time the appointment was created
            updated_at: Time the appointment was last updated
            cancelled_at: Time the appointment was cancelled
            cancelled_by: ID of the user who cancelled the appointment
            cancellation_reason: Reason for cancellation
            reminder_sent: Whether a reminder has been sent
            reminder_sent_at: Time the reminder was sent
            follow_up_scheduled: Whether a follow-up has been scheduled
            follow_up_appointment_id: ID of the follow-up appointment
            previous_appointment_id: ID of the previous appointment
            metadata: Additional metadata
        """
        self.id = id if id else uuid4()
        self.patient_id = patient_id
        self.provider_id = provider_id
        self.start_time = start_time
        self.end_time = end_time
        
        # Convert string to enum if necessary
        if isinstance(appointment_type, str):
            self.appointment_type = AppointmentType(appointment_type)
        else:
            self.appointment_type = appointment_type
        
        # Convert string to enum if necessary
        if isinstance(status, str):
            self.status = AppointmentStatus(status)
        else:
            self.status = status
        
        # Convert string to enum if necessary
        if isinstance(priority, str):
            self.priority = AppointmentPriority(priority)
        else:
            self.priority = priority
        
        self.location = location
        self.notes = notes
        self.reason = reason
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.cancelled_at = cancelled_at
        self.cancelled_by = cancelled_by
        self.cancellation_reason = cancellation_reason
        self.reminder_sent = reminder_sent
        self.reminder_sent_at = reminder_sent_at
        self.follow_up_scheduled = follow_up_scheduled
        self.follow_up_appointment_id = follow_up_appointment_id
        self.previous_appointment_id = previous_appointment_id
        self.metadata = metadata or {}
        
        # Validate the appointment
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate the appointment.
        
        Raises:
            InvalidAppointmentTimeError: If the appointment times are invalid
            InvalidAppointmentStateError: If the appointment state is invalid
        """
        # Check required fields
        if not self.patient_id:
            raise InvalidAppointmentStateError("Patient ID is required")
        
        if not self.provider_id:
            raise InvalidAppointmentStateError("Provider ID is required")
        
        if not self.start_time:
            raise InvalidAppointmentStateError("Start time is required")
        
        if not self.end_time:
            raise InvalidAppointmentStateError("End time is required")
        
        if not self.appointment_type:
            raise InvalidAppointmentStateError("Appointment type is required")
        
        # Check that start time is before end time
        if self.start_time >= self.end_time:
            raise InvalidAppointmentTimeError("Start time must be before end time")
        
        # Check that appointment is not in the past
        if self.start_time < datetime.now() and self.status == AppointmentStatus.SCHEDULED:
            raise InvalidAppointmentTimeError("Cannot schedule an appointment in the past")
    
    def confirm(self) -> None:
        """
        Confirm the appointment.
        
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be confirmed
        """
        if self.status != AppointmentStatus.SCHEDULED:
            raise InvalidAppointmentStateError(
                f"Cannot confirm appointment with status {self.status.value}"
            )
        
        self.status = AppointmentStatus.CONFIRMED
        self.updated_at = datetime.now()
    
    def check_in(self) -> None:
        """
        Check in the patient for the appointment.
        
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be checked in
        """
        if self.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]:
            raise InvalidAppointmentStateError(
                f"Cannot check in appointment with status {self.status.value}"
            )
        
        self.status = AppointmentStatus.CHECKED_IN
        self.updated_at = datetime.now()
    
    def start(self) -> None:
        """
        Start the appointment.
        
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be started
        """
        if self.status != AppointmentStatus.CHECKED_IN:
            raise InvalidAppointmentStateError(
                f"Cannot start appointment with status {self.status.value}"
            )
        
        self.status = AppointmentStatus.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """
        Complete the appointment.
        
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be completed
        """
        if self.status != AppointmentStatus.IN_PROGRESS:
            raise InvalidAppointmentStateError(
                f"Cannot complete appointment with status {self.status.value}"
            )
        
        self.status = AppointmentStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def cancel(self, cancelled_by: UUID | str, reason: str | None = None) -> None:
        """
        Cancel the appointment.
        
        Args:
            cancelled_by: ID of the user cancelling the appointment
            reason: Reason for cancellation
            
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be cancelled
        """
        if self.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW
        ]:
            raise InvalidAppointmentStateError(
                f"Cannot cancel appointment with status {self.status.value}"
            )
        
        self.status = AppointmentStatus.CANCELLED
        self.cancelled_at = datetime.now()
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.updated_at = datetime.now()
    
    def mark_no_show(self) -> None:
        """
        Mark the appointment as a no-show.
        
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be marked as no-show
        """
        if self.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]:
            raise InvalidAppointmentStateError(
                f"Cannot mark appointment with status {self.status.value} as no-show"
            )
        
        self.status = AppointmentStatus.NO_SHOW
        self.updated_at = datetime.now()
    
    def reschedule(
        self,
        new_start_time: datetime,
        new_end_time: datetime,
        reason: str | None = None
    ) -> None:
        """
        Reschedule the appointment.
        
        Args:
            new_start_time: New start time
            new_end_time: New end time
            reason: Reason for rescheduling
            
        Raises:
            InvalidAppointmentStateError: If the appointment cannot be rescheduled
            InvalidAppointmentTimeError: If the new times are invalid
        """
        if self.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.NO_SHOW
        ]:
            raise InvalidAppointmentStateError(
                f"Cannot reschedule appointment with status {self.status.value}"
            )
        
        # Validate new times
        if new_start_time >= new_end_time:
            raise InvalidAppointmentTimeError("Start time must be before end time")
        
        if new_start_time < datetime.now():
            raise InvalidAppointmentTimeError("Cannot reschedule to a time in the past")
        
        # Update appointment
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.status = AppointmentStatus.RESCHEDULED
        self.notes = f"{self.notes or ''}\nRescheduled: {reason}" if reason else self.notes
        self.updated_at = datetime.now()
    
    def schedule_follow_up(
        self,
        follow_up_appointment_id: UUID | str
    ) -> None:
        """
        Schedule a follow-up appointment.
        
        Args:
            follow_up_appointment_id: ID of the follow-up appointment
            
        Raises:
            InvalidAppointmentStateError: If a follow-up cannot be scheduled
        """
        if self.status != AppointmentStatus.COMPLETED:
            raise InvalidAppointmentStateError(
                f"Cannot schedule follow-up for appointment with status {self.status.value}"
            )
        
        self.follow_up_scheduled = True
        self.follow_up_appointment_id = follow_up_appointment_id
        self.updated_at = datetime.now()
    
    def send_reminder(self) -> None:
        """
        Mark that a reminder has been sent for this appointment.
        """
        self.reminder_sent = True
        self.reminder_sent_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_notes(self, notes: str) -> None:
        """
        Update the appointment notes.
        
        Args:
            notes: New notes
        """
        self.notes = notes
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the appointment to a dictionary.
        
        Returns:
            Dictionary representation of the appointment
        """
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "provider_id": str(self.provider_id),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "appointment_type": self.appointment_type.value if self.appointment_type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "location": self.location,
            "notes": self.notes,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancelled_by": str(self.cancelled_by) if self.cancelled_by else None,
            "cancellation_reason": self.cancellation_reason,
            "reminder_sent": self.reminder_sent,
            "reminder_sent_at": self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
            "follow_up_scheduled": self.follow_up_scheduled,
            "follow_up_appointment_id": str(self.follow_up_appointment_id) if self.follow_up_appointment_id else None,
            "previous_appointment_id": str(self.previous_appointment_id) if self.previous_appointment_id else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Appointment':
        """
        Create an appointment from a dictionary.
        
        Args:
            data: Dictionary representation of an appointment
            
        Returns:
            Appointment instance
        """
        # Convert ISO format strings to datetime objects
        for field in [
            "start_time", "end_time", "created_at", "updated_at",
            "cancelled_at", "reminder_sent_at"
        ]:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def __eq__(self, other: object) -> bool:
        """
        Check if two appointments are equal.
        
        Args:
            other: Other object to compare with
            
        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, Appointment):
            return False
        
        return str(self.id) == str(other.id)
    
    def __hash__(self) -> int:
        """
        Get the hash of the appointment.
        
        Returns:
            Hash value
        """
        return hash(str(self.id))
    
    def __str__(self) -> str:
        """
        Get a string representation of the appointment.
        
        Returns:
            String representation
        """
        return (
            f"Appointment(id={self.id}, "
            f"patient_id={self.patient_id}, "
            f"provider_id={self.provider_id}, "
            f"start_time={self.start_time}, "
            f"end_time={self.end_time}, "
            f"status={self.status.value if self.status else None})"
        )
