# -*- coding: utf-8 -*-
"""
Tests for the Appointment entity.
"""

from datetime import datetime, timedelta
import uuid
import pytest

from app.domain.entities.appointment import (
    Appointment,  
    AppointmentStatus,  
    AppointmentType,  
    AppointmentPriority
)
from app.domain.exceptions import (
    InvalidAppointmentStateError,  
    InvalidAppointmentTimeError
)


@pytest.fixture
def future_datetime():
    """Fixture for a future datetime."""
    
    return datetime.now() + timedelta(days=1)


@pytest.fixture
def valid_appointment_data(future_datetime):
    """Fixture for valid appointment data."""
    
    return {
        "id": str(uuid.uuid4()),
        "patient_id": str(uuid.uuid4()),
        "provider_id": str(uuid.uuid4()),
        "start_time": future_datetime,
        "end_time": future_datetime + timedelta(hours=1),
        "appointment_type": AppointmentType.INITIAL_CONSULTATION,
        "status": AppointmentStatus.SCHEDULED,
        "priority": AppointmentPriority.NORMAL,
        "location": "Office 101",
        "notes": "Initial consultation for anxiety",
        "reason": "Anxiety and depression",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def valid_appointment(valid_appointment_data):
    """Fixture for a valid appointment."""
    
    return Appointment(**valid_appointment_data)


@pytest.mark.venv_only()
class TestAppointment:
    """Tests for the Appointment class."""
    
    def test_create_appointment(self, valid_appointment_data):
        """Test creating an appointment."""
        appointment = Appointment(**valid_appointment_data)
        
    assert appointment.id  ==  valid_appointment_data["id"]
    assert appointment.patient_id  ==  valid_appointment_data["patient_id"]
    assert appointment.provider_id  ==  valid_appointment_data["provider_id"]
    assert appointment.start_time  ==  valid_appointment_data["start_time"]
    assert appointment.end_time  ==  valid_appointment_data["end_time"]
    assert appointment.appointment_type  ==  valid_appointment_data["appointment_type"]
    assert appointment.status  ==  valid_appointment_data["status"]
    assert appointment.priority  ==  valid_appointment_data["priority"]
    assert appointment.location  ==  valid_appointment_data["location"]
    assert appointment.notes  ==  valid_appointment_data["notes"]
    assert appointment.reason  ==  valid_appointment_data["reason"]
    
    def test_create_appointment_with_string_enums(self, valid_appointment_data):
        """Test creating an appointment with string enums."""
        # Convert enums to strings
        data = valid_appointment_data.copy()
        data["appointment_type"] = AppointmentType.INITIAL_CONSULTATION.value
        data["status"] = AppointmentStatus.SCHEDULED.value
        data["priority"] = AppointmentPriority.NORMAL.value
        
    appointment = Appointment(**data)
        
    assert appointment.appointment_type  ==  AppointmentType.INITIAL_CONSULTATION
    assert appointment.status  ==  AppointmentStatus.SCHEDULED
    assert appointment.priority  ==  AppointmentPriority.NORMAL
    
    def test_create_appointment_with_auto_id(self, valid_appointment_data):
        """Test creating an appointment with auto-generated ID."""
        data = valid_appointment_data.copy()
        data.pop("id")
        
    appointment = Appointment(**data)
        
    assert appointment.id is not None
    assert isinstance(appointment.id, uuid.UUID)
    
    def test_validate_required_fields(self):
        """Test validation of required fields."""
        # Missing patient_id
        with pytest.raises(InvalidAppointmentStateError):
        Appointment(
                provider_id=str(uuid.uuid4()),
                start_time=datetime.now() + timedelta(days=1),
                end_time=datetime.now() + timedelta(days=1, hours=1),
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )
        
        # Missing provider_id
    with pytest.raises(InvalidAppointmentStateError):
    Appointment(
    patient_id=str(uuid.uuid4()),
    start_time=datetime.now() + timedelta(days=1),
    end_time=datetime.now() + timedelta(days=1, hours=1),
    appointment_type=AppointmentType.INITIAL_CONSULTATION
    )
        
        # Missing start_time
    with pytest.raises(InvalidAppointmentStateError):
    Appointment(
    patient_id=str(uuid.uuid4()),
    provider_id=str(uuid.uuid4()),
    end_time=datetime.now() + timedelta(days=1, hours=1),
    appointment_type=AppointmentType.INITIAL_CONSULTATION
    )
        
        # Missing end_time
    with pytest.raises(InvalidAppointmentStateError):
    Appointment(
    patient_id=str(uuid.uuid4()),
    provider_id=str(uuid.uuid4()),
    start_time=datetime.now() + timedelta(days=1),
    appointment_type=AppointmentType.INITIAL_CONSULTATION
    )
        
        # Missing appointment_type
    with pytest.raises(InvalidAppointmentStateError):
    Appointment(
    patient_id=str(uuid.uuid4()),
    provider_id=str(uuid.uuid4()),
    start_time=datetime.now() + timedelta(days=1),
    end_time=datetime.now() + timedelta(days=1, hours=1)
    )
    
    def test_validate_appointment_times(self, future_datetime):
        """Test validation of appointment times."""
        # End time before start time
        with pytest.raises(InvalidAppointmentTimeError):
        Appointment(
                patient_id=str(uuid.uuid4()),
                provider_id=str(uuid.uuid4()),
                start_time=future_datetime + timedelta(hours=1),
                end_time=future_datetime,
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )
        
        # Start time in the past
    with pytest.raises(InvalidAppointmentTimeError):
    Appointment(
    patient_id=str(uuid.uuid4()),
    provider_id=str(uuid.uuid4()),
    start_time=datetime.now() - timedelta(days=1),
    end_time=datetime.now() + timedelta(hours=1),
    appointment_type=AppointmentType.INITIAL_CONSULTATION
    )
    
    def test_confirm_appointment(self, valid_appointment):
        """Test confirming an appointment."""
        valid_appointment.confirm()
        
    assert valid_appointment.status  ==  AppointmentStatus.CONFIRMED
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_confirm_non_scheduled_appointment(self, valid_appointment):
        """Test confirming a non-scheduled appointment."""
        valid_appointment.status = AppointmentStatus.CANCELLED
        
    with pytest.raises(InvalidAppointmentStateError):
    valid_appointment.confirm()
    
    def test_check_in_appointment(self, valid_appointment):
        """Test checking in an appointment."""
        valid_appointment.check_in()
        
    assert valid_appointment.status  ==  AppointmentStatus.CHECKED_IN
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_check_in_confirmed_appointment(self, valid_appointment):
        """Test checking in a confirmed appointment."""
        valid_appointment.status = AppointmentStatus.CONFIRMED
        valid_appointment.check_in()
        
    assert valid_appointment.status  ==  AppointmentStatus.CHECKED_IN
    
    def test_check_in_invalid_appointment(self, valid_appointment):
        """Test checking in an invalid appointment."""
        valid_appointment.status = AppointmentStatus.CANCELLED
        
    with pytest.raises(InvalidAppointmentStateError):
    valid_appointment.check_in()
    
    def test_start_appointment(self, valid_appointment):
        """Test starting an appointment."""
        valid_appointment.status = AppointmentStatus.CHECKED_IN
        valid_appointment.start()
        
    assert valid_appointment.status  ==  AppointmentStatus.IN_PROGRESS
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_start_invalid_appointment(self, valid_appointment):
        """Test starting an invalid appointment."""
        with pytest.raises(InvalidAppointmentStateError):
        valid_appointment.start()
    
    def test_complete_appointment(self, valid_appointment):
        """Test completing an appointment."""
        valid_appointment.status = AppointmentStatus.IN_PROGRESS
        valid_appointment.complete()
        
    assert valid_appointment.status  ==  AppointmentStatus.COMPLETED
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_complete_invalid_appointment(self, valid_appointment):
        """Test completing an invalid appointment."""
        with pytest.raises(InvalidAppointmentStateError):
        valid_appointment.complete()
    
    def test_cancel_appointment(self, valid_appointment):
        """Test cancelling an appointment."""
        cancelled_by = str(uuid.uuid4())
        reason = "Patient requested cancellation"
        
    valid_appointment.cancel(cancelled_by, reason)
        
    assert valid_appointment.status  ==  AppointmentStatus.CANCELLED
    assert valid_appointment.cancelled_at is not None
    assert valid_appointment.cancelled_by  ==  cancelled_by
    assert valid_appointment.cancellation_reason  ==  reason
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_cancel_invalid_appointment(self, valid_appointment):
        """Test cancelling an invalid appointment."""
        valid_appointment.status = AppointmentStatus.COMPLETED
        
    with pytest.raises(InvalidAppointmentStateError):
    valid_appointment.cancel(str(uuid.uuid4()))
    
    def test_mark_no_show(self, valid_appointment):
        """Test marking an appointment as no-show."""
        valid_appointment.mark_no_show()
        
    assert valid_appointment.status  ==  AppointmentStatus.NO_SHOW
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_mark_no_show_confirmed_appointment(self, valid_appointment):
        """Test marking a confirmed appointment as no-show."""
        valid_appointment.status = AppointmentStatus.CONFIRMED
        valid_appointment.mark_no_show()
        
    assert valid_appointment.status  ==  AppointmentStatus.NO_SHOW
    
    def test_mark_no_show_invalid_appointment(self, valid_appointment):
        """Test marking an invalid appointment as no-show."""
        valid_appointment.status = AppointmentStatus.COMPLETED
        
    with pytest.raises(InvalidAppointmentStateError):
    valid_appointment.mark_no_show()
    
    def test_reschedule_appointment(self, valid_appointment, future_datetime):
        """Test rescheduling an appointment."""
        new_start_time = future_datetime + timedelta(days=1)
        new_end_time = new_start_time + timedelta(hours=1)
        reason = "Provider unavailable"
        
    valid_appointment.reschedule(new_start_time, new_end_time, reason)
        
    assert valid_appointment.status  ==  AppointmentStatus.RESCHEDULED
    assert valid_appointment.start_time  ==  new_start_time
    assert valid_appointment.end_time  ==  new_end_time
    assert reason in valid_appointment.notes
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_reschedule_invalid_appointment(self, valid_appointment, future_datetime):
        """Test rescheduling an invalid appointment."""
        valid_appointment.status = AppointmentStatus.COMPLETED
        
    with pytest.raises(InvalidAppointmentStateError):
    valid_appointment.reschedule(
    future_datetime + timedelta(days=1),
    future_datetime + timedelta(days=1, hours=1)
    )
    
    def test_reschedule_invalid_times(self, valid_appointment, future_datetime):
        """Test rescheduling with invalid times."""
        # End time before start time
        with pytest.raises(InvalidAppointmentTimeError):
        valid_appointment.reschedule(
                future_datetime + timedelta(hours=2),
                future_datetime + timedelta(hours=1)
            )
        
        # Start time in the past
    with pytest.raises(InvalidAppointmentTimeError):
    valid_appointment.reschedule(
    datetime.now() - timedelta(hours=1),
    datetime.now() + timedelta(hours=1)
    )
    
    def test_schedule_follow_up(self, valid_appointment):
        """Test scheduling a follow-up appointment."""
        valid_appointment.status = AppointmentStatus.COMPLETED
        follow_up_id = str(uuid.uuid4())
        
    valid_appointment.schedule_follow_up(follow_up_id)
        
    assert valid_appointment.follow_up_scheduled is True
    assert valid_appointment.follow_up_appointment_id  ==  follow_up_id
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_schedule_follow_up_invalid_appointment(self, valid_appointment):
        """Test scheduling a follow-up for an invalid appointment."""
        follow_up_id = str(uuid.uuid4())
        
    with pytest.raises(InvalidAppointmentStateError):
    valid_appointment.schedule_follow_up(follow_up_id)
    
    def test_send_reminder(self, valid_appointment):
        """Test sending a reminder for an appointment."""
        valid_appointment.send_reminder()
        
    assert valid_appointment.reminder_sent is True
    assert valid_appointment.reminder_sent_at is not None
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_update_notes(self, valid_appointment):
        """Test updating appointment notes."""
        new_notes = "Patient reported improvement in symptoms"
        
    valid_appointment.update_notes(new_notes)
        
    assert valid_appointment.notes  ==  new_notes
    assert valid_appointment.updated_at > valid_appointment.created_at
    
    def test_to_dict(self, valid_appointment):
        """Test converting an appointment to a dictionary."""
        appointment_dict = valid_appointment.to_dict()
        
    assert appointment_dict["id"] == str(valid_appointment.id)
    assert appointment_dict["patient_id"] == str(valid_appointment.patient_id)
    assert appointment_dict["provider_id"] == str(valid_appointment.provider_id)
    assert appointment_dict["start_time"] == valid_appointment.start_time.isoformat()
    assert appointment_dict["end_time"] == valid_appointment.end_time.isoformat()
    assert appointment_dict["appointment_type"] == valid_appointment.appointment_type.value
    assert appointment_dict["status"] == valid_appointment.status.value
    assert appointment_dict["priority"] == valid_appointment.priority.value
    
    def test_from_dict(self, valid_appointment):
        """Test creating an appointment from a dictionary."""
        appointment_dict = valid_appointment.to_dict()
        new_appointment = Appointment.from_dict(appointment_dict)
        
    assert new_appointment.id  ==  valid_appointment.id
    assert new_appointment.patient_id  ==  valid_appointment.patient_id
    assert new_appointment.provider_id  ==  valid_appointment.provider_id
    assert new_appointment.start_time  ==  valid_appointment.start_time
    assert new_appointment.end_time  ==  valid_appointment.end_time
    assert new_appointment.appointment_type  ==  valid_appointment.appointment_type
    assert new_appointment.status  ==  valid_appointment.status
    assert new_appointment.priority  ==  valid_appointment.priority
    
    def test_equality(self, valid_appointment_data):
        """Test appointment equality."""
        appointment1 = Appointment(**valid_appointment_data)
        appointment2 = Appointment(**valid_appointment_data)
        
    assert appointment1  ==  appointment2
    assert hash(appointment1) == hash(appointment2)
    
    def test_inequality(self, valid_appointment_data):
        """Test appointment inequality."""
        appointment1 = Appointment(**valid_appointment_data)
        
    data2 = valid_appointment_data.copy()
    data2["id"] = str(uuid.uuid4())
    appointment2 = Appointment(**data2)
        
    assert appointment1  !=  appointment2
    assert hash(appointment1) != hash(appointment2)
    assert appointment1  !=  "not an appointment"
    
    def test_string_representation(self, valid_appointment):
        """Test string representation of an appointment."""
        string_repr = str(valid_appointment)
        
    assert str(valid_appointment.id) in string_repr
    assert str(valid_appointment.patient_id) in string_repr
    assert str(valid_appointment.provider_id) in string_repr
    assert valid_appointment.status.value in string_repr