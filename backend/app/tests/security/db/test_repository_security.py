# -*- coding: utf-8 -*-
"""
Repository Security Tests

These tests verify that repositories handling PHI/ePHI properly:
    1. Encrypt sensitive fields before storage
    2. Decrypt fields when retrieving records
    3. Never expose raw PHI in logs or exceptions
    4. Validate access permissions before operations
    5. Maintain audit trails for all operations
    """
import pytest
import json
import uuid
from unittest.mock import patch, MagicMock, ANY

from app.infrastructure.persistence.sqlalchemy.patient_repository import PatientRepository
from app.infrastructure.security.encryption_service import EncryptionService
from app.domain.entities.patient import Patient


@pytest.fixture
def encryption_service():
    """Create a test encryption service."""
    # Use a test key, never use in production
    test_key = b"testkeyfortestingonly1234567890abcdef"
    service = EncryptionService()
    # Set the key directly to avoid loading from environment or generating a new one
    service._encryption_key = test_key
    return service

@pytest.fixture
def db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.add.return_value = None
    session.commit.return_value = None
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    return session

@pytest.fixture
def patient_repository(db_session, encryption_service):
    """Create a patient repository with mocked dependencies."""
    repo = PatientRepository(db_session, encryption_service)
    # Add missing methods for testing
    def mock_get_all(limit=100, offset=0, include_inactive=False):
        return []
    repo.get_all = mock_get_all
    
    def mock_search(criteria, limit=100, offset=0):
        return []
    repo.search = mock_search
    return repo

@pytest.mark.db_required()
def test_patient_creation_encrypts_phi(patient_repository, encryption_service, db_session):
    """Test that patient creation encrypts PHI fields before storage."""
    # Arrange
    patient_data = {
        "id": str(uuid.uuid4()),
        "ssn": "123-45-6789",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St"
    }
    patient = Patient(**patient_data)
    
    # Mock encryption calls
    with patch.object(encryption_service, "encrypt", side_effect=lambda x: f"ENC_{x}") as mock_encrypt:
        # Act
        patient_repository.create(patient)
        
        # Assert
        assert mock_encrypt.call_count >= 2, "Expected at least 2 encryption calls for PHI fields"
        db_session.add.assert_called()
        db_session.commit.assert_called()

def test_patient_retrieval_decrypts_phi(patient_repository, encryption_service, db_session):
    """Test that patient retrieval decrypts PHI fields."""
    # Arrange
    patient_id = str(uuid.uuid4())
    encrypted_data = {
        "id": patient_id,
        "ssn": "ENC_123-45-6789",
        "email": "ENC_john.doe@example.com",
        "phone": "ENC_555-123-4567",
        "address": "ENC_123 Main St"
    }
    decrypted_data = {
        "id": patient_id,
        "ssn": "123-45-6789",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St"
    }
    db_session.first.return_value = Patient(**encrypted_data)
    
    # Mock decryption calls
    with patch.object(encryption_service, "decrypt", side_effect=lambda x: x[4:] if x.startswith("ENC_") else x) as mock_decrypt:
        # Act
        retrieved_patient = patient_repository.get_by_id(patient_id)
        
        # Assert
        assert mock_decrypt.call_count >= 2, "Expected at least 2 decryption calls"
        assert retrieved_patient.ssn == decrypted_data["ssn"]
        assert retrieved_patient.email == decrypted_data["email"]

def test_repository_filters_inactive_records(patient_repository, db_session):
    """Test that repository filters out inactive/deleted records by default."""
    # Setup mock to verify filtering
    db_session.filter = MagicMock(return_value=db_session)

    # Call the get_all method
    patient_repository.get_all()

    # Verify filter was called with is_active=True
    db_session.filter.assert_called_once()
    # Extract the filter criteria (varies by ORM implementation)
    filter_args = db_session.filter.call_args[0][0]
    assert "is_active" in str(filter_args), "Should filter by is_active"

def test_audit_logging_on_patient_changes(patient_repository, encryption_service):
    """Test that all patient changes are audit logged."""
    # Arrange
    patient_data = {
        "id": str(uuid.uuid4()),
        "ssn": "123-45-6789",
        "email": "john.doe@example.com"
    }
    patient = Patient(**patient_data)
    
    with patch("app.infrastructure.persistence.sqlalchemy.patient_repository.audit_log") as mock_audit:
        # Act - Create
        patient_repository.create(patient)
        
        # Assert create logged
        mock_audit.log.assert_called_with(ANY, "CREATE", patient.id, ANY)
        
        # Act - Update
        patient.email = "jane.doe@example.com"
        patient_repository.update(patient)
        
        # Assert update logged
        mock_audit.log.assert_called_with(ANY, "UPDATE", patient.id, ANY)
        
        # Act - Delete
        patient_repository.delete(patient.id)
        
        # Assert delete logged
        mock_audit.log.assert_called_with(ANY, "DELETE", patient.id, ANY)

def test_authorization_check_before_operations(patient_repository):
    """Test that authorization is checked before sensitive operations."""
    # Arrange
    patient_data = {
        "id": str(uuid.uuid4()),
        "ssn": "123-45-6789"
    }
    patient = Patient(**patient_data)
    
    with patch.object(patient_repository, "_check_authorization") as mock_auth:
        # Act
        patient_repository.create(patient)
        patient_repository.get_by_id(patient.id)
        patient_repository.update(patient)
        patient_repository.delete(patient.id)
        
        # Assert
        assert mock_auth.call_count == 4, "Authorization should be checked for each operation"

def test_phi_never_appears_in_exceptions(patient_repository, db_session):
    """Test that PHI never appears in exception messages."""
    # Arrange
    patient_id = str(uuid.uuid4())
    db_session.first.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        patient_repository.get_by_id(patient_id)
    assert "123-45-6789" not in str(exc_info.value), "SSN should not appear in exception"
    assert "john.doe" not in str(exc_info.value), "Email should not appear in exception"

def test_bulk_operations_maintain_encryption(patient_repository, encryption_service):
    """Test that bulk operations maintain encryption for all records."""
    # Arrange
    patients_data = [
        {"id": str(uuid.uuid4()), "ssn": "123-45-6789", "email": "john.doe@example.com"},
        {"id": str(uuid.uuid4()), "ssn": "987-65-4321", "email": "jane.doe@example.com"}
    ]
    patients = [Patient(**data) for data in patients_data]
    
    with patch.object(encryption_service, "encrypt", side_effect=lambda x: f"ENC_{x}") as mock_encrypt:
        # Act - Bulk create should encrypt
        patient_repository.bulk_create(patients)
        
        # Assert
        assert mock_encrypt.call_count >= 4, "Expected encryption calls for each PHI field in bulk operation"

def test_search_filters_without_exposing_phi(patient_repository, db_session):
    """Test that search operations filter records without exposing PHI."""
    # Mock query builder
    mock_query = MagicMock()
    db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []

    # Test search by various criteria
    search_criteria = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
    }

    # Execute search
    results = patient_repository.search(search_criteria)

    # Verify filtering was done through safe parameters
    assert mock_query.filter.call_count >= len(search_criteria)

    # Check that we're not logging or exposing criteria directly
    with patch("app.infrastructure.persistence.sqlalchemy.patient_repository.logger") as mock_logger:
        patient_repository.search({"ssn": "123-45-6789"})

        # Verify no SSN in logs
        for call in mock_logger.info.call_args_list:
            log_message = call[0][0]
            assert "123-45-6789" not in log_message, "SSN should not appear in logs"

def test_encryption_key_rotation(encryption_service):
    """Test that encryption key rotation works correctly."""
    # Arrange
    old_key = encryption_service._encryption_key
    data = "sensitive patient data"
    encrypted_data = encryption_service.encrypt(data)
    
    # Act - Rotate key
    encryption_service.rotate_key()
    new_key = encryption_service._encryption_key
    
    # Assert old encrypted data can still be decrypted with new key
    decrypted_data = encryption_service.decrypt(encrypted_data)
    assert decrypted_data == data, "Data encrypted with old key should decrypt with new key"
    assert old_key != new_key, "Key should have been rotated"

def test_field_level_encryption(encryption_service):
    """Test that encryption operates at the field level not record level."""
    # Encrypt multiple fields
    ssn = "123-45-6789"
    email = "patient@example.com"
    phone = "555-123-4567"

    encrypted_ssn = encryption_service.encrypt(ssn)
    encrypted_email = encryption_service.encrypt(email)
    encrypted_phone = encryption_service.encrypt(phone)

    # Verify each field has different encryption
    assert encrypted_ssn != encrypted_email
    assert encrypted_email != encrypted_phone
    assert encrypted_ssn != encrypted_phone

    # Verify we can decrypt each independently
    assert encryption_service.decrypt(encrypted_ssn) == ssn
    assert encryption_service.decrypt(encrypted_email) == email
    assert encryption_service.decrypt(encrypted_phone) == phone
