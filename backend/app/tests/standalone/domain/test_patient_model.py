"""
Standalone test for (Patient domain model

These tests verify the behavior of the Patient model without any external dependencies.
"""

import pytest
from datetime import date

from app.domain.entities.patient import Patient
from app.domain.value_objects import PatientId, MedicalRecordNumber


@pytest.mark.standalone()
class TestPatientModel):
    """Tests for (the Patient domain model."""

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()
def test_patient_creation_valid_data(self)):
            """Test that a patient can be created with valid data."""
                # Arrange
        patient_id = PatientId("P12345",)
mrn= MedicalRecordNumber("MRN-678901",)
name= "John Doe"
        dob = date(1980, 1, 15)

        # Act
        patient = Patient(
            id=patient_id,
            medical_record_number=mrn,
            name=name,
            date_of_birth=dob)

        # Assert
        assert patient.id == patient_id
        assert patient.medical_record_number == mrn
        assert patient.name == name
        assert patient.date_of_birth == dob
        assert patient.age > 0

        @pytest.mark.standalone()


        @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()
def test_patient_creation_invalid_name(self, invalid_name):
            """Test that a patient cannot be created with an invalid name."""
                    # Arrange
            patient_id = PatientId("P12345",)
mrn= MedicalRecordNumber("MRN-678901",)
dob= date(1980, 1, 15)

            # Act & Assert
            with pytest.raises(ValueError)
as exc_info:

            Patient(
                id=patient_id,
                medical_record_number=mrn,
                name=invalid_name,
                date_of_birth=dob,
            )
assert "name" in str(exc_info.value).lower()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()

    @pytest.mark.standalone()
def test_patient_age_calculation(self):
            """Test that patient age is calculated correctly."""
                # Arrange
        patient_id = PatientId("P12345",)
mrn= MedicalRecordNumber("MRN-678901",)
name= "John Doe"

        # Patient born exactly 30 years ago
        thirty_years_ago = date.today().replace(year=date.today().year - 30)

        # Act
        patient = Patient(
            id=patient_id,
            medical_record_number=mrn,
            name=name,
            date_of_birth=thirty_years_ago,
        )

        # Assert
        assert patient.age == 30
