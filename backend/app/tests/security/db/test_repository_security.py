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
    return PatientRepository(db_session, encryption_service)

@pytest.mark.db_required()
def test_patient_creation_encrypts_phi(patient_repository, encryption_service):
    """Test that patient creation encrypts PHI fields."""
    # Spy on the encryption service
    with patch.object(encryption_service, "encrypt", wraps=encryption_service.encrypt) as mock_encrypt:
        # Create a test patient with PHI
        patient_id = str(uuid.uuid4())
        patient = Patient(
            id=patient_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            date_of_birth="1980-01-01",
            ssn="123-45-6789",
            address="123 Main St, Anytown, USA",
            medical_record_number="MRN-12345",
            insurance_member_id="INS-67890",
        )

        # Save the patient
        patient_repository.create(patient)

        # Verify encryption was called for PHI fields
        assert mock_encrypt.call_count >= 5, "Expected at least 5 encryption calls for PHI fields"

        # Check specific fields were encrypted
        encrypted_fields = [call.args[0] for call in mock_encrypt.call_args_list]
        assert "123-45-6789" in encrypted_fields, "SSN should be encrypted"
        assert "john.doe@example.com" in encrypted_fields, "Email should be encrypted"
        assert "555-123-4567" in encrypted_fields, "Phone should be encrypted"
        assert "MRN-12345" in encrypted_fields, "Medical record number should be encrypted"
        assert "INS-67890" in encrypted_fields, "Insurance ID should be encrypted"

def test_patient_retrieval_decrypts_phi(patient_repository, encryption_service, db_session):
    """Test that patient retrieval decrypts PHI fields."""
    # Create an "encrypted" patient record in the mock DB
    patient_id = str(uuid.uuid4())
    encrypted_ssn = encryption_service.encrypt("123-45-6789")
    encrypted_email = encryption_service.encrypt("john.doe@example.com")

    # Create a mock patient model with encrypted fields
    mock_patient_model = MagicMock()
    mock_patient_model.id = patient_id
    mock_patient_model.first_name = "John"
    mock_patient_model.last_name = "Doe"
    mock_patient_model.email = encrypted_email
    mock_patient_model.ssn = encrypted_ssn
    mock_patient_model.is_active = True

    # Setup mock DB to return our encrypted patient
    db_session.query().filter().first.return_value = mock_patient_model

    # Spy on the decryption service
    with patch.object(encryption_service, "decrypt", wraps=encryption_service.decrypt) as mock_decrypt:
        # Retrieve the patient
        patient = patient_repository.get_by_id(patient_id)

        # Verify decryption was called
        assert mock_decrypt.call_count >= 2, "Expected at least 2 decryption calls"

        # Verify the decrypted values
        assert patient.ssn == "123-45-6789"
        assert patient.email == "john.doe@example.com"

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
    patient_id = str(uuid.uuid4())
    patient = Patient(
        id=patient_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        ssn="123-45-6789",
    )

    # Mock the audit logger
    with patch("app.infrastructure.persistence.sqlalchemy.patient_repository.audit_logger") as mock_logger:
        # Perform operations
        patient_repository.create(patient)
        patient.email = "john.updated@example.com"
        patient_repository.update(patient)
        patient_repository.delete(patient_id)

        # Verify audit logging for each operation
        assert mock_logger.log_create.call_count == 1
        assert mock_logger.log_update.call_count == 1
        assert mock_logger.log_delete.call_count == 1

        # Verify no PHI in audit logs
        for call in mock_logger.log_create.call_args_list:
            log_payload = call[0][1]  # Extract log payload
            assert "123-45-6789" not in json.dumps(log_payload), "SSN should not be in audit log"
            assert "john.doe@example.com" not in json.dumps(log_payload), "Email should not be in audit log"

def test_authorization_check_before_operations(patient_repository):
    """Test that authorization is checked before sensitive operations."""
    patient_id = str(uuid.uuid4())
    patient = Patient(id=patient_id, first_name="John", last_name="Doe")

    # Mock the authorization service
    with patch("app.infrastructure.persistence.sqlalchemy.patient_repository.check_authorization") as mock_auth:
        mock_auth.return_value = True

        # Perform operations
        patient_repository.create(patient)
        patient_repository.get_by_id(patient_id)
        patient_repository.update(patient)
        patient_repository.delete(patient_id)

        # Verify authorization checked for sensitive operations
        assert mock_auth.call_count >= 3, "Authorization should be checked for create, update, delete"

        # Make auth check fail
        mock_auth.return_value = False

        # Operations should raise exceptions
        with pytest.raises(Exception, match="Unauthorized"):
            patient_repository.create(patient)

        with pytest.raises(Exception, match="Unauthorized"):
            patient_repository.update(patient)

        with pytest.raises(Exception, match="Unauthorized"):
            patient_repository.delete(patient_id)

def test_phi_never_appears_in_exceptions(patient_repository, db_session):
    """Test that PHI never appears in exception messages."""
    # Make DB session fail with an exception containing PHI
    error_msg = "Error processing patient John Doe with SSN 123-45-6789"
    db_session.commit.side_effect = Exception(error_msg)

    # Create a patient with PHI
    patient_id = str(uuid.uuid4())
    patient = Patient(id=patient_id, first_name="John", last_name="Doe", ssn="123-45-6789")

    # Attempt to save the patient, which will fail
    with pytest.raises(Exception) as excinfo:
        patient_repository.create(patient)

    # Verify the exception doesn't contain PHI
    exception_str = str(excinfo.value)
    assert "123-45-6789" not in exception_str, "SSN should not appear in exceptions"
    assert "John Doe" not in exception_str, "Patient name should not appear in exceptions"
    assert "[REDACTED]" in exception_str or "PHI redacted" in exception_str, "Exception should indicate PHI redaction"

def test_bulk_operations_maintain_encryption(patient_repository, encryption_service):
    """Test that bulk operations maintain encryption for all records."""
    # Create multiple patients
    patients = [Patient(id=str(uuid.uuid4()), first_name=f"Patient-{i}", ssn=f"123-45-{1000 + i}") for i in range(5)]

    # Spy on encryption
    with patch.object(encryption_service, "encrypt", wraps=encryption_service.encrypt) as mock_encrypt:
        # Perform bulk create
        patient_repository.bulk_create(patients)

        # Each patient should have SSN encrypted
        assert mock_encrypt.call_count >= 5, "All patient SSNs should be encrypted"

        # Check encryption was called for each SSN
        for patient in patients:
            assert any(patient.ssn in call.args for call in mock_encrypt.call_args_list), f"SSN {patient.ssn} should be encrypted"

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
    # Encrypt data with the current key
    original_text = "sensitive patient data"
    encrypted = encryption_service.encrypt(original_text)

    # Simulate key rotation - create a new key
    new_key = b"newtestkeyfortestingonly1234567890ab"
    old_key = encryption_service._encryption_key

    # Setup re-encryption function
    def reencrypt(old_encrypted_value, old_key, new_key):
        # Decrypt with old key
        temp_service = EncryptionService()
        temp_service._encryption_key = old_key
        decrypted = temp_service.decrypt(old_encrypted_value)

        # Encrypt with new key
        temp_service._encryption_key = new_key
        return temp_service.encrypt(decrypted)

    # Re-encrypt the value
    new_encrypted = reencrypt(encrypted, old_key, new_key)

    # Verify the new encrypted value is different
    assert encrypted != new_encrypted

    # Check that we can decrypt with the new key
    encryption_service._encryption_key = new_key
    decrypted = encryption_service.decrypt(new_encrypted)
    assert decrypted == original_text

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
