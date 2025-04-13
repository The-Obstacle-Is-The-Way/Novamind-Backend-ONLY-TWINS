"""Unit tests for patient model encryption.

This module tests HIPAA-compliant encryption functionality for the Patient model,
ensuring proper PHI protection while maintaining data integrity.
"""
import pytest
from unittest.mock import patch, MagicMock
import base64

# Use infrastructure layer imports to avoid circular dependencies
from app.infrastructure.security.encryption import (
    encrypt_value,
    decrypt_value,
    get_encryption_key,
)


@pytest.fixture
def mock_encryption_key():

            """Mock encryption key for testing."""
    # Generate a valid Fernet key for testing
    return base64.urlsafe_b64encode(b"0" * 32)@pytest.fixture
    def patient_data():

            """Sample patient data for testing."""
        return {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1980-01-01",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St, Anytown, USA",
        "medical_record_number": "MRN12345",
        "extra_data": {
            "insurance": "Blue Cross",
            "emergency_contact": "Jane Doe",
            "allergies": ["Penicillin"],
        },
    }


# Mock Patient class for testingclass Patient:
    """Mock Patient model with encrypted fields."""

    def __init__(self, **kwargs):


                    """Initialize patient with encrypted fields."""
        self._first_name = (
            encrypt_value(kwargs.get("first_name"))
            if kwargs.get("first_name")
            else None
        )
        self._last_name = (encrypt_value(kwargs.get("last_name"))
                           if kwargs.get("last_name") else None)
        self._dob = encrypt_value(
            kwargs.get("dob")) if kwargs.get("dob") else None
        self._email = (
            encrypt_value(kwargs.get("email")) if kwargs.get("email") else None
        )
        self._phone = (
            encrypt_value(kwargs.get("phone")) if kwargs.get("phone") else None
        )
        self._address = (encrypt_value(kwargs.get("address"))
                         if kwargs.get("address") else None)
        self._medical_record_number = (
            encrypt_value(kwargs.get("medical_record_number"))
            if kwargs.get("medical_record_number")
            else None
        )

        if kwargs.get("extra_data"):
            import json

            self._extra_data = encrypt_value(
                json.dumps(kwargs.get("extra_data")))
            else:
                self._extra_data = None

                @property
                def first_name(self):

                            """Get decrypted first name."""
                    return decrypt_value(self._first_name)

                    @first_name.setter
                    def first_name(self, value):

                        """Set encrypted first name."""
                    self._first_name = encrypt_value(value) if value else None

                    @property
                    def last_name(self):

                        """Get decrypted last name."""
                return decrypt_value(self._last_name)

                @last_name.setter
                def last_name(self, value):

                        """Set encrypted last name."""
                self._last_name = encrypt_value(value) if value else None

                @property
                def dob(self):

                        """Get decrypted date of birth."""
                return decrypt_value(self._dob)

                @dob.setter
                def dob(self, value):

                        """Set encrypted date of birth."""
                self._dob = encrypt_value(value) if value else None

                @property
                def email(self):

                        """Get decrypted email."""
                return decrypt_value(self._email)

                @email.setter
                def email(self, value):

                        """Set encrypted email."""
                self._email = encrypt_value(value) if value else None

                @property
                def phone(self):

                        """Get decrypted phone."""
                return decrypt_value(self._phone)

                @phone.setter
                def phone(self, value):

                        """Set encrypted phone."""
                self._phone = encrypt_value(value) if value else None

                @property
                def address(self):

                        """Get decrypted address."""
                return decrypt_value(self._address)

                @address.setter
                def address(self, value):

                        """Set encrypted address."""
                self._address = encrypt_value(value) if value else None

                @property
                def medical_record_number(self):

                        """Get decrypted medical record number."""
                return decrypt_value(self._medical_record_number)

                @medical_record_number.setter
                def medical_record_number(self, value):

                        """Set encrypted medical record number."""
                self._medical_record_number = encrypt_value(value) if value else None

                @property
                def extra_data(self):

                        """Get decrypted extra data."""
                if self._extra_data:
                import json

                return json.loads(decrypt_value(self._extra_data))
                return None

                @extra_data.setter
                def extra_data(self, value):

                            """Set encrypted extra data."""
                if value:
                    import json

                    self._extra_data = encrypt_value(json.dumps(value))
                    else:
                self._extra_data = Noneclass TestPatientEncryption:
                    """Tests for the Patient model encryption functionality."""

                    @patch("app.infrastructure.security.encryption.get_encryption_key")
                    def test_patient_initialization(
                    self, mock_get_key, mock_encryption_key, patient_data
    ):
        """Test that patient fields are encrypted during initialization."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key

        # Create patient
        patient = Patient(**patient_data)

        # Check that sensitive fields are stored as encrypted values
        assert patient._first_name != patient_data["first_name"]
        assert patient._last_name != patient_data["last_name"]
        assert patient._dob != patient_data["dob"]
        assert patient._email != patient_data["email"]
        assert patient._phone != patient_data["phone"]
        assert patient._address != patient_data["address"]
        assert patient._medical_record_number != patient_data["medical_record_number"]
        assert patient._extra_data is not None

        # Check that accessing properties returns decrypted values
        assert patient.first_name == patient_data["first_name"]
        assert patient.last_name == patient_data["last_name"]
        assert patient.dob == patient_data["dob"]
        assert patient.email == patient_data["email"]
        assert patient.phone == patient_data["phone"]
        assert patient.address == patient_data["address"]
        assert patient.medical_record_number == patient_data["medical_record_number"]
        assert patient.extra_data == patient_data["extra_data"]

        @patch("app.infrastructure.security.encryption.get_encryption_key")
        def test_patient_property_updates(
            self, mock_get_key, mock_encryption_key, patient_data
        ):
            """Test that updating patient properties properly encrypts new values."""
            # Set up mock encryption key
            mock_get_key.return_value = mock_encryption_key

            # Create patient
            patient = Patient(**patient_data)

            # Update properties
            patient.first_name = "Jane"
            patient.last_name = "Smith"
            patient.email = "jane.smith@example.com"

            # Check that new values are encrypted in storage
            assert patient._first_name != "Jane"
            assert patient._last_name != "Smith"
            assert patient._email != "jane.smith@example.com"

            # Check that accessing properties returns decrypted values
            assert patient.first_name == "Jane"
            assert patient.last_name == "Smith"
            assert patient.email == "jane.smith@example.com"

            @patch("app.infrastructure.security.encryption.get_encryption_key")
            def test_patient_extra_data(
                self,
                mock_get_key,
                mock_encryption_key,
                patient_data):
                    """Test encryption and decryption of extra_data JSON."""
                    # Set up mock encryption key
                    mock_get_key.return_value = mock_encryption_key

                    # Create patient
                    patient = Patient(**patient_data)

                    # Check that extra_data is encrypted in storage
                    assert patient._extra_data != patient_data["extra_data"]

                    # Check that accessing extra_data returns decrypted JSON
                    assert patient.extra_data == patient_data["extra_data"]
                    assert patient.extra_data["insurance"] == "Blue Cross"
                    assert patient.extra_data["emergency_contact"] == "Jane Doe"
                    assert patient.extra_data["allergies"] == ["Penicillin"]

                    # Update extra_data
                    new_extra_data = {
                    "insurance": "Aetna",
                    "emergency_contact": "John Smith",
                    "allergies": ["Sulfa", "Latex"],
        }
        patient.extra_data = new_extra_data

        # Check that new extra_data is encrypted in storage
        import json

        assert patient._extra_data != json.dumps(new_extra_data)

        # Check that accessing extra_data returns decrypted JSON
        assert patient.extra_data == new_extra_data
        assert patient.extra_data["insurance"] == "Aetna"
        assert patient.extra_data["allergies"] == ["Sulfa", "Latex"]

    @patch("app.infrastructure.security.encryption.get_encryption_key")
    def test_null_values(self, mock_get_key, mock_encryption_key):

                    """Test handling of null values in encrypted fields."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key

        # Create patient with some null fields
        patient = Patient(
            first_name="John", last_name=None, dob="1980-01-01", email=None
        )

        # Check that null values are handled correctly
        assert patient.first_name == "John"
        assert patient.last_name is None
        assert patient.dob == "1980-01-01"
        assert patient.email is None

        # Set a field to None after initialization
        patient.first_name = None
        assert patient.first_name is None

    @patch("app.infrastructure.security.encryption.get_encryption_key")
    def test_encryption_key_handling(self, mock_get_key, mock_encryption_key):

                    """Test that encryption key is properly handled when encrypting/decrypting."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key

        # Create patient
        patient = Patient(first_name="Test", last_name="Patient")

        # Verify the encryption key was used
        mock_get_key.assert_called()

        # Check that values are properly decrypted
        assert patient.first_name == "Test"
        assert patient.last_name == "Patient"

        @patch("app.infrastructure.security.encryption.get_encryption_key")
        def test_encryption_error_handling(
                self, mock_get_key, mock_encryption_key):
                    """Test encryption error handling."""
                    # Set up mock encryption key
                    mock_get_key.return_value = mock_encryption_key

                    # Create patient
                    patient = Patient(first_name="Test", last_name="Patient")

                    # Modify _first_name to be invalid encrypted data
                    patient._first_name = "invalid_encrypted_data"

                    # Test that the property gracefully handles decryption failures
                    # by returning None instead of raising an exception
                    assert patient.first_name is None
