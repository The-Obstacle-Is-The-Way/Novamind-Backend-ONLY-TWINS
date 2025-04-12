"""Unit tests for patient data encryption in SQLAlchemy models."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, date
import json
import base64
from cryptography.fernet import Fernet

from app.core.config.settings import get_settings
from app.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientModel,
    EncryptedPatient
)
from app.domain.entities.patient import Patient
from app.core.security.encryption import encrypt_value, decrypt_value


@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    return Fernet.generate_key()


@pytest.fixture
def mock_encryption_settings(encryption_key):
    """Mock encryption settings."""
    with patch('app.core.config.settings.get_settings') as mock_settings:
        settings = MagicMock()
        settings.ENCRYPTION_KEY = encryption_key.decode()
        mock_settings.return_value = settings
        yield settings


@pytest.fixture
def patient_data():
    """Sample patient data for testing."""
    return {
        "id": "p12345",
        "first_name": "John",
        "last_name": "Doe",
        "dob": date(1980, 1, 15),
        "ssn": "123-45-6789",
        "address": "123 Main St, Anytown, US 12345",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "insurance_id": "INS123456",
        "medical_record_number": "MRN987654",
        "emergency_contact": "Jane Doe, 555-987-6543",
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "updated_at": datetime(2023, 2, 15, 14, 30, 0),
    }


@pytest.fixture
def patient_entity(patient_data):
    """Create a Patient entity from data."""
    return Patient(**patient_data)


@pytest.fixture
def encrypted_patient_model(patient_entity, mock_encryption_settings):
    """Create an encrypted patient model from entity."""
    return EncryptedPatient.from_entity(patient_entity)


class TestPatientEncryption:
    """Test suite for patient data encryption."""
    
    def test_phi_fields_defined(self):
        """Test that PHI fields are properly defined."""
        assert hasattr(EncryptedPatient, "PHI_FIELDS")
        assert isinstance(EncryptedPatient.PHI_FIELDS, set)
        assert "first_name" in EncryptedPatient.PHI_FIELDS
        assert "last_name" in EncryptedPatient.PHI_FIELDS
        assert "ssn" in EncryptedPatient.PHI_FIELDS
        assert "address" in EncryptedPatient.PHI_FIELDS
        assert "email" in EncryptedPatient.PHI_FIELDS
        assert "phone" in EncryptedPatient.PHI_FIELDS
        assert "insurance_id" in EncryptedPatient.PHI_FIELDS
    
    def test_encrypt_patient_data(self, patient_data, mock_encryption_settings):
        """Test encryption of patient PHI data."""
        # Create model with auto-encryption
        patient = EncryptedPatient(
            id=patient_data["id"],
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            dob=patient_data["dob"],
            ssn=patient_data["ssn"],
            address=patient_data["address"],
            email=patient_data["email"],
            phone=patient_data["phone"],
            insurance_id=patient_data["insurance_id"],
            medical_record_number=patient_data["medical_record_number"],
            emergency_contact=patient_data["emergency_contact"]
        )
        
        # Verify PHI fields are encrypted
        assert patient.first_name != patient_data["first_name"]
        assert patient.last_name != patient_data["last_name"]
        assert patient.ssn != patient_data["ssn"]
        assert patient.address != patient_data["address"]
        assert patient.email != patient_data["email"]
        assert patient.phone != patient_data["phone"]
        assert patient.insurance_id != patient_data["insurance_id"]
        
        # Verify encrypted values are in expected format (base64)
        try:
            # Encryption format is base64, so try to decode it
            base64.b64decode(patient.first_name)
            base64.b64decode(patient.ssn)
        except Exception as e:
            pytest.fail(f"Encrypted values not in expected format: {e}")
    
    def test_decrypt_patient_data(self, encrypted_patient_model, patient_data):
        """Test decryption of patient PHI data."""
        # Get decrypted entity
        patient_entity = encrypted_patient_model.to_entity()
        
        # Verify decrypted values match original data
        assert patient_entity.first_name == patient_data["first_name"]
        assert patient_entity.last_name == patient_data["last_name"]
        assert patient_entity.ssn == patient_data["ssn"]
        assert patient_entity.address == patient_data["address"]
        assert patient_entity.email == patient_data["email"]
        assert patient_entity.phone == patient_data["phone"]
        assert patient_entity.insurance_id == patient_data["insurance_id"]
    
    def test_from_entity_encrypt(self, patient_entity, mock_encryption_settings):
        """Test conversion from domain entity to encrypted model."""
        # Convert entity to model
        model = EncryptedPatient.from_entity(patient_entity)
        
        # Verify PHI fields are encrypted
        for field in EncryptedPatient.PHI_FIELDS:
            entity_value = getattr(patient_entity, field)
            model_value = getattr(model, field)
            # Skip None values
            if entity_value is not None:
                assert model_value != entity_value, f"Field {field} not encrypted"
    
    def test_to_entity_decrypt(self, encrypted_patient_model, patient_data):
        """Test conversion from encrypted model to domain entity."""
        entity = encrypted_patient_model.to_entity()
        
        # Verify all fields are properly decrypted
        for field in EncryptedPatient.PHI_FIELDS:
            if field in patient_data and patient_data[field] is not None:
                assert getattr(entity, field) == patient_data[field]
    
    def test_encryption_idempotence(self, patient_entity, mock_encryption_settings):
        """Test that multiple encryption/decryption cycles preserve data."""
        # First cycle
        model1 = EncryptedPatient.from_entity(patient_entity)
        entity1 = model1.to_entity()
        
        # Second cycle
        model2 = EncryptedPatient.from_entity(entity1)
        entity2 = model2.to_entity()
        
        # Compare all attributes
        for attr in patient_entity.__dict__:
            original_value = getattr(patient_entity, attr)
            final_value = getattr(entity2, attr)
            assert final_value == original_value, f"Data loss in {attr} after multiple encryption cycles"
    
    @patch('app.infrastructure.persistence.sqlalchemy.models.patient.encrypt_value')
    def test_encryption_error_handling(self, mock_encrypt, patient_entity):
        """Test handling of encryption errors."""
        # Make encryption fail
        mock_encrypt.side_effect = Exception("Encryption failed")
        
        # Should raise exception during from_entity
        with pytest.raises(Exception) as exc_info:
            EncryptedPatient.from_entity(patient_entity)
        
        assert "Encryption failed" in str(exc_info.value)
    
    @patch('app.infrastructure.persistence.sqlalchemy.models.patient.decrypt_value')
    def test_decryption_error_handling(self, mock_decrypt, encrypted_patient_model):
        """Test handling of decryption errors."""
        # Make decryption fail
        mock_decrypt.side_effect = Exception("Decryption failed")
        
        # Should raise exception during to_entity
        with pytest.raises(Exception) as exc_info:
            encrypted_patient_model.to_entity()
        
        assert "Decryption failed" in str(exc_info.value)