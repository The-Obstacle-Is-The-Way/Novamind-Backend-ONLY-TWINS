"""Unit tests for the patient encryption functionality in SQLAlchemy models."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from app.domain.entities.patient import Patient, Address
from app.domain.enums.patient import Gender, MaritalStatus


class TestPatientEncryption:
    """Test suite for patient encryption functionality."""
    
    @pytest.fixture
    def mock_encryption_service(self):
        """Create a mock encryption service for testing."""
        mock_service = MagicMock()
        mock_service.encrypt.side_effect = lambda text: f"ENC:{text}" if text else None
        mock_service.decrypt.side_effect = lambda text: text[4:] if text and text.startswith("ENC:") else None
        
    return mock_service
    
    @pytest.fixture
    def sample_patient(self):
        """Create a sample patient domain entity for testing."""
        return Patient(
            id=None,  # Will be assigned by DB
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 1),
            email="john.doe@example.com",
            phone="555-123-4567",
            address=Address(
                line1="123 Main St",
                line2="Apt 4B",
                city="Anytown",
                state="CA",
                zip_code="12345",
                country="US"
            ),
            gender=Gender.MALE,
            marital_status=MaritalStatus.SINGLE,
            insurance_id="INS12345",
            insurance_provider="Health Insurance Co",
            emergency_contact_name="Jane Doe",
            emergency_contact_phone="555-987-6543",
            active=True,
            created_by=None
        )
    
    def test_encrypt_patient_data(self, sample_patient, mock_encryption_service):
        """Test that patient PHI is encrypted when converted to a model."""
        # Import here to avoid circular imports
        with patch('app.infrastructure.persistence.sqlalchemy.models.patient.encryption_service',
                  mock_encryption_service):
        from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
            
            # Convert domain entity to model
    patient_model = PatientModel.from_domain(sample_patient)
            
            # Verify PHI data is encrypted
    assert patient_model.first_name == f"ENC:{sample_patient.first_name}"
    assert patient_model.last_name == f"ENC:{sample_patient.last_name}"
    assert patient_model.email == f"ENC:{sample_patient.email}"
    assert patient_model.phone == f"ENC:{sample_patient.phone}"
    assert patient_model.address_line1 == f"ENC:{sample_patient.address.line1}"
    assert patient_model.address_line2 == f"ENC:{sample_patient.address.line2}"
            
            # Non-PHI data should not be encrypted
    assert patient_model.gender == sample_patient.gender
    assert patient_model.marital_status == sample_patient.marital_status
    
    def test_decrypt_patient_data(self, sample_patient, mock_encryption_service):
        """Test that patient PHI is decrypted when converted back to a domain entity."""
        # Import here to avoid circular imports
        with patch('app.infrastructure.persistence.sqlalchemy.models.patient.encryption_service',
                  mock_encryption_service):
        from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
            
            # First convert domain to model (will encrypt)
    patient_model = PatientModel.from_domain(sample_patient)
            
            # Then convert back to domain (should decrypt)
    decrypted_patient = patient_model.to_domain()
            
            # Verify PHI data is correctly decrypted and matches original
    assert decrypted_patient.first_name == sample_patient.first_name
    assert decrypted_patient.last_name == sample_patient.last_name
    assert decrypted_patient.email == sample_patient.email
    assert decrypted_patient.phone == sample_patient.phone
    assert decrypted_patient.address.line1 == sample_patient.address.line1
    assert decrypted_patient.address.line2 == sample_patient.address.line2