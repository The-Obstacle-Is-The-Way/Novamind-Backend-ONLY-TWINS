# -*- coding: utf-8 -*-
"""
Tests for the enhanced PHI detector utility.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.utils.enhanced_phi_detector import (
    EnhancedPHIDetector,
    EnhancedPHISanitizer,
    EnhancedPHISecureLogger,
    get_enhanced_phi_secure_logger,
)
from app.core.utils.phi_sanitizer import PHIType


class TestEnhancedPHIDetector:
    """Tests for the EnhancedPHIDetector class."""

    @pytest.mark.standalone()
    def test_contains_phi_with_standard_patterns(self):
        """Test detection of PHI using standard patterns."""
        # Test with SSN
        text = "Patient SSN: 123-45-6789"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with email
        text = "Contact: patient@example.com"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with phone number
        text = "Call at (123) 456-7890"
        assert EnhancedPHIDetector.contains_phi(text) is True

    @pytest.mark.standalone()
    def test_contains_phi_with_enhanced_patterns(self):
        """Test detection of PHI using enhanced patterns."""
        # Test with MRN
        text = "MRN: 12345678"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with patient name
        text = "Patient Name: John Doe"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with address
        text = "123 Main St, Apt 4, Springfield, IL 62701"
        assert EnhancedPHIDetector.contains_phi(text) is True

    @pytest.mark.standalone()
    def test_contains_phi_with_medical_context(self):
        """Test detection of PHI in medical context."""
        # Test with medical record context
        text = "Dr. Smith reviewed the chart for John Doe"
        assert EnhancedPHIDetector.contains_phi(text) is True

        # Test with diagnosis context
        text = "Patient diagnosed with condition ABC on 2025-04-01"
        assert EnhancedPHIDetector.contains_phi(text) is True

    @pytest.mark.standalone()
    def test_contains_phi_negative_cases(self):
        """Test cases that should not be detected as PHI."""
        # Test with general medical terms
        text = "The treatment protocol includes medication and therapy"
        assert EnhancedPHIDetector.contains_phi(text) is False

        # Test with non-specific dates
        text = "Follow-up in 30 days"
        assert EnhancedPHIDetector.contains_phi(text) is False

        # Test with anonymous references
        text = "The patient reported improvement"
        assert EnhancedPHIDetector.contains_phi(text) is False

    @pytest.mark.standalone()
    def test_detect_phi_types(self):
        """Test detection of specific PHI types."""
        # Test with multiple PHI types
        text = "Patient John Doe (SSN: 123-45-6789) lives at 123 Main St"
        phi_types = EnhancedPHIDetector.detect_phi_types(text)
        
        assert PHIType.NAME in phi_types
        assert PHIType.SSN in phi_types
        assert PHIType.ADDRESS in phi_types

    @pytest.mark.standalone()
    def test_detect_phi_types_with_context(self):
        """Test detection of PHI types with context."""
        # Test with medical context
        text = "Dr. Smith saw patient on 2025-04-01 for follow-up"
        phi_types = EnhancedPHIDetector.detect_phi_types(text)
        
        assert PHIType.NAME in phi_types
        assert PHIType.DATE in phi_types

    @pytest.mark.standalone()
    def test_detect_phi_locations(self):
        """Test detection of PHI locations in text."""
        text = "Patient John Doe (SSN: 123-45-6789)"
        locations = EnhancedPHIDetector.detect_phi_locations(text)
        
        # Should have at least 2 locations (name and SSN)
        assert len(locations) >= 2
        
        # Check structure of location data
        for location in locations:
            assert "start" in location
            assert "end" in location
            assert "type" in location
            assert "value" in location


class TestEnhancedPHISanitizer:
    """Tests for the EnhancedPHISanitizer class."""

    @pytest.mark.standalone()
    def test_sanitize_text_with_standard_phi(self):
        """Test sanitization of text with standard PHI."""
        # Test with SSN
        text = "Patient SSN: 123-45-6789"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        assert "123-45-6789" not in sanitized
        assert "SSN-" in sanitized

        # Test with email
        text = "Contact: patient@example.com"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        assert "patient@example.com" not in sanitized
        assert "anonymized.email" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_text_with_enhanced_phi(self):
        """Test sanitization of text with enhanced PHI patterns."""
        # Test with MRN
        text = "MRN: 12345678"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        assert "12345678" not in sanitized
        assert "MRN-" in sanitized

        # Test with patient name
        text = "Patient Name: John Doe"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        assert "John Doe" not in sanitized
        assert "[REDACTED NAME]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_text_with_medical_context(self):
        """Test sanitization of text with medical context."""
        # Test with medical record context
        text = "Dr. Smith reviewed the chart for John Doe"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        assert "Dr. Smith" not in sanitized
        assert "John Doe" not in sanitized
        assert "[REDACTED NAME]" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_text_preserves_non_phi(self):
        """Test that non-PHI content is preserved during sanitization."""
        text = "The treatment includes 20mg of medication twice daily"
        sanitized = EnhancedPHISanitizer.sanitize_text(text)
        assert sanitized == text  # Should be unchanged

    @pytest.mark.standalone()
    def test_sanitize_text_with_custom_replacement(self):
        """Test sanitization with custom replacement patterns."""
        text = "Patient SSN: 123-45-6789"
        sanitized = EnhancedPHISanitizer.sanitize_text(
            text, 
            replacements={PHIType.SSN: "XXX-XX-XXXX"}
        )
        assert "123-45-6789" not in sanitized
        assert "XXX-XX-XXXX" in sanitized

    @pytest.mark.standalone()
    def test_sanitize_json_with_phi(self):
        """Test sanitization of JSON data containing PHI."""
        data = {
            "patient": {
                "name": "John Doe",
                "contact": {
                    "email": "patient@example.com",
                    "phone": "123-456-7890"
                },
                "medical_info": {
                    "diagnosis": "Condition ABC",
                    "treatment": "Medication XYZ"
                }
            }
        }
        
        sanitized = EnhancedPHISanitizer.sanitize_json(data)
        
        # Check that PHI is sanitized
        assert sanitized["patient"]["name"] != "John Doe"
        assert sanitized["patient"]["contact"]["email"] != "patient@example.com"
        assert sanitized["patient"]["contact"]["phone"] != "123-456-7890"
        
        # Check that non-PHI is preserved
        assert sanitized["patient"]["medical_info"]["diagnosis"] == "Condition ABC"
        assert sanitized["patient"]["medical_info"]["treatment"] == "Medication XYZ"


class TestEnhancedPHISecureLogger:
    """Tests for the EnhancedPHISecureLogger class."""

    @patch("logging.Logger.debug")
    @pytest.mark.standalone()
    def test_debug_log_sanitization(self, mock_debug):
        """Test that debug logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        logger.debug("Processing record for SSN: 123-45-6789")

        # Verify the sanitized message was logged
        mock_debug.assert_called_once()
        logged_message = mock_debug.call_args[0][0]

        assert "123-45-6789" not in logged_message
        assert "SSN-" in logged_message

    @patch("logging.Logger.info")
    @pytest.mark.standalone()
    def test_info_log_sanitization(self, mock_info):
        """Test that info logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        logger.info("Email sent to {email}", email="patient@example.com")

        # Verify the sanitized message was logged
        mock_info.assert_called_once()
        logged_message = mock_info.call_args[0][0]

        assert "patient@example.com" not in logged_message
        assert "anonymized.email" in logged_message

    @patch("logging.Logger.error")
    @pytest.mark.standalone()
    def test_error_log_sanitization(self, mock_error):
        """Test that error logs are sanitized."""
        logger = EnhancedPHISecureLogger("test_logger")
        logger.error("Failed to process record for MRN: 12345678")

        # Verify the sanitized message was logged
        mock_error.assert_called_once()
        logged_message = mock_error.call_args[0][0]

        assert "12345678" not in logged_message
        assert "MRN-" in logged_message

    @patch("logging.Logger.exception")
    @pytest.mark.standalone()
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

    @pytest.mark.standalone()
    def test_get_enhanced_phi_secure_logger(self):
        """Test the factory function for getting a logger."""
        logger = get_enhanced_phi_secure_logger("test_module")
        assert isinstance(logger, EnhancedPHISecureLogger)
        assert logger.logger.name == "test_module"