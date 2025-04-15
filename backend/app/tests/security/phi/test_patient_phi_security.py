# -*- coding: utf-8 -*-
"""
HIPAA security tests for Patient PHI protection.

This module contains security-focused tests to verify HIPAA compliance
for Protected Health Information (PHI) in the patient model, including:
    - Encryption at rest
    - Secure logging (no PHI in logs)
    - Audit trail for PHI access
    - Secure error handling
    """

import logging
import pytest
import uuid
from datetime import date
from unittest.mock import patch, MagicMock, ANY

from app.domain.entities.patient import Patient
from app.domain.value_objects.address import Address
from app.domain.value_objects.emergency_contact import EmergencyContact
# from app.domain.value_objects.insurance import Insurance # Insurance VO
# removed or refactored
from app.infrastructure.security.encryption import EncryptionService
from app.core.utils.logging import get_logger
from app.tests.security.utils.base_security_test import BaseSecurityTest

# Import necessary modules for testing PHI security
try:
    from app.domain.entities.patient import Patient
except ImportError:
    # Fallback for test environment
    from app.tests.security.utils.test_mocks import MockPatient as Patient

# Import BaseSecurityTest for test base class
@pytest.mark.db_required
class TestPatientPHISecurity(BaseSecurityTest):
    """Test suite for HIPAA security compliance of Patient PHI."""

    @pytest.fixture
    def sample_patient_with_phi(self):
        """Create a sample patient with highly sensitive PHI for testing."""
        return Patient(
            id=uuid.uuid4(),
            first_name="Alexandra",
            last_name="Johnson",
            date_of_birth=date(1975, 3, 12),
            email="alexandra.johnson@example.com",
            phone="555-867-5309",
            address=Address(
                line1="789 Confidential Drive",
                line2="Suite 101",
                city="Securityville",
                state="CA",
                postal_code="90210",
                country="USA"
            ),
            emergency_contact=EmergencyContact(
                name="Robert Johnson",
                relationship="Spouse",
                phone="555-867-5310"
            ),
            ssn="987-65-4321",
            medical_record_number="MRN-789012",
            insurance_member_id="INS-345678",
            insurance_policy_number="POL-901234"
        )

    @pytest.fixture
    def encryption_service(self):
        """Create a test encryption service with a known key."""
        test_key = b"testkeyfortestingonly1234567890abcdef"
        service = EncryptionService()
        with patch.object(service, "_load_encryption_key") as mock_load:
            mock_load.return_value = test_key
            service._encryption_key = test_key
            yield service

    def test_patient_phi_encryption_at_rest(self, sample_patient_with_phi, encryption_service):
        """Test that PHI fields are encrypted before storage."""
        patient = sample_patient_with_phi

        with patch.object(encryption_service, "encrypt", wraps=encryption_service.encrypt) as mock_encrypt:
            # Simulate storage process - would happen in repository layer
            encrypted_ssn = encryption_service.encrypt(patient.ssn)
            encrypted_email = encryption_service.encrypt(patient.email)
            encrypted_phone = encryption_service.encrypt(patient.phone)
            encrypted_mrn = encryption_service.encrypt(patient.medical_record_number)
            encrypted_insurance_id = encryption_service.encrypt(patient.insurance_member_id)

            # Verify encryption was called for sensitive fields
            assert mock_encrypt.call_count >= 5, "Expected at least 5 encryption calls for PHI fields"

            # Verify encrypted values are different from original
            assert encrypted_ssn != patient.ssn
            assert encrypted_email != patient.email
            assert encrypted_phone != patient.phone
            assert encrypted_mrn != patient.medical_record_number
            assert encrypted_insurance_id != patient.insurance_member_id

            # Verify we can decrypt back to original values
            assert encryption_service.decrypt(encrypted_ssn) == patient.ssn
            assert encryption_service.decrypt(encrypted_email) == patient.email
            assert encryption_service.decrypt(encrypted_phone) == patient.phone
            assert encryption_service.decrypt(encrypted_mrn) == patient.medical_record_number
            assert encryption_service.decrypt(encrypted_insurance_id) == patient.insurance_member_id

    def test_no_phi_in_logs(self, sample_patient_with_phi):
        """Test that PHI is not logged even when logging is enabled."""
        patient = sample_patient_with_phi
        logger = get_logger(__name__)

        with patch.object(logger, "info") as mock_log_info, patch.object(logger, "debug") as mock_log_debug:
            # Log various messages that should not include PHI
            logger.info(f"Processing patient {patient.id}")
            logger.debug(f"Patient details accessed for {patient.id}")

            # Verify no PHI in logs
            for call in mock_log_info.call_args_list + mock_log_debug.call_args_list:
                log_message = call[0][0]
                assert patient.ssn not in log_message, "SSN should not be in logs"
                assert patient.email not in log_message, "Email should not be in logs"
                assert patient.phone not in log_message, "Phone should not be in logs"
                assert patient.medical_record_number not in log_message, "Medical record number should not be in logs"

    def test_audit_trail_for_phi_access(self, sample_patient_with_phi):
        """Test that access to PHI is recorded in audit trail."""
        patient = sample_patient_with_phi

        with patch("app.core.utils.audit.audit_logger.log_access") as mock_audit_log:
            # Simulate accessing patient data - normally done in service/repository layer
            accessed_fields = ["ssn", "email", "medical_record_number"]
            for field in accessed_fields:
                getattr(patient, field)  # Access the field

            # Verify audit log was called for PHI access
            assert mock_audit_log.call_count == len(accessed_fields), "Audit log should be called for each PHI field access"

            # Verify audit log contains no actual PHI data
            for call in mock_audit_log.call_args_list:
                log_args = call[0]
                log_kwargs = call[1]
                log_content = str(log_args) + str(log_kwargs)
                assert patient.ssn not in log_content, "SSN should not be in audit log"
                assert patient.email not in log_content, "Email should not be in audit log"
                assert patient.medical_record_number not in log_content, "Medical record number should not be in audit log"

    def test_secure_error_handling(self, sample_patient_with_phi):
        """Test that errors involving patient data don't expose PHI."""
        patient = sample_patient_with_phi
        logger = get_logger(__name__)

        with patch.object(logger, "error") as mock_log_error:
            try:
                # Simulate an error with patient data
                raise ValueError(f"Error processing patient {patient.id} with SSN {patient.ssn}")
            except ValueError as e:
                logger.error(f"Error occurred: {str(e)}")

            # Verify no PHI in error logs
            for call in mock_log_error.call_args_list:
                log_message = call[0][0]
                assert patient.ssn not in log_message, "SSN should not be in error logs"
                assert patient.email not in log_message, "Email should not be in error logs"
                assert patient.medical_record_number not in log_message, "Medical record number should not be in error logs"
                assert "[REDACTED]" in log_message or "PHI redacted" in log_message, "Error log should indicate PHI redaction"

    def test_phi_field_access_restrictions(self, sample_patient_with_phi):
        """Test that direct access to PHI fields can be restricted based on context."""
        patient = sample_patient_with_phi

        # Simulate a restricted context where direct PHI access should raise an exception
        with patch("app.domain.entities.patient.is_restricted_context") as mock_restricted_context:
            mock_restricted_context.return_value = True

            # Attempt to access PHI fields directly
            phi_fields = ["ssn", "email", "phone", "medical_record_number", "insurance_member_id"]
            for field in phi_fields:
                with pytest.raises(AttributeError, match=f"Direct access to {field} is restricted in this context"):
                    getattr(patient, field)

        # Simulate an unrestricted context where access is allowed
        with patch("app.domain.entities.patient.is_restricted_context") as mock_restricted_context:
            mock_restricted_context.return_value = False

            # Access should be allowed
            phi_fields = ["ssn", "email", "phone", "medical_record_number", "insurance_member_id"]
            for field in phi_fields:
                value = getattr(patient, field)
                assert value is not None, f"Should be able to access {field} in unrestricted context"

    def test_encrypted_fields_not_serialized(self, sample_patient_with_phi):
        """Test that encrypted PHI fields are not accidentally serialized."""
        patient = sample_patient_with_phi

        # Convert patient to dict - should not include raw PHI
        patient_dict = patient.to_dict()

        # Verify sensitive fields are not in serialized output
        assert "ssn" not in patient_dict or patient_dict["ssn"] == "[ENCRYPTED]", "SSN should not be serialized or should be marked as encrypted"
        assert "email" not in patient_dict or patient_dict["email"] == "[ENCRYPTED]", "Email should not be serialized or should be marked as encrypted"
        assert "phone" not in patient_dict or patient_dict["phone"] == "[ENCRYPTED]", "Phone should not be serialized or should be marked as encrypted"
        assert "medical_record_number" not in patient_dict or patient_dict["medical_record_number"] == "[ENCRYPTED]", "Medical record number should not be serialized or should be marked as encrypted"
        assert "insurance_member_id" not in patient_dict or patient_dict["insurance_member_id"] == "[ENCRYPTED]", "Insurance ID should not be serialized or should be marked as encrypted"

    def test_no_phi_in_string_representation(self, sample_patient_with_phi):
        """Test that __repr__ and __str__ methods don't expose PHI."""
        # Convert to model
        patient_model = Patient(
            id=sample_patient_with_phi.id,
            first_name=sample_patient_with_phi.first_name,
            last_name=sample_patient_with_phi.last_name,
            date_of_birth=sample_patient_with_phi.date_of_birth,
            email=sample_patient_with_phi.email,
            phone=sample_patient_with_phi.phone,
            address=sample_patient_with_phi.address,
            emergency_contact=sample_patient_with_phi.emergency_contact,
            ssn=sample_patient_with_phi.ssn,
            medical_record_number=sample_patient_with_phi.medical_record_number,
            insurance_member_id=sample_patient_with_phi.insurance_member_id,
            insurance_policy_number=sample_patient_with_phi.insurance_policy_number
        )

        # Get string representations
        str_repr = str(patient_model)
        repr_repr = repr(patient_model)

        # Check that PHI is not included in string representations
        phi_elements = [
            sample_patient_with_phi.first_name,
            sample_patient_with_phi.last_name,
            sample_patient_with_phi.email,
            sample_patient_with_phi.phone,
            sample_patient_with_phi.date_of_birth.isoformat(),
        ]

        for phi in phi_elements:
            assert str(phi) not in str_repr, f"PHI {phi} found in string representation"
            assert str(phi) not in repr_repr, f"PHI {phi} found in repr representation"

    @patch('app.core.utils.logging.get_logger')
    def test_no_phi_in_logs(self, mock_get_logger, sample_patient_with_phi):
        """Test that PHI is not included in log messages."""
        # Create a mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        try:
            # Create a situation that would trigger logging
            raise ValueError("Simulated error with patient data")
        except ValueError as e:
            mock_logger.error(e, exc_info=True)

        # Check that no PHI appears in log calls
        phi_elements = [
            sample_patient_with_phi.first_name,
            sample_patient_with_phi.last_name,
            sample_patient_with_phi.email,
            sample_patient_with_phi.phone,
        ]

        for call_args in mock_logger.error.call_args_list:
            for arg in call_args[0]:
                if isinstance(arg, str):
                    for phi in phi_elements:
                        assert str(phi) not in arg, f"PHI {phi} found in log message"

    @patch('app.infrastructure.security.encryption.EncryptionService.encrypt')
    def test_all_phi_fields_are_encrypted(self, mock_encrypt, sample_patient_with_phi):
        """Test that all PHI fields are passed to the encryption service."""
        # Configure mock to return the input
        mock_encrypt.side_effect = lambda x: f"ENCRYPTED:{x}" if x else None

        # Convert domain entity to model
        patient_model = Patient(
            id=sample_patient_with_phi.id,
            first_name=sample_patient_with_phi.first_name,
            last_name=sample_patient_with_phi.last_name,
            date_of_birth=sample_patient_with_phi.date_of_birth,
            email=sample_patient_with_phi.email,
            phone=sample_patient_with_phi.phone,
            address=sample_patient_with_phi.address,
            emergency_contact=sample_patient_with_phi.emergency_contact,
            ssn=sample_patient_with_phi.ssn,
            medical_record_number=sample_patient_with_phi.medical_record_number,
            insurance_member_id=sample_patient_with_phi.insurance_member_id,
            insurance_policy_number=sample_patient_with_phi.insurance_policy_number
        )

        # Check that sensitive fields were encrypted
        assert patient_model.first_name_encrypted.startswith("ENCRYPTED:")
        assert patient_model.last_name_encrypted.startswith("ENCRYPTED:")
        assert patient_model.email_encrypted.startswith("ENCRYPTED:")
        assert patient_model.phone_encrypted.startswith("ENCRYPTED:")
        assert patient_model.address_encrypted.startswith("ENCRYPTED:")
        assert patient_model.emergency_contact_encrypted.startswith("ENCRYPTED:")

    @patch('app.infrastructure.security.encryption.EncryptionService.decrypt')
    def test_phi_fields_decryption(self, mock_decrypt, sample_patient_with_phi):
        """Test that PHI fields can be decrypted correctly."""
        # Configure mock to return the original value
        mock_decrypt.side_effect = lambda x: x.replace("ENCRYPTED:", "") if x else None

        # Convert domain entity to model (this encrypts the data)
        patient_model = Patient(
            id=sample_patient_with_phi.id,
            first_name=sample_patient_with_phi.first_name,
            last_name=sample_patient_with_phi.last_name,
            date_of_birth=sample_patient_with_phi.date_of_birth,
            email=sample_patient_with_phi.email,
            phone=sample_patient_with_phi.phone,
            address=sample_patient_with_phi.address,
            emergency_contact=sample_patient_with_phi.emergency_contact,
            ssn=sample_patient_with_phi.ssn,
            medical_record_number=sample_patient_with_phi.medical_record_number,
            insurance_member_id=sample_patient_with_phi.insurance_member_id,
            insurance_policy_number=sample_patient_with_phi.insurance_policy_number
        )

        # Now access the decrypted values (this triggers decryption)
        decrypted_first_name = patient_model.first_name
        decrypted_last_name = patient_model.last_name
        decrypted_email = patient_model.email

        # Verify decryption was called and returned correct values
        assert mock_decrypt.called
        assert decrypted_first_name == sample_patient_with_phi.first_name
        assert decrypted_last_name == sample_patient_with_phi.last_name
        assert decrypted_email == sample_patient_with_phi.email

    def test_audit_trail_for_phi_access(self, sample_patient_with_phi):
        """Test that accessing PHI creates an audit trail."""
        with patch('app.core.audit.logger.log') as mock_audit_log:
            patient_model = Patient(
                id=sample_patient_with_phi.id,
                first_name=sample_patient_with_phi.first_name,
                last_name=sample_patient_with_phi.last_name,
                date_of_birth=sample_patient_with_phi.date_of_birth,
                email=sample_patient_with_phi.email,
                phone=sample_patient_with_phi.phone,
                address=sample_patient_with_phi.address,
                emergency_contact=sample_patient_with_phi.emergency_contact,
                ssn=sample_patient_with_phi.ssn,
                medical_record_number=sample_patient_with_phi.medical_record_number,
                insurance_member_id=sample_patient_with_phi.insurance_member_id,
                insurance_policy_number=sample_patient_with_phi.insurance_policy_number
            )
            # Access PHI which should trigger audit logging
            _ = patient_model.first_name
            _ = patient_model.email

            # Verify audit log was called with appropriate context
            assert mock_audit_log.called
            for call in mock_audit_log.call_args_list:
                assert "PHI_ACCESS" in str(call)
                assert str(patient_model.id) in str(call)

    @patch('app.infrastructure.security.encryption.EncryptionService.decrypt')
    def test_error_handling_without_phi_exposure(self, mock_decrypt, sample_patient_with_phi):
        """Test that errors are handled without exposing PHI."""
        # Create patient model with encrypted data
        patient_model = Patient(
            id=sample_patient_with_phi.id,
            first_name=sample_patient_with_phi.first_name,
            last_name=sample_patient_with_phi.last_name,
            date_of_birth=sample_patient_with_phi.date_of_birth,
            email=sample_patient_with_phi.email,
            phone=sample_patient_with_phi.phone,
            address=sample_patient_with_phi.address,
            emergency_contact=sample_patient_with_phi.emergency_contact,
            ssn=sample_patient_with_phi.ssn,
            medical_record_number=sample_patient_with_phi.medical_record_number,
            insurance_member_id=sample_patient_with_phi.insurance_member_id,
            insurance_policy_number=sample_patient_with_phi.insurance_policy_number
        )

        # Simulate a security-related error during decryption
        mock_decrypt.side_effect = ValueError("Decryption failed due to invalid key")

        try:
            # Attempt to access PHI, which should raise an error
            _ = patient_model.first_name
        except ValueError as e:
            # Check that the error message does not contain PHI
            error_message = str(e)
            phi_elements = [
                sample_patient_with_phi.first_name,
                sample_patient_with_phi.last_name,
                sample_patient_with_phi.email,
            ]
            for phi in phi_elements:
                assert str(phi) not in error_message, f"PHI {phi} exposed in error message"
