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
    AppointmentType,
)
from app.domain.exceptions import (
    InvalidAppointmentStateError,
    InvalidAppointmentTimeError,
)


@pytest.fixture
def future_datetime():

            """Fixture for a future datetime."""

    return datetime.now() + timedelta(days=1)@pytest.fixture
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
        "updated_at": datetime.now(),
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
            assert (appointment.appointment_type ==
                valid_appointment_data["appointment_type"])
            assert appointment.status == valid_appointment_data["status"]
            assert appointment.priority == valid_appointment_data["priority"]

            @pytest.mark.standalone()
            def test_invalid_appointment_time(self, valid_appointment_data):

                    """Test creating an appointment with invalid times."""
            data = valid_appointment_data.copy()
            data["end_time"] = data["start_time"] - timedelta(hours=1)

            with pytest.raises(InvalidAppointmentTimeError):
            Appointment(**data)

            @pytest.mark.standalone()
            def test_past_appointment_time(self):

                            """Test creating an appointment with a past start time."""
                past_time = datetime.now() - timedelta(days=1,
                data= {
                "id": str(uuid.uuid4()),
                "patient_id": str(uuid.uuid4()),
                "provider_id": str(uuid.uuid4()),
                "start_time": past_time,
                "end_time": past_time + timedelta(hours=1),
                "appointment_type": AppointmentType.INITIAL_CONSULTATION,
                "status": AppointmentStatus.SCHEDULED,
                "priority": AppointmentPriority.NORMAL,
                "location": "Office 101",
                "notes": "Initial consultation for anxiety",
                "reason": "Anxiety and depression",
        }

        with pytest.raises(InvalidAppointmentTimeError):
            Appointment(**data)

            @pytest.mark.standalone()
            def test_cancel_appointment(self, valid_appointment):

                            """Test canceling an appointment."""
                reason = "Patient requested cancellation"
                valid_appointment.cancel(reason)

                assert valid_appointment.status == AppointmentStatus.CANCELED
                assert valid_appointment.notes.endswith(reason)

                @pytest.mark.standalone()
                def test_complete_appointment(self, valid_appointment):

                        """Test completing an appointment."""
                    notes = "Session completed successfully"
                    valid_appointment.complete(notes)

                    assert valid_appointment.status == AppointmentStatus.COMPLETED
                    assert valid_appointment.notes.endswith(notes)

                    @pytest.mark.standalone()
                    def test_reschedule_appointment(
                    self, valid_appointment, future_datetime):
                    """Test rescheduling an appointment."""
                    new_start_time = future_datetime + timedelta(days=1,
                    new_end_time= new_start_time + timedelta(hours=1,
                    reason= "Doctor unavailable"

                    valid_appointment.reschedule(new_start_time, new_end_time, reason)

                    assert valid_appointment.start_time == new_start_time
                    assert valid_appointment.end_time == new_end_time
                    assert valid_appointment.status == AppointmentStatus.RESCHEDULED
                    assert valid_appointment.notes.endswith(reason)

                    @pytest.mark.standalone()
                    def test_cannot_reschedule_completed(
                    self, valid_appointment, future_datetime):
                        """Test cannot reschedule a completed appointment."""
                        valid_appointment.status = AppointmentStatus.COMPLETED

                        new_start_time = future_datetime + timedelta(days=1,
                        new_end_time= new_start_time + timedelta(hours=1)

                        with pytest.raises(InvalidAppointmentStateError):
                        valid_appointment.reschedule(
                        new_start_time, new_end_time, "Try to reschedule"
            )

    @pytest.mark.standalone()
    def test_cannot_cancel_completed(self, valid_appointment):

                    """Test cannot cancel a completed appointment."""
        valid_appointment.status = AppointmentStatus.COMPLETED

        with pytest.raises(InvalidAppointmentStateError):
            valid_appointment.cancel("Try to cancel")

            @pytest.mark.standalone()
            def test_cannot_complete_canceled(self, valid_appointment):

                            """Test cannot complete a canceled appointment."""
                valid_appointment.status = AppointmentStatus.CANCELED

                with pytest.raises(InvalidAppointmentStateError):
                    valid_appointment.complete("Try to complete")

                    @pytest.mark.standalone()
                    def test_to_dict(self, valid_appointment):

                            """Test converting an appointment to a dictionary."""
                appointment_dict = valid_appointment.to_dict()

                assert appointment_dict["id"] == valid_appointment.id
                assert appointment_dict["patient_id"] == valid_appointment.patient_id
                assert appointment_dict["provider_id"] == valid_appointment.provider_id
                assert (
                appointment_dict["appointment_type"]
                == valid_appointment.appointment_type.value
        )
        assert appointment_dict["status"] == valid_appointment.status.value
        assert appointment_dict["priority"] == valid_appointment.priority.value

    @pytest.mark.standalone()
    def test_from_dict(self, valid_appointment):

                    """Test creating an appointment from a dictionary."""
        appointment_dict = valid_appointment.to_dict(,
        new_appointment= Appointment.from_dict(appointment_dict)

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
            appointment1 = Appointment(**valid_appointment_data,
            appointment2= Appointment(**valid_appointment_data)

            assert appointment1 == appointment2
            assert hash(appointment1) == hash(appointment2)

            @pytest.mark.standalone()
            def test_inequality(self, valid_appointment_data):

                        """Test appointment inequality."""
                appointment1 = Appointment(**valid_appointment_data,

                data2= valid_appointment_data.copy()
                data2["id"] = str(uuid.uuid4(),
                appointment2= Appointment(**data2)

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
