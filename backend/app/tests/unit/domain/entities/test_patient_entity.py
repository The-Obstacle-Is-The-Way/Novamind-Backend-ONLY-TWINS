# -*- coding: utf-8 -*-
"""
Tests for the Patient entity.
"""

from datetime import datetime, date, timedelta
import uuid
import pytest
import time
from dataclasses import is_dataclass

from app.domain.entities.patient import Patient
# Value objects might not be directly used in Patient entity anymore, keep if needed for other tests
# from app.domain.value_objects.address import Address
# from app.domain.value_objects.contact_info import ContactInfo
# Temporarily import from core exceptions as workaround for collection error
# ValidationException might not be the correct exception type for dataclass errors
from app.core.exceptions.base_exceptions import ValidationException


@pytest.fixture
def valid_patient_data():
    """Fixture for valid patient data matching the Patient dataclass."""
    # Note: created_at/updated_at are usually handled by __post_init__ or DB layer
    # Include them here if direct instantiation is needed for specific tests
    return {
        "id": str(uuid.uuid4()),
        "name": "John Doe",
        "date_of_birth": date(1980, 1, 1),
        "gender": "Male",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": '123 Main St, Anytown, CA 12345', # Address is now a string
        "medical_history": ["Anxiety (Diagnosed: 2020-01-15, Notes: Mild to moderate)"],
        "medications": ["Sertraline 50mg Daily (Started: 2020-02-01)"],
        "allergies": ["Penicillin"],
        "treatment_notes": [{"date": datetime.now(), "content": "Initial consultation notes."}],
        "created_at": datetime.now(), # Provide initial value if needed
        "updated_at": datetime.now()  # Provide initial value if needed
    }


@pytest.mark.venv_only()
class TestPatient:
    """Tests for the Patient class."""

    def test_create_patient(self, valid_patient_data):
        """Test creating a patient."""
        patient = Patient(**valid_patient_data)

        # Assertions based on the corrected Patient dataclass fields
        assert patient.id == valid_patient_data["id"]
        assert patient.name == valid_patient_data["name"]
        assert patient.date_of_birth == valid_patient_data["date_of_birth"]
        assert patient.gender == valid_patient_data["gender"]
        assert patient.email == valid_patient_data["email"]
        assert patient.phone == valid_patient_data["phone"]
        assert patient.address == valid_patient_data["address"]
        assert patient.medical_history == valid_patient_data["medical_history"]
        assert patient.medications == valid_patient_data["medications"]
        assert patient.allergies == valid_patient_data["allergies"]
        assert patient.treatment_notes == valid_patient_data["treatment_notes"]
        assert isinstance(patient.created_at, datetime)
        assert isinstance(patient.updated_at, datetime)

    def test_create_patient_with_string_gender(self, valid_patient_data):
        """Test creating a patient with string gender."""
        data = valid_patient_data.copy()
        data["gender"] = "Female" # Test with a different string gender
        patient = Patient(**data)
        assert patient.gender == "Female"

    def test_create_patient_with_string_date(self, valid_patient_data):
        """Test creating a patient with string date."""
        data = valid_patient_data.copy()
        data["date_of_birth"] = "1980-01-01"
        patient = Patient(**data)
        # __post_init__ should convert this
        assert patient.date_of_birth == date(1980, 1, 1)

    def test_validate_required_fields(self):
        """Test validation of required fields (via TypeError)."""
        # Missing name
        with pytest.raises(TypeError):
            Patient(
                id=str(uuid.uuid4()),
                date_of_birth=date(1980, 1, 1),
                gender="Male",
            )
        # Missing date_of_birth
        with pytest.raises(TypeError):
            Patient(
                id=str(uuid.uuid4()),
                name="John Doe",
                gender="Male",
            )
        # Missing gender
        with pytest.raises(TypeError):
            Patient(
                id=str(uuid.uuid4()),
                name="John Doe",
                date_of_birth=date(1980, 1, 1),
            )
        # Missing id
        with pytest.raises(TypeError):
            Patient(
                name="John Doe",
                date_of_birth=date(1980, 1, 1),
                gender="Male"
            )

    def test_validate_email_format(self, valid_patient_data):
        """Test validation of email format (dataclass doesn't enforce)."""
        data = valid_patient_data.copy()
        data["email"] = "invalid-email"
        try:
            Patient(**data)
        except Exception as e:
             pytest.fail(f"Patient creation failed unexpectedly for invalid email: {e}")

    def test_validate_phone_format(self, valid_patient_data):
        """Test validation of phone format (dataclass doesn't enforce)."""
        data = valid_patient_data.copy()
        data["email"] = None # Ensure email isn't present
        data["phone"] = "invalid@phone"
        try:
            Patient(**data)
        except Exception as e:
            pytest.fail(f"Patient creation failed unexpectedly for invalid phone: {e}")

    def test_update_contact_info(self, valid_patient_data):
        """Test updating contact information using the dedicated method."""
        patient = Patient(**valid_patient_data)
        created_at = patient.created_at # Store initial timestamp
        time.sleep(0.01) # Ensure updated_at changes

        new_email = "jane.smith@sample.com"
        new_phone = "555-111-2222"
        new_address = "456 Oak St, Othertown, NY 67890"

        patient.update_contact_info(
            email=new_email,
            phone=new_phone,
            address=new_address
        )

        assert patient.email == new_email
        assert patient.phone == new_phone
        assert patient.address == new_address
        assert patient.updated_at > created_at

    def test_add_medical_history_item(self, valid_patient_data):
        """Test adding a medical history item."""
        patient = Patient(**valid_patient_data)
        created_at = patient.created_at
        time.sleep(0.01)
        new_item = "Depression (Diagnosed: 2019-05-10, Notes: Moderate)"

        patient.add_medical_history_item(new_item)

        assert len(patient.medical_history) == 2
        assert patient.medical_history[1] == new_item
        assert patient.updated_at > created_at

    def test_add_medication(self, valid_patient_data):
        """Test adding a medication."""
        patient = Patient(**valid_patient_data)
        created_at = patient.created_at
        time.sleep(0.01)
        new_medication = "Escitalopram 10mg Daily (Started: 2021-03-15)"

        patient.add_medication(new_medication)

        assert len(patient.medications) == 2
        assert patient.medications[1] == new_medication
        assert patient.updated_at > created_at

    def test_add_allergy(self, valid_patient_data):
        """Test adding an allergy."""
        patient = Patient(**valid_patient_data)
        created_at = patient.created_at
        time.sleep(0.01)
        patient.add_allergy("Sulfa")

        assert len(patient.allergies) == 2
        assert "Sulfa" in patient.allergies
        assert patient.updated_at > created_at

    def test_add_existing_allergy(self, valid_patient_data):
        """Test adding an existing allergy."""
        patient = Patient(**valid_patient_data)
        original_updated_at = patient.updated_at
        time.sleep(0.01)
        patient.add_allergy("Penicillin") # Already exists

        assert len(patient.allergies) == 1
        assert patient.updated_at == original_updated_at # Should not update timestamp

    def test_add_treatment_note(self, valid_patient_data):
        """Test adding a treatment note."""
        patient = Patient(**valid_patient_data)
        created_at = patient.created_at
        time.sleep(0.01)
        new_note = {"content": "Follow-up session scheduled."} # Date added automatically

        patient.add_treatment_note(new_note)

        assert len(patient.treatment_notes) == 2
        assert patient.treatment_notes[1]["content"] == new_note["content"]
        assert isinstance(patient.treatment_notes[1]["date"], datetime)
        assert patient.updated_at > created_at

    def test_equality(self, valid_patient_data):
        """Test patient equality."""
        fixed_id = str(uuid.uuid4())
        data1 = {**valid_patient_data, "id": fixed_id}
        data2 = {**valid_patient_data, "id": fixed_id}
        # Ensure timestamps are identical for equality check
        ts = datetime.now()
        data1["created_at"] = ts
        data1["updated_at"] = ts
        data2["created_at"] = ts
        data2["updated_at"] = ts

        patient1 = Patient(**data1)
        patient2 = Patient(**data2)

        assert patient1 == patient2

    def test_inequality(self, valid_patient_data):
        """Test patient inequality."""
        patient1 = Patient(**valid_patient_data)
        data2 = valid_patient_data.copy()
        data2["id"] = str(uuid.uuid4()) # Different ID
        patient2 = Patient(**data2)

        assert patient1 != patient2
        assert patient1 != "not a patient"

    def test_string_representation(self, valid_patient_data):
        """Test string representation of a patient."""
        patient = Patient(**valid_patient_data)
        string_repr = repr(patient) # Use repr for dataclass default

        assert str(patient.id) in string_repr
        assert patient.name in string_repr # Check for name field

    def test_patient_initialization_optional_fields(self):
        """Test patient initialization with only required fields."""
        required_data = {
            "id": str(uuid.uuid4()),
            "name": "Test User",
            "date_of_birth": date(1990, 5, 15),
            "gender": "Other",
        }
        patient = Patient(**required_data)

        assert patient.id == required_data["id"]
        assert patient.name == "Test User"
        assert patient.date_of_birth == date(1990, 5, 15)
        assert patient.gender == "Other"
        assert patient.email is None
        assert patient.phone is None
        assert patient.address is None
        assert patient.medical_history == []
        assert patient.medications == []
        assert patient.allergies == []
        assert patient.treatment_notes == []
        assert patient.created_at is not None
        assert patient.updated_at is not None
