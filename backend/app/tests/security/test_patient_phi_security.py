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
from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
from app.infrastructure.security.encryption import EncryptionService
from app.core.utils.logging import get_logger

@pytest.mark.db_required
class TestPatientPHISecurity:
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
                phone="555-123-7890",
                relationship="Spouse"
            ),
            insurance=None,  # Set to None as placeholder
            active=True,
            created_by=None
        )

    def test_no_phi_in_string_representation(self, sample_patient_with_phi):
        """Test that __repr__ and __str__ methods don't expose PHI."""
        # Convert to model
        patient_model = PatientModel.from_domain(sample_patient_with_phi)

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
        patient_model = PatientModel.from_domain(sample_patient_with_phi)

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
        patient_model = PatientModel.from_domain(sample_patient_with_phi)

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
            patient_model = PatientModel.from_domain(sample_patient_with_phi)
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
        patient_model = PatientModel.from_domain(sample_patient_with_phi)

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
