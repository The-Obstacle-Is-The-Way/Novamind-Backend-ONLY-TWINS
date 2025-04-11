# -*- coding: utf-8 -*-
"""
Tests for the Appointment Service.
"""

from datetime import datetime, timedelta
import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.domain.entities.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    AppointmentPriority
)
from app.domain.exceptions import (
    EntityNotFoundError,
    AppointmentConflictError,
    InvalidAppointmentStateError,
    InvalidAppointmentTimeError,
    # Removed AppointmentNotFoundException, PatientNotFoundException, ProviderNotFoundException
)
from app.domain.services.appointment_service import AppointmentService


@pytest.fixture
def future_datetime():
    """Fixture for a future datetime."""
    return datetime.now() + timedelta(days=1)


@pytest.fixture
def appointment_repository():
    """Fixture for appointment repository."""
    repository = MagicMock()
    repository.get_by_id.return_value = None
    repository.save.side_effect = lambda x: x
    return repository


@pytest.fixture
def patient_repository():
    """Fixture for patient repository."""
    repository = MagicMock()
    repository.get_by_id.return_value = {"id": "patient123", "name": "John Doe"}
    return repository


@pytest.fixture
def provider_repository():
    """Fixture for provider repository."""
    repository = MagicMock()
    repository.get_by_id.return_value = {"id": "provider456", "name": "Dr. Smith"}
    return repository


@pytest.fixture
def appointment_service(appointment_repository, patient_repository, provider_repository):
    """Fixture for appointment service."""
    return AppointmentService(
        appointment_repository=appointment_repository,
        patient_repository=patient_repository,
        provider_repository=provider_repository,
        default_appointment_duration=60,
        min_reschedule_notice=24,
        max_appointments_per_day=8,
        buffer_between_appointments=15
    )


@pytest.fixture
def valid_appointment(future_datetime):
    """Fixture for a valid appointment."""
    return Appointment(
        id=str(uuid.uuid4()),
        patient_id="patient123",
        provider_id="provider456",
        start_time=future_datetime,
        end_time=future_datetime + timedelta(hours=1),
        appointment_type=AppointmentType.INITIAL_CONSULTATION,
        status=AppointmentStatus.SCHEDULED,
        priority=AppointmentPriority.NORMAL,
        location="Office 101",
        notes="Initial consultation for anxiety",
        reason="Anxiety and depression"
    )


@pytest.mark.venv_only
class TestAppointmentService:
    """Tests for the AppointmentService class."""
    
    def test_get_appointment(self, appointment_service, appointment_repository, valid_appointment):
        """Test getting an appointment."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Get the appointment
        appointment = appointment_service.get_appointment(valid_appointment.id)
        
        # Check the appointment
        assert appointment == valid_appointment
        
        # Check that the repository was called
        appointment_repository.get_by_id.assert_called_once_with(valid_appointment.id)
    
    def test_get_appointment_not_found(self, appointment_service):
        """Test getting a non-existent appointment."""
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.get_appointment("nonexistent_id")
    
    def test_get_appointments_for_patient(self, appointment_service, appointment_repository, valid_appointment):
        """Test getting appointments for a patient."""
        # Set up the repository to return a list of appointments
        appointment_repository.get_by_patient_id.return_value = [valid_appointment]
        
        # Get the appointments
        appointments = appointment_service.get_appointments_for_patient("patient123")
        
        # Check the appointments
        assert len(appointments) == 1
        assert appointments[0] == valid_appointment
        
        # Check that the repository was called
        appointment_repository.get_by_patient_id.assert_called_once_with(
            "patient123", None, None, None
        )
    
    def test_get_appointments_for_patient_not_found(self, appointment_service, patient_repository):
        """Test getting appointments for a non-existent patient."""
        # Set up the repository to return None
        patient_repository.get_by_id.return_value = None
        
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.get_appointments_for_patient("nonexistent_id")
    
    def test_get_appointments_for_provider(self, appointment_service, appointment_repository, valid_appointment):
        """Test getting appointments for a provider."""
        # Set up the repository to return a list of appointments
        appointment_repository.get_by_provider_id.return_value = [valid_appointment]
        
        # Get the appointments
        appointments = appointment_service.get_appointments_for_provider("provider456")
        
        # Check the appointments
        assert len(appointments) == 1
        assert appointments[0] == valid_appointment
        
        # Check that the repository was called
        appointment_repository.get_by_provider_id.assert_called_once_with(
            "provider456", None, None, None
        )
    
    def test_get_appointments_for_provider_not_found(self, appointment_service, provider_repository):
        """Test getting appointments for a non-existent provider."""
        # Set up the repository to return None
        provider_repository.get_by_id.return_value = None
        
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.get_appointments_for_provider("nonexistent_id")
    
    def test_create_appointment(self, appointment_service, appointment_repository, future_datetime):
        """Test creating an appointment."""
        # Create the appointment
        appointment = appointment_service.create_appointment(
            patient_id="patient123",
            provider_id="provider456",
            start_time=future_datetime,
            end_time=future_datetime + timedelta(hours=1),
            appointment_type=AppointmentType.INITIAL_CONSULTATION,
            priority=AppointmentPriority.NORMAL,
            location="Office 101",
            notes="Initial consultation for anxiety",
            reason="Anxiety and depression"
        )
        
        # Check the appointment
        assert appointment.patient_id == "patient123"
        assert appointment.provider_id == "provider456"
        assert appointment.start_time == future_datetime
        assert appointment.end_time == future_datetime + timedelta(hours=1)
        assert appointment.appointment_type == AppointmentType.INITIAL_CONSULTATION
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.priority == AppointmentPriority.NORMAL
        assert appointment.location == "Office 101"
        assert appointment.notes == "Initial consultation for anxiety"
        assert appointment.reason == "Anxiety and depression"
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_create_appointment_with_default_end_time(self, appointment_service, future_datetime):
        """Test creating an appointment with default end time."""
        # Create the appointment
        appointment = appointment_service.create_appointment(
            patient_id="patient123",
            provider_id="provider456",
            start_time=future_datetime,
            appointment_type=AppointmentType.INITIAL_CONSULTATION
        )
        
        # Check the appointment
        assert appointment.start_time == future_datetime
        assert appointment.end_time == future_datetime + timedelta(minutes=60)
    
    def test_create_appointment_patient_not_found(self, appointment_service, patient_repository, future_datetime):
        """Test creating an appointment with a non-existent patient."""
        # Set up the repository to return None
        patient_repository.get_by_id.return_value = None
        
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.create_appointment(
                patient_id="nonexistent_id",
                provider_id="provider456",
                start_time=future_datetime
            )
    
    def test_create_appointment_provider_not_found(self, appointment_service, provider_repository, future_datetime):
        """Test creating an appointment with a non-existent provider."""
        # Set up the repository to return None
        provider_repository.get_by_id.return_value = None
        
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.create_appointment(
                patient_id="patient123",
                provider_id="nonexistent_id",
                start_time=future_datetime
            )
    
    def test_create_appointment_conflict(self, appointment_service, appointment_repository, future_datetime):
        """Test creating an appointment with a conflict."""
        # Set up the repository to return a list of appointments
        appointment_repository.get_by_provider_id.return_value = [
            Appointment(
                id=str(uuid.uuid4()),
                patient_id="patient789",
                provider_id="provider456",
                start_time=future_datetime - timedelta(minutes=30),
                end_time=future_datetime + timedelta(minutes=30),
                appointment_type=AppointmentType.FOLLOW_UP,
                status=AppointmentStatus.SCHEDULED
            )
        ]
        
        with pytest.raises(AppointmentConflictError):
            appointment_service.create_appointment(
                patient_id="patient123",
                provider_id="provider456",
                start_time=future_datetime,
                end_time=future_datetime + timedelta(hours=1)
            )
    
    def test_create_appointment_daily_limit(self, appointment_service, appointment_repository, future_datetime):
        """Test creating an appointment when the daily limit is reached."""
        # Set up the repository to return a list of appointments
        appointment_repository.get_by_provider_id.return_value = [
            Appointment(
                id=str(uuid.uuid4()),
                patient_id=f"patient{i}",
                provider_id="provider456",
                start_time=future_datetime + timedelta(hours=i),
                end_time=future_datetime + timedelta(hours=i+1),
                appointment_type=AppointmentType.FOLLOW_UP,
                status=AppointmentStatus.SCHEDULED
            )
            for i in range(8)  # 8 appointments (max per day)
        ]
        
        with pytest.raises(AppointmentConflictError):
            appointment_service.create_appointment(
                patient_id="patient123",
                provider_id="provider456",
                start_time=future_datetime + timedelta(hours=9),
                end_time=future_datetime + timedelta(hours=10)
            )
    
    def test_reschedule_appointment(self, appointment_service, appointment_repository, valid_appointment, future_datetime):
        """Test rescheduling an appointment."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # New times
        new_start_time = future_datetime + timedelta(days=1)
        new_end_time = new_start_time + timedelta(hours=1)
        
        # Reschedule the appointment
        updated_appointment = appointment_service.reschedule_appointment(
            appointment_id=valid_appointment.id,
            new_start_time=new_start_time,
            new_end_time=new_end_time,
            reason="Provider unavailable"
        )
        
        # Check the appointment
        assert updated_appointment.start_time == new_start_time
        assert updated_appointment.end_time == new_end_time
        assert updated_appointment.status == AppointmentStatus.RESCHEDULED
        assert "Provider unavailable" in updated_appointment.notes
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_reschedule_appointment_with_default_end_time(self, appointment_service, appointment_repository, valid_appointment, future_datetime):
        """Test rescheduling an appointment with default end time."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # New start time
        new_start_time = future_datetime + timedelta(days=1)
        
        # Reschedule the appointment
        updated_appointment = appointment_service.reschedule_appointment(
            appointment_id=valid_appointment.id,
            new_start_time=new_start_time
        )
        
        # Check the appointment
        assert updated_appointment.start_time == new_start_time
        assert updated_appointment.end_time == new_start_time + timedelta(hours=1)
    
    def test_reschedule_appointment_not_found(self, appointment_service):
        """Test rescheduling a non-existent appointment."""
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.reschedule_appointment(
                appointment_id="nonexistent_id",
                new_start_time=datetime.now() + timedelta(days=1)
            )
    
    def test_reschedule_appointment_conflict(self, appointment_service, appointment_repository, valid_appointment, future_datetime):
        """Test rescheduling an appointment with a conflict."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Set up the repository to return a list of appointments
        appointment_repository.get_by_provider_id.return_value = [
            Appointment(
                id=str(uuid.uuid4()),
                patient_id="patient789",
                provider_id="provider456",
                start_time=future_datetime + timedelta(days=1, minutes=-30),
                end_time=future_datetime + timedelta(days=1, minutes=30),
                appointment_type=AppointmentType.FOLLOW_UP,
                status=AppointmentStatus.SCHEDULED
            )
        ]
        
        with pytest.raises(AppointmentConflictError):
            appointment_service.reschedule_appointment(
                appointment_id=valid_appointment.id,
                new_start_time=future_datetime + timedelta(days=1),
                new_end_time=future_datetime + timedelta(days=1, hours=1)
            )
    
    def test_cancel_appointment(self, appointment_service, appointment_repository, valid_appointment):
        """Test cancelling an appointment."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Cancel the appointment
        updated_appointment = appointment_service.cancel_appointment(
            appointment_id=valid_appointment.id,
            cancelled_by="user123",
            reason="Patient request"
        )
        
        # Check the appointment
        assert updated_appointment.status == AppointmentStatus.CANCELLED
        assert updated_appointment.cancelled_by == "user123"
        assert updated_appointment.cancellation_reason == "Patient request"
        assert updated_appointment.cancelled_at is not None
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_cancel_appointment_not_found(self, appointment_service):
        """Test cancelling a non-existent appointment."""
        with pytest.raises(EntityNotFoundError): # Changed exception type
            appointment_service.cancel_appointment(
                appointment_id="nonexistent_id",
                cancelled_by="user123"
            )
    
    def test_confirm_appointment(self, appointment_service, appointment_repository, valid_appointment):
        """Test confirming an appointment."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Confirm the appointment
        updated_appointment = appointment_service.confirm_appointment(
            appointment_id=valid_appointment.id
        )
        
        # Check the appointment
        assert updated_appointment.status == AppointmentStatus.CONFIRMED
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_check_in_appointment(self, appointment_service, appointment_repository, valid_appointment):
        """Test checking in an appointment."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Check in the appointment
        updated_appointment = appointment_service.check_in_appointment(
            appointment_id=valid_appointment.id
        )
        
        # Check the appointment
        assert updated_appointment.status == AppointmentStatus.CHECKED_IN
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_start_appointment(self, appointment_service, appointment_repository, valid_appointment):
        """Test starting an appointment."""
        # Set up the repository to return the appointment
        valid_appointment.status = AppointmentStatus.CHECKED_IN
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Start the appointment
        updated_appointment = appointment_service.start_appointment(
            appointment_id=valid_appointment.id
        )
        
        # Check the appointment
        assert updated_appointment.status == AppointmentStatus.IN_PROGRESS
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_complete_appointment(self, appointment_service, appointment_repository, valid_appointment):
        """Test completing an appointment."""
        # Set up the repository to return the appointment
        valid_appointment.status = AppointmentStatus.IN_PROGRESS
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Complete the appointment
        updated_appointment = appointment_service.complete_appointment(
            appointment_id=valid_appointment.id
        )
        
        # Check the appointment
        assert updated_appointment.status == AppointmentStatus.COMPLETED
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_mark_no_show(self, appointment_service, appointment_repository, valid_appointment):
        """Test marking an appointment as no-show."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Mark as no-show
        updated_appointment = appointment_service.mark_no_show(
            appointment_id=valid_appointment.id
        )
        
        # Check the appointment
        assert updated_appointment.status == AppointmentStatus.NO_SHOW
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_schedule_follow_up(self, appointment_service, appointment_repository, valid_appointment, future_datetime):
        """Test scheduling a follow-up appointment."""
        # Set up the repository to return the appointment
        valid_appointment.status = AppointmentStatus.COMPLETED
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Follow-up time
        follow_up_time = future_datetime + timedelta(days=7)
        
        # Schedule the follow-up
        follow_up_appointment = appointment_service.schedule_follow_up(
            appointment_id=valid_appointment.id,
            follow_up_start_time=follow_up_time,
            follow_up_end_time=follow_up_time + timedelta(hours=1),
            appointment_type=AppointmentType.FOLLOW_UP,
            reason="Follow-up on treatment progress"
        )
        
        # Check the follow-up appointment
        assert follow_up_appointment.patient_id == valid_appointment.patient_id
        assert follow_up_appointment.provider_id == valid_appointment.provider_id
        assert follow_up_appointment.start_time == follow_up_time
        assert follow_up_appointment.end_time == follow_up_time + timedelta(hours=1)
        assert follow_up_appointment.appointment_type == AppointmentType.FOLLOW_UP
        assert follow_up_appointment.status == AppointmentStatus.SCHEDULED
        assert follow_up_appointment.reason == "Follow-up on treatment progress"
        assert follow_up_appointment.previous_appointment_id == valid_appointment.id
        
        # Check that the repository was called twice (once for the follow-up, once for the original)
        assert appointment_repository.save.call_count == 2
    
    def test_send_reminder(self, appointment_service, appointment_repository, valid_appointment):
        """Test sending a reminder for an appointment."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # Send the reminder
        updated_appointment = appointment_service.send_reminder(
            appointment_id=valid_appointment.id
        )
        
        # Check the appointment
        assert updated_appointment.reminder_sent is True
        assert updated_appointment.reminder_sent_at is not None
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()
    
    def test_update_notes(self, appointment_service, appointment_repository, valid_appointment):
        """Test updating appointment notes."""
        # Set up the repository to return the appointment
        appointment_repository.get_by_id.return_value = valid_appointment
        
        # New notes
        new_notes = "Patient reported improvement in symptoms"
        
        # Update the notes
        updated_appointment = appointment_service.update_notes(
            appointment_id=valid_appointment.id,
            notes=new_notes
        )
        
        # Check the appointment
        assert updated_appointment.notes == new_notes
        
        # Check that the repository was called
        appointment_repository.save.assert_called_once()