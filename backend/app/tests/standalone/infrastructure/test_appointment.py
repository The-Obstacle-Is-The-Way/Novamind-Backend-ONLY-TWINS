"""
Tests for the Appointment entity.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from app.domain.entities.appointment import (
    Appointment,
    AppointmentPriority,
    AppointmentStatus,
    AppointmentType
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


class TestAppointment:
    """Tests for the Appointment class."""

    @pytest.mark.standalone()
    def test_create_appointment(self, valid_appointment_data):
        """Test creating an appointment."""
        appointment = Appointment(**valid_appointment_data)
        assert appointment.id == valid_appointment_data["id"]
        assert appointment.patient_id == valid_appointment_data["patient_id"]
        assert appointment.provider_id == valid_appointment_data["provider_id"]
        assert appointment.start_time == valid_appointment_data["start_time"]
        assert appointment.end_time == valid_appointment_data["end_time"]
        assert appointment.appointment_type == valid_appointment_data["appointment_type"]
        assert appointment.status == valid_appointment_data["status"]
        assert appointment.priority == valid_appointment_data["priority"]
        assert appointment.location == valid_appointment_data["location"]
        assert appointment.notes == valid_appointment_data["notes"]
        assert appointment.reason == valid_appointment_data["reason"]

    @pytest.mark.standalone()
    def test_create_appointment_with_string_enums(self, valid_appointment_data):
        """Test creating an appointment with string enums."""
        # Convert enums to strings
        data = valid_appointment_data.copy()
        data["appointment_type"] = AppointmentType.INITIAL_CONSULTATION.value
        data["status"] = AppointmentStatus.SCHEDULED.value
        data["priority"] = AppointmentPriority.NORMAL.value

        appointment = Appointment(**data)
        assert appointment.appointment_type == AppointmentType.INITIAL_CONSULTATION
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.priority == AppointmentPriority.NORMAL

    @pytest.mark.standalone()
    def test_create_appointment_with_auto_id(self, valid_appointment_data):
        """Test creating an appointment with auto-generated ID."""
        data = valid_appointment_data.copy()
        data.pop("id")
        appointment = Appointment(**data)
        assert appointment.id is not None
        assert isinstance(appointment.id, uuid.UUID)

    @pytest.mark.standalone()
    def test_validate_times(self, future_datetime):
        """Test validation of appointment times."""
        # Start time in the past
        past_datetime = datetime.now() - timedelta(days=1)
        with pytest.raises(InvalidAppointmentTimeError):
            Appointment(
                patient_id=str(uuid.uuid4()),
                provider_id=str(uuid.uuid4()),
                start_time=past_datetime,
                end_time=future_datetime,
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )

        # End time before start time
        early_datetime = future_datetime - timedelta(hours=1)
        with pytest.raises(InvalidAppointmentTimeError):
            Appointment(
                patient_id=str(uuid.uuid4()),
                provider_id=str(uuid.uuid4()),
                start_time=future_datetime,
                end_time=early_datetime,
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )

    @pytest.mark.standalone()
    def test_validate_required_fields(self, future_datetime):
        """Test validation of required fields."""
        # Missing patient_id
        with pytest.raises(ValueError):
            Appointment(
                provider_id=str(uuid.uuid4()),
                start_time=future_datetime,
                end_time=future_datetime + timedelta(hours=1),
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )

        # Missing provider_id
        with pytest.raises(ValueError):
            Appointment(
                patient_id=str(uuid.uuid4()),
                start_time=future_datetime,
                end_time=future_datetime + timedelta(hours=1),
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )

        # Missing start_time
        with pytest.raises(ValueError):
            Appointment(
                patient_id=str(uuid.uuid4()),
                provider_id=str(uuid.uuid4()),
                end_time=future_datetime + timedelta(hours=1),
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )

        # Missing end_time
        with pytest.raises(ValueError):
            Appointment(
                patient_id=str(uuid.uuid4()),
                provider_id=str(uuid.uuid4()),
                start_time=future_datetime,
                appointment_type=AppointmentType.INITIAL_CONSULTATION
            )

        # Missing appointment_type
        with pytest.raises(ValueError):
            Appointment(
                patient_id=str(uuid.uuid4()),
                provider_id=str(uuid.uuid4()),
                start_time=future_datetime,
                end_time=future_datetime + timedelta(hours=1)
            )

    @pytest.mark.standalone()
    def test_confirm_appointment(self, valid_appointment):
        """Test confirming an appointment."""
        assert valid_appointment.status == AppointmentStatus.SCHEDULED

        valid_appointment.confirm()
        assert valid_appointment.status == AppointmentStatus.CONFIRMED
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_cannot_confirm_completed_appointment(self, valid_appointment):
        """Test that a completed appointment cannot be confirmed."""
        valid_appointment.complete()
        
        with pytest.raises(InvalidAppointmentStateError):
            valid_appointment.confirm()

    @pytest.mark.standalone()
    def test_cancel_appointment(self, valid_appointment):
        """Test canceling an appointment."""
        assert valid_appointment.status == AppointmentStatus.SCHEDULED

        reason = "Patient request"
        valid_appointment.cancel(reason)
        
        assert valid_appointment.status == AppointmentStatus.CANCELLED
        assert valid_appointment.cancellation_reason == reason
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_cannot_cancel_completed_appointment(self, valid_appointment):
        """Test that a completed appointment cannot be canceled."""
        valid_appointment.complete()
        
        with pytest.raises(InvalidAppointmentStateError):
            valid_appointment.cancel("Too late")

    @pytest.mark.standalone()
    def test_reschedule_appointment(self, valid_appointment, future_datetime):
        """Test rescheduling an appointment."""
        new_start_time = future_datetime + timedelta(days=2)
        new_end_time = new_start_time + timedelta(hours=1)
        
        valid_appointment.reschedule(new_start_time, new_end_time)
        
        assert valid_appointment.start_time == new_start_time
        assert valid_appointment.end_time == new_end_time
        assert valid_appointment.status == AppointmentStatus.RESCHEDULED
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_cannot_reschedule_cancelled_appointment(self, valid_appointment, future_datetime):
        """Test that a cancelled appointment cannot be rescheduled."""
        valid_appointment.cancel("Patient request")
        
        new_start_time = future_datetime + timedelta(days=2)
        new_end_time = new_start_time + timedelta(hours=1)
        
        with pytest.raises(InvalidAppointmentStateError):
            valid_appointment.reschedule(new_start_time, new_end_time)

    @pytest.mark.standalone()
    def test_complete_appointment(self, valid_appointment):
        """Test completing an appointment."""
        notes = "Patient reported improvement"
        valid_appointment.complete(notes)
        
        assert valid_appointment.status == AppointmentStatus.COMPLETED
        assert valid_appointment.notes == notes
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_cannot_complete_cancelled_appointment(self, valid_appointment):
        """Test that a cancelled appointment cannot be completed."""
        valid_appointment.cancel("Patient request")
        
        with pytest.raises(InvalidAppointmentStateError):
            valid_appointment.complete("This should fail")

    @pytest.mark.standalone()
    def test_no_show_appointment(self, valid_appointment):
        """Test marking an appointment as no-show."""
        valid_appointment.no_show()
        
        assert valid_appointment.status == AppointmentStatus.NO_SHOW
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_cannot_no_show_cancelled_appointment(self, valid_appointment):
        """Test that a cancelled appointment cannot be marked as no-show."""
        valid_appointment.cancel("Patient request")
        
        with pytest.raises(InvalidAppointmentStateError):
            valid_appointment.no_show()

    @pytest.mark.standalone()
    def test_update_priority(self, valid_appointment):
        """Test updating appointment priority."""
        assert valid_appointment.priority == AppointmentPriority.NORMAL
        
        valid_appointment.update_priority(AppointmentPriority.HIGH)
        assert valid_appointment.priority == AppointmentPriority.HIGH
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_update_priority_with_string(self, valid_appointment):
        """Test updating appointment priority with a string."""
        valid_appointment.update_priority("urgent")
        assert valid_appointment.priority == AppointmentPriority.URGENT

    @pytest.mark.standalone()
    def test_update_notes(self, valid_appointment):
        """Test updating appointment notes."""
        original_notes = valid_appointment.notes
        new_notes = "Updated patient notes"
        
        valid_appointment.update_notes(new_notes)
        assert valid_appointment.notes == new_notes
        assert valid_appointment.notes != original_notes
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_update_location(self, valid_appointment):
        """Test updating appointment location."""
        original_location = valid_appointment.location
        new_location = "Office 202"
        
        valid_appointment.update_location(new_location)
        assert valid_appointment.location == new_location
        assert valid_appointment.location != original_location
        assert valid_appointment.updated_at > valid_appointment.created_at

    @pytest.mark.standalone()
    def test_to_dict(self, valid_appointment):
        """Test converting an appointment to a dictionary."""
        appointment_dict = valid_appointment.to_dict()
        
        assert appointment_dict["id"] == str(valid_appointment.id)
        assert appointment_dict["patient_id"] == str(valid_appointment.patient_id)
        assert appointment_dict["provider_id"] == str(valid_appointment.provider_id)
        assert appointment_dict["appointment_type"] == valid_appointment.appointment_type.value
        assert appointment_dict["status"] == valid_appointment.status.value
        assert appointment_dict["priority"] == valid_appointment.priority.value
        assert appointment_dict["location"] == valid_appointment.location
        assert appointment_dict["notes"] == valid_appointment.notes
        assert appointment_dict["reason"] == valid_appointment.reason
        
        # Check datetime formatting
        assert isinstance(appointment_dict["start_time"], str)
        assert isinstance(appointment_dict["end_time"], str)
        assert isinstance(appointment_dict["created_at"], str)
        assert isinstance(appointment_dict["updated_at"], str)

    @pytest.mark.standalone()
    def test_from_dict(self, valid_appointment):
        """Test creating an appointment from a dictionary."""
        # Convert the appointment to a dictionary
        appointment_dict = valid_appointment.to_dict()
        
        # Create a new appointment from the dictionary
        new_appointment = Appointment.from_dict(appointment_dict)
        
        # Verify the fields match
        assert new_appointment.id == valid_appointment.id
        assert new_appointment.patient_id == valid_appointment.patient_id
        assert new_appointment.provider_id == valid_appointment.provider_id
        assert new_appointment.start_time == valid_appointment.start_time
        assert new_appointment.end_time == valid_appointment.end_time
        assert new_appointment.appointment_type == valid_appointment.appointment_type
        assert new_appointment.status == valid_appointment.status
        assert new_appointment.priority == valid_appointment.priority

    @pytest.mark.standalone()
    def test_equality(self, valid_appointment_data):
        """Test appointment equality."""
        appointment1 = Appointment(**valid_appointment_data)
        appointment2 = Appointment(**valid_appointment_data)
        assert appointment1 == appointment2
        assert hash(appointment1) == hash(appointment2)

    @pytest.mark.standalone()
    def test_inequality(self, valid_appointment_data):
        """Test appointment inequality."""
        appointment1 = Appointment(**valid_appointment_data)
        data2 = valid_appointment_data.copy()
        data2["id"] = str(uuid.uuid4())
        appointment2 = Appointment(**data2)
        assert appointment1 != appointment2
        assert hash(appointment1) != hash(appointment2)
        assert appointment1 != "not an appointment"

    @pytest.mark.standalone()
    def test_string_representation(self, valid_appointment):
        """Test string representation of an appointment."""
        string_repr = str(valid_appointment)
        assert str(valid_appointment.id) in string_repr
        assert str(valid_appointment.patient_id) in string_repr
        assert str(valid_appointment.provider_id) in string_repr
        assert valid_appointment.status.value in string_repr