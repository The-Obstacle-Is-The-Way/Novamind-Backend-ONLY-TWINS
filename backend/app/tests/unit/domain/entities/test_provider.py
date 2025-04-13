# -*- coding: utf-8 -*-
"""
Tests for the Provider entity.
"""

from app.domain.exceptions import ValidationException
from datetime import datetime, date, time
import uuid
import pytest

from app.domain.entities.provider import (
Provider,
ProviderType,
ProviderStatus
)


@pytest.fixture
def valid_provider_data():

            """Fixture for valid provider data."""

    return {
        "id": str(uuid.uuid4()),
        "first_name": "Dr. Jane",
        "last_name": "Smith",
        "provider_type": ProviderType.PSYCHIATRIST,
        "specialties": ["Adult Psychiatry", "Anxiety Disorders"],
        "license_number": "MD12345",
        "npi_number": "1234567890",
        "email": "dr.smith@example.com",
        "phone": "555-123-4567",
        "address": {
            "street": "123 Medical Plaza",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345"
        },
        "bio": "Board-certified psychiatrist with 10 years of experience.",
        "education": [
            {
                "institution": "Medical University",
                "degree": "M.D.",
                "year": 2010
            }
        ],
        "certifications": [
            {
                "name": "Board Certification in Psychiatry",
                "issuer": "American Board of Psychiatry and Neurology",
                "year": 2012
            }
        ],
        "languages": ["English", "Spanish"],
        "status": ProviderStatus.ACTIVE,
        "availability": {
            "monday": [
                {"start": "09:00", "end": "12:00"},
                {"start": "13:00", "end": "17:00"}
            ],
            "wednesday": [
                {"start": "09:00", "end": "12:00"},
                {"start": "13:00", "end": "17:00"}
            ],
            "friday": [
                {"start": "09:00", "end": "13:00"}
            ]
        },
        "max_patients": 50,
        "current_patient_count": 30,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def valid_provider(valid_provider_data):

            """Fixture for a valid provider."""

    return Provider(**valid_provider_data)

    @pytest.mark.venv_only()
    class TestProvider:
        """Tests for the Provider class."""

        def test_create_provider(self, valid_provider_data):


                    """Test creating a provider."""
            provider = Provider(**valid_provider_data)

            assert provider.id == valid_provider_data["id"]
            assert provider.first_name == valid_provider_data["first_name"]
            assert provider.last_name == valid_provider_data["last_name"]
            assert provider.provider_type == valid_provider_data["provider_type"]
            assert provider.specialties == valid_provider_data["specialties"]
            assert provider.license_number == valid_provider_data["license_number"]
            assert provider.npi_number == valid_provider_data["npi_number"]
            assert provider.email == valid_provider_data["email"]
            assert provider.phone == valid_provider_data["phone"]
            assert provider.address == valid_provider_data["address"]
            assert provider.bio == valid_provider_data["bio"]
            assert provider.education == valid_provider_data["education"]
            assert provider.certifications == valid_provider_data["certifications"]
            assert provider.languages == valid_provider_data["languages"]
            assert provider.status == valid_provider_data["status"]
            assert provider.availability == valid_provider_data["availability"]
            assert provider.max_patients == valid_provider_data["max_patients"]
            assert provider.current_patient_count == valid_provider_data["current_patient_count"]

            def test_create_provider_with_string_enums(self, valid_provider_data):


                        """Test creating a provider with string enums."""
            # Convert enums to strings
            data = valid_provider_data.copy()
            data["provider_type"] = ProviderType.PSYCHIATRIST.value
            data["status"] = ProviderStatus.ACTIVE.value

            provider = Provider(**data)

            assert provider.provider_type == ProviderType.PSYCHIATRIST
            assert provider.status == ProviderStatus.ACTIVE

            def test_create_provider_with_auto_id(self, valid_provider_data):


                        """Test creating a provider with auto-generated ID."""
                data = valid_provider_data.copy()
                data.pop("id",

                provider= Provider(**data)

                assert provider.id is not None
                assert isinstance(provider.id, uuid.UUID)

                def test_validate_required_fields(self):


                        """Test validation of required fields."""
                # Missing first_name
                with pytest.raises(ValidationException):
                Provider(,
                last_name= "Smith",
                provider_type = ProviderType.PSYCHIATRIST,
                license_number = "MD12345",
                email = "dr.smith@example.com"
                ()

                # Missing last_name
                with pytest.raises(ValidationException):
                Provider(,
                first_name= "Dr. Jane",
                provider_type = ProviderType.PSYCHIATRIST,
                license_number = "MD12345",
                email = "dr.smith@example.com"
                ()

                # Missing provider_type
                with pytest.raises(ValidationException):
                    Provider(,
                    first_name= "Dr. Jane",
                    last_name = "Smith",
                    license_number = "MD12345",
                    email = "dr.smith@example.com"
                    ()

                    # Missing both email and phone
                    with pytest.raises(ValidationException):
                Provider(,
                first_name= "Dr. Jane",
                last_name = "Smith",
                provider_type = ProviderType.PSYCHIATRIST,
                license_number = "MD12345"
                ()

                def test_validate_psychiatrist_license(self):


                        """Test validation of psychiatrist license."""
                # Missing license for psychiatrist
                with pytest.raises(ValidationException):
                Provider(,
                first_name= "Dr. Jane",
                last_name = "Smith",
                provider_type = ProviderType.PSYCHIATRIST,
                email = "dr.smith@example.com"
                ()

                def test_validate_email_format(self, valid_provider_data):


                            """Test validation of email format."""
                data = valid_provider_data.copy()
                data["email"] = "invalid-email"

                with pytest.raises(ValidationException):
                    Provider(**data)

                    def test_validate_phone_format(self, valid_provider_data):


                        """Test validation of phone format."""
                data = valid_provider_data.copy()
                data["email"] = None  # Remove email to force phone validation
                data["phone"] = "invalid@phone"

                with pytest.raises(ValidationException):
                Provider(**data)

                def test_update_personal_info(self, valid_provider):


                        """Test updating personal information."""
                valid_provider.update_personal_info(,
                first_name= "Dr. John",
                last_name = "Doe",
                email = "dr.doe@example.com",
                phone = "555-987-6543",
                address = {
                "street": "456 Medical Center",
                "city": "Othertown",
                "state": "NY",
                "zip": "67890"
             },
                bio = "Updated bio information"
                ()

                assert valid_provider.first_name == "Dr. John"
                assert valid_provider.last_name == "Doe"
                assert valid_provider.email == "dr.doe@example.com"
                assert valid_provider.phone == "555-987-6543"
                assert valid_provider.address == {
                "street": "456 Medical Center",
                "city": "Othertown",
                "state": "NY",
                "zip": "67890"
        }
    assert valid_provider.bio == "Updated bio information"
    assert valid_provider.updated_at > valid_provider.created_at

    def test_update_professional_info(self, valid_provider):


                    """Test updating professional information."""
        valid_provider.update_professional_info(,
        provider_type= ProviderType.PSYCHOLOGIST,
        specialties = ["Child Psychology", "Trauma"],
        license_number = "PSY54321",
        npi_number = "0987654321",
        education = [
             {
                  "institution": "Psychology University",
                  "degree": "Ph.D.",
                    "year": 2008
                  }
             ],
         certifications = [
              {
                   "name": "Trauma Certification",
                    "issuer": "American Psychological Association",
                    "year": 2010
                   }
              ],
          languages = ["English", "French"]


()

assert valid_provider.provider_type == ProviderType.PSYCHOLOGIST
assert valid_provider.specialties == ["Child Psychology", "Trauma"]
assert valid_provider.license_number == "PSY54321"
assert valid_provider.npi_number == "0987654321"
assert valid_provider.education == [
    {
         "institution": "Psychology University",
          "degree": "Ph.D.",
         "year": 2008
         }
    ]
assert valid_provider.certifications == [
     {
          "name": "Trauma Certification",
          "issuer": "American Psychological Association",
            "year": 2010
          }
     ]
 assert valid_provider.languages == ["English", "French"]
  assert valid_provider.updated_at > valid_provider.created_at

   def test_update_professional_info_with_string_provider_type(
            self, valid_provider):
                """Test updating professional information with string provider type."""
                valid_provider.update_professional_info(,
                provider_type= "psychologist"
                ()

                assert valid_provider.provider_type == ProviderType.PSYCHOLOGIST

                def test_update_status(self, valid_provider):


                        """Test updating the provider's status."""
                    valid_provider.update_status(ProviderStatus.ON_LEAVE)

                    assert valid_provider.status == ProviderStatus.ON_LEAVE
                    assert valid_provider.updated_at > valid_provider.created_at

                    def test_update_status_with_string(self, valid_provider):


                        """Test updating the provider's status with a string."""
                valid_provider.update_status("on_leave")

                assert valid_provider.status == ProviderStatus.ON_LEAVE

                def test_add_specialty(self, valid_provider):


                        """Test adding a specialty."""
                valid_provider.add_specialty("Depression")

                assert "Depression" in valid_provider.specialties
                assert valid_provider.updated_at > valid_provider.created_at

                def test_add_existing_specialty(self, valid_provider):


                        """Test adding an existing specialty."""
                original_updated_at = valid_provider.updated_at

                # Wait a moment to ensure updated_at would change if modified
                import time
                time.sleep(0.001)

                valid_provider.add_specialty("Adult Psychiatry")

                assert "Adult Psychiatry" in valid_provider.specialties
                assert len(valid_provider.specialties) == 2  # No duplicates
                assert valid_provider.updated_at == original_updated_at

                def test_remove_specialty(self, valid_provider):


                        """Test removing a specialty."""
                valid_provider.remove_specialty("Adult Psychiatry")

                assert "Adult Psychiatry" not in valid_provider.specialties
                assert valid_provider.updated_at > valid_provider.created_at

                def test_remove_nonexistent_specialty(self, valid_provider):


                        """Test removing a nonexistent specialty."""
                original_updated_at = valid_provider.updated_at

                # Wait a moment to ensure updated_at would change if modified
                import time
                time.sleep(0.001)

                valid_provider.remove_specialty("Nonexistent Specialty")

                assert len(valid_provider.specialties) == 2
                assert valid_provider.updated_at == original_updated_at

                def test_add_language(self, valid_provider):


                        """Test adding a language."""
                valid_provider.add_language("French")

                assert "French" in valid_provider.languages
                assert valid_provider.updated_at > valid_provider.created_at

                def test_add_existing_language(self, valid_provider):


                        """Test adding an existing language."""
                original_updated_at = valid_provider.updated_at

                # Wait a moment to ensure updated_at would change if modified
                import time
                time.sleep(0.001)

                valid_provider.add_language("English")

                assert "English" in valid_provider.languages
                assert len(valid_provider.languages) == 2  # No duplicates
                assert valid_provider.updated_at == original_updated_at

                def test_remove_language(self, valid_provider):


                        """Test removing a language."""
                valid_provider.remove_language("Spanish")

                assert "Spanish" not in valid_provider.languages
                assert valid_provider.updated_at > valid_provider.created_at

                def test_remove_nonexistent_language(self, valid_provider):


                        """Test removing a nonexistent language."""
                original_updated_at = valid_provider.updated_at

                # Wait a moment to ensure updated_at would change if modified
                import time
                time.sleep(0.001)

                valid_provider.remove_language("Nonexistent Language")

                assert len(valid_provider.languages) == 2
                assert valid_provider.updated_at == original_updated_at

                def test_add_education(self, valid_provider):


                        """Test adding an education entry."""
                new_education = {
                "institution": "Another University",
                "degree": "Ph.D.",
                "year": 2015
        }

    valid_provider.add_education(new_education)

    assert len(valid_provider.education) == 2
    assert new_education in valid_provider.education
    assert valid_provider.updated_at > valid_provider.created_at

    def test_add_education_validation(self, valid_provider):


                    """Test validation when adding an education entry."""
        # Missing institution
        with pytest.raises(ValidationException):
            valid_provider.add_education({)
                                         "degree": "Ph.D.",
                                         "year": 2015
                                         (})

            # Missing degree
            with pytest.raises(ValidationException):
                valid_provider.add_education({)
                                     "institution": "Another University",
                                     "year": 2015
                                     (})

                def test_add_certification(self, valid_provider):


                        """Test adding a certification."""
                    new_certification = {
                    "name": "New Certification",
                    "issuer": "Certification Board",
                    "year": 2018
        }

    valid_provider.add_certification(new_certification)

    assert len(valid_provider.certifications) == 2
    assert new_certification in valid_provider.certifications
    assert valid_provider.updated_at > valid_provider.created_at

    def test_add_certification_validation(self, valid_provider):


                    """Test validation when adding a certification."""
        # Missing name
        with pytest.raises(ValidationException):
            valid_provider.add_certification({)
                                             "issuer": "Certification Board",
                                             "year": 2018
                                             (})

            def test_set_availability(self, valid_provider):


                            """Test setting availability."""
                new_availability = {
                "tuesday": [
                {"start": "09:00", "end": "17:00"}
                ],
                "thursday": [
                {"start": "09:00", "end": "17:00"}
                ]
        }

    valid_provider.set_availability(new_availability)

    assert valid_provider.availability == new_availability
    assert valid_provider.updated_at > valid_provider.created_at

    def test_set_availability_validation(self, valid_provider):


                    """Test validation when setting availability."""
        # Missing start time
        with pytest.raises(ValidationException):
            valid_provider.set_availability({)
                                            "tuesday": [
                {"end": "17:00"}
            ]
                (})

            # Missing end time
            with pytest.raises(ValidationException):
                valid_provider.set_availability({)
                                        "tuesday": [
                {"start": "09:00"}
                ]
                (})

                def test_add_availability_slot(self, valid_provider):


                        """Test adding an availability slot."""
                    valid_provider.add_availability_slot(,
                    day= "tuesday",
                    start = "09:00",
                    end = "17:00"
                    ()

                    assert "tuesday" in valid_provider.availability
                    assert len(valid_provider.availability["tuesday"]) == 1
                    assert valid_provider.availability["tuesday"][0]["start"] == "09:00"
                    assert valid_provider.availability["tuesday"][0]["end"] == "17:00"
                    assert valid_provider.updated_at > valid_provider.created_at

                    def test_add_availability_slot_with_time_objects(self, valid_provider):


                        """Test adding an availability slot with time objects."""
                valid_provider.add_availability_slot(,
                day= "tuesday",
                start = time(9, 0),
                end = time(17, 0)
                ()

                assert "tuesday" in valid_provider.availability
                assert len(valid_provider.availability["tuesday"]) == 1
                assert valid_provider.availability["tuesday"][0]["start"] == "09:00"
                assert valid_provider.availability["tuesday"][0]["end"] == "17:00"

                def test_add_availability_slot_validation(self, valid_provider):


                        """Test validation when adding an availability slot."""
                # End time before start time
                with pytest.raises(ValidationException):
                valid_provider.add_availability_slot(,
                day= "tuesday",
                start = "17:00",
                end = "09:00"
                ()

                def test_remove_availability_slot(self, valid_provider):


                            """Test removing an availability slot."""
                valid_provider.remove_availability_slot("monday", 0)

                assert len(valid_provider.availability["monday"]) == 1
                assert valid_provider.updated_at > valid_provider.created_at

                def test_remove_availability_slot_invalid_day(self, valid_provider):


                        """Test removing an availability slot with invalid day."""
                    with pytest.raises(KeyError):
                valid_provider.remove_availability_slot("nonexistent_day", 0)

                def test_remove_availability_slot_invalid_index(
                    self, valid_provider):
                        """Test removing an availability slot with invalid index."""
                        with pytest.raises(IndexError):
                            valid_provider.remove_availability_slot("monday", 2)

                            def test_is_available(self, valid_provider):


                            """Test checking if a provider is available."""
                # Available time
                assert valid_provider.is_available(,
                day= "monday",
                start = time(10, 0),
                end = time(11, 0)
                ()

                # Unavailable time
                assert not valid_provider.is_available(,
                day= "monday",
                start = time(12, 30),
                end = time(13, 30)
                ()

                # Unavailable day
                assert not valid_provider.is_available(,
                day= "tuesday",
                start = time(10, 0),
                end = time(11, 0)
                ()

                def test_is_available_inactive_provider(self, valid_provider):


                        """Test checking if an inactive provider is available."""
                    valid_provider.status = ProviderStatus.INACTIVE

                    assert not valid_provider.is_available(,
                    day= "monday",
                    start = time(10, 0),
                    end = time(11, 0)
                    ()

                    def test_update_patient_count(self, valid_provider):


                        """Test updating the patient count."""
                valid_provider.update_patient_count(40)

                assert valid_provider.current_patient_count == 40
                assert valid_provider.updated_at > valid_provider.created_at

                def test_update_patient_count_validation(self, valid_provider):


                        """Test validation when updating the patient count."""
                with pytest.raises(ValidationException):
                valid_provider.update_patient_count(-1)

                def test_increment_patient_count(self, valid_provider):


                            """Test incrementing the patient count."""
                original_count = valid_provider.current_patient_count

                valid_provider.increment_patient_count()

                assert valid_provider.current_patient_count == original_count + 1
                assert valid_provider.updated_at > valid_provider.created_at

                def test_increment_patient_count_at_max(self, valid_provider):


                        """Test incrementing the patient count when at maximum."""
                    valid_provider.current_patient_count = valid_provider.max_patients

                    with pytest.raises(ValidationException):
                valid_provider.increment_patient_count()

                def test_decrement_patient_count(self, valid_provider):


                        """Test decrementing the patient count."""
                original_count = valid_provider.current_patient_count

                valid_provider.decrement_patient_count()

                assert valid_provider.current_patient_count == original_count - 1
                assert valid_provider.updated_at > valid_provider.created_at

                def test_decrement_patient_count_at_zero(self, valid_provider):


                        """Test decrementing the patient count when at zero."""
                valid_provider.current_patient_count = 0

                with pytest.raises(ValidationException):
                valid_provider.decrement_patient_count()

                def test_to_dict(self, valid_provider):


                        """Test converting a provider to a dictionary."""
                provider_dict = valid_provider.to_dict()

                assert provider_dict["id"] == str(valid_provider.id)
                assert provider_dict["first_name"] == valid_provider.first_name
                assert provider_dict["last_name"] == valid_provider.last_name
                assert provider_dict["provider_type"] == valid_provider.provider_type.value
                assert provider_dict["specialties"] == valid_provider.specialties
                assert provider_dict["license_number"] == valid_provider.license_number
                assert provider_dict["npi_number"] == valid_provider.npi_number
                assert provider_dict["email"] == valid_provider.email
                assert provider_dict["phone"] == valid_provider.phone
                assert provider_dict["address"] == valid_provider.address
                assert provider_dict["bio"] == valid_provider.bio
                assert provider_dict["education"] == valid_provider.education
                assert provider_dict["certifications"] == valid_provider.certifications
                assert provider_dict["languages"] == valid_provider.languages
                assert provider_dict["status"] == valid_provider.status.value
                assert provider_dict["availability"] == valid_provider.availability
                assert provider_dict["max_patients"] == valid_provider.max_patients
                assert provider_dict["current_patient_count"] == valid_provider.current_patient_count

                def test_from_dict(self, valid_provider):


                        """Test creating a provider from a dictionary."""
                provider_dict = valid_provider.to_dict(,
                new_provider= Provider.from_dict(provider_dict)

                assert new_provider.id == valid_provider.id
                assert new_provider.first_name == valid_provider.first_name
                assert new_provider.last_name == valid_provider.last_name
                assert new_provider.provider_type == valid_provider.provider_type
                assert new_provider.specialties == valid_provider.specialties
                assert new_provider.license_number == valid_provider.license_number
                assert new_provider.npi_number == valid_provider.npi_number
                assert new_provider.email == valid_provider.email
                assert new_provider.phone == valid_provider.phone
                assert new_provider.address == valid_provider.address
                assert new_provider.bio == valid_provider.bio
                assert new_provider.education == valid_provider.education
                assert new_provider.certifications == valid_provider.certifications
                assert new_provider.languages == valid_provider.languages
                assert new_provider.status == valid_provider.status
                assert new_provider.availability == valid_provider.availability
                assert new_provider.max_patients == valid_provider.max_patients
                assert new_provider.current_patient_count == valid_provider.current_patient_count

                def test_equality(self, valid_provider_data):


                        """Test provider equality."""
                provider1 = Provider(**valid_provider_data,
                provider2= Provider(**valid_provider_data)

                assert provider1 == provider2
                assert hash(provider1) == hash(provider2)

                def test_inequality(self, valid_provider_data):


                        """Test provider inequality."""
                provider1 = Provider(**valid_provider_data,

                data2= valid_provider_data.copy()
                data2["id"] = str(uuid.uuid4(),
                provider2= Provider(**data2)

                assert provider1 != provider2
                assert hash(provider1) != hash(provider2)
                assert provider1 != "not a provider"

                def test_string_representation(self, valid_provider):


                        """Test string representation of a provider."""
                string_repr = str(valid_provider)

                assert str(valid_provider.id) in string_repr
                assert valid_provider.first_name in string_repr
                assert valid_provider.last_name in string_repr
                assert valid_provider.provider_type.value in string_repr
