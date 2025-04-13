"""
Tests for the Patient entity.
"""

import uuid
from datetime import date, datetime, timedelta
import pytest

from app.tests.mocks.patient_mock import Patient, Gender, InsuranceStatus, PatientStatus, ValidationException


@pytest.fixture
def valid_patient_data():

            """Fixture for valid patient data."""

    return {
        "id": str(uuid.uuid4()),
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": date(1980, 1, 1),
        "gender": Gender.MALE,
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345"
        },
        "emergency_contacts": [
            {
                "name": "Jane Doe",
                "relationship": "Spouse",
                "phone": "555-987-6543"
            }
        ],
        "insurance_info": {
            "provider": "Health Insurance Co",
            "policy_number": "ABC123456",
            "group_number": "XYZ789"
        },
        "insurance_status": InsuranceStatus.VERIFIED,
        "medical_history": [
            {
                "condition": "Anxiety",
                "diagnosed_date": "2020-01-15",
                "notes": "Mild to moderate"
            }
        ],
        "medications": [
            {
                "name": "Sertraline",
                "dosage": "50mg",
                "frequency": "Daily",
                "start_date": "2020-02-01"
            }
        ],
        "allergies": ["Penicillin"],
        "notes": "Patient notes here",
        "status": PatientStatus.ACTIVE,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def valid_patient(valid_patient_data):

            """Fixture for a valid patient."""

    return Patient(**valid_patient_data)class TestPatient:
    """Tests for the Patient class."""

    @pytest.mark.standalone()
    def test_create_patient(self, valid_patient_data):

                    """Test creating a patient."""
        patient = Patient(**valid_patient_data)

        assert patient.id == valid_patient_data["id"]
        assert patient.first_name == valid_patient_data["first_name"]
        assert patient.last_name == valid_patient_data["last_name"]
        assert patient.date_of_birth == valid_patient_data["date_of_birth"]
        assert patient.gender == valid_patient_data["gender"]
        assert patient.email == valid_patient_data["email"]
        assert patient.phone == valid_patient_data["phone"]
        assert patient.address == valid_patient_data["address"]
        assert patient.emergency_contacts == valid_patient_data["emergency_contacts"]
        assert patient.insurance_info == valid_patient_data["insurance_info"]
        assert patient.insurance_status == valid_patient_data["insurance_status"]
        assert patient.medical_history == valid_patient_data["medical_history"]
        assert patient.medications == valid_patient_data["medications"]
        assert patient.allergies == valid_patient_data["allergies"]
        assert patient.notes == valid_patient_data["notes"]
        assert patient.status == valid_patient_data["status"]

        @pytest.mark.standalone()
        def test_create_patient_with_string_enums(self, valid_patient_data):

                        """Test creating a patient with string enums."""
        # Convert enums to strings
        data = valid_patient_data.copy()
        data["gender"] = Gender.MALE.value
        data["insurance_status"] = InsuranceStatus.VERIFIED.value
        data["status"] = PatientStatus.ACTIVE.value

        patient = Patient(**data)

        assert patient.gender == Gender.MALE
        assert patient.insurance_status == InsuranceStatus.VERIFIED
        assert patient.status == PatientStatus.ACTIVE

        @pytest.mark.standalone()
        def test_create_patient_with_string_date(self, valid_patient_data):

                        """Test creating a patient with string date."""
        # Convert date to string
        data = valid_patient_data.copy()
        data["date_of_birth"] = "1980-01-01"

        patient = Patient(**data)

        assert patient.date_of_birth == date(1980, 1, 1)

        @pytest.mark.standalone()
        def test_create_patient_with_auto_id(self, valid_patient_data):

                        """Test creating a patient with auto-generated ID."""
        data = valid_patient_data.copy()
        data.pop("id",

        patient= Patient(**data)

        assert patient.id is not None
        assert isinstance(patient.id, uuid.UUID)

        @pytest.mark.standalone()
        def test_validate_required_fields(self):

                        """Test validation of required fields."""
        # Missing first_name
        with pytest.raises(ValidationException):
            Patient(,
            last_name= "Doe",
             date_of_birth = date(1980, 1, 1),
              gender = Gender.MALE,
               email = "john.doe@example.com"
            ()

            # Missing last_name
            with pytest.raises(ValidationException):
        Patient(,
        first_name= "John",
        date_of_birth = date(1980, 1, 1),
        gender = Gender.MALE,
        email = "john.doe@example.com"
        ()

        # Missing date_of_birth
        with pytest.raises(ValidationException):
        Patient(,
        first_name= "John",
        last_name = "Doe",
        gender = Gender.MALE,
        email = "john.doe@example.com"
        ()

        # Missing gender
        with pytest.raises(ValidationException):
        Patient(,
        first_name= "John",
        last_name = "Doe",
        date_of_birth = date(1980, 1, 1),
        email = "john.doe@example.com"
        ()

        # Missing both email and phone
        with pytest.raises(ValidationException):
        Patient(,
        first_name= "John",
        last_name = "Doe",
        date_of_birth = date(1980, 1, 1),
        gender = Gender.MALE
        ()

        @pytest.mark.standalone()
        def test_validate_email_format(self, valid_patient_data):

                        """Test validation of email format."""
        data = valid_patient_data.copy()
        data["email"] = "invalid-email"

        with pytest.raises(ValidationException):
        Patient(**data)

        @pytest.mark.standalone()
        def test_validate_phone_format(self, valid_patient_data):

                        """Test validation of phone format."""
        data = valid_patient_data.copy()
        data["email"] = None  # Remove email to force phone validation
        data["phone"] = "invalid@phone"

        with pytest.raises(ValidationException):
        Patient(**data)

        @pytest.mark.standalone()
        def test_update_personal_info(self, valid_patient):

                        """Test updating personal information."""
        valid_patient.update_personal_info(,
        first_name= "Jane",
         last_name = "Smith",
          date_of_birth = date(1981, 2, 2),
           gender = Gender.FEMALE,
            email = "jane.smith@example.com",
            phone = "555-987-6543",
            address = {
                "street": "456 Oak St",
                "city": "Othertown",
                "state": "NY",
                "zip": "67890"
            }


()

assert valid_patient.first_name == "Jane"
assert valid_patient.last_name == "Smith"
 assert valid_patient.date_of_birth == date(1981, 2, 2)
  assert valid_patient.gender == Gender.FEMALE
   assert valid_patient.email == "jane.smith@example.com"
    assert valid_patient.phone == "555-987-6543"
    assert valid_patient.address == {
        "street": "456 Oak St",
        "city": "Othertown",
        "state": "NY",
        "zip": "67890"
    }
    assert valid_patient.updated_at > valid_patient.created_at

    @pytest.mark.standalone()
    def test_update_personal_info_with_string_date(self, valid_patient):

                    """Test updating personal information with string date."""
        valid_patient.update_personal_info(,
        date_of_birth= "1981-02-02"
        ()

        assert valid_patient.date_of_birth == date(1981, 2, 2)

        @pytest.mark.standalone()
        def test_update_personal_info_with_string_gender(self, valid_patient):

                        """Test updating personal information with string gender."""
        valid_patient.update_personal_info(,
        gender= "female"
        ()

        assert valid_patient.gender == Gender.FEMALE

        @pytest.mark.standalone()
        def test_update_insurance_info(self, valid_patient):

                        """Test updating insurance information."""
        new_insurance_info = {
            "provider": "New Health Insurance Co",
            "policy_number": "DEF789012",
            "group_number": "UVW345"
        }

    valid_patient.update_insurance_info(,
    insurance_info= new_insurance_info,
    insurance_status = InsuranceStatus.PENDING
()

assert valid_patient.insurance_info == new_insurance_info
assert valid_patient.insurance_status == InsuranceStatus.PENDING
 assert valid_patient.updated_at > valid_patient.created_at

  @pytest.mark.standalone()
   def test_update_insurance_info_with_string_status(self, valid_patient):

                   """Test updating insurance information with string status."""
        valid_patient.update_insurance_info(,
        insurance_info= valid_patient.insurance_info,
         insurance_status = "pending"
        ()

        assert valid_patient.insurance_status == InsuranceStatus.PENDING

        @pytest.mark.standalone()
        def test_add_emergency_contact(self, valid_patient):

                        """Test adding an emergency contact."""
        new_contact = {
            "name": "Robert Doe",
            "relationship": "Father",
            "phone": "555-555-5555"
        }

    valid_patient.add_emergency_contact(new_contact)

    assert len(valid_patient.emergency_contacts) == 2
    assert valid_patient.emergency_contacts[1] == new_contact
    assert valid_patient.updated_at > valid_patient.created_at

    @pytest.mark.standalone()
    def test_add_emergency_contact_validation(self, valid_patient):

                    """Test validation when adding an emergency contact."""
        # Missing name
        with pytest.raises(ValidationException):
            valid_patient.add_emergency_contact({)
                                                "relationship": "Father",
                                                "phone": "555-555-5555"
                                                (})

            # Missing both phone and email
            with pytest.raises(ValidationException):
        valid_patient.add_emergency_contact({)
                                            "name": "Robert Doe",
                                            "relationship": "Father"
                                            (})

        @pytest.mark.standalone()
        def test_remove_emergency_contact(self, valid_patient):

                        """Test removing an emergency contact."""
        valid_patient.remove_emergency_contact(0)

        assert len(valid_patient.emergency_contacts) == 0
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_remove_emergency_contact_invalid_index(self, valid_patient):

                        """Test removing an emergency contact with invalid index."""
        with pytest.raises(IndexError):
            valid_patient.remove_emergency_contact(1)

            @pytest.mark.standalone()
            def test_add_medical_history_item(self, valid_patient):

                            """Test adding a medical history item."""
        new_item = {
            "condition": "Depression",
            "diagnosed_date": "2019-05-10",
            "notes": "Moderate"
        }

    valid_patient.add_medical_history_item(new_item)

    assert len(valid_patient.medical_history) == 2
    assert valid_patient.medical_history[1] == new_item
    assert valid_patient.updated_at > valid_patient.created_at

    @pytest.mark.standalone()
    def test_add_medical_history_item_validation(self, valid_patient):

                    """Test validation when adding a medical history item."""
        # Missing condition
        with pytest.raises(ValidationException):
            valid_patient.add_medical_history_item({)
                                                   "diagnosed_date": "2019-05-10",
                                                   "notes": "Moderate"
                                                   (})

            @pytest.mark.standalone()
            def test_add_medication(self, valid_patient):

                            """Test adding a medication."""
        new_medication = {
            "name": "Escitalopram",
            "dosage": "10mg",
            "frequency": "Daily",
            "start_date": "2021-03-15"
        }

    valid_patient.add_medication(new_medication)

    assert len(valid_patient.medications) == 2
    assert valid_patient.medications[1] == new_medication
    assert valid_patient.updated_at > valid_patient.created_at

    @pytest.mark.standalone()
    def test_add_medication_validation(self, valid_patient):

                    """Test validation when adding a medication."""
        # Missing name
        with pytest.raises(ValidationException):
            valid_patient.add_medication({)
                                         "dosage": "10mg",
                                         "frequency": "Daily",
                                         "start_date": "2021-03-15"
                                         (})

            # Missing dosage
            with pytest.raises(ValidationException):
        valid_patient.add_medication({)
                                     "name": "Escitalopram",
                                     "frequency": "Daily",
                                     "start_date": "2021-03-15"
                                     (})

        @pytest.mark.standalone()
        def test_remove_medication(self, valid_patient):

                        """Test removing a medication."""
        valid_patient.remove_medication(0)

        assert len(valid_patient.medications) == 0
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_remove_medication_invalid_index(self, valid_patient):

                        """Test removing a medication with invalid index."""
        with pytest.raises(IndexError):
            valid_patient.remove_medication(1)

            @pytest.mark.standalone()
            def test_add_allergy(self, valid_patient):

                            """Test adding an allergy."""
        valid_patient.add_allergy("Sulfa")

        assert len(valid_patient.allergies) == 2
        assert "Sulfa" in valid_patient.allergies
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_add_existing_allergy(self, valid_patient):

                        """Test adding an existing allergy."""
        original_updated_at = valid_patient.updated_at

        # Wait a moment to ensure updated_at would change if modified
        import time
        time.sleep(0.001)

        valid_patient.add_allergy("Penicillin")

        assert len(valid_patient.allergies) == 1
        assert valid_patient.updated_at == original_updated_at

        @pytest.mark.standalone()
        def test_remove_allergy(self, valid_patient):

                        """Test removing an allergy."""
        valid_patient.remove_allergy("Penicillin")

        assert len(valid_patient.allergies) == 0
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_remove_nonexistent_allergy(self, valid_patient):

                        """Test removing a nonexistent allergy."""
        original_updated_at = valid_patient.updated_at

        # Wait a moment to ensure updated_at would change if modified
        import time
        time.sleep(0.001)

        valid_patient.remove_allergy("Sulfa")

        assert len(valid_patient.allergies) == 1
        assert valid_patient.updated_at == original_updated_at

        @pytest.mark.standalone()
        def test_update_status(self, valid_patient):

                        """Test updating the patient's status."""
        valid_patient.update_status(PatientStatus.INACTIVE)

        assert valid_patient.status == PatientStatus.INACTIVE
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_update_status_with_string(self, valid_patient):

                        """Test updating the patient's status with a string."""
        valid_patient.update_status("inactive")

        assert valid_patient.status == PatientStatus.INACTIVE

        @pytest.mark.standalone()
        def test_update_notes(self, valid_patient):

                        """Test updating the patient's notes."""
        new_notes = "Updated patient notes"

        valid_patient.update_notes(new_notes)

        assert valid_patient.notes == new_notes
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_update_appointment_times(self, valid_patient):

                        """Test updating appointment times."""
        last_appointment = datetime.now() - timedelta(days=7,
        next_appointment= datetime.now() + timedelta(days=7)

        valid_patient.update_appointment_times(,
        last_appointment= last_appointment,
        next_appointment = next_appointment
        ()

        assert valid_patient.last_appointment == last_appointment
        assert valid_patient.next_appointment == next_appointment
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_set_preferred_provider(self, valid_patient):

                        """Test setting the preferred provider."""
        provider_id = str(uuid.uuid4())

        valid_patient.set_preferred_provider(provider_id)

        assert valid_patient.preferred_provider_id == provider_id
        assert valid_patient.updated_at > valid_patient.created_at

        @pytest.mark.standalone()
        def test_to_dict(self, valid_patient):

                        """Test converting a patient to a dictionary."""
        patient_dict = valid_patient.to_dict()

        assert patient_dict["id"] == str(valid_patient.id)
        assert patient_dict["first_name"] == valid_patient.first_name
        assert patient_dict["last_name"] == valid_patient.last_name
        assert patient_dict["date_of_birth"] == valid_patient.date_of_birth.isoformat(
        )
        assert patient_dict["gender"] == valid_patient.gender.value
        assert patient_dict["status"] == valid_patient.status.value

        @pytest.mark.standalone()
        def test_from_dict(self, valid_patient):

                        """Test creating a patient from a dictionary."""
        # Convert patient to dict and back
        patient_dict = valid_patient.to_dict(,
        new_patient= Patient.from_dict(patient_dict)

        assert new_patient.id == valid_patient.id
        assert new_patient.first_name == valid_patient.first_name
        assert new_patient.last_name == valid_patient.last_name
        assert new_patient.date_of_birth == valid_patient.date_of_birth
        assert new_patient.gender == valid_patient.gender
        assert new_patient.email == valid_patient.email
        assert new_patient.status == valid_patient.status

        @pytest.mark.standalone()
        def test_equality(self, valid_patient_data):

                        """Test patient equality."""
        patient1 = Patient(**valid_patient_data,
        patient2= Patient(**valid_patient_data)

        assert patient1 == patient2
        assert hash(patient1) == hash(patient2)

        @pytest.mark.standalone()
        def test_inequality(self, valid_patient_data):

                        """Test patient inequality."""
        patient1 = Patient(**valid_patient_data)

        # Copy data and change ID
        data2 = valid_patient_data.copy()
        data2["id"] = str(uuid.uuid4(),
        patient2= Patient(**data2)

        assert patient1 != patient2
        assert hash(patient1) != hash(patient2)

        @pytest.mark.standalone()
        def test_string_representation(self, valid_patient):

                        """Test patient string representation."""
        patient_str = str(valid_patient)

        assert valid_patient.first_name in patient_str
        assert valid_patient.last_name in patient_str
        assert str(valid_patient.id) in patient_str
