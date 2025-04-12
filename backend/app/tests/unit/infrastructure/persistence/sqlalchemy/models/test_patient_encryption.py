"""Unit tests for patient model encryption."""
import pytest
from unittest.mock import patch, MagicMock
import base64

from app.infrastructure.persistence.sqlalchemy.models.patient import Patient
from app.core.security.encryption import encrypt_value, decrypt_value


@pytest.fixture
def mock_encryption_key():
    """Mock encryption key for testing."""
    # Generate a valid Fernet key for testing
    return base64.urlsafe_b64encode(b"0" * 32)


@pytest.fixture
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
            "allergies": ["Penicillin"]
        }
    }


class TestPatientEncryption:
    """Tests for the Patient model encryption functionality."""
    
    @patch("app.core.security.encryption.get_encryption_key")
    def test_patient_initialization(self, mock_get_key, mock_encryption_key, patient_data):
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
        
        # Check that properties return decrypted values
        assert patient.first_name == patient_data["first_name"]
        assert patient.last_name == patient_data["last_name"]
        assert patient.dob == patient_data["dob"]
        assert patient.email == patient_data["email"]
        assert patient.phone == patient_data["phone"]
        assert patient.address == patient_data["address"]
        assert patient.medical_record_number == patient_data["medical_record_number"]
        assert patient.extra_data == patient_data["extra_data"]
    
    @patch("app.core.security.encryption.get_encryption_key")
    def test_setting_encrypted_fields(self, mock_get_key, mock_encryption_key):
        """Test that patient fields are encrypted when set."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key
        
        # Create empty patient
        patient = Patient()
        
        # Set fields
        patient.first_name = "Jane"
        patient.last_name = "Smith"
        patient.dob = "1985-05-15"
        
        # Check that sensitive fields are stored as encrypted values
        assert patient._first_name != "Jane"
        assert patient._last_name != "Smith"
        assert patient._dob != "1985-05-15"
        
        # Check that properties return decrypted values
        assert patient.first_name == "Jane"
        assert patient.last_name == "Smith"
        assert patient.dob == "1985-05-15"
    
    @patch("app.core.security.encryption.get_encryption_key")
    def test_extra_data_encryption(self, mock_get_key, mock_encryption_key):
        """Test that extra_data is properly encrypted and decrypted."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key
        
        # Complex nested data
        extra_data = {
            "conditions": ["Depression", "Anxiety"],
            "medications": [
                {"name": "Fluoxetine", "dosage": "20mg", "frequency": "daily"},
                {"name": "Alprazolam", "dosage": "0.5mg", "frequency": "as needed"}
            ],
            "preferences": {
                "communication": "email",
                "appointment_reminders": True,
                "telehealth": True
            }
        }
        
        # Create patient with extra data
        patient = Patient(extra_data=extra_data)
        
        # Check that extra_data is stored as encrypted value
        assert patient._extra_data is not None
        assert patient._extra_data != str(extra_data)
        
        # Check that property returns decrypted value
        assert patient.extra_data == extra_data
        
        # Check specific nested data is preserved
        assert patient.extra_data["medications"][0]["name"] == "Fluoxetine"
        assert patient.extra_data["preferences"]["telehealth"] is True
    
    @patch("app.core.security.encryption.get_encryption_key")
    def test_to_dict_with_phi(self, mock_get_key, mock_encryption_key, patient_data):
        """Test to_dict method with PHI included."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key
        
        # Create patient
        patient = Patient(**patient_data)
        
        # Get dictionary with PHI
        result = patient.to_dict(include_phi=True)
        
        # Check that PHI fields are included and decrypted
        assert result["first_name"] == patient_data["first_name"]
        assert result["last_name"] == patient_data["last_name"]
        assert result["dob"] == patient_data["dob"]
        assert result["email"] == patient_data["email"]
        assert result["extra_data"] == patient_data["extra_data"]
    
    @patch("app.core.security.encryption.get_encryption_key")
    def test_to_dict_without_phi(self, mock_get_key, mock_encryption_key, patient_data):
        """Test to_dict method without PHI included."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key
        
        # Create patient
        patient = Patient(**patient_data)
        
        # Get dictionary without PHI
        result = patient.to_dict(include_phi=False)
        
        # Check that PHI fields are not included
        assert "first_name" not in result
        assert "last_name" not in result
        assert "dob" not in result
        assert "email" not in result
        assert "extra_data" not in result
        
        # Check that non-PHI fields are included
        assert "id" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "is_active" in result
    
    @patch("app.core.security.encryption.get_encryption_key")
    def test_null_values(self, mock_get_key, mock_encryption_key):
        """Test handling of null/None values in encrypted fields."""
        # Set up mock encryption key
        mock_get_key.return_value = mock_encryption_key
        
        # Create patient with some null fields
        patient = Patient(
            first_name="John",
            last_name=None,
            dob="1980-01-01",
            email=None
        )
        
        # Check that null values are handled correctly
        assert patient.first_name == "John"
        assert patient.last_name is None
        assert patient.dob == "1980-01-01"
        assert patient.email is None
        
        # Set a field to None after initialization
        patient.first_name = None
        assert patient.first_name is None

    @patch("app.core.security.encryption.get_encryption_key")
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
        
    @patch("app.core.security.encryption.get_encryption_key")
    def test_encryption_error_handling(self, mock_get_key, mock_encryption_key):
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