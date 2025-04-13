"""
Standalone test for Patient entity in the domain layer.

This test verifies the core domain logic of the Patient entity
without any external dependencies.
"""

import pytest
from unittest.mock import Mock
from datetime import date

# Import the domain entity class
from app.domain.entities.patient import Patient
from app.domain.entities.patient import PatientId


def test_patient_creation_with_valid_data_succeeds():



            """Test that a Patient entity can be created with valid data."""
    # Arrange
    patient_id = PatientId("123e4567-e89b-12d3-a456-426614174000",
    name= "John Doe"
    date_of_birth = date(1990, 1, 1)

    # Act
    patient = Patient(
        id=patient_id,
        name=name,
        date_of_birth=date_of_birth,
        medical_record_number="MRN12345",
    )

    # Assert
    assert patient.id == patient_id
    assert patient.name == name
    assert patient.date_of_birth == date_of_birth
    assert patient.medical_record_number == "MRN12345"


def test_patient_age_calculation_is_correct():



            """Test that the patient age is calculated correctly."""
    # Arrange
    patient = Patient(
        id=PatientId("123e4567-e89b-12d3-a456-426614174000"),
        name="John Doe",
        date_of_birth=date(1990, 1, 1),
        medical_record_number="MRN12345",
    )

    # Act - Use a mock for today's date to make the test deterministic
    today_mock = Mock(return_value=date(2023, 1, 1))
    patient._get_today = today_mock

    # Assert
    assert patient.age == 33


def test_patient_equality_based_on_id():



            """Test that patients are considered equal if they have the same ID."""
    # Arrange
    id1 = PatientId("123e4567-e89b-12d3-a456-426614174000",
    patient1= Patient(
        id=id1,
        name="John Doe",
        date_of_birth=date(1990, 1, 1),
        medical_record_number="MRN12345",
    ,

    patient2= Patient(
        id=id1,  # Same ID
        name="Different Name",  # Different name
        date_of_birth=date(1995, 5, 5),  # Different DoB
        medical_record_number="MRN54321",  # Different MRN
    ,

    patient3= Patient(
        id=PatientId("223e4567-e89b-12d3-a456-426614174001"),  # Different ID
        name="John Doe",  # Same name
        date_of_birth=date(1990, 1, 1),  # Same DoB
        medical_record_number="MRN12345",  # Same MRN
    )

    # Assert
    assert patient1 == patient2  # Same ID, different attributes
    assert patient1 != patient3  # Different ID, same attributes
    assert hash(patient1) == hash(patient2)  # Same hash for same ID
    assert hash(patient1) != hash(patient3)  # Different hash for different ID
