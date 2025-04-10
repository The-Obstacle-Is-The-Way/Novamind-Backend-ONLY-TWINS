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
# from app.domain.value_objects.insurance import Insurance # Insurance VO removed or refactored
from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
from app.infrastructure.security.encryption import EncryptionService
from app.core.utils.logging import get_logger


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
            # insurance=Insurance( # Insurance VO removed or refactored
            #     provider="PremiumHealth Inc",
            #     policy_number="HIPAA-12345",
            #     group_number="PHI-6789"
            # ),
            insurance=None, # Set to None as placeholder
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
            patient_model = PatientModel.from_domain(sample_patient_with_phi)
            
            # Trigger an error that would normally log PHI
            # We'll simulate a decryption error
            with patch.object(EncryptionService, 'decrypt', side_effect=Exception("Decryption error")):
                # This should trigger error logging
                patient_model.to_domain()
        except Exception:
            pass  # We expect an exception
        
        # Check that log messages were captured
        assert mock_logger.error.called or mock_logger.exception.called
        
        # Check all captured log messages for PHI
        all_calls = mock_logger.method_calls
        for call in all_calls:
            log_message = str(call)
            phi_elements = [
                sample_patient_with_phi.first_name,
                sample_patient_with_phi.last_name,
                sample_patient_with_phi.email,
                sample_patient_with_phi.phone,
                str(sample_patient_with_phi.date_of_birth),
                sample_patient_with_phi.address.line1 if sample_patient_with_phi.address else "",
                # sample_patient_with_phi.insurance.policy_number if sample_patient_with_phi.insurance else "", # Insurance VO removed
            ]
            
            for phi in phi_elements:
                assert str(phi) not in log_message, f"PHI '{phi}' found in log message: {log_message}"
    
    @patch('app.infrastructure.security.encryption.EncryptionService.encrypt')
    def test_all_phi_fields_are_encrypted(self, mock_encrypt, sample_patient_with_phi):
        """Test that all PHI fields are passed to the encryption service."""
        # Configure mock to return the input
        mock_encrypt.side_effect = lambda x: f"ENCRYPTED:{x}" if x else None
        
        # Convert domain entity to model
        PatientModel.from_domain(sample_patient_with_phi)
        
        # Verify all PHI fields were encrypted
        expected_encrypted_fields = [
            sample_patient_with_phi.first_name,
            sample_patient_with_phi.last_name,
            sample_patient_with_phi.date_of_birth.isoformat(),
            sample_patient_with_phi.email,
            sample_patient_with_phi.phone,
            sample_patient_with_phi.address.line1,
            sample_patient_with_phi.address.line2,
            sample_patient_with_phi.address.city,
            sample_patient_with_phi.address.state,
            sample_patient_with_phi.address.postal_code,
            sample_patient_with_phi.address.country,
            sample_patient_with_phi.emergency_contact.name,
            sample_patient_with_phi.emergency_contact.phone,
            sample_patient_with_phi.emergency_contact.relationship,
            # sample_patient_with_phi.insurance.provider, # Insurance VO removed
            # sample_patient_with_phi.insurance.policy_number,
            # sample_patient_with_phi.insurance.group_number,
        ]
        
        # Remove None values
        expected_encrypted_fields = [f for f in expected_encrypted_fields if f is not None]
        
        # Assert that encrypt was called for each field
        assert mock_encrypt.call_count >= len(expected_encrypted_fields)
        
        # Check each field was encrypted
        for field in expected_encrypted_fields:
            mock_encrypt.assert_any_call(field)
    
    @patch('app.infrastructure.security.audit.AuditLogger.log_data_access')
    def test_phi_access_is_audited(self, mock_log_data_access, sample_patient_with_phi):
        """Test that PHI access generates appropriate audit logs."""
        from app.infrastructure.security.audit import AuditLogger
        
        # Set up the audit context
        with patch('app.infrastructure.security.audit.get_current_user_id', return_value=uuid.uuid4()):
            # Create a patient model
            patient_model = PatientModel.from_domain(sample_patient_with_phi)
            
            # Access PHI data by converting back to domain
            with patch.object(EncryptionService, 'decrypt', side_effect=lambda x: x[9:] if x and x.startswith("ENCRYPTED:") else None):
                patient_model.to_domain()
        
        # Verify audit logging was called for PHI access
        assert mock_log_data_access.called
        
        # Verify the audit log contains patient ID but not the actual PHI
        mock_log_data_access.assert_any_call(
            resource_type="Patient",
            resource_id=ANY,  # The patient ID
            action_type="read",
            details=ANY
        )
        
        # Check that the audit log details don't contain PHI
        for call in mock_log_data_access.call_args_list:
            details = call[1].get('details', '')
            phi_elements = [
                sample_patient_with_phi.first_name,
                sample_patient_with_phi.last_name,
                sample_patient_with_phi.email,
                sample_patient_with_phi.phone,
                str(sample_patient_with_phi.date_of_birth),
            ]
            
            for phi in phi_elements:
                assert str(phi) not in str(details), f"PHI '{phi}' found in audit log details"
    
    def test_error_handling_without_phi_exposure(self, sample_patient_with_phi):
        """Test that errors are handled without exposing PHI."""
        # Create patient model with encrypted data
        patient_model = PatientModel.from_domain(sample_patient_with_phi)
        
        # Simulate a security-related error during decryption
        with patch.object(EncryptionService, 'decrypt', side_effect=Exception("Security error")):
            # Capture exception details to check for PHI
            try:
                patient_model.to_domain()
                assert False, "Exception should have been raised"
            except Exception as e:
                error_message = str(e)
                
                # Verify error message doesn't contain PHI
                phi_elements = [
                    sample_patient_with_phi.first_name,
                    sample_patient_with_phi.last_name,
                    sample_patient_with_phi.email,
                    sample_patient_with_phi.phone,
                    str(sample_patient_with_phi.date_of_birth),
                    sample_patient_with_phi.address.line1 if sample_patient_with_phi.address else "",
                ]
                
                for phi in phi_elements:
                    assert str(phi) not in error_message, f"PHI '{phi}' found in error message: {error_message}"