"""
Tests for PHI sanitization functionality.

This module tests the PHI (Protected Health Information) detection 
and sanitization capabilities of the Novamind Digital Twin Platform,
ensuring HIPAA compliance for all data handling processes.
"""
import pytest
from unittest.mock import MagicMock

from app.tests.security.base_test import BaseSecurityTest
from app.core.security.phi_sanitizer import PHISanitizer


@pytest.mark.db_required
class TestPHISanitization(BaseSecurityTest):
    """Tests for PHI detection and sanitization functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method execution."""
        super().setUp()
        self.sanitizer = PHISanitizer()
        
    @pytest.mark.db_required
def test_sanitize_text_with_names(self):
        """Test that patient names are properly sanitized."""
        # Test text with common name patterns
        text = "Patient John Smith reported symptoms."
        sanitized = self.sanitizer.sanitize(text)
        
        # Verify name is replaced with [REDACTED]
        self.assertNotIn("John Smith", sanitized)
        self.assertIn("[REDACTED]", sanitized)
        self.assertIn("Patient", sanitized)
        self.assertIn("reported symptoms", sanitized)
        
    @pytest.mark.db_required
def test_sanitize_text_with_phone_numbers(self):
        """Test that phone numbers are properly sanitized."""
        # Test various phone number formats
        formats = [
            "Phone: 555-123-4567",
            "Call at (555) 123-4567",
            "5551234567 is the contact number"
        ]
        
        for text in formats:
            sanitized = self.sanitizer.sanitize(text)
            self.assertNotIn("555", sanitized)
            self.assertNotIn("123", sanitized)
            self.assertNotIn("4567", sanitized)
            self.assertIn("[REDACTED]", sanitized)
            
    @pytest.mark.db_required
def test_sanitize_text_with_dates(self):
        """Test that dates are properly sanitized."""
        # Test various date formats
        formats = [
            "DOB: 01/15/1980",
            "Born on January 15, 1980",
            "Date of birth: 1980-01-15"
        ]
        
        for text in formats:
            sanitized = self.sanitizer.sanitize(text)
            self.assertNotIn("1980", sanitized)
            self.assertNotIn("01/15", sanitized)
            self.assertNotIn("January 15", sanitized)
            self.assertNotIn("1980-01-15", sanitized)
            self.assertIn("[REDACTED]", sanitized)
            
    @pytest.mark.db_required
def test_sanitize_text_with_ssn(self):
        """Test that Social Security Numbers are properly sanitized."""
        # Test various SSN formats
        formats = [
            "SSN: 123-45-6789",
            "Social Security: 123456789",
            "SSN 123-45-6789 is on file"
        ]
        
        for text in formats:
            sanitized = self.sanitizer.sanitize(text)
            self.assertNotIn("123-45-6789", sanitized)
            self.assertNotIn("123456789", sanitized)
            self.assertIn("[REDACTED]", sanitized)
            
    @pytest.mark.db_required
def test_sanitize_text_with_addresses(self):
        """Test that addresses are properly sanitized."""
        # Test address formats
        text = "Lives at 123 Main St, Apt 4B, New York, NY 10001"
        sanitized = self.sanitizer.sanitize(text)
        
        self.assertNotIn("123 Main St", sanitized)
        self.assertNotIn("Apt 4B", sanitized)
        self.assertNotIn("10001", sanitized)
        self.assertIn("[REDACTED]", sanitized)
        
    @pytest.mark.db_required
def test_sanitize_medical_record_numbers(self):
        """Test that medical record numbers are properly sanitized."""
        # Test MRN formats
        formats = [
            "MRN: MR12345",
            "Medical Record #: 12345-A",
            "Record Number MR-12345-B is on file"
        ]
        
        for text in formats:
            sanitized = self.sanitizer.sanitize(text)
            self.assertNotIn("MR12345", sanitized)
            self.assertNotIn("12345-A", sanitized)
            self.assertNotIn("MR-12345-B", sanitized)
            self.assertIn("[REDACTED]", sanitized)
            
    @pytest.mark.db_required
def test_sanitize_nested_dictionary(self):
        """Test that PHI in nested dictionary structures is properly sanitized."""
        # Test dictionary with nested PHI
        data = {
            "patient": {
                "name": "John Smith",
                "contact": {
                    "phone": "555-123-4567",
                    "email": "john.smith@example.com"
                },
                "dateOfBirth": "1980-01-15",
                "notes": "Patient reports symptoms"
            },
            "visit": {
                "date": "2023-05-15",
                "provider": "Dr. Jane Doe",
                "location": "Main Clinic"
            }
        }
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Check that PHI is sanitized but other data is preserved
        self.assertNotIn("John Smith", str(sanitized))
        self.assertNotIn("555-123-4567", str(sanitized))
        self.assertNotIn("1980-01-15", str(sanitized))
        self.assertIn("[REDACTED]", str(sanitized))
        self.assertIn("Patient reports symptoms", str(sanitized))
        self.assertIn("Main Clinic", str(sanitized))
        
    @pytest.mark.db_required
def test_sanitize_list_data(self):
        """Test that PHI in list structures is properly sanitized."""
        # Test list with PHI
        data = [
            "Patient: John Smith",
            "Phone: 555-123-4567",
            "DOB: 1980-01-15",
            "Notes: Patient reports symptoms"
        ]
        
        sanitized = self.sanitizer.sanitize(data)
        
        # Check that PHI is sanitized but other data is preserved
        self.assertNotIn("John Smith", str(sanitized))
        self.assertNotIn("555-123-4567", str(sanitized))
        self.assertNotIn("1980-01-15", str(sanitized))
        self.assertIn("[REDACTED]", str(sanitized))
        self.assertIn("Patient reports symptoms", str(sanitized))
        
    @pytest.mark.db_required
def test_audit_logging_on_phi_detection(self):
        """Test that PHI detection is properly audit logged."""
        # Replace the sanitizer's logger with our mock
        original_logger = self.sanitizer._logger
        self.sanitizer._logger = self.mock_audit_logger
        
        try:
            # Sanitize text with PHI
            text = "Patient John Smith (DOB: 1980-01-15)"
            self.sanitizer.sanitize(text)
            
            # Verify that PHI detection was logged
            self.mock_audit_logger.log_phi_detection.assert_called()
            
            # Verify log contains the right information
            args, kwargs = self.mock_audit_logger.log_phi_detection.call_args
            self.assertEqual(kwargs.get('user_id'), self.test_user_id)
            self.assertIn('text_length', kwargs.get('details', {}))
            self.assertIn('detected_types', kwargs.get('details', {}))
            
        finally:
            # Restore the original logger
            self.sanitizer._logger = original_logger
            
    @pytest.mark.db_required
def test_no_false_positives(self):
        """Test that non-PHI text is not incorrectly sanitized."""
        # Test text without PHI
        text = "The patient reported feeling better after treatment. Follow-up in 2 weeks."
        sanitized = self.sanitizer.sanitize(text)
        
        # The text should remain unchanged
        self.assertEqual(text, sanitized)