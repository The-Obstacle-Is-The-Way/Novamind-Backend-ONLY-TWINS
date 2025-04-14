# -*- coding: utf-8 -*-
"""
Tests for the enhanced PHI detector utility.
"""

from app.core.utils.phi_sanitizer import PHIType
import pytest
from unittest.mock import patch, MagicMock

from app.core.utils.enhanced_phi_detector import (
    EnhancedPHIDetector,
    EnhancedPHISanitizer,
    EnhancedPHISecureLogger,
    get_enhanced_phi_secure_logger
)



@pytest.mark.db_required()
class TestEnhancedPHIDetector:
    """Tests for the EnhancedPHIDetector class."""

    def test_contains_phi_with_standard_patterns(self):
        """Test detection of PHI using standard patterns."""
        # Test with email
        assert EnhancedPHIDetector.contains_phi("Contact me at john.doe@example.com")

        # Test with phone number
        assert EnhancedPHIDetector.contains_phi("Call me at 555-123-4567")

        # Test with SSN
        assert EnhancedPHIDetector.contains_phi("SSN: 123-45-6789")

        # Test with date of birth
        assert EnhancedPHIDetector.contains_phi("DOB: 1980-01-01")

        # Test with name
        assert EnhancedPHIDetector.contains_phi("Patient: John Doe")

    def test_contains_phi_with_enhanced_patterns(self):
        """Test detection of PHI using enhanced patterns."""
        # Test with more complex name format
        assert EnhancedPHIDetector.contains_phi("Dr. Smith will see you now")

        # Test with address
        assert EnhancedPHIDetector.contains_phi("Lives at 123 Main Street, Anytown")

        # Test with medical record number
        assert EnhancedPHIDetector.contains_phi("MRN: ABC123456")

        # Test with policy number
        assert EnhancedPHIDetector.contains_phi("Insurance Policy: XYZ987654")

        # Test with alternative date format
        assert EnhancedPHIDetector.contains_phi("Born on Jan 1, 1980")

    def test_contains_phi_with_medical_context(self):
        """Test detection of PHI in medical context."""
        # Test with medical context and potential identifiers
        assert EnhancedPHIDetector.contains_phi(
            "Patient Smith was diagnosed with anxiety and prescribed medication."
        )

        # Test with medical context but no identifiers
        assert not EnhancedPHIDetector.contains_phi(
            "The diagnosis was anxiety and treatment includes medication."
        )

    def test_detect_phi_types(self):
        """Test detection of specific PHI types."""
        # Test with multiple PHI types
        text = "Patient John Doe (DOB: 1980-01-01) with MRN: 12345678 lives at 123 Main St."
        results = EnhancedPHIDetector.detect_phi_types(text)

        # Convert results to a dict for easier testing
        detected_types = {
            phi_type.name.lower(): match for phi_type, match in results
        }

        assert "name" in detected_types
        assert "dob" in detected_types
        assert any(key in ["mrn", "medical_record"] for key in detected_types.keys())
        assert "address" in detected_types

        # Verify specific matches
        assert "John Doe" in detected_types.values()
        assert "1980-01-01" in detected_types.values()
        assert any("MRN: 12345678" in match for match in detected_types.values())
        assert any("123 Main St" in match for match in detected_types.values())

    def test_no_phi_in_regular_text(self):
        """Test that regular text without PHI is not flagged."""
        assert not EnhancedPHIDetector.contains_phi(
            "This is a regular message without any personal health information."
        )


class TestEnhancedPHISanitizer:
    """Tests for the EnhancedPHISanitizer class."""

    def test_sanitize_text(self):
        """Test sanitization of text containing PHI."""
        # Test with multiple PHI types
        text = "Patient John Doe (DOB: 1980-01-01) with MRN: 12345678 lives at 123 Main St."
        sanitized = EnhancedPHISanitizer.sanitize_text(text)

        # Verify PHI has been replaced
        assert "John Doe" not in sanitized
        assert "ANONYMIZED_NAME" in sanitized
        assert "1980-01-01" not in sanitized
        assert "YYYY-MM-DD" in sanitized
        assert "12345678" not in sanitized
        assert "MRN-" in sanitized
        assert "123 Main St" not in sanitized
        assert "ANONYMIZED_ADDRESS" in sanitized

    def test_create_safe_log_message(self):
        """Test creation of safe log messages."""
        # Test with format string and arguments
        message = "Patient {name} (DOB: {dob}) has appointment on {date}"
        args = {"name": "John Doe", "dob": "1980-01-01", "date": "2025-04-01"}

        safe_message = EnhancedPHISanitizer.create_safe_log_message(
            message, **args
        )

        # Verify PHI has been sanitized
        assert "John Doe" not in safe_message
        assert "ANONYMIZED_NAME" in safe_message
        assert "1980-01-01" not in safe_message
        assert "YYYY-MM-DD" in safe_message
        # Non-PHI date should be preserved
        assert "2025-04-01" in safe_message

    def test_sanitize_structured_data(self):
        """Test sanitization of structured data."""
        # Test with nested dictionary
        data = {
            "patient": {
                "name": "John Doe",
                "contact": {
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567"
                },
                "medical_info": {
                    "mrn": "12345678",
                    "diagnosis": "Anxiety"
                }
            },
            "appointment_date": "2025-04-01"
        }

        sanitized = EnhancedPHISanitizer.sanitize_structured_data(data)

        # Verify PHI has been sanitized
        assert sanitized["patient"]["name"] != "John Doe"
        assert "ANONYMIZED_NAME" in sanitized["patient"]["name"]
        assert "john.doe@example.com" not in str(sanitized)
        assert "anonymized.email" in sanitized["patient"]["contact"]["email"]
        assert "555-123-4567" not in str(sanitized)
        assert "555-000-0000" in sanitized["patient"]["contact"]["phone"]
        assert "12345678" not in str(sanitized)
        # Non-PHI should be preserved
        assert sanitized["patient"]["medical_info"]["diagnosis"] == "Anxiety"
        assert sanitized["appointment_date"] == "2025-04-01"


class TestEnhancedPHISecureLogger:
    """Tests for the EnhancedPHISecureLogger class."""

    @patch('logging.Logger.debug')
    def test_debug_log_sanitization(self, mock_debug):
        """Test that debug logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        logger.debug("Patient John Doe (SSN: 123-45-6789) has an appointment")

        # Verify the sanitized message was logged
        mock_debug.assert_called_once()
        logged_message = mock_debug.call_args[0][0]

        assert "John Doe" not in logged_message
        assert "ANONYMIZED_NAME" in logged_message
        assert "123-45-6789" not in logged_message
        assert "000-00-0000" in logged_message

    @patch('logging.Logger.info')
    def test_info_log_sanitization(self, mock_info):

        """Test that info logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        logger.info("Email sent to {email}", email="patient@example.com")

        # Verify the sanitized message was logged
        mock_info.assert_called_once()
        logged_message = mock_info.call_args[0][0]

        assert "patient@example.com" not in logged_message
        assert "anonymized.email" in logged_message

    @patch('logging.Logger.error')
    def test_error_log_sanitization(self, mock_error):
        """Test that error logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        logger.error("Failed to process record for MRN: 12345678")

        # Verify the sanitized message was logged
        mock_error.assert_called_once()
        logged_message = mock_error.call_args[0][0]

        assert "12345678" not in logged_message
        assert "MRN-" in logged_message

    @patch('logging.Logger.exception')
    def test_exception_log_sanitization(self, mock_exception):
        """Test that exception logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        try:
            raise ValueError("Error processing patient John Doe")
        except ValueError:
            logger.exception("Exception occurred")

        # Verify the sanitized message was logged
        mock_exception.assert_called_once()
        # Exception message is handled separately by the logging module
        # We're just checking that our message was sanitized
        assert "Exception occurred" in mock_exception.call_args[0][0]

    def test_get_enhanced_phi_secure_logger(self):
        """Test the factory function for getting a logger."""
        logger = get_enhanced_phi_secure_logger("test_module")
        assert isinstance(logger, EnhancedPHISecureLogger)
        assert logger.logger.name == "test_module"
